import base64
import json
import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def get_user_id(req: func.HttpRequest) -> str:
    principal = req.headers.get("X-MS-CLIENT-PRINCIPAL")
    if not principal:
        raise PermissionError("Missing Easy Auth principal header")

    decoded = base64.b64decode(principal).decode("utf-8")
    principal_data = json.loads(decoded)
    claims = {
        c["typ"]: c["val"]
        for c in principal_data.get("claims", [])
    }

    user_id = claims.get(
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    ) or claims.get("preferred_username") or claims.get("name")

    if not user_id:
        raise PermissionError("Unable to determine authenticated user")

    return user_id.lower()


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        user_id = get_user_id(req)

        storage_account_name = get_required_env("STORAGE_ACCOUNT_NAME")
        safe_container = get_required_env("SAFE_CONTAINER")

        credential = DefaultAzureCredential()
        blob_service = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=credential,
        )
        container_client = blob_service.get_container_client(safe_container)

        files = []

        blobs = container_client.list_blobs(
            name_starts_with=f"{user_id}/",
            include=["metadata"]
        )

        for blob in blobs:
            metadata = blob.metadata or {}
            if metadata.get("scanStatus") != "clean":
                continue

            display_name = blob.name.replace(f"{user_id}/", "", 1)

            files.append({
                "name": display_name,
                "fullName": blob.name,
                "size": blob.size,
                "lastModified": blob.last_modified.isoformat() if blob.last_modified else None,
                "scanStatus": metadata.get("scanStatus"),
                "scanReason": metadata.get("scanReason"),
                "scannedAtUtc": metadata.get("scannedAtUtc"),
            })

        logger.info("Listed files. user=%s count=%s", user_id, len(files))

        return func.HttpResponse(
            json.dumps({"files": files, "user": user_id}),
            status_code=200,
            mimetype="application/json"
        )

    except PermissionError:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json"
        )
    except Exception as exc:
        logger.exception("Failed to list files: %s", str(exc))
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve file list"}),
            status_code=500,
            mimetype="application/json"
        )
