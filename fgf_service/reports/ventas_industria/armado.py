"""Armado del reporte ventas industria.

Funciones específicas de ESTE reporte: comparación año contra año (mismo
período del año anterior) y armado de la estructura final, sectorizada por
mercado (externo, interno, total). El router solo llama a `armar_reporte`.
"""

import math
from datetime import date

import numpy as np
import pandas as pd

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
    }


def _variacion(actual: pd.DataFrame, anterior: pd.DataFrame) -> pd.DataFrame:
    """Columnas VAR % = valor año actual / valor año anterior (ratio, como Marco)."""
    m = actual.merge(anterior, on="segmento", how="left", suffixes=("", "_ant"))
    out = pd.DataFrame({"segmento": m["segmento"]})
    out["var_usd"] = (m["ventas_usd"] / m["ventas_usd_ant"].replace(0, np.nan)).round(4)
    out["var_precio"] = (
        m["precio_usd_tn"] / m["precio_usd_tn_ant"].replace(0, np.nan)
    ).round(4)
    return out


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → lista de dicts, con NaN convertido a None (JSON no acepta NaN)."""
    return [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()}
        for r in df.to_dict(orient="records")
    ]


def bloque_comparado(
    actual: pd.DataFrame, anterior: pd.DataFrame, stock: pd.DataFrame
) -> dict:
    """Arma un bloque sectorizado: año actual y año anterior.

    - anio_actual: ventas_usd, ventas_tn, precio_usd_tn + stock_tn.
    - anio_anterior: ventas_real_usd, precio_fob_real + var_usd, var_precio
      (sin ventas_tn, que ese bloque del reporte no muestra).
    """
    variacion = _variacion(actual, anterior)  # se calcula con los nombres originales
    actual_out = actual.merge(stock, on="segmento", how="left")
    anterior_out = (
        anterior.rename(columns=_NOMBRES_ANIO_ANTERIOR)
        .drop(columns=["ventas_tn"])
        .merge(variacion, on="segmento", how="left")
    )
    return {
        "anio_actual": _records(actual_out),
        "anio_anterior": _records(anterior_out),
    }


def armar_reporte(datos_actual, datos_anterior) -> dict:
    """Arma el reporte final completo: los tres mercados sectorizados, cada uno
    con año actual, año anterior y variación."""
    act = calcular_bloques(datos_actual)
    ant = calcular_bloques(datos_anterior)
    stock = act["stock"]  # mismo stock (inventario actual) para los tres bloques
    return {
        "mercado_externo": bloque_comparado(act["me"], ant["me"], stock),
        "mercado_interno": bloque_comparado(act["mi"], ant["mi"], stock),
        "total": bloque_comparado(act["total"], ant["total"], stock),
    }
