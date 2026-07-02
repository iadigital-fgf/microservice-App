"""Endpoints del reporte ventas industria.

UN SOLO endpoint: le pega a todas las APIs de Finnegans (vía el orquestador)
y devuelve un único JSON consolidado, con una tabla ("cajón") por conexión.
El Excel le pega una vez y cada tabla del Excel toma su cajón.
"""

import asyncio
from datetime import date

from fastapi import APIRouter

from fgf_service.reports.ventas_industria.service import traer_todo

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])


# Cache en memoria, SIN expiración: la primera llamada de cada (fecha_desde,
# fecha_hasta) calcula y guarda; las siguientes salen al instante. Para datos
# frescos se reinicia el servidor (eso limpia el cache).
#
# El candado evita la saturación: cuando el Excel dispara las 15 tablas casi a
# la vez y el cache está vacío, UNA sola calcula y las otras esperan ese mismo
# resultado, en vez de pegarle 15 veces a Finnegans (que es lo que tumbaba la
# descarga de algunas tablas).
#
# La clave es (fecha_desde, fecha_hasta): el access_token no cambia el dato (es
# solo autenticación), así que no entra en la clave.
_cache: dict = {}
_locks: dict = {}


@router.get("")
async def reporte_crudo(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    access_token: str | None = None,  # ignorado: el token ahora lo maneja el servicio
) -> dict:
    """Devuelve TODAS las conexiones crudas en un solo JSON consolidado (cacheado).

    Los parámetros son opcionales a propósito: Power Query "sondea" la URL base
    SIN parámetros para validar la fuente; sin las fechas se devuelve un dict
    vacío (si fueran obligatorios daría 422 y rompería la carga).

    `access_token` se sigue ACEPTANDO para no romper el Excel actual de Marco,
    pero se IGNORA: el servicio genera y renueva su propio token con las
    credenciales del .env (core/finnegans.py). El Excel solo necesita las fechas.
    """
    if not (fecha_desde and fecha_hasta):
        return {}

    clave = (fecha_desde, fecha_hasta)
    if clave in _cache:
        return _cache[clave]

    candado = _locks.setdefault(clave, asyncio.Lock())
    async with candado:
        # Re-chequeo: otra llamada pudo haberlo calculado mientras esperábamos.
        if clave in _cache:
            return _cache[clave]
        reporte, completo = await traer_todo(fecha_desde, fecha_hasta)
        if completo:
            _cache[clave] = reporte  # solo se cachea una corrida sin fallas
        return reporte
