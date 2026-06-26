"""Endpoints del reporte ventas industria.

Tres ventanillas:
- ""                → reporte final (KPIs por segmento, con comparación año anterior) — Power BI
- "/detalle/ventas" → renglones de factura apilados — consumidor: Excel de depuración
- "/detalle/stock"  → lotes de stock apilados — consumidor: Excel de depuración

La lógica de armado vive en `armado.py`; acá solo están los endpoints.
"""

import asyncio
import time
from datetime import date

from fastapi import APIRouter

from fgf_service.connectors.APIContratosIndustria import fetch_APIContratosIndustria
from fgf_service.helpers.parsers import parse_finnegans
from fgf_service.reports.ventas_industria import armado
from fgf_service.reports.ventas_industria.service import reporte_ventas_industria
from fgf_service.reports.ventas_industria.schemas import APIContratosIndustriaRaw
from fgf_service.reports.ventas_industria.presupuesto import apilar_presupuesto
from fgf_service.reports.ventas_industria.detalle import (
    apilar_detalle_ventas,
    apilar_detalle_stock,
)

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])


# Cache en memoria del reporte. La primera llamada de cada (fecha_desde,
# fecha_hasta) calcula (~3 min) y las siguientes salen al instante hasta que
# vence el TTL. El candado evita que varias llamadas simultáneas (ej. las
# consultas de Power Query) disparen el cálculo en paralelo: una calcula y el
# resto espera ese mismo resultado, en vez de pegarle 6 veces a Finnegans.
_CACHE_TTL_SEG = 1800  # 30 minutos
_cache: dict = {}
_locks: dict = {}


async def _construir_reporte(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> dict:
    """Arma el reporte de cero (las llamadas a Finnegans + el armado)."""
    # Se traen los dos años (secuencial para no saturar Finnegans). El año
    # anterior se deriva restando un año a las fechas pedidas.
    datos_actual = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    datos_anterior = await reporte_ventas_industria(
        armado.menos_un_anio(fecha_desde),
        armado.menos_un_anio(fecha_hasta),
        access_token,
    )
    # Presupuesto: se TRAE desde el 1/1 del año ANTERIOR hasta fin del año del
    # corte. Los contratos-presupuesto del año suelen cargarse durante el año
    # previo (al planificar), y la API filtra por FECHA del contrato — si se
    # arrancaba en el año corriente se perdían ~75% de los contratos. El corte
    # NO se aplica acá: solo decide qué entregas se SUMAN, dentro de apilar/kpis.
    contratos_raw = await fetch_APIContratosIndustria(
        date(fecha_hasta.year - 1, 1, 1), date(fecha_hasta.year, 12, 31), access_token
    )
    contratos = parse_finnegans(contratos_raw, APIContratosIndustriaRaw)
    presupuesto = apilar_presupuesto(contratos, fecha_hasta.year)

    return armado.armar_reporte(
        datos_actual, datos_anterior, presupuesto, fecha_desde, fecha_hasta
    )


@router.get("")
async def reporte_final(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Reporte directorio: KPIs por segmento, sectorizado por mercado, con
    año actual, presupuesto y año anterior.

    Cacheado por (fecha_desde, fecha_hasta): la primera llamada calcula y las
    siguientes salen al instante hasta que vence el TTL (reiniciar el server
    también limpia el cache si querés forzar un refresco).
    """
    clave = (fecha_desde, fecha_hasta)
    cacheado = _cache.get(clave)
    if cacheado and time.monotonic() - cacheado[0] < _CACHE_TTL_SEG:
        return cacheado[1]

    candado = _locks.setdefault(clave, asyncio.Lock())
    async with candado:
        # Re-chequeo: otra llamada pudo haberlo calculado mientras esperábamos.
        cacheado = _cache.get(clave)
        if cacheado and time.monotonic() - cacheado[0] < _CACHE_TTL_SEG:
            return cacheado[1]
        reporte = await _construir_reporte(fecha_desde, fecha_hasta, access_token)
        _cache[clave] = (time.monotonic(), reporte)
        return reporte


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
    # Agrupado por mercado/familia/segmento para ver cómo clasifica cada familia
    # de contrato (sin filtrar por fecha: muestra TODO el presupuesto del año).
    resumen = ppto.groupby(
        ["mercado", "familia", "segmento"], as_index=False
    ).agg(usd=("usd", "sum"), tn=("tn", "sum"))
    return resumen.sort_values(["mercado", "segmento", "familia"]).round(2).to_dict(
        orient="records"
    )


@router.get("/detalle/stock")
async def detalle_stock(fecha_desde: date, fecha_hasta: date, access_token: str):
    """Lotes de stock apilados (ARG + EXT + DT), fila por fila,
    con depósito y segmento asignados. Para depurar datos."""
    datos = await reporte_ventas_industria(fecha_desde, fecha_hasta, access_token)
    stock = apilar_detalle_stock(datos.stock_arg, datos.stock_ext, datos.stock_dt)
    return stock.to_dict(orient="records")
