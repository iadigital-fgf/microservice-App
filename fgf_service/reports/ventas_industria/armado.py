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
from fgf_service.reports.ventas_industria.presupuesto import kpis_presupuesto
from fgf_service.reports.ventas_industria.detalle import (
    apilar_detalle_ventas,
    apilar_detalle_stock,
)

# El año anterior usa los nombres del reporte de Marco (columnas "REAL")
_NOMBRES_ANIO_ANTERIOR = {
    "ventas_usd": "ventas_real_usd",
    "ventas_tn": "ventas_real_tn",
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


def _bloque_presupuesto(actual: pd.DataFrame, ppto: pd.DataFrame) -> pd.DataFrame:
    """Bloque PPTO con los nombres del reporte de Marco + VAR real-vs-ppto.

    - actual: bloque año actual ya completado (segmento, ventas_usd, precio_usd_tn).
    - ppto:   kpis_presupuesto (segmento, ventas_ppto_usd, precio_ppto_usd_tn).

    real_vs_ppto_var = ventas reales / ventas presupuestadas
    var_precio_ppto  = precio real / precio presupuestado
    """
    ppto = _completar_segmentos(
        ppto, ["ventas_ppto_usd", "ppto_tn", "precio_ppto_usd_tn"]
    )
    m = actual.merge(ppto, on="segmento", how="left")
    out = pd.DataFrame({"segmento": m["segmento"]})
    out["ventas_ppto_usd"] = m["ventas_ppto_usd"].fillna(0)
    out["ventas_ppto_tn"] = m["ppto_tn"].fillna(0)
    out["real_vs_ppto_var"] = (
        m["ventas_usd"] / m["ventas_ppto_usd"].replace(0, np.nan)
    ).round(4).fillna(0)
    out["precio_ppto"] = m["precio_ppto_usd_tn"]
    out["var_precio_ppto"] = (
        m["precio_usd_tn"] / m["precio_ppto_usd_tn"].replace(0, np.nan)
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


def _totales(
    actual: pd.DataFrame,
    anterior: pd.DataFrame,
    stock: pd.DataFrame,
    ppto: pd.DataFrame,
) -> tuple[dict, dict, dict]:
    """Fila TOTAL de cada sección (segmento="TOTAL").

    Suma USD/TN/stock y calcula el precio PONDERADO (USD total / TN total, nunca
    promedio de promedios). Los VAR del total son ratios de los totales.
    """
    a_usd = float(actual["ventas_usd"].sum())
    a_tn = float(actual["ventas_tn"].sum())
    an_usd = float(anterior["ventas_usd"].sum())
    an_tn = float(anterior["ventas_tn"].sum())
    p_usd = float(ppto["ventas_ppto_usd"].sum())
    p_tn = float(ppto["ppto_tn"].sum())
    stk = float(stock["stock_tn"].sum())

    def precio(usd, tn):
        return round(usd / tn, 2) if tn else None

    def ratio(num, den):
        return round(num / den, 4) if den else 0.0

    pr_act, pr_ppto, pr_ant = precio(a_usd, a_tn), precio(p_usd, p_tn), precio(an_usd, an_tn)

    total_actual = {
        "segmento": "TOTAL",
        "ventas_usd": round(a_usd, 2),
        "ventas_tn": round(a_tn, 2),
        "precio_usd_tn": pr_act,
        "stock_tn": round(stk, 2),
    }
    total_ppto = {
        "segmento": "TOTAL",
        "ventas_ppto_usd": round(p_usd, 2),
        "ventas_ppto_tn": round(p_tn, 2),
        "real_vs_ppto_var": ratio(a_usd, p_usd),
        "precio_ppto": pr_ppto,
        "var_precio_ppto": ratio(pr_act or 0, pr_ppto) if pr_ppto else 0.0,
    }
    total_anterior = {
        "segmento": "TOTAL",
        "ventas_real_usd": round(an_usd, 2),
        "ventas_real_tn": round(an_tn, 2),
        "precio_fob_real": pr_ant,
        "var_usd": ratio(a_usd, an_usd),
        "var_precio": ratio(pr_act or 0, pr_ant) if pr_ant else 0.0,
    }
    return total_actual, total_ppto, total_anterior


def bloque_comparado(
    actual: pd.DataFrame,
    anterior: pd.DataFrame,
    stock: pd.DataFrame,
    sub_actual: pd.DataFrame,
    sub_anterior: pd.DataFrame,
    ppto: pd.DataFrame,
) -> dict:
    """Arma un bloque sectorizado: año actual, presupuesto y año anterior.

    - anio_actual: ventas_usd, ventas_tn, precio_usd_tn + stock_tn.
    - presupuesto: ventas_ppto_usd, real_vs_ppto_var, precio_ppto, var_precio_ppto
      (solo del año actual; los nombres espejan las columnas del reporte).
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
        .merge(variacion, on="segmento", how="left")
    )
    sub_anterior_out = (
        sub_anterior.rename(columns=_NOMBRES_ANIO_ANTERIOR)
        .merge(sub_variacion, on="subsegmento", how="left")
    )

    presupuesto_out = _bloque_presupuesto(actual, ppto)

    # Fila TOTAL al final de cada sección (Totales al FOB / Total / Total General)
    total_actual, total_ppto, total_anterior = _totales(actual, anterior, stock, ppto)

    anio_actual = _records_segmentos(actual_out, sub_actual, incluir_subsegmentos=True)
    anio_actual.append(total_actual)

    presupuesto = _records_segmentos(presupuesto_out)
    presupuesto.append(total_ppto)

    anio_anterior = _records_segmentos(
        anterior_out,
        sub_anterior_out,
        incluir_subsegmentos=True,
        renombrar=_NOMBRES_ANIO_ANTERIOR,
        columnas_extra=["var_usd", "var_precio"],
    )
    anio_anterior.append(total_anterior)

    return {
        "anio_actual": anio_actual,
        "presupuesto": presupuesto,
        "anio_anterior": anio_anterior,
    }


def armar_reporte(
    datos_actual, datos_anterior, presupuesto, fecha_desde, fecha_hasta
) -> dict:
    """Arma el reporte final completo: los tres mercados sectorizados, cada uno
    con año actual, presupuesto y año anterior.

    - presupuesto: tabla de apilar_presupuesto (mercado, segmento, fecha_entrega,
      usd, tn).
    - fecha_desde/fecha_hasta: el rango pedido; el PPTO suma las entregas que
      caen ahí (el mismo rango que las ventas).
    """
    act = calcular_bloques(datos_actual)
    ant = calcular_bloques(datos_anterior)
    stock = act["stock"]  # mismo stock (inventario actual) para los tres bloques

    # PPTO por mercado; el TOTAL es externo + interno (mercado=None)
    ppto_me = kpis_presupuesto(presupuesto, fecha_desde, fecha_hasta, "externo")
    ppto_mi = kpis_presupuesto(presupuesto, fecha_desde, fecha_hasta, "interno")
    ppto_total = kpis_presupuesto(presupuesto, fecha_desde, fecha_hasta)

    return {
        "mercado_externo": bloque_comparado(
            act["me"], ant["me"], stock, act["sub_me"], ant["sub_me"], ppto_me
        ),
        "mercado_interno": bloque_comparado(
            act["mi"], ant["mi"], stock, act["sub_mi"], ant["sub_mi"], ppto_mi
        ),
        "total": bloque_comparado(
            act["total"], ant["total"], stock, act["sub_total"], ant["sub_total"], ppto_total
        ),
    }
