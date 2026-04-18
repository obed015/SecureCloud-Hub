import base64
import datetime
import json
import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

logger = logging.getLogger(__name__)


def parse_easy_auth_principal(req: func.HttpRequest) -> dict:
    principal_header = req.headers.get("X-MS-CLIENT-PRINCIPAL")
    if not principal_header:
        return {}

    try:
        decoded = base64.b64decode(principal_header).decode("utf-8")
        principal = json.loads(decoded)
        claims = {c["typ"]: c["val"] for c in principal.get("claims", [])}
        return {
            "user_id": claims.get(
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                claims.get("preferred_username", "unknown"),
            ).lower(),
            "name": claims.get("name", "unknown"),
        }
    except Exception as exc:
        logger.warning("Failed to parse Easy Auth principal: %s", str(exc))
        return {}


def is_valid_filename(filename: str) -> bool:
    if not filename:
        return False
    if "/" in filename or "\\" in filename or ".." in filename:
        return False
    return True


def main(req: func.HttpRequest) -> func.HttpResponse:
    principal = parse_easy_auth_principal(req)
    user_id = principal.get("user_id", "unknown")

    if user_id == "unknown":
        logger.warning("Missing or invalid authenticated user.")
        return func.HttpResponse("Unauthorized.", status_code=401)

    file_name = req.params.get("fileName")
    if not file_name:
        logger.warning("Missing fileName. user=%s", user_id)
        return func.HttpResponse("fileName query parameter is required.", status_code=400)

    if not is_valid_filename(file_name):
        logger.warning("Rejected invalid fileName. user=%s file=%s", user_id, file_name)
        return func.HttpResponse("Invalid file name.", status_code=400)

    storage_url = os.environ["STORAGE_ACCOUNT_URL"]
    safe_container = os.environ["SAFE_CONTAINER"]

    # Build the real blob path using the authenticated user namespace
    blob_name = f"{user_id}/{file_name}"

    credential = DefaultAzureCredential()
    blob_service = BlobServiceClient(account_url=storage_url, credential=credential)
    blob_client = blob_service.get_blob_client(container=safe_container, blob=blob_name)

    try:
        properties = blob_client.get_blob_properties()
    except Exception:
        logger.warning("Blob not found. user=%s file=%s blob=%s", user_id, file_name, blob_name)
        return func.HttpResponse("File not found.", status_code=404)

    metadata = properties.metadata or {}
    scan_status = metadata.get("scanstatus", metadata.get("scanStatus", "unknown"))

    if scan_status != "clean":
        logger.warning(
            "Denied SAS issuance. user=%s file=%s blob=%s scan_status=%s",
            user_id,
            file_name,
            blob_name,
            scan_status,
        )
        return func.HttpResponse("File is not available for download.", status_code=403)

    now = datetime.datetime.now(datetime.timezone.utc)
    expiry = now + datetime.timedelta(minutes=15)

    delegation_key = blob_service.get_user_delegation_key(
        key_start_time=now,
        key_expiry_time=expiry,
    )

    account_name = storage_url.split("//", 1)[1].split(".", 1)[0]

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=safe_container,
        blob_name=blob_name,
        user_delegation_key=delegation_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
    )

    sas_url = f"{storage_url}/{safe_container}/{blob_name}?{sas_token}"

    logger.info(
        "Issued SAS. user=%s file=%s blob=%s expiry=%s",
        user_id,
        file_name,
        blob_name,
        expiry.isoformat(),
    )
    return func.HttpResponse(sas_url, status_code=200)