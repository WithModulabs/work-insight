"""Microsoft Graph mail subscription and webhook ingestion service."""
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional

from config import settings
from app.schemas.schemas import (
    EmailAttachmentMetadata,
    GraphSubscriptionCreateRequest,
    ReceivedEmailSaveRequest,
)
from app.services.microsoft_graph import (
    MicrosoftGraphClient,
    MicrosoftGraphRequestError,
)
from app.services.sharepoint_email_storage import SharePointEmailStorageService, SharePointUploadError


class GraphWebhookConfigurationError(RuntimeError):
    """Raised when webhook subscription settings are incomplete."""


class GraphWebhookProcessingError(RuntimeError):
    """Raised when notification processing fails."""


class GraphEmailIngestionService:
    """Handles Graph subscriptions and converts messages into SharePoint storage requests."""

    def __init__(self):
        self.graph_client = MicrosoftGraphClient()
        self.storage_service = SharePointEmailStorageService()
        self.default_mailbox_user_id = settings.GRAPH_MAILBOX_USER_ID
        self.default_notification_url = settings.GRAPH_NOTIFICATION_URL
        self.default_client_state = settings.GRAPH_SUBSCRIPTION_CLIENT_STATE
        self.default_resource = settings.GRAPH_SUBSCRIPTION_RESOURCE
        self.default_expiration_minutes = settings.GRAPH_SUBSCRIPTION_EXPIRATION_MINUTES

    def get_status(self) -> dict:
        return {
            "graph_configured": self.graph_client.is_configured(),
            "mailbox_user_id": self.default_mailbox_user_id,
            "notification_url": self.default_notification_url,
            "has_client_state": bool(self.default_client_state),
            "sharepoint_ready": self.storage_service.is_configured(),
        }

    async def create_subscription(self, request: GraphSubscriptionCreateRequest) -> dict:
        mailbox_user_id = request.mailbox_user_id or self.default_mailbox_user_id
        notification_url = request.notification_url or self.default_notification_url
        client_state = request.client_state or self.default_client_state or None
        resource = request.resource or self.default_resource or self._build_default_resource(mailbox_user_id)
        expiration_minutes = request.expiration_minutes or self.default_expiration_minutes

        if not mailbox_user_id:
            raise GraphWebhookConfigurationError("GRAPH_MAILBOX_USER_ID or mailbox_user_id is required.")
        if not notification_url:
            raise GraphWebhookConfigurationError("GRAPH_NOTIFICATION_URL or notification_url is required.")

        try:
            token = await self.graph_client.get_access_token()
        except MicrosoftGraphRequestError as exc:
            raise GraphWebhookProcessingError("Failed to acquire Graph token for subscription creation.") from exc

        expiration = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)

        payload = {
            "changeType": "created",
            "notificationUrl": notification_url,
            "resource": resource,
            "expirationDateTime": expiration.isoformat().replace("+00:00", "Z"),
        }
        if client_state:
            payload["clientState"] = client_state

        try:
            response = await self.graph_client.request(
                method="POST",
                url="https://graph.microsoft.com/v1.0/subscriptions",
                token=token,
                json=payload,
            )
        except MicrosoftGraphRequestError as exc:
            raise GraphWebhookProcessingError("Failed to create Microsoft Graph subscription.") from exc

        body = response.json()
        return {
            "id": body["id"],
            "resource": body["resource"],
            "expiration_date_time": self._parse_datetime(body["expirationDateTime"]),
            "client_state": body.get("clientState"),
            "notification_url": body["notificationUrl"],
        }

    async def process_notification(self, notification: dict, sharepoint_folder: Optional[str] = None) -> dict:
        if not self._is_valid_client_state(notification.get("clientState")):
            raise GraphWebhookProcessingError("Invalid Graph clientState received.")

        resource = notification.get("resource", "")
        mailbox_user_id, message_id = self._parse_resource(resource)
        if not mailbox_user_id or not message_id:
            raise GraphWebhookProcessingError(f"Unsupported Graph resource format: {resource}")

        try:
            token = await self.graph_client.get_access_token()
            message = await self._get_message(token, mailbox_user_id, message_id)
            mime_base64 = await self._get_message_mime_base64(token, mailbox_user_id, message_id)
            attachments = await self._get_attachment_metadata(token, mailbox_user_id, message_id)
        except MicrosoftGraphRequestError as exc:
            raise GraphWebhookProcessingError("Failed to retrieve message details from Microsoft Graph.") from exc

        request = ReceivedEmailSaveRequest(
            message_id=message["id"],
            internet_message_id=message.get("internetMessageId"),
            subject=message.get("subject") or "(no subject)",
            from_address=self._extract_email_address(message.get("from")),
            to_addresses=self._extract_recipients(message.get("toRecipients", [])),
            cc_addresses=self._extract_recipients(message.get("ccRecipients", [])),
            received_at=self._parse_datetime(message["receivedDateTime"]),
            body_text=message.get("bodyPreview"),
            body_html=(message.get("body") or {}).get("content"),
            raw_mime_base64=mime_base64,
            attachments=attachments,
            metadata={
                "source": "microsoft-graph-webhook",
                "subscription_id": notification.get("subscriptionId"),
                "change_type": notification.get("changeType"),
                "resource": resource,
                "tenant_id": notification.get("tenantId"),
            },
            sharepoint_folder=sharepoint_folder,
        )

        try:
            return await self.storage_service.save_email(request)
        except SharePointUploadError as exc:
            raise GraphWebhookProcessingError("Failed to persist email to SharePoint.") from exc

    def _build_default_resource(self, mailbox_user_id: str) -> str:
        return f"users/{mailbox_user_id}/mailFolders('Inbox')/messages"

    def _is_valid_client_state(self, client_state: Optional[str]) -> bool:
        if not self.default_client_state:
            return True
        return client_state == self.default_client_state

    def _parse_resource(self, resource: str) -> tuple[Optional[str], Optional[str]]:
        parts = resource.split("/")
        if len(parts) >= 4 and parts[0] == "users" and parts[-2] == "messages":
            return parts[1], parts[-1]
        return None, None

    async def _get_message(self, token: str, mailbox_user_id: str, message_id: str) -> dict:
        url = (
            f"https://graph.microsoft.com/v1.0/users/{mailbox_user_id}/messages/{message_id}"
            "?$select=id,internetMessageId,subject,receivedDateTime,body,bodyPreview,from,toRecipients,ccRecipients"
        )
        response = await self.graph_client.request("GET", url, token=token)
        return response.json()

    async def _get_message_mime_base64(self, token: str, mailbox_user_id: str, message_id: str) -> str:
        url = f"https://graph.microsoft.com/v1.0/users/{mailbox_user_id}/messages/{message_id}/$value"
        response = await self.graph_client.request("GET", url, token=token, timeout=60.0)
        return base64.b64encode(response.content).decode("ascii")

    async def _get_attachment_metadata(self, token: str, mailbox_user_id: str, message_id: str) -> list[EmailAttachmentMetadata]:
        url = (
            f"https://graph.microsoft.com/v1.0/users/{mailbox_user_id}/messages/{message_id}/attachments"
            "?$select=name,contentType,size"
        )

        try:
            response = await self.graph_client.request("GET", url, token=token)
        except MicrosoftGraphRequestError:
            return []

        payload = response.json()
        attachments = []
        for item in payload.get("value", []):
            attachments.append(
                EmailAttachmentMetadata(
                    file_name=item.get("name") or "attachment",
                    content_type=item.get("contentType"),
                    size_bytes=item.get("size"),
                )
            )
        return attachments

    def _extract_email_address(self, sender: Optional[dict]) -> str:
        address = ((sender or {}).get("emailAddress") or {}).get("address")
        if not address:
            raise GraphWebhookProcessingError("Graph message does not contain sender email address.")
        return address

    def _extract_recipients(self, recipients: list[dict]) -> list[str]:
        addresses = []
        for recipient in recipients:
            address = (recipient.get("emailAddress") or {}).get("address")
            if address:
                addresses.append(address)
        return addresses

    def _parse_datetime(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)