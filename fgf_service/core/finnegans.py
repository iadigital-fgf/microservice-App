import asyncio
import logging
from typing import Any

import httpx

from fgf_service.core.config import settings

logger = logging.getLogger(__name__)

# Algunos reportes pesados de Finnegans (ej. el stock de Argentina, EMPRE01)
# fallan con 500 de forma intermitente y andan al reintentar. Reintentamos
# solo ante errores de servidor (5xx); los 4xx no se reintentan porque no
# cambiarían. Espera creciente entre intentos (2s, 4s, ...).
_REINTENTOS_5XX = 3
_ESPERA_BASE_SEG = 2


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

        async with httpx.AsyncClient(timeout=600) as client:
            for intento in range(1, _REINTENTOS_5XX + 1):
                response = await client.get(url, params=auth_params)
                # 5xx = error del servidor (suele ser transitorio) → reintentar
                # mientras queden intentos. El resto se resuelve normal.
                if response.status_code >= 500 and intento < _REINTENTOS_5XX:
                    logger.warning(
                        "Finnegans %s devolvió %s; reintento %s/%s",
                        path, response.status_code, intento, _REINTENTOS_5XX,
                    )
                    await asyncio.sleep(_ESPERA_BASE_SEG * intento)
                    continue
                response.raise_for_status()
                return response.json()


finnegans = FinnegansClient()
