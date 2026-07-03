"""Endpoints del reporte ventas industria.

- GET ""        → el reporte consolidado (15 cajones), cacheado.
- GET "/refresh" → recalcula desde Finnegans y PISA el cache (botón manual).

El cache vive en cache_memoria.py (compartido con el job 3am y el /refresh).
"""

from datetime import date

from fastapi import APIRouter

from fgf_service.reports.ventas_industria import cache_memoria
from fgf_service.reports.ventas_industria.refresh import refrescar
from fgf_service.reports.ventas_industria.service import traer_todo

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])


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
    cacheado = cache_memoria.obtener(clave)
    if cacheado is not None:
        return cacheado

    async with cache_memoria.candado(clave):
        # Re-chequeo: otra llamada pudo haberlo calculado mientras esperábamos.
        cacheado = cache_memoria.obtener(clave)
        if cacheado is not None:
            return cacheado
        reporte, completo = await traer_todo(fecha_desde, fecha_hasta)
        if completo:
            cache_memoria.guardar(clave, reporte)  # solo corridas sin fallas
        return reporte


@router.get("/refresh")
async def refresh_manual() -> dict:
    """Trae datos frescos de Finnegans YA y pisa el cache (fechas estándar).

    Es el botón manual para no esperar a las 3am: tarda ~2 min y responde un
    resumen con las filas por cajón. Mientras corre, el cache viejo sigue
    sirviendo. Si alguna conexión falla, el cache NO se pisa (queda el anterior).
    """
    return await refrescar()
