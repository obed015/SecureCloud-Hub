import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def scan_content(content: bytes) -> tuple[bool, str]:
    if EICAR_SIGNATURE in content:
        return False, "EICAR test signature detected"
    return True, "clean"


def main(event: func.EventGridEvent) -> None:
    event_data = event.get_json()
    blob_url = event_data.get("url", "")

    logger.info("Scan triggered. blob_url=%s", blob_url)

    try:
        _, path = blob_url.split(".blob.core.windows.net/", 1)
        source_container, blob_name = path.split("/", 1)
    except (ValueError, AttributeError) as exc:
        logger.error("Failed to parse blob URL. blob_url=%s error=%s", blob_url, str(exc))
        return

    incoming_container = os.environ["INCOMING_CONTAINER"]
    safe_container = os.environ["SAFE_CONTAINER"]
    quarantine_container = os.environ["QUARANTINE_CONTAINER"]
    storage_url = os.environ["STORAGE_ACCOUNT_URL"]

    if source_container != incoming_container:
        logger.info("Ignoring blob outside incoming container. container=%s", source_container)
        return

    credential = DefaultAzureCredential()
    blob_service = BlobServiceClient(account_url=storage_url, credential=credential)

    source_client = blob_service.get_blob_client(container=incoming_container, blob=blob_name)

    try:
        content = source_client.download_blob().readall()
    except Exception as exc:
        logger.error("Failed to download blob. blob=%s error=%s", blob_name, str(exc))
        return

    is_clean, reason = scan_content(content)
    destination_container = safe_container if is_clean else quarantine_container
    scan_status = "clean" if is_clean else "infected"

    destination_client = blob_service.get_blob_client(
        container=destination_container,
        blob=blob_name,
    )

    try:
        destination_client.upload_blob(
            content,
            overwrite=True,
            metadata={"scanStatus": scan_status},
        )
        logger.info(
            "Uploaded scanned blob. blob=%s destination=%s scan_status=%s reason=%s",
            blob_name,
            destination_container,
            scan_status,
            reason,
        )
    except Exception as exc:
        logger.error("Failed to upload scanned blob. blob=%s error=%s", blob_name, str(exc))
        return

    try:
        source_client.delete_blob()
        logger.info("Deleted original blob from incoming container. blob=%s", blob_name)
    except Exception as exc:
        logger.error("Failed to delete original blob. blob=%s error=%s", blob_name, str(exc))
