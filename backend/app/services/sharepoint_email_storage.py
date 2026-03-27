"""SharePoint email storage service."""
import base64
import json
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

from config import settings
from app.schemas.schemas import ReceivedEmailSaveRequest
from app.services.microsoft_graph import MicrosoftGraphClient, MicrosoftGraphConfigurationError, MicrosoftGraphRequestError


class SharePointConfigurationError(RuntimeError):
    """Raised when SharePoint storage settings are incomplete."""


class SharePointUploadError(RuntimeError):
    """Raised when an upload to SharePoint fails."""


class SharePointEmailStorageService:
    """Stores inbound email payloads in SharePoint via Microsoft Graph."""

    def __init__(self):
        self.site_id = settings.SHAREPOINT_SITE_ID
        self.drive_id = settings.SHAREPOINT_DRIVE_ID
        self.default_folder = settings.SHAREPOINT_EMAIL_FOLDER
        self.graph_client = MicrosoftGraphClient()

    def is_configured(self) -> bool:
        """Return whether required SharePoint settings exist."""
        required_values = [
            self.site_id,
            self.drive_id,
        ]
        return self.graph_client.is_configured() and all(bool(value) for value in required_values)

    def _ensure_configured(self) -> None:
        if self.is_configured():
            return

        raise SharePointConfigurationError(
            "SharePoint email storage is not configured. "
            "Set MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, "
            "SHAREPOINT_SITE_ID, and SHAREPOINT_DRIVE_ID."
        )

    async def save_email(self, email: ReceivedEmailSaveRequest) -> dict:
        """Save email metadata and optional MIME content to SharePoint."""
        self._ensure_configured()

        folder = self._normalize_folder(email.sharepoint_folder or self.default_folder)
        token = await self.graph_client.get_access_token()
        storage_time = datetime.now(timezone.utc)
        base_name = self._build_file_stem(email)

        metadata_payload = {
            "message_id": email.message_id,
            "internet_message_id": email.internet_message_id,
            "subject": email.subject,
            "from_address": str(email.from_address),
            "to_addresses": [str(address) for address in email.to_addresses],
            "cc_addresses": [str(address) for address in email.cc_addresses],
            "received_at": email.received_at.isoformat(),
            "body_text": email.body_text,
            "body_html": email.body_html,
            "attachments": [attachment.model_dump() for attachment in email.attachments],
            "metadata": email.metadata,
            "stored_at": storage_time.isoformat(),
        }

        metadata_bytes = json.dumps(metadata_payload, ensure_ascii=False, indent=2).encode("utf-8")
        metadata_file = await self._upload_bytes(
            token=token,
            folder=folder,
            file_name=f"{base_name}.json",
            content=metadata_bytes,
            content_type="application/json; charset=utf-8",
        )

        mime_file = None
        if email.raw_mime_base64:
            try:
                mime_bytes = base64.b64decode(email.raw_mime_base64, validate=True)
            except ValueError as exc:
                raise SharePointUploadError("raw_mime_base64 is not valid base64 data.") from exc

            mime_file = await self._upload_bytes(
                token=token,
                folder=folder,
                file_name=f"{base_name}.eml",
                content=mime_bytes,
                content_type="message/rfc822",
            )

        return {
            "stored_at": storage_time,
            "message_id": email.message_id,
            "subject": email.subject,
            "sharepoint_folder": folder,
            "metadata_file": metadata_file,
            "mime_file": mime_file,
        }

    async def _upload_bytes(
        self,
        token: str,
        folder: str,
        file_name: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        relative_path = f"{folder}/{file_name}" if folder else file_name
        encoded_path = quote(relative_path, safe="/")
        upload_url = (
            f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}"
            f"/root:/{encoded_path}:/content"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
        }

        try:
            response = await self.graph_client.request(
                method="PUT",
                url=upload_url,
                token=token,
                headers=headers,
                content=content,
                timeout=60.0,
            )
        except (MicrosoftGraphConfigurationError, MicrosoftGraphRequestError) as exc:
            raise SharePointUploadError(f"Failed to upload {file_name} to SharePoint.") from exc

        payload = response.json()
        return {
            "item_id": payload["id"],
            "name": payload["name"],
            "path": relative_path,
            "web_url": payload.get("webUrl"),
        }

    def _build_file_stem(self, email: ReceivedEmailSaveRequest) -> str:
        received_at = email.received_at.astimezone(timezone.utc)
        timestamp = received_at.strftime("%Y%m%dT%H%M%SZ")
        subject = self._slugify(email.subject)
        message_id = self._slugify(email.message_id)
        return f"{timestamp}_{subject}_{message_id}"[:180]

    def _normalize_folder(self, folder: Optional[str]) -> str:
        if not folder:
            return ""
        normalized = folder.strip().strip("/")
        normalized = re.sub(r"/{2,}", "/", normalized)
        return normalized

    def _slugify(self, value: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
        sanitized = sanitized.strip("-._")
        return sanitized[:80] or "email"