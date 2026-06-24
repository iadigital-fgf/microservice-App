"""Endpoints del reporte ventas industria.

Tres ventanillas:
- ""                → reporte final (KPIs por segmento, con comparación año anterior) — Power BI
- "/detalle/ventas" → renglones de factura apilados — consumidor: Excel de depuración
- "/detalle/stock"  → lotes de stock apilados — consumidor: Excel de depuración

La lógica de armado vive en `armado.py`; acá solo están los endpoints.
"""

from datetime import date

from fastapi import APIRouter

from fgf_service.connectors.APIContratosIndustria import fetch_APIContratosIndustria
from fgf_service.helpers.parsers import parse_finnegans
from fgf_service.reports.ventas_industria import armado
from fgf_service.reports.ventas_industria.service import reporte_ventas_industria
from fgf_service.reports.ventas_industria.schemas import APIContratosIndustriaRaw
from fgf_service.reports.ventas_industria.presupuesto import (
    apilar_presupuesto,
    meses_del_periodo,
)
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
    # Presupuesto del año actual: se trae el AÑO COMPLETO de contratos (1/1→31/12),
    # no hasta el corte. Si no, se pierden contratos-presupuesto cargados después
    # del corte (aunque su entrega sea de un mes anterior). El corte solo decide
    # qué meses del presupuesto se SUMAN (ver `meses`), no qué contratos se traen.
    contratos_raw = await fetch_APIContratosIndustria(
        date(fecha_hasta.year, 1, 1), date(fecha_hasta.year, 12, 31), access_token
    )
    contratos = parse_finnegans(contratos_raw, APIContratosIndustriaRaw)
    presupuesto = apilar_presupuesto(contratos, fecha_hasta.year)
    meses = meses_del_periodo(fecha_desde, fecha_hasta)

    return armado.armar_reporte(datos_actual, datos_anterior, presupuesto, meses)


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


@router.get("/detalle/contratos")
async def detalle_contratos(
    fecha_desde: date,
    fecha_hasta: date,
    access_token: str,
    solo_ppto: bool = True,
):
    """Contratos crudos de APIContratosIndustria — para inspeccionar la data
    real antes de armar el cálculo del presupuesto.

    - solo_ppto=True (default): solo los contratos del presupuesto
      (DESCRIPCION contiene "PPTO", sin distinguir mayúsculas).
    Devuelve el total de filas + una muestra con TODOS los campos, así
    confirmamos los nombres reales (sobre todo cómo viene el mes de entrega).
    """
    registros = await fetch_APIContratosIndustria(fecha_desde, fecha_hasta, access_token)
    if solo_ppto:
        registros = [
            r for r in registros if "PPTO" in str(r.get("DESCRIPCION", "")).upper()
        ]
    descripciones = sorted({str(r.get("DESCRIPCION", "")) for r in registros})
    return {
        "total_filas": len(registros),
        "descripciones_distintas": descripciones[:30],
        "muestra": registros[:3],
    }


@router.get("/detalle/presupuesto")
async def detalle_presupuesto(
    fecha_desde: date, fecha_hasta: date, access_token: str
):
    """Presupuesto (PPTO) agregado por mercado / segmento / mes de entrega.

    Para validar contra la hoja mensual de Marco antes de enchufarlo al
    reporte. El año del PPTO sale de `fecha_desde`. Tip: para ver el año
    completo, pedí fecha_hasta=AÑO-12-31.
    """
    raw = await fetch_APIContratosIndustria(fecha_desde, fecha_hasta, access_token)
    contratos = parse_finnegans(raw, APIContratosIndustriaRaw)
    ppto = apilar_presupuesto(contratos, fecha_desde.year)
    resumen = ppto.groupby(["mercado", "segmento", "mes"], as_index=False).agg(
        usd=("usd", "sum"), tn=("tn", "sum")
    )
    return resumen.round(2).to_dict(orient="records")


@router.get("/detalle/stock")
async def detalle_stock(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Lotes de stock apilados (ARG + EXT + DT), fila por fila,
    con depósito y segmento asignados. Para depurar datos."""
    datos = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    stock = apilar_detalle_stock(datos.stock_arg, datos.stock_ext, datos.stock_dt)
    return stock.to_dict(orient="records")
