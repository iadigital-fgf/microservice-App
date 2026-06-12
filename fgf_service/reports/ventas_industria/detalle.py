"""Arma el detalle de ventas: traduce los renglones crudos de cada API
al formato común y los apila en una sola tabla.

Cada fila del detalle es un renglón de factura (o nota de crédito, que
viene con valores negativos y resta sola al sumar).
"""

import pandas as pd

from fgf_service.core.empresas import MERCADO_POR_EMPRESA
from fgf_service.core.segmentos import asignar_segmento
from fgf_service.reports.ventas_industria.schemas import (
    APIVentasCapRaw,
    APIAnalisisFacturacionRaw,
    APIStockProdIndustriaRaw,
)

# Columnas comunes del detalle (el "idioma común" de las dos fuentes)
COLUMNAS_DETALLE = [
    "fuente", "mercado", "segmento",          # asignadas por nosotros
    "fecha", "comprobante", "transaccionid",  # trazabilidad hacia Finnegans
    "empresa", "cliente", "producto",
    "familia", "subfamilia",                  # clasificación fabril original
    "usd", "tn",                              # los números que se suman
]


def _toneladas(cantidad: float | None, unidad: str | None) -> float:
    """Convierte la cantidad a toneladas: si viene en kilos, divide por 1000."""
    cantidad = cantidad or 0.0
    if (unidad or "").strip().lower() == "kilos":
        return cantidad / 1000
    return cantidad


def detalle_ventas_cap(registros: list[APIVentasCapRaw]) -> pd.DataFrame:
    """Renglones de APIVentasCap → formato común. Todo es mercado externo.

    Los USD salen de totalfob (valor FOB del renglón completo).
    """
    filas = []
    for r in registros:
        filas.append({
            "fuente": "APIVentasCap",
            "mercado": "externo",
            # VentasCap no trae subfamilia: clasifica por nombre de producto
            "segmento": asignar_segmento(r.familia, None, r.producto),
            "fecha": r.fecha,
            "comprobante": r.comprobante,
            "transaccionid": r.transaccionid,
            "empresa": r.empresa,
            "cliente": r.cliente,
            "producto": r.producto,
            "familia": r.familia,
            "subfamilia": None,
            "usd": r.totalfob or 0.0,
            "tn": _toneladas(r.cantidadstock2, r.unidadstock2),
        })
    return pd.DataFrame(filas, columns=COLUMNAS_DETALLE)


def detalle_facturacion(registros: list[APIAnalisisFacturacionRaw]) -> pd.DataFrame:
    """Renglones de APIAnalisisFacturacion → formato común.

    El mercado sale del campo EMPRESA. Los USD según el mercado:
    externo (fibras Dohler) usa fobtotal, interno usa importemonsecundaria
    (la factura en pesos convertida a USD al tipo de cambio del día).
    """
    filas = []
    for r in registros:
        mercado = MERCADO_POR_EMPRESA.get((r.empresa or "").strip())
        usd = r.fobtotal if mercado == "externo" else r.importemonsecundaria
        filas.append({
            "fuente": "APIAnalisisFacturacion",
            "mercado": mercado or "sin clasificar",
            "segmento": asignar_segmento(r.familia, r.subfamilia, r.producto),
            "fecha": r.fecha,
            "comprobante": r.comprobante,
            "transaccionid": r.transaccionid,
            "empresa": r.empresa,
            "cliente": r.cliente,
            "producto": r.producto,
            "familia": r.familia,
            "subfamilia": r.subfamilia,
            "usd": usd or 0.0,
            "tn": _toneladas(r.cantidadstock2, r.unidadstock2),
        })
    return pd.DataFrame(filas, columns=COLUMNAS_DETALLE)


def apilar_detalle_ventas(
    ventas_cap: list[APIVentasCapRaw],
    facturacion: list[APIAnalisisFacturacionRaw],
) -> pd.DataFrame:
    """Apila las dos fuentes en la tabla única del detalle de ventas."""
    return pd.concat(
        [detalle_ventas_cap(ventas_cap), detalle_facturacion(facturacion)],
        ignore_index=True,
    )


# ---------------------------------------------------------------------------
# Detalle de stock
#
# El stock no son facturas: son LOTES (partidas físicas de producción que
# están en una cámara esperando comprador). Cada fila de APIStockProdIndustria
# dice "en el depósito X hay tantos kilos del lote L de tal producto".
# Es una foto del momento, no un histórico.
# ---------------------------------------------------------------------------

# Columnas comunes del detalle de stock
COLUMNAS_DETALLE_STOCK = [
    "fuente", "deposito", "segmento",       # asignadas por nosotros
    "producto", "productocodigo", "lugar",
    "partida",                              # el lote (trazabilidad hacia Finnegans)
    "familia", "subfamilia",                # clasificación fabril original
    "tn",                                   # lo único que se suma
]


def detalle_stock(
    registros: list[APIStockProdIndustriaRaw], deposito: str
) -> pd.DataFrame:
    """Lotes de APIStockProdIndustria → formato común.

    `deposito` etiqueta de qué llamada vino cada fila: "ARG" (Argentina),
    "EXT" (exterior) o "DT" (Dohler). Las toneladas salen de cantidad2,
    convertidas con la misma regla que ventas (si está en kilos, /1000).
    """
    filas = []
    for r in registros:
        filas.append({
            "fuente": "APIStockProdIndustria",
            "deposito": deposito,
            "segmento": asignar_segmento(r.familia, r.subfamilia, r.producto),
            "producto": r.producto,
            "productocodigo": r.productocodigo,
            "lugar": r.lugar,
            "partida": r.partida,
            "familia": r.familia,
            "subfamilia": r.subfamilia,
            "tn": _toneladas(r.cantidad2, r.unidad2),
        })
    return pd.DataFrame(filas, columns=COLUMNAS_DETALLE_STOCK)


def apilar_detalle_stock(
    stock_arg: list[APIStockProdIndustriaRaw],
    stock_ext: list[APIStockProdIndustriaRaw],
    stock_dt: list[APIStockProdIndustriaRaw],
) -> pd.DataFrame:
    """Apila los 3 depósitos en la tabla única del detalle de stock.

    El stock total del grupo es la suma de los tres: lo que hay en
    Argentina + lo ya embarcado al exterior + lo de Dohler.
    """
    return pd.concat(
        [
            detalle_stock(stock_arg, "ARG"),
            detalle_stock(stock_ext, "EXT"),
            detalle_stock(stock_dt, "DT"),
        ],
        ignore_index=True,
    )
