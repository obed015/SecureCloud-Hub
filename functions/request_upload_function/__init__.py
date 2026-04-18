import base64
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    generate_blob_sas,
)

logger = logging.getLogger(__name__)

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".ps1",
    ".msi", ".vbs", ".js", ".jar"
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def sanitise_filename(filename: str) -> str:
    filename = filename.replace("/", "").replace("\\", "").replace("..", "")
    filename = filename.lstrip(".").strip()
    return filename or f"upload-{uuid.uuid4()}"


def get_user_id(req: func.HttpRequest) -> str:
    principal = req.headers.get("X-MS-CLIENT-PRINCIPAL")
    if not principal:
        raise PermissionError("Missing Easy Auth principal header")

    try:
        decoded = base64.b64decode(principal).decode("utf-8")
        principal_data = json.loads(decoded)
        claims = {
            c["typ"]: c["val"]
            for c in principal_data.get("claims", [])
        }

        user_id = claims.get(
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
        ) or claims.get(
            "preferred_username"
        ) or claims.get(
            "name"
        )

        if not user_id:
            raise PermissionError("Unable to determine authenticated user")

        return user_id.lower()
    except Exception as exc:
        raise PermissionError(f"Failed to parse Easy Auth identity: {exc}") from exc


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        user_id = get_user_id(req)

        body = req.get_json()
        original_file_name = sanitise_filename(body.get("fileName", ""))
        content_type = body.get("contentType", "application/octet-stream")
        file_size = int(body.get("fileSize", 0))

        if not original_file_name:
            return func.HttpResponse(
                json.dumps({"error": "fileName is required"}),
                status_code=400,
                mimetype="application/json"
            )

        if file_size <= 0:
            return func.HttpResponse(
                json.dumps({"error": "fileSize must be greater than 0"}),
                status_code=400,
                mimetype="application/json"
            )

        if file_size > MAX_FILE_SIZE:
            return func.HttpResponse(
                json.dumps({"error": "File exceeds 50MB limit"}),
                status_code=400,
                mimetype="application/json"
            )

        _, ext = os.path.splitext(original_file_name)
        if ext.lower() in BLOCKED_EXTENSIONS:
            return func.HttpResponse(
                json.dumps({"error": f"File type '{ext}' is not permitted"}),
                status_code=400,
                mimetype="application/json"
            )

        storage_account_name = get_required_env("STORAGE_ACCOUNT_NAME")
        incoming_container = get_required_env("INCOMING_CONTAINER")
        upload_sas_expiry_minutes = int(os.environ.get("UPLOAD_SAS_EXPIRY_MINUTES", "10"))

        blob_name = f"{user_id}/{original_file_name}"

        credential = DefaultAzureCredential()
        blob_service = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=credential,
        )

        starts_on = datetime.now(timezone.utc) - timedelta(minutes=1)
        expires_on = datetime.now(timezone.utc) + timedelta(minutes=upload_sas_expiry_minutes)

        delegation_key = blob_service.get_user_delegation_key(
            key_start_time=starts_on,
            key_expiry_time=expires_on,
        )

        sas_token = generate_blob_sas(
            account_name=storage_account_name,
            container_name=incoming_container,
            blob_name=blob_name,
            user_delegation_key=delegation_key,
            permission=BlobSasPermissions(create=True, write=True),
            expiry=expires_on,
            start=starts_on,
            protocol="https",
            content_type=content_type,
        )

        encoded_blob_name = quote(blob_name, safe="/")
        upload_url = (
            f"https://{storage_account_name}.blob.core.windows.net/"
            f"{incoming_container}/{encoded_blob_name}?{sas_token}"
        )

        logger.info(
            "Issued upload SAS. user=%s blob_name=%s expires=%s content_type=%s file_size=%s",
            user_id,
            blob_name,
            expires_on.isoformat(),
            content_type,
            file_size,
        )

        return func.HttpResponse(
            json.dumps({
                "uploadUrl": upload_url,
                "blobName": blob_name,
                "expiresOnUtc": expires_on.isoformat(),
                "maxFileSize": MAX_FILE_SIZE
            }),
            status_code=200,
            mimetype="application/json"
        )

    except PermissionError as exc:
        logger.warning("Unauthorized upload SAS request: %s", str(exc))
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json"
        )
    except Exception as exc:
        logger.exception("Failed to issue upload SAS: %s", str(exc))
        return func.HttpResponse(
            json.dumps({"error": "Failed to issue upload URL"}),
            status_code=500,
            mimetype="application/json"
        )
