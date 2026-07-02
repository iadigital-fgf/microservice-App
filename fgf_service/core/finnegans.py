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
    """Cliente async para APIs de Finnegans. Maneja su PROPIO token.

    El token ya no viene del Excel: el cliente lo pide a Finnegans con las
    credenciales del .env (client_id/client_secret) y lo guarda en memoria.
    Como el token vence, cuando una llamada devuelve 401/403 se pide uno nuevo
    y se reintenta — se renueva solo, sin reloj ni vencimiento estimado.
    """

    def __init__(self) -> None:
        self.base_url = settings.finnegans_base_url.rstrip("/") + "/"
        self._token: str | None = None
        self._token_lock = asyncio.Lock()

    async def _obtener_token(self, vencido: str | None = None) -> str:
        """Devuelve el token vigente; se lo pide a Finnegans solo si hace falta.

        `vencido` es el token que acaba de fallar con 401/403. El candado evita
        que las 14 conexiones en paralelo pidan 14 tokens: UNA lo pide y las
        demás reusan ese. Si al entrar el token guardado ya es otro distinto de
        `vencido`, alguien lo renovó mientras esperábamos → se usa ese.
        """
        async with self._token_lock:
            if self._token and self._token != vencido:
                return self._token
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(
                    settings.finnegans_token_url,
                    params={
                        "grant_type": "client_credentials",
                        "client_id": settings.finnegans_client_id,
                        "client_secret": settings.finnegans_client_secret,
                    },
                )
                response.raise_for_status()
            # El cuerpo de la respuesta ES el token (texto plano, un UUID).
            self._token = response.text.strip().strip('"')
            logger.info("Token de Finnegans obtenido/renovado")
            return self._token

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path.lstrip('/')}"
        token = await self._obtener_token()
        renovar_disponible = True  # el token se renueva a lo sumo UNA vez por request

        async with httpx.AsyncClient(timeout=600) as client:
            intento = 1
            while True:
                auth_params = dict(params or {})
                auth_params["ACCESS_TOKEN"] = token
                response = await client.get(url, params=auth_params)
                # 401/403 = token vencido → renovar y repetir la llamada.
                if response.status_code in (401, 403) and renovar_disponible:
                    renovar_disponible = False
                    logger.warning("Finnegans %s devolvió %s; renuevo token", path, response.status_code)
                    token = await self._obtener_token(vencido=token)
                    continue
                # 5xx = error del servidor (suele ser transitorio) → reintentar
                # mientras queden intentos. El resto se resuelve normal.
                if response.status_code >= 500 and intento < _REINTENTOS_5XX:
                    logger.warning(
                        "Finnegans %s devolvió %s; reintento %s/%s",
                        path, response.status_code, intento, _REINTENTOS_5XX,
                    )
                    await asyncio.sleep(_ESPERA_BASE_SEG * intento)
                    intento += 1
                    continue
                response.raise_for_status()
                return response.json()


finnegans = FinnegansClient()
