"""Shared Microsoft Graph client helpers."""
from typing import Any, Optional

import httpx

from config import settings


class MicrosoftGraphConfigurationError(RuntimeError):
    """Raised when Microsoft Graph configuration is incomplete."""


class MicrosoftGraphRequestError(RuntimeError):
    """Raised when a Microsoft Graph request fails."""


class MicrosoftGraphClient:
    """Small helper for Graph token acquisition and HTTP requests."""

    def __init__(self):
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET

    def is_configured(self) -> bool:
        return all([self.tenant_id, self.client_id, self.client_secret])

    def ensure_configured(self) -> None:
        if self.is_configured():
            return

        raise MicrosoftGraphConfigurationError(
            "Microsoft Graph is not configured. "
            "Set MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_ID, and MICROSOFT_CLIENT_SECRET."
        )

    async def get_access_token(self) -> str:
        self.ensure_configured()

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(token_url, data=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MicrosoftGraphRequestError("Failed to acquire Microsoft Graph access token.") from exc

        return response.json()["access_token"]

    async def request(
        self,
        method: str,
        url: str,
        token: str,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> httpx.Response:
        merged_headers = {"Authorization": f"Bearer {token}"}
        if headers:
            merged_headers.update(headers)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, headers=merged_headers, **kwargs)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MicrosoftGraphRequestError(f"Graph request failed: {method} {url}") from exc

        return response