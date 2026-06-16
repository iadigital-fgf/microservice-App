"""Endpoints del reporte ventas industria.

Tres ventanillas:
- ""                → reporte final (KPIs por segmento) — consumidor: Power BI
- "/detalle/ventas" → renglones de factura apilados — consumidor: Excel de depuración
- "/detalle/stock"  → lotes de stock apilados — consumidor: Excel de depuración
"""

from datetime import date
from fastapi import APIRouter

from fgf_service.reports.ventas_industria.service import reporte_ventas_industria
from fgf_service.reports.ventas_industria.detalle import (
    apilar_detalle_ventas,
    apilar_detalle_stock,
)
from fgf_service.reports.ventas_industria import kpis
from fgf_service.helpers.formato import formatear_bloque

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])

# Columnas numéricas que se formatean como texto en el reporte final
_COLS_VENTAS = ["ventas_usd", "ventas_tn", "precio_usd_tn"]
_COLS_STOCK = ["stock_tn"]


@router.get("")
async def reporte_final(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Reporte directorio: KPIs por segmento, en 4 bloques
    (mercado externo, mercado interno, total y stock)."""
    datos = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)

    ventas = apilar_detalle_ventas(
        datos.ventas_cap, datos.facturacion
    )
    stock = apilar_detalle_stock(datos.stock_arg, datos.stock_ext, datos.stock_dt)

    me = kpis.kpis_mercado_externo(ventas)
    mi = kpis.kpis_mercado_interno(ventas)
    total = kpis.kpis_total(me, mi)
    stock_kpi = kpis.kpis_stock(stock)

    # Formateo visual (.miles y ,decimal) como último paso, después de todo cálculo
    return {
        "mercado_externo": formatear_bloque(me.to_dict(orient="records"), _COLS_VENTAS),
        "mercado_interno": formatear_bloque(mi.to_dict(orient="records"), _COLS_VENTAS),
        "total": formatear_bloque(total.to_dict(orient="records"), _COLS_VENTAS),
        "stock": formatear_bloque(stock_kpi.to_dict(orient="records"), _COLS_STOCK),
    }


@router.get("/detalle/ventas")
async def detalle_ventas(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Renglones de factura apilados (VentasCap + Facturación), fila por fila,
    con fuente, mercado y segmento asignados. Para depurar datos."""
    datos = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    ventas = apilar_detalle_ventas(
        datos.ventas_cap, datos.facturacion
    )
    return ventas.to_dict(orient="records")


@router.get("/detalle/stock")
async def detalle_stock(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Lotes de stock apilados (ARG + EXT + DT), fila por fila,
    con depósito y segmento asignados. Para depurar datos."""
    datos = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    stock = apilar_detalle_stock(datos.stock_arg, datos.stock_ext, datos.stock_dt)
    return stock.to_dict(orient="records")
