"""Armado del reporte ventas industria.

Funciones específicas de ESTE reporte: comparación año contra año (mismo
período del año anterior) y armado de la estructura final, sectorizada por
mercado (externo, interno, total). El router solo llama a `armar_reporte`.
"""

import math
from datetime import date

import numpy as np
import pandas as pd

from fgf_service.core.segmentos import SEGMENTOS_REPORTE, SUBSEGMENTOS_OTROS
from fgf_service.reports.ventas_industria import kpis
from fgf_service.reports.ventas_industria.detalle import (
    apilar_detalle_ventas,
    apilar_detalle_stock,
)

# El año anterior usa los nombres del reporte de Marco (columnas "REAL")
_NOMBRES_ANIO_ANTERIOR = {
    "ventas_usd": "ventas_real_usd",
    "precio_usd_tn": "precio_fob_real",
}


def menos_un_anio(d: date) -> date:
    """Misma fecha, un año antes (29/02 → 28/02 en años no bisiestos)."""
    try:
        return d.replace(year=d.year - 1)
    except ValueError:
        return d.replace(year=d.year - 1, day=28)


def calcular_bloques(datos) -> dict[str, pd.DataFrame]:
    """Calcula los KPIs por bloque (ME, MI, total, stock) desde los datos crudos."""
    ventas = apilar_detalle_ventas(datos.ventas_cap, datos.facturacion)
    stock = apilar_detalle_stock(datos.stock_arg, datos.stock_ext, datos.stock_dt)
    me = kpis.kpis_mercado_externo(ventas)
    mi = kpis.kpis_mercado_interno(ventas)
    return {
        "me": me,
        "mi": mi,
        "total": kpis.kpis_total(me, mi),
        "stock": kpis.kpis_stock(stock),
        "sub_me": kpis.kpis_subsegmentos_otros_mercado_externo(ventas),
        "sub_mi": kpis.kpis_subsegmentos_otros_mercado_interno(ventas),
        "sub_total": kpis.kpis_subsegmentos_otros_total(ventas),
    }


def _completar_segmentos(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Orden fijo de segmentos; filas faltantes con ceros en las columnas pedidas."""
    if df.empty:
        out = pd.DataFrame({"segmento": SEGMENTOS_REPORTE})
    else:
        out = (
            df.set_index("segmento")
            .reindex(SEGMENTOS_REPORTE)
            .reset_index()
        )
    for col in columnas:
        if col in out.columns:
            out[col] = out[col].fillna(0)
        else:
            out[col] = 0.0
    return out


def _completar_subsegmentos(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Orden fijo de sub-rubros OTROS; filas faltantes con ceros."""
    if df.empty:
        out = pd.DataFrame({"subsegmento": SUBSEGMENTOS_OTROS})
    else:
        out = (
            df.set_index("subsegmento")
            .reindex(SUBSEGMENTOS_OTROS)
            .reset_index()
        )
    for col in columnas:
        if col in out.columns:
            out[col] = out[col].fillna(0)
        else:
            out[col] = 0.0
    return out


def _variacion(actual: pd.DataFrame, anterior: pd.DataFrame, clave: str = "segmento") -> pd.DataFrame:
    """Columnas VAR = valor año actual / valor año anterior (ratio, como Marco)."""
    m = actual.merge(anterior, on=clave, how="left", suffixes=("", "_ant"))
    out = pd.DataFrame({clave: m[clave]})
    out["var_usd"] = (
        m["ventas_usd"] / m["ventas_usd_ant"].replace(0, np.nan)
    ).round(4).fillna(0)
    out["var_precio"] = (
        m["precio_usd_tn"] / m["precio_usd_tn_ant"].replace(0, np.nan)
    ).round(4).fillna(0)
    return out


def _limpiar_valor(v):
    """NaN → None para JSON; el resto se deja igual."""
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _record(row: dict) -> dict:
    return {k: _limpiar_valor(v) for k, v in row.items()}


def _records_segmentos(
    df: pd.DataFrame,
    sub_df: pd.DataFrame | None = None,
    incluir_subsegmentos: bool = False,
    renombrar: dict[str, str] | None = None,
    columnas_extra: list[str] | None = None,
) -> list[dict]:
    """DataFrame → lista de dicts; OTROS lleva subsegmentos anidados si corresponde."""
    records = []
    for row in df.to_dict(orient="records"):
        rec = _record(row)
        if renombrar:
            for origen, destino in renombrar.items():
                if origen in rec:
                    rec[destino] = rec.pop(origen)
        if columnas_extra:
            for col in columnas_extra:
                rec.setdefault(col, 0)
        if incluir_subsegmentos and rec.get("segmento") == "OTROS" and sub_df is not None:
            rec["subsegmentos"] = [
                _record({"segmento": r.pop("subsegmento"), **r})
                for r in sub_df.to_dict(orient="records")
            ]
        records.append(rec)
    return records


def bloque_comparado(
    actual: pd.DataFrame,
    anterior: pd.DataFrame,
    stock: pd.DataFrame,
    sub_actual: pd.DataFrame,
    sub_anterior: pd.DataFrame,
) -> dict:
    """Arma un bloque sectorizado: año actual y año anterior.

    - anio_actual: ventas_usd, ventas_tn, precio_usd_tn + stock_tn.
    - anio_anterior: ventas_real_usd, precio_fob_real + var_usd, var_precio
      (sin ventas_tn, que ese bloque del reporte no muestra).
    - OTROS incluye subsegmentos anidados (Aceite de semilla, Terpeno).
    """
    cols_ventas = ["ventas_usd", "ventas_tn", "precio_usd_tn"]
    actual = _completar_segmentos(actual, cols_ventas)
    anterior = _completar_segmentos(anterior, cols_ventas)
    stock = _completar_segmentos(stock, ["stock_tn"])
    sub_actual = _completar_subsegmentos(sub_actual, cols_ventas)
    sub_anterior = _completar_subsegmentos(sub_anterior, cols_ventas)

    variacion = _variacion(actual, anterior)
    sub_variacion = _variacion(sub_actual, sub_anterior, clave="subsegmento")

    actual_out = actual.merge(stock, on="segmento", how="left")
    actual_out["stock_tn"] = actual_out["stock_tn"].fillna(0)

    anterior_out = (
        anterior.rename(columns=_NOMBRES_ANIO_ANTERIOR)
        .drop(columns=["ventas_tn"])
        .merge(variacion, on="segmento", how="left")
    )
    sub_anterior_out = (
        sub_anterior.rename(columns=_NOMBRES_ANIO_ANTERIOR)
        .drop(columns=["ventas_tn"])
        .merge(sub_variacion, on="subsegmento", how="left")
    )

    return {
        "anio_actual": _records_segmentos(
            actual_out, sub_actual, incluir_subsegmentos=True
        ),
        "anio_anterior": _records_segmentos(
            anterior_out,
            sub_anterior_out,
            incluir_subsegmentos=True,
            renombrar=_NOMBRES_ANIO_ANTERIOR,
            columnas_extra=["var_usd", "var_precio"],
        ),
    }


def armar_reporte(datos_actual, datos_anterior) -> dict:
    """Arma el reporte final completo: los tres mercados sectorizados, cada uno
    con año actual, año anterior y variación."""
    act = calcular_bloques(datos_actual)
    ant = calcular_bloques(datos_anterior)
    stock = act["stock"]  # mismo stock (inventario actual) para los tres bloques
    return {
        "mercado_externo": bloque_comparado(
            act["me"], ant["me"], stock, act["sub_me"], ant["sub_me"]
        ),
        "mercado_interno": bloque_comparado(
            act["mi"], ant["mi"], stock, act["sub_mi"], ant["sub_mi"]
        ),
        "total": bloque_comparado(
            act["total"], ant["total"], stock, act["sub_total"], ant["sub_total"]
        ),
    }
