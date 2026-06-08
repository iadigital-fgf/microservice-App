import asyncio
from datetime import date

from fgf_service.apis.analisis_facturacion import fetch_analisis_facturacion
from fgf_service.apis.ventas_cap import fetch_ventas_cap
from fgf_service.reports.ventas_industria.schemas import (
    ConsolidacionVentasIndustria,
    FacturacionRaw,
    VentasCapRaw,
)


async def reporte_ventas_industria(
    fecha_desde: date, fecha_hasta: date
) -> ConsolidacionVentasIndustria:
    """Llama a las dos APIs en paralelo y devuelve los datos consolidados."""

    raw_cap, raw_fac = await asyncio.gather(
        fetch_ventas_cap(fecha_desde, fecha_hasta),
        fetch_analisis_facturacion(fecha_desde, fecha_hasta),
    )

    return ConsolidacionVentasIndustria(
        ventas_cap=[VentasCapRaw(**item) for item in raw_cap],
        analisis_fac=[FacturacionRaw(**item) for item in raw_fac],
    )
