"""Endpoints del reporte ventas industria.

UN SOLO endpoint: le pega a todas las APIs de Finnegans (vía el orquestador)
y devuelve un único JSON consolidado, con una tabla ("cajón") por conexión.
El Excel le pega una vez y cada tabla del Excel toma su cajón.
"""

from datetime import date

from fastapi import APIRouter

from fgf_service.reports.ventas_industria.service import traer_todo

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])


@router.get("")
async def reporte_crudo(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    access_token: str | None = None,
) -> dict:
    """Devuelve TODAS las conexiones crudas en un solo JSON consolidado.

    Los parámetros son opcionales a propósito: Power Query "sondea" la URL base
    SIN parámetros para validar la fuente, y si fueran obligatorios devolvería
    422 y rompería la carga. Sin los tres datos, se devuelve un dict vacío; con
    los tres, se arma el reporte real.
    """
    if not (fecha_desde and fecha_hasta and access_token):
        return {}
    return await traer_todo(fecha_desde, fecha_hasta, access_token)
