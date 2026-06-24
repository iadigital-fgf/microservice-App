"""Cálculo del presupuesto (PPTO) de ventas industria.

El presupuesto sale de los CONTRATOS (APIContratosIndustria): las filas
marcadas DESCRIPCION="PPTO ME {año}" / "PPTO MI {año}" son los objetivos de
venta. Cada fila es una entrega programada de un contrato-presupuesto.

Receta (la de Marco):
- mercado  = "PPTO ME ..." → externo ; "PPTO MI ..." → interno
- segmento = asignar_segmento(familia, subfamilia, producto)  (el mismo de ventas)
- mes      = mes de FECHAENTREGA (la entrega se imputa al mes en que se entrega)
- USD      = IMPORTEMONSECUNDARIA
- TN       = CANTIDADSTOCK2 (kilos) / 1000
"""

import calendar
from datetime import date, datetime

import numpy as np
import pandas as pd

from fgf_service.core.segmentos import SEGMENTOS_EXCLUIDOS_KPIS, asignar_segmento
from fgf_service.reports.ventas_industria.detalle import _toneladas
from fgf_service.reports.ventas_industria.schemas import APIContratosIndustriaRaw


def _mercado_ppto(descripcion: str | None, anio: int) -> str | None:
    """externo si "PPTO ME {año}", interno si "PPTO MI {año}", si no None.

    Sin distinguir mayúsculas (en los datos aparecen typos como "PPTO Mi").
    """
    d = (descripcion or "").upper()
    if f"PPTO ME {anio}" in d:
        return "externo"
    if f"PPTO MI {anio}" in d:
        return "interno"
    return None


def _mes_entrega(fechaentrega: str | None) -> int | None:
    """Mes (1–12) a partir de FECHAENTREGA (formato dd-mm-YYYY)."""
    if not fechaentrega:
        return None
    try:
        return datetime.strptime(fechaentrega, "%d-%m-%Y").month
    except ValueError:
        return None


def meses_del_periodo(fecha_desde: date, fecha_hasta: date) -> list[int]:
    """Meses COMPLETOS dentro del período (como Marco: corte 03/06 → Ene–May).

    Un mes cuenta si su último día cae dentro de [fecha_desde, fecha_hasta];
    así un mes a medias (junio con corte el 03) no entra.
    """
    meses = []
    for m in range(1, 13):
        ultimo_dia = calendar.monthrange(fecha_hasta.year, m)[1]
        fin_de_mes = date(fecha_hasta.year, m, ultimo_dia)
        if fecha_desde <= fin_de_mes <= fecha_hasta:
            meses.append(m)
    return meses


def apilar_presupuesto(
    contratos: list[APIContratosIndustriaRaw], anio: int
) -> pd.DataFrame:
    """Contratos PPTO → tabla del presupuesto, una fila por entrega.

    Columnas: mercado, segmento, mes, usd, tn. Solo las filas "PPTO" del año
    pedido; el resto de contratos se descarta.
    """
    filas = []
    for c in contratos:
        mercado = _mercado_ppto(c.descripcion, anio)
        if mercado is None:
            continue
        filas.append({
            "mercado": mercado,
            "segmento": asignar_segmento(c.familia, c.subfamilia, c.producto),
            "mes": _mes_entrega(c.fechaentrega),
            "usd": c.importemonsecundaria or 0.0,
            "tn": _toneladas(c.cantidadstock2, c.unidadstock2),
        })
    return pd.DataFrame(filas, columns=["mercado", "segmento", "mes", "usd", "tn"])


def kpis_presupuesto(
    presupuesto: pd.DataFrame, meses: list[int], mercado: str | None = None
) -> pd.DataFrame:
    """PPTO por segmento, sumando los meses del período.

    - mercado="externo"/"interno" → solo ese mercado.
    - mercado=None → todos (sirve para el bloque TOTAL: externo + interno).

    ventas_ppto_usd = suma de IMPORTEMONSECUNDARIA de esos meses
    precio_ppto_usd_tn = ppto_usd / ppto_tn (si tn=0 queda vacío)
    """
    cols = ["segmento", "ventas_ppto_usd", "precio_ppto_usd_tn"]
    df = presupuesto[presupuesto["mes"].isin(meses)]
    if mercado is not None:
        df = df[df["mercado"] == mercado]
    df = df[~df["segmento"].isin(SEGMENTOS_EXCLUIDOS_KPIS)]
    if df.empty:
        return pd.DataFrame(columns=cols)
    resumen = df.groupby("segmento", as_index=False).agg(
        ventas_ppto_usd=("usd", "sum"), ppto_tn=("tn", "sum")
    )
    resumen["precio_ppto_usd_tn"] = (
        resumen["ventas_ppto_usd"] / resumen["ppto_tn"].replace(0, np.nan)
    ).round(2)
    resumen["ventas_ppto_usd"] = resumen["ventas_ppto_usd"].round(2)
    return resumen[cols]
