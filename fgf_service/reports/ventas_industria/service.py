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

    raw_cap, raw_dt, raw_fac, raw_lab, raw_stock_arg, raw_stock_dohler63, raw_stock_empre01 = await asyncio.gather(
        #API Ventas Cap
        fetch_APIVentas_cap(fecha_desde, fecha_hasta, access_token, empresa="CAPACITACION43"),
        fetch_APIVentas_cap(fecha_desde, fecha_hasta, access_token, empresa="DOHLER63"),
        #API Analisis Facturacion
        fetch_APIAnalisis_facturacion(fecha_desde, fecha_hasta, access_token),
        #API Analisis Laboratorio
        fetch_APIAnalisis_laboratorio(access_token),
        #API Stock Prod Industria
        #STOCKARG
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa="EMPRE01")
        #STOCKDOHLER63
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa="DOHLER63"),
        #STOCKEMPRE01
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa="EMPRE01"),
    )

    return ConsolidacionVentasIndustria(
        #API Ventas Cap
        ventas_cap=[APIVentasCapRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_cap],
        #API Ventas DT
        ventas_dt=[APIVentasCapRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_dt],
        #API Analisis Facturacion
        analisis_fac=[APIAnalisisFacturacionRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_fac],
        #API Analisis Laboratorio
        analisis_lab=[APIAnalisisLaboratorioRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_lab],
        #API Stock Prod Industria
        #STOCKARG
        stock_prod_industria_arg=[APIStockProdIndustriaRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_stock_arg],
        #STOCKDOHLER63
        stock_prod_industria_dohler63=[APIStockProdIndustriaRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_stock_dohler63],
        #STOCKEMPRE01
        stock_prod_industria_empre01=[APIStockProdIndustriaRaw.model_validate({k.lower(): v for k, v in item.items()}) for item in raw_stock_empre01],
    )