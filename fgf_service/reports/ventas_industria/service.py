import asyncio
from datetime import date

from fgf_service.connectors.APIanalisis_facturacion import fetch_APIAnalisis_facturacion
from fgf_service.connectors.APIStockProdIndustria import fetch_APIStockProdIndustria
from fgf_service.connectors.APIanalisis_laboratorio import fetch_APIAnalisis_laboratorio
from fgf_service.connectors.APIventas_cap import fetch_APIVentas_cap
from fgf_service.reports.ventas_industria.schemas import (
    ConsolidacionVentasIndustria,
    APIVentasCapRaw,
    APIAnalisisFacturacionRaw,
    APIAnalisisLaboratorioRaw,
    APIStockProdIndustriaRaw,
)

async def reporte_ventas_industria(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> ConsolidacionVentasIndustria:
    """Llama a las dos APIs en paralelo y devuelve los datos consolidados."""

    raw_cap, raw_fac, raw_lab, raw_stock = await asyncio.gather(
        fetch_APIVentas_cap(fecha_desde, fecha_hasta, access_token),
        fetch_APIAnalisis_facturacion(fecha_desde, fecha_hasta, access_token),
        fetch_APIAnalisis_laboratorio(access_token),
        fetch_APIStockProdIndustria(fecha_hasta, access_token),
    )

    return ConsolidacionVentasIndustria(
        ventas_cap=[APIVentasCapRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_cap],
        analisis_fac=[APIAnalisisFacturacionRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_fac],
        analisis_lab=[APIAnalisisLaboratorioRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_lab],
        stock_prod_industria=[APIStockProdIndustriaRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_stock],
    )
