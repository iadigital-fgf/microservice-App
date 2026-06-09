from datetime import date
from fastapi import APIRouter

from fgf_service.connectors.APIanalisis_laboratorio import fetch_APIAnalisis_laboratorio
from fgf_service.reports.ventas_industria.schemas import ConsolidacionVentasIndustria 
from fgf_service.reports.ventas_industria.service import reporte_ventas_industria

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])

@router.get("/prueba1", response_model=ConsolidacionVentasIndustria)
async def prueba(
    fecha_desde: date,
    fecha_hasta: date,
    access_token: str,
) -> ConsolidacionVentasIndustria:
    """
    Devuelve los registros consolidados de APIVentasCap y APIAnalisisFacturacion
    para el período indicado. El token se reenvía a Finnegans; si es inválido,
    Finnegans responde con error.
    """
    return await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
