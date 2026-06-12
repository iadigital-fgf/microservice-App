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
