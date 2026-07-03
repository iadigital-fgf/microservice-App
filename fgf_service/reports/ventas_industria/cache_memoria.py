"""Cache en memoria del reporte VENTAS INDUSTRIA.

Un dict simple, SIN expiración: los datos frescos entran "pisando" (el job de
las 3am o el /refresh recalculan y sobreescriben). Reiniciar el servidor lo
limpia. Vive en su propio módulo para que lo compartan el router (lee/guarda),
el job 3am y el /refresh (pisan).

La clave es (fecha_desde, fecha_hasta): el rango pedido. El Excel usa siempre
el rango estándar (ver refresh.fechas_estandar), así que su clave está caliente.
"""

import asyncio

_cache: dict = {}
_locks: dict = {}


def obtener(clave: tuple) -> dict | None:
    """El reporte cacheado para esa clave, o None si no está."""
    return _cache.get(clave)


def guardar(clave: tuple, reporte: dict) -> None:
    """Guarda (o PISA) el reporte para esa clave."""
    _cache[clave] = reporte


def candado(clave: tuple) -> asyncio.Lock:
    """Candado por clave: cuando el Excel dispara sus 15 tablas a la vez con el
    cache vacío, UNA sola calcula y las otras esperan ese mismo resultado."""
    return _locks.setdefault(clave, asyncio.Lock())
