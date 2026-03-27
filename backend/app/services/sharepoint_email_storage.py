"""SharePoint list email storage service."""
import json
from datetime import datetime, timezone

from config import settings
from app.schemas.schemas import ReceivedEmailSaveRequest
from app.services.microsoft_graph import MicrosoftGraphClient, MicrosoftGraphConfigurationError, MicrosoftGraphRequestError


class SharePointConfigurationError(RuntimeError):
    """Raised when SharePoint storage settings are incomplete."""


class SharePointUploadError(RuntimeError):
    """Raised when an item insert to SharePoint list fails."""


class SharePointEmailStorageService:
    """Stores inbound email as list items in SharePoint via Microsoft Graph."""

    def __init__(self):
        self.site_id = settings.SHAREPOINT_SITE_ID
        self.list_id = settings.SHAREPOINT_LIST_ID
        self.graph_client = MicrosoftGraphClient()

    def is_configured(self) -> bool:
        """Return whether required SharePoint settings exist."""
        required_values = [
            self.site_id,
            self.list_id,
        ]
        return self.graph_client.is_configured() and all(bool(value) for value in required_values)

    def _ensure_configured(self) -> None:
        if self.is_configured():
            return

        raise SharePointConfigurationError(
            "SharePoint email storage is not configured. "
            "Set MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, "
            "SHAREPOINT_SITE_ID, and SHAREPOINT_LIST_ID."
        )

    async def save_email(self, email: ReceivedEmailSaveRequest) -> dict:
        """Save email as a list item in SharePoint RawWorkReports list."""
        self._ensure_configured()

        storage_time = datetime.now(timezone.utc)

        # Map payload to existing RawWorkReports internal column names.
        fields = {
            "Title": self._build_title(email),
            "Sender": str(email.from_address),
            "ReportContent": email.body_text or email.body_html or "",
            "ReceivedTime": email.received_at.isoformat(),
            "AISummary": json.dumps(
                {
                    "message_id": email.message_id,
                    "subject": email.subject,
                    "to_addresses": [str(addr) for addr in email.to_addresses],
                    "cc_addresses": [str(addr) for addr in email.cc_addresses],
                    "attachments": [att.model_dump() for att in email.attachments],
                    "metadata": email.metadata,
                    "stored_at": storage_time.isoformat(),
                },
                ensure_ascii=False,
            ),
        }

        # Create list item via Graph API
        return await self._create_list_item(fields, storage_time, email)

    async def _create_list_item(
        self,
        fields: dict,
        storage_time: datetime,
        email: ReceivedEmailSaveRequest,
    ) -> dict:
        """Insert item into SharePoint list."""
        token = await self.graph_client.get_access_token()
        url = (
            f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/lists/{self.list_id}/items"
        )

        payload = {
            "fields": fields,
        }

        try:
            response = await self.graph_client.request(
                method="POST",
                url=url,
                token=token,
                json=payload,
                timeout=30.0,
            )
        except (MicrosoftGraphConfigurationError, MicrosoftGraphRequestError) as exc:
            raise SharePointUploadError(f"Failed to insert email item to SharePoint list.") from exc

        response_data = response.json()
        
        return {
            "stored_at": storage_time,
            "message_id": email.message_id,
            "subject": email.subject,
            "list_item_id": response_data.get("id"),
            "list_item_url": response_data.get("webUrl"),
            "field_count": len(fields),
        }

    def _build_title(self, email: ReceivedEmailSaveRequest) -> str:
        """Build list item Title from email subject and timestamp."""
        timestamp = email.received_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        subject = email.subject.replace("\r", "").replace("\n", " ")[:100]
        return f"[{timestamp}] {subject}"[:255]  # SharePoint Title max 255 chars