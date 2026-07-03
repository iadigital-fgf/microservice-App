"""Refresco del reporte: recalcula desde Finnegans y PISA el cache.

Lo usan los dos caminos de la Etapa 2 del plan de hosting:
- el job diario de las 3am (registrado en main.py), y
- el endpoint manual GET .../ventas-industria/refresh (router.py).

Regla clave: primero se calcula TODO y recién si la corrida vino completa se
pisa el cache. Si Finnegans falla, el cache viejo queda intacto (Marco ve los
datos de ayer, nunca cajones vacíos).
"""

import logging
import time
from datetime import date

from fgf_service.reports.ventas_industria import cache_memoria
from fgf_service.reports.ventas_industria.service import traer_todo

logger = logging.getLogger(__name__)


def fechas_estandar() -> tuple[date, date]:
    """Rango FIJO que comparten el job 3am y el Excel: 1/1 → 31/12 del año actual.

    Es la misma clave de cache todo el año (cambia sola el 1 de enero). El Excel
    pide con este mismo rango, así que siempre encuentra el cache caliente. Los
    datos "viejos" no se piden con otras fechas: se filtran en el Excel (los
    cajones ya traen el año anterior + históricos).
    """
    hoy = date.today()
    return date(hoy.year, 1, 1), date(hoy.year, 12, 31)


async def refrescar() -> dict:
    """Recalcula el reporte con las fechas estándar y pisa el cache si vino completo.

    Devuelve un resumen (para el log del job 3am y la respuesta del /refresh).
    Tarda lo que tarda Finnegans (~100 seg con las 14 conexiones).
    """
    fecha_desde, fecha_hasta = fechas_estandar()
    inicio = time.monotonic()
    reporte, completo = await traer_todo(fecha_desde, fecha_hasta)
    duracion = round(time.monotonic() - inicio, 1)

    if completo:
        cache_memoria.guardar((fecha_desde, fecha_hasta), reporte)

    resumen = {
        "ok": completo,
        "cache_actualizado": completo,  # si falló, queda el cache anterior
        "fecha_desde": str(fecha_desde),
        "fecha_hasta": str(fecha_hasta),
        "duracion_seg": duracion,
        "filas_por_cajon": {cajon: len(filas) for cajon, filas in reporte.items()},
    }
    if completo:
        logger.info("Refresh OK en %s seg", duracion)
    else:
        logger.warning("Refresh INCOMPLETO (cache NO pisado): %s", resumen)
    return resumen
