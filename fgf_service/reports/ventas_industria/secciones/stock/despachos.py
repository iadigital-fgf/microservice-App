"""STOCK — Despachos.

Despachos/embarques por rango de fechas. Crudo, tal cual la API.
"""

from datetime import date

from fgf_service.connectors.APIDespachosIndustria import fetch_APIDespachosIndustria


# Despachos
async def traer_despachos(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """APIDespachosIndustria tal cual la API (crudo)."""
    return await fetch_APIDespachosIndustria(fecha_desde, fecha_hasta, access_token)
