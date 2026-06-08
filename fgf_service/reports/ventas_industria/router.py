from datetime import date

from fastapi import APIRouter, Depends

from fgf_service.core.auth import verify_token
from fgf_service.reports.ventas_industria.schemas import ConsolidacionVentasIndustria
from fgf_service.reports.ventas_industria.service import reporte_ventas_industria

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])


@router.get("/", response_model=ConsolidacionVentasIndustria, dependencies=[Depends(verify_token)])
async def consolidacion(fecha_desde: date, fecha_hasta: date) -> ConsolidacionVentasIndustria:
    """
    Devuelve los registros consolidados de APIVentasCap y APIAnalisisFacturacion
    para el período indicado.
    """
    return await reporte_ventas_industria(fecha_desde, fecha_hasta)
