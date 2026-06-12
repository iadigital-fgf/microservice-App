import asyncio
import logging
from datetime import date

from fgf_service.connectors.APIanalisis_facturacion import fetch_APIAnalisis_facturacion
from fgf_service.connectors.APIanalisis_laboratorio import fetch_APIAnalisis_laboratorio
from fgf_service.connectors.APIStockProdIndustria import fetch_APIStockProdIndustria
from fgf_service.connectors.APIventas_cap import fetch_APIVentas_cap
from fgf_service.core.empresas import MERCADO_POR_EMPRESA, Stock
from fgf_service.helpers.parsers import parse_finnegans
from fgf_service.reports.ventas_industria.schemas import (
    ConsolidacionVentasIndustria,
    APIVentasCapRaw,
    APIAnalisisFacturacionRaw,
    APIAnalisisLaboratorioRaw,
    APIStockProdIndustriaRaw,
)

logger = logging.getLogger(__name__)


def separar_por_mercado(registros: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separa registros de APIAnalisisFacturacion en (externo, interno) según el campo EMPRESA."""
    externo: list[dict] = []
    interno: list[dict] = []
    sin_clasificar: set[str] = set()

    for registro in registros:
        empresa = registro.get("EMPRESA", "")
        mercado = MERCADO_POR_EMPRESA.get(empresa)
        if mercado == "externo":
            externo.append(registro)
        elif mercado == "interno":
            interno.append(registro)
        else:
            sin_clasificar.add(empresa)

    if sin_clasificar:
        logger.warning(
            "Empresas sin clasificar en MERCADO_POR_EMPRESA (registros descartados): %s",
            sorted(sin_clasificar),
        )

    return externo, interno


async def reporte_ventas_industria(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> ConsolidacionVentasIndustria:

    (
        raw_ventas_cap,
        raw_facturacion,
        raw_lab,
        raw_stock_arg,
        raw_stock_ext,
        raw_stock_dt,
    ) = await asyncio.gather(
        # Mercado Externo — APIVentasCap sin empresa: trae todas las exportaciones
        # en una sola llamada (el parámetro empresa no filtra de verdad y duplicaba datos)
        fetch_APIVentas_cap(fecha_desde, fecha_hasta, access_token),
        # APIAnalisisFacturacion — sin empresa: trae todas, se separan por mercado abajo
        fetch_APIAnalisis_facturacion(fecha_desde, fecha_hasta, access_token),
        # Laboratorio
        fetch_APIAnalisis_laboratorio(access_token),
        # Stock Argentina
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa=Stock.ARG),
        # Stock Exterior
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa=Stock.EXT),
        # Stock DT
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa=Stock.DT),
    )

    raw_fac_me, raw_fac_mi = separar_por_mercado(raw_facturacion)

    return ConsolidacionVentasIndustria(
        # Mercado Externo — APIVentasCap
        ventas_cap=parse_finnegans(raw_ventas_cap, APIVentasCapRaw),
        # APIAnalisisFacturacion separado por mercado
        fac_me=parse_finnegans(raw_fac_me, APIAnalisisFacturacionRaw),
        fac_mi=parse_finnegans(raw_fac_mi, APIAnalisisFacturacionRaw),
        # Laboratorio
        analisis_lab=parse_finnegans(raw_lab, APIAnalisisLaboratorioRaw),
        # Stock
        stock_arg=parse_finnegans(raw_stock_arg, APIStockProdIndustriaRaw),
        stock_ext=parse_finnegans(raw_stock_ext, APIStockProdIndustriaRaw),
        stock_dt=parse_finnegans(raw_stock_dt, APIStockProdIndustriaRaw),
    )
