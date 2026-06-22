class MercadoExterno:
    DOHLER = "DOHLER63"
    TGT = "TGT61"

class MercadoInterno:
    FGF_TRAPANI = "EMPRE01"
    EXPORTADORA = "EXPORTADORA59"
    AUSTRAL = "AUSTRAL57"
    LABORES_AGRICOLAS = "LABORESAGRICOLAS51"
    NEWA_EXPORT = "NEWAEXPORT67"
    TUCUMAN_TRAPANI = "TUCUMANTRAPANI69"
    TAFI_HOUSING = "TAFIHOUSING45"
    TRAPANI_FRESH = "TRAPANIFRESH55"


# Valores del campo EMPRESA en los registros (la sociedad que emite la factura)
EMPRESA_DOHLER = "DOHLER-TRAPANI ARGENTINA S.A."  # vende la fibra
EMPRESA_FGF = "FGF TRAPANI S.A."  # mercado interno (ventas locales)


# Valores del campo EMPRESA en los registros de APIAnalisisFacturacion → mercado
MERCADO_POR_EMPRESA = {
    "CAPACITACION": "externo",
    "DOHLER-TRAPANI ARGENTINA S.A.": "externo",
    "FGF TRAPANI S.A.": "interno",
    "SA TUCUMAN TRAPANI": "interno",
}


class Stock:
    ARG = "EMPRE01"
    EXT = "CAPACITACION43"
    DT = "DOHLER63"


# Empresas del propio grupo FGF Trapani, como aparecen en el campo CLIENTE.
# Una venta a una de estas es intercompany (movimiento interno del grupo),
# no una venta real al mercado → se excluye de los KPIs.
# OJO: "Dohler Trapani ARGENTINA" es del grupo; "Dohler Trapani NETHERLANDS"
# es el destino de exportación y NO se excluye.
EMPRESAS_GRUPO = (
    "TUCUMAN TRAPANI",
    "DOHLER TRAPANI ARGENTINA",
    "FGF TRAPANI",
    "CAPACITACION",
    "EXPORTADORA TRAPANI",
    "LABORATORIO AUSTRAL",
    "LABORES AGRICOLAS",
    "NEWA EXPORT",
    "TAFI HOUSING",
    "TRAPANI FRESH",
    "TGT",
)


def es_cliente_del_grupo(cliente: str | None) -> bool:
    """True si el cliente es otra empresa del grupo (venta intercompany)."""
    c = (cliente or "").upper()
    return any(g in c for g in EMPRESAS_GRUPO)
