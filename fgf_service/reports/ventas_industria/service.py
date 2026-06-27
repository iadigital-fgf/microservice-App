"""Orquestador del reporte VENTAS INDUSTRIA.

Una sola función junta TODAS las conexiones a Finnegans (las de cada sección)
y devuelve un único dict con una tabla ("cajón") por conexión. Eso es lo que
sirve el endpoint único y lo que se cachea (corrida 3am): el Excel le pega
una sola vez y cada tabla del Excel toma su cajón.

Se va llenando sección por sección. Hoy: ME real + MI real.
"""

import asyncio
from datetime import date

from fgf_service.reports.ventas_industria.secciones.me_real.ventas_cap import (
    traer_ventas_cap,
)
from fgf_service.reports.ventas_industria.secciones.mi_real.facturacion import (
    traer_facturacion_fgf,
    traer_facturacion_dohler,
    traer_facturacion_tucuman,
    traer_facturacion_tgt,
)
from fgf_service.reports.ventas_industria.secciones.ppto.contratos import (
    traer_contratos,
)
from fgf_service.reports.ventas_industria.secciones.stock.stock import (
    traer_stock_arg,
    traer_stock_ext,
    traer_stock_dt,
)
from fgf_service.reports.ventas_industria.secciones.stock.despachos import (
    traer_despachos,
)
from fgf_service.reports.ventas_industria.secciones.stock.laboratorio import (
    traer_analisis_type,
)
from fgf_service.core import producto_segmento


async def traer_todo(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> dict:
    """Llama a todas las conexiones (en paralelo) y arma el JSON consolidado."""
    (
        ventas_cap,          # ME real
        facturacion_fgf,     # MI real — EMPRE01
        facturacion_dohler,  # MI real — DOHLER63
        facturacion_tucuman, # MI real — TUCUMANTRAPANI69
        facturacion_tgt,     # MI real — TGT61
        contratos,           # PPTO
        stock_arg,           # Stock — EMPRE01
        stock_ext,           # Stock — CAPACITACION43
        stock_dt,            # Stock — DOHLER63
        despachos,           # Stock — despachos
        analisis_type,       # Stock — laboratorio (AnalisisType)
    ) = await asyncio.gather(
        traer_ventas_cap(fecha_desde, fecha_hasta, access_token),
        traer_facturacion_fgf(fecha_desde, fecha_hasta, access_token),
        traer_facturacion_dohler(fecha_desde, fecha_hasta, access_token),
        traer_facturacion_tucuman(fecha_desde, fecha_hasta, access_token),
        traer_facturacion_tgt(fecha_desde, fecha_hasta, access_token),
        traer_contratos(fecha_desde, fecha_hasta, access_token),
        traer_stock_arg(access_token),
        traer_stock_ext(access_token),
        traer_stock_dt(access_token),
        traer_despachos(fecha_desde, fecha_hasta, access_token),
        traer_analisis_type(access_token),
    )

    return {
        # ── ME real ──
        "ventas_cap": ventas_cap,
        # ── MI real ──
        "facturacion_fgf": facturacion_fgf,
        "facturacion_dohler": facturacion_dohler,
        "facturacion_tucuman": facturacion_tucuman,
        "facturacion_tgt": facturacion_tgt,
        # ── PPTO ──
        "contratos": contratos,
        # ── Stock ──
        "stock_arg": stock_arg,
        "stock_ext": stock_ext,
        "stock_dt": stock_dt,
        "despachos": despachos,
        "analisis_type": analisis_type,
        # ── Tabla de referencia (estática, mantenida por Marco) ──
        "producto_segmento": producto_segmento.tabla(),
    }
