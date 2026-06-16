import asyncio
import logging
from datetime import date

from fgf_service.connectors.APIanalisis_facturacion import fetch_APIAnalisis_facturacion
from fgf_service.connectors.APIanalisis_laboratorio import fetch_APIAnalisis_laboratorio
from fgf_service.connectors.APIStockProdIndustria import fetch_APIStockProdIndustria
from fgf_service.connectors.APIventas_cap import fetch_APIVentas_cap
from fgf_service.core.empresas import MercadoExterno, Stock
from fgf_service.helpers.parsers import parse_finnegans
from fgf_service.reports.ventas_industria.schemas import (
    ConsolidacionVentasIndustria,
    APIVentasCapRaw,
    APIAnalisisFacturacionRaw,
    APIAnalisisLaboratorioRaw,
    APIStockProdIndustriaRaw,
)

logger = logging.getLogger(__name__)

# Nombre del campo EMPRESA de Dohler en los registros. La llamada general
# (sin empresa) no devuelve las exportaciones de Dohler, así que las traemos
# con una llamada dedicada (empresa=DOHLER63). Para no duplicar, sacamos las
# filas de Dohler de la llamada general.
EMPRESA_DOHLER = "DOHLER-TRAPANI ARGENTINA S.A."


async def reporte_ventas_industria(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> ConsolidacionVentasIndustria:

    (
        raw_ventas_cap,
        raw_facturacion,
        raw_fac_dohler,
        raw_lab,
        raw_stock_arg,
        raw_stock_ext,
        raw_stock_dt,
    ) = await asyncio.gather(
        # Mercado Externo — APIVentasCap sin empresa: trae todas las exportaciones
        # en una sola llamada (el parámetro empresa no filtra de verdad y duplicaba datos)
        fetch_APIVentas_cap(fecha_desde, fecha_hasta, access_token),
        # APIAnalisisFacturacion sin empresa: trae el grueso de la facturación
        fetch_APIAnalisis_facturacion(fecha_desde, fecha_hasta, access_token),
        # APIAnalisisFacturacion empresa=DOHLER63: las fibras de Dohler (export
        # e interno) que la llamada general no devuelve
        fetch_APIAnalisis_facturacion(
            fecha_desde, fecha_hasta, access_token, empresa=MercadoExterno.DOHLER
        ),
        # Laboratorio
        fetch_APIAnalisis_laboratorio(access_token),
        # Stock Argentina
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa=Stock.ARG),
        # Stock Exterior
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa=Stock.EXT),
        # Stock DT
        fetch_APIStockProdIndustria(fecha_hasta, access_token, empresa=Stock.DT),
    )

    # Combinar facturación: la general SIN las filas de Dohler (para no duplicar)
    # + la llamada dedicada de Dohler completa.
    facturacion_general = [
        r for r in raw_facturacion if r.get("EMPRESA") != EMPRESA_DOHLER
    ]
    raw_facturacion_total = facturacion_general + raw_fac_dohler

    return ConsolidacionVentasIndustria(
        # Mercado Externo — APIVentasCap
        ventas_cap=parse_finnegans(raw_ventas_cap, APIVentasCapRaw),
        # APIAnalisisFacturacion (general sin Dohler + Dohler dedicada);
        # el mercado se decide después por tipo de documento en detalle.py
        facturacion=parse_finnegans(raw_facturacion_total, APIAnalisisFacturacionRaw),
        # Laboratorio
        analisis_lab=parse_finnegans(raw_lab, APIAnalisisLaboratorioRaw),
        # Stock
        stock_arg=parse_finnegans(raw_stock_arg, APIStockProdIndustriaRaw),
        stock_ext=parse_finnegans(raw_stock_ext, APIStockProdIndustriaRaw),
        stock_dt=parse_finnegans(raw_stock_dt, APIStockProdIndustriaRaw),
    )
