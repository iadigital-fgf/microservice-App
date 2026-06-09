import logging
from typing import Any

import httpx

from fgf_service.core.config import settings

logger = logging.getLogger(__name__)


class FinnegansClient:
    """Cliente async para APIs de Finnegans. El token lo envía el cliente en cada request."""

    def __init__(self) -> None:
        self.base_url = settings.finnegans_base_url.rstrip("/") + "/"

    def _auth_params(
        self, access_token: str, params: dict[str, Any] | None
    ) -> dict[str, Any]:
        merged = dict(params or {})
        merged["ACCESS_TOKEN"] = access_token
        return merged

    async def get(
        self,
        path: str,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path.lstrip('/')}"
        auth_params = self._auth_params(access_token, params)

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(url, params=auth_params)
            response.raise_for_status()
            return response.json()


finnegans = FinnegansClient()
