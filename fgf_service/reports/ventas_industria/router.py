"""Endpoints del reporte ventas industria.

UN SOLO endpoint: le pega a todas las APIs de Finnegans (vía el orquestador)
y devuelve un único JSON consolidado, con una tabla ("cajón") por conexión.
El Excel le pega una vez y cada tabla del Excel toma su cajón.

Se va llenando sección por sección (hoy: ME real / ventas_cap).
"""

from datetime import date

from fastapi import APIRouter

from fgf_service.reports.ventas_industria.service import traer_todo

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])


@router.get("")
async def reporte_crudo(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> dict:
    """Devuelve TODAS las conexiones crudas en un solo JSON consolidado."""
    return await traer_todo(fecha_desde, fecha_hasta, access_token)
