"""Cálculo de los KPIs del reporte ventas industria.

Recibe las tablas apiladas del detalle (ventas y stock) y produce
el resumen por segmento que consume el reporte final:
VENTAS USD, VENTAS TN, PRECIO USD/TN y STOCK TN, por mercado.

Acá vive la "receta" del reporte directorio (sacada del Excel de Marco):
qué filas entran a cada mercado y cómo se evita el doble conteo entre
APIVentasCap y APIAnalisisFacturacion.
"""

import pandas as pd

from fgf_service.core.segmentos import SEGMENTOS_EXCLUIDOS_KPIS

# Empresa de Facturación cuyas exportaciones NO están en VentasCap
# (las fibras de Dohler) y por eso SÍ se suman al mercado externo.
EMPRESA_FIBRAS_ME = "DOHLER-TRAPANI ARGENTINA S.A."

# Única sociedad cuyas ventas locales entran al bloque Mercado Interno
# del reporte directorio (las demás sociedades quedan en el detalle).
EMPRESA_MI = "FGF TRAPANI S.A."


def _solo_industria(df: pd.DataFrame) -> pd.DataFrame:
    """Excluye de los KPIs la fruta fresca y lo sin clasificar.

    Este reporte es solo de productos industriales; la fruta fresca es
    otro negocio. Las filas excluidas siguen visibles en el detalle.
    """
    return df[~df["segmento"].isin(SEGMENTOS_EXCLUIDOS_KPIS)]


def _resumir(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa un conjunto de filas de ventas por segmento y calcula los 3 KPIs.

    ventas_usd = suma de usd | ventas_tn = suma de tn
    precio_usd_tn = usd / tn (promedio ponderado; si tn es 0 queda vacío
    en vez de explotar por división por cero).
    """
    if df.empty:
        return pd.DataFrame(columns=["segmento", "ventas_usd", "ventas_tn", "precio_usd_tn"])
    resumen = (
        df.groupby("segmento", as_index=False)
        .agg(ventas_usd=("usd", "sum"), ventas_tn=("tn", "sum"))
    )
    resumen["precio_usd_tn"] = (
        resumen["ventas_usd"] / resumen["ventas_tn"].replace(0, pd.NA)
    ).round(2)
    return resumen


def kpis_mercado_externo(detalle_ventas: pd.DataFrame) -> pd.DataFrame:
    """KPIs de exportación.

    Receta:
    - VentasCap entero: es la ventanilla de exportación, todo cuenta.
    - De Facturación, SOLO las filas externas de Dohler (fibras):
      son las únicas exportaciones que VentasCap no ve.
    - El resto de filas externas de Facturación se excluye porque
      repiten ventas que ya están en VentasCap (doble conteo).
    """
    cap = detalle_ventas["fuente"] == "APIVentasCap"
    fibras_dohler = (
        (detalle_ventas["fuente"] == "APIAnalisisFacturacion")
        & (detalle_ventas["mercado"] == "externo")
        & (detalle_ventas["empresa"] == EMPRESA_FIBRAS_ME)
    )
    return _resumir(_solo_industria(detalle_ventas[cap | fibras_dohler]))


def kpis_mercado_interno(detalle_ventas: pd.DataFrame) -> pd.DataFrame:
    """KPIs de ventas locales.

    Receta: solo la sociedad principal (FGF Trapani) + las fibras locales
    de Dohler. Las demás sociedades del grupo quedan fuera de este bloque
    (igual que en el reporte de Marco), visibles en el detalle.

    Los USD de estas filas ya vienen de importemonsecundaria (la factura
    en pesos convertida a USD), asignado en detalle.py.
    """
    interno = (detalle_ventas["mercado"] == "interno") & (
        detalle_ventas["empresa"].isin([EMPRESA_MI, EMPRESA_FIBRAS_ME])
    )
    return _resumir(_solo_industria(detalle_ventas[interno]))


def kpis_stock(detalle_stock: pd.DataFrame) -> pd.DataFrame:
    """Stock en toneladas por segmento, sumando los 3 depósitos (ARG+EXT+DT)."""
    if detalle_stock.empty:
        return pd.DataFrame(columns=["segmento", "stock_tn"])
    return (
        detalle_stock.groupby("segmento", as_index=False)
        .agg(stock_tn=("tn", "sum"))
    )


def kpis_total(me: pd.DataFrame, mi: pd.DataFrame) -> pd.DataFrame:
    """Bloque TOTAL del reporte: ME + MI segmento por segmento.

    Se suman USD y TN; el precio se recalcula sobre los totales
    (es un promedio ponderado: nunca se suman precios).
    """
    juntos = pd.concat([me, mi], ignore_index=True)
    if juntos.empty:
        return pd.DataFrame(columns=["segmento", "ventas_usd", "ventas_tn", "precio_usd_tn"])
    total = (
        juntos.groupby("segmento", as_index=False)
        .agg(ventas_usd=("ventas_usd", "sum"), ventas_tn=("ventas_tn", "sum"))
    )
    total["precio_usd_tn"] = (
        total["ventas_usd"] / total["ventas_tn"].replace(0, pd.NA)
    ).round(2)
    return total
