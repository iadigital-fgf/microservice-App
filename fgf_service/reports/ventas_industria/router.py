"""Endpoints del reporte ventas industria.

Tres ventanillas:
- ""                → reporte final (KPIs por segmento, con comparación año anterior) — Power BI
- "/detalle/ventas" → renglones de factura apilados — consumidor: Excel de depuración
- "/detalle/stock"  → lotes de stock apilados — consumidor: Excel de depuración

La lógica de armado vive en `armado.py`; acá solo están los endpoints.
"""

from datetime import date

from fastapi import APIRouter

from fgf_service.reports.ventas_industria import armado
from fgf_service.reports.ventas_industria.service import reporte_ventas_industria
from fgf_service.reports.ventas_industria.detalle import (
    apilar_detalle_ventas,
    apilar_detalle_stock,
)

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])


@router.get("")
async def reporte_final(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Reporte directorio: KPIs por segmento, sectorizado por mercado, con
    comparación contra el mismo período del año anterior (derivado restando
    un año a las fechas pedidas)."""
    # Se traen los dos años (secuencial para no saturar Finnegans con 14 llamadas
    # simultáneas). El año anterior es histórico: candidato a cachearse más adelante.
    datos_actual = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    datos_anterior = await reporte_ventas_industria(
        armado.menos_un_anio(fecha_desde),
        armado.menos_un_anio(fecha_hasta),
        access_token,
    )
    return armado.armar_reporte(datos_actual, datos_anterior)


@router.get("/detalle/ventas")
async def detalle_ventas(
    fecha_desde: date,
    fecha_hasta: date,
    access_token: str,
    segmento: str | None = None,
    mercado: str | None = None,
    empresa: str | None = None,
):
    """Renglones de factura apilados (VentasCap + Facturación), fila por fila,
    con fuente, mercado y segmento asignados. Para depurar datos.

    Filtros opcionales (para no traer todo y que Excel no se cuelgue):
    - segmento: exacto (ej. "FIBRAS")
    - mercado: exacto (ej. "interno")
    - empresa: coincidencia parcial, sin distinguir mayúsculas (ej. "DOHLER")
    """
    datos = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    ventas = apilar_detalle_ventas(datos.ventas_cap, datos.facturacion)
    if segmento:
        ventas = ventas[ventas["segmento"] == segmento]
    if mercado:
        ventas = ventas[ventas["mercado"] == mercado]
    if empresa:
        ventas = ventas[ventas["empresa"].str.contains(empresa, case=False, na=False)]
    return ventas.to_dict(orient="records")


@router.get("/detalle/stock")
async def detalle_stock(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Lotes de stock apilados (ARG + EXT + DT), fila por fila,
    con depósito y segmento asignados. Para depurar datos."""
    datos = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    stock = apilar_detalle_stock(datos.stock_arg, datos.stock_ext, datos.stock_dt)
    return stock.to_dict(orient="records")
