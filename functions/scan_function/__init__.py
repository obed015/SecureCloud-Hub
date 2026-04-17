import logging
import os
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def scan_content(content: bytes) -> tuple[bool, str]:
    if EICAR_SIGNATURE in content:
        return False, "EICAR test signature detected"
    return True, "clean"


def parse_blob_url(blob_url: str) -> tuple[str, str]:
    if not blob_url:
        raise ValueError("Event payload did not include blob URL")

    parsed = urlparse(blob_url)

    if not parsed.netloc.endswith(".blob.core.windows.net"):
        raise ValueError(f"Unexpected blob host in URL: {blob_url}")

    path = parsed.path.lstrip("/")
    parts = path.split("/", 1)

    if len(parts) != 2:
        raise ValueError(f"Unable to parse container/blob from URL: {blob_url}")

    source_container = parts[0]
    blob_name = unquote(parts[1])

    return source_container, blob_name


def main(event: func.EventGridEvent) -> None:
    event_data = event.get_json()
    blob_url = event_data.get("url", "")
    event_id = getattr(event, "id", "unknown")

    logger.info("Scan triggered. event_id=%s blob_url=%s", event_id, blob_url)

    incoming_container = get_required_env("INCOMING_CONTAINER")
    safe_container = get_required_env("SAFE_CONTAINER")
    quarantine_container = get_required_env("QUARANTINE_CONTAINER")
    storage_url = get_required_env("STORAGE_ACCOUNT_URL")

    source_container, blob_name = parse_blob_url(blob_url)

    logger.info(
        "Parsed event payload. event_id=%s source_container=%s blob_name=%s",
        event_id,
        source_container,
        blob_name,
    )

    if source_container != incoming_container:
        logger.warning(
            "Ignoring blob outside incoming container. event_id=%s source_container=%s expected_container=%s blob_name=%s",
            event_id,
            source_container,
            incoming_container,
            blob_name,
        )
        return

    credential = DefaultAzureCredential()
    blob_service = BlobServiceClient(account_url=storage_url, credential=credential)

    source_client = blob_service.get_blob_client(container=incoming_container, blob=blob_name)

    logger.info(
        "Attempting blob download. event_id=%s container=%s blob=%s",
        event_id,
        incoming_container,
        blob_name,
    )

    content = source_client.download_blob().readall()

    logger.info(
        "Blob downloaded successfully. event_id=%s blob=%s bytes=%s",
        event_id,
        blob_name,
        len(content),
    )

    is_clean, reason = scan_content(content)
    destination_container = safe_container if is_clean else quarantine_container
    scan_status = "clean" if is_clean else "infected"

    logger.info(
        "Scan completed. event_id=%s blob=%s scan_status=%s reason=%s destination=%s",
        event_id,
        blob_name,
        scan_status,
        reason,
        destination_container,
    )

    destination_client = blob_service.get_blob_client(
        container=destination_container,
        blob=blob_name,
    )

    metadata = {
        "scanStatus": scan_status,
        "scanReason": reason,
        "scannedAtUtc": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Uploading scanned blob. event_id=%s blob=%s destination=%s metadata=%s",
        event_id,
        blob_name,
        destination_container,
        metadata,
    )

    destination_client.upload_blob(
        content,
        overwrite=True,
        metadata=metadata,
    )

    logger.info(
        "Uploaded scanned blob successfully. event_id=%s blob=%s destination=%s",
        event_id,
        blob_name,
        destination_container,
    )

    source_client.delete_blob()

    logger.info(
        "Deleted original blob from incoming container. event_id=%s blob=%s",
        event_id,
        blob_name,
    )