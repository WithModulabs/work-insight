"""API Router - SharePoint email storage."""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.schemas.schemas import (
    GraphSubscriptionCreateRequest,
    GraphSubscriptionResponse,
    GraphWebhookAcceptedResponse,
    GraphWebhookPayload,
    ReceivedEmailSaveRequest,
    ReceivedEmailSaveResponse,
)
from app.services.graph_email_ingestion import (
    GraphEmailIngestionService,
    GraphWebhookConfigurationError,
    GraphWebhookProcessingError,
)
from app.services.sharepoint_email_storage import (
    SharePointConfigurationError,
    SharePointEmailStorageService,
    SharePointUploadError,
)

router = APIRouter()
sharepoint_email_storage = SharePointEmailStorageService()
graph_email_ingestion = GraphEmailIngestionService()


@router.get("/sharepoint/status", response_model=dict)
async def get_sharepoint_storage_status():
    """Return whether SharePoint email storage is configured."""
    return {
        "configured": sharepoint_email_storage.is_configured(),
        "default_folder": sharepoint_email_storage.default_folder,
        "graph": graph_email_ingestion.get_status(),
    }


@router.post("/sharepoint/store", response_model=ReceivedEmailSaveResponse)
async def store_email_in_sharepoint(request: ReceivedEmailSaveRequest):
    """Store a received email as an item in SharePoint RawWorkReports list."""
    try:
        return await sharepoint_email_storage.save_email(request)
    except SharePointConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SharePointUploadError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/graph/subscriptions", response_model=GraphSubscriptionResponse)
async def create_graph_mail_subscription(request: GraphSubscriptionCreateRequest):
    """Create a Microsoft Graph subscription for inbound messages."""
    try:
        return await graph_email_ingestion.create_subscription(request)
    except GraphWebhookConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (GraphWebhookProcessingError, SharePointUploadError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/graph/webhook", response_model=GraphWebhookAcceptedResponse)
async def receive_graph_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    validationToken: str | None = Query(default=None),
):
    """Accept Graph webhook validation and message notifications."""
    if validationToken:
        return PlainTextResponse(content=validationToken, media_type="text/plain")

    raw_payload = await request.json()
    payload = GraphWebhookPayload.model_validate(raw_payload)

    for notification in payload.value:
        background_tasks.add_task(
            _process_graph_notification,
            notification.model_dump(),
        )

    return {
        "accepted": True,
        "notification_count": len(payload.value),
    }


async def _process_graph_notification(notification: dict) -> None:
    try:
        await graph_email_ingestion.process_notification(notification)
    except (GraphWebhookConfigurationError, GraphWebhookProcessingError, SharePointUploadError):
        return