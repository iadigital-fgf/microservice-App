import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from fgf_service.core.config import settings

load_dotenv()

logger = logging.getLogger(__name__)


class FinnegansClient:
    """Cliente base async para todas las APIs de Finnegans."""

    def __init__(self) -> None:
        self.base_url = settings.finnegans_base_url.rstrip("/")
        self.token_url = os.getenv("IA_DIGITAL_TOKEN")
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(self.token_url)
            response.raise_for_status()
            return response.text.strip()

    async def _ensure_token(self) -> None:
        if not self._access_token:
            self._access_token = await self._get_access_token()

    def _auth_params(self, params: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(params or {})
        if self._access_token:
            merged["ACCESS_TOKEN"] = self._access_token
        return merged

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        await self._ensure_token()
        auth_params = self._auth_params(params)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=auth_params)

            if response.status_code == 401:
                self._access_token = await self._get_access_token()
                auth_params = self._auth_params(params)
                response = await client.get(url, params=auth_params)

            response.raise_for_status()
            return response.json()


finnegans = FinnegansClient()
