"""MI REAL — Análisis Facturación (mercado interno).

Cada consulta del Excel = una función = un cajón (1:1). Las EMPRESAS quedan
fijas; las fechas: el histórico de EMPRE01 (2017-2022) va con fechas FIJAS, el
resto con fechas parametrizadas. Cada empresa trae SOLO su propia data.
Crudo, tal cual la API.
"""

from datetime import date

from fgf_service.connectors.APIanalisis_facturacion import fetch_APIAnalisis_facturacion
from fgf_service.core.empresas import MercadoExterno, MercadoInterno


# AnalisisFacturasVentas-A  (EMPRE01, base; arranca el año ANTERIOR, ver nota)
async def traer_facturacion_fgf_base(fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Facturación EMPRE01 (FGF), base, crudo.

    Igual que contratos/ventas_cap: arranca el 1/1 del año anterior al corte (NO
    desde fecha_desde), para traer el MI real del año previo (ej. 2025) además del
    actual. El histórico 2017-2022 va en su propio cajón y se appendea en el Excel.
    OJO: esto deja 2023-2024 sin traer; si hicieran falta, pasar a inicio fijo.
    """
    inicio = date(fecha_hasta.year - 1, 1, 1)  # corte 2026 -> 2025-01-01
    return await fetch_APIAnalisis_facturacion(
        inicio, fecha_hasta, empresa=MercadoInterno.FGF_TRAPANI
    )


# AnalisisFacturasVentas-A 2017-2022  (EMPRE01, histórico, fechas FIJAS)
async def traer_facturacion_fgf_2017_2022() -> list[dict]:
    """Facturación EMPRE01 (FGF), 2017-01-01 → 2022-12-31 (fijo), crudo."""
    return await fetch_APIAnalisis_facturacion(
        date(2017, 1, 1), date(2022, 12, 31),
        empresa=MercadoInterno.FGF_TRAPANI,
    )


# AnalisisFacturasVentas-A DTARG  (DOHLER63, base, fechas parametrizadas)
async def traer_facturacion_dohler(fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Facturación DOHLER63 (Dohler), su propia data, crudo."""
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, empresa=MercadoExterno.DOHLER
    )


# AnalisisFacturasVentas-A SA TT  (TUCUMANTRAPANI69, base; arranca el año ANTERIOR)
async def traer_facturacion_tucuman(fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Facturación TUCUMANTRAPANI69 (SA TT), su propia data, crudo.

    También es mercado interno → misma lógica que EMPRE01: arranca el 1/1 del año
    anterior al corte, para tener el MI real del año previo (ej. 2025).
    """
    inicio = date(fecha_hasta.year - 1, 1, 1)  # corte 2026 -> 2025-01-01
    return await fetch_APIAnalisis_facturacion(
        inicio, fecha_hasta, empresa=MercadoInterno.TUCUMAN_TRAPANI
    )


# AnalisisFacturasVentas-A TGT  (TGT61, base, fechas parametrizadas)
async def traer_facturacion_tgt(fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Facturación TGT61 (TGT), su propia data, crudo."""
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, empresa=MercadoExterno.TGT
    )
