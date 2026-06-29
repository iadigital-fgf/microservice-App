"""MI REAL — Análisis Facturación (mercado interno).

Cada consulta del Excel = una función = un cajón (1:1). Las EMPRESAS quedan
fijas; las fechas: el histórico de EMPRE01 (2017-2022) va con fechas FIJAS, el
resto con fechas parametrizadas. Cada empresa trae SOLO su propia data.
Crudo, tal cual la API.
"""

from datetime import date

from fgf_service.connectors.APIanalisis_facturacion import fetch_APIAnalisis_facturacion
from fgf_service.core.empresas import MercadoExterno, MercadoInterno


# AnalisisFacturasVentas-A  (EMPRE01, base, fechas parametrizadas)
async def traer_facturacion_fgf_base(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """Facturación EMPRE01 (FGF), base, fechas que se pasan, crudo."""
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoInterno.FGF_TRAPANI
    )


# AnalisisFacturasVentas-A 2017-2022  (EMPRE01, histórico, fechas FIJAS)
async def traer_facturacion_fgf_2017_2022(access_token: str) -> list[dict]:
    """Facturación EMPRE01 (FGF), 2017-01-01 → 2022-12-31 (fijo), crudo."""
    return await fetch_APIAnalisis_facturacion(
        date(2017, 1, 1), date(2022, 12, 31), access_token,
        empresa=MercadoInterno.FGF_TRAPANI,
    )


# AnalisisFacturasVentas-A DTARG  (DOHLER63, base, fechas parametrizadas)
async def traer_facturacion_dohler(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """Facturación DOHLER63 (Dohler), su propia data, crudo."""
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoExterno.DOHLER
    )


# AnalisisFacturasVentas-A SA TT  (TUCUMANTRAPANI69, base, fechas parametrizadas)
async def traer_facturacion_tucuman(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """Facturación TUCUMANTRAPANI69 (SA TT), su propia data, crudo."""
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoInterno.TUCUMAN_TRAPANI
    )


# AnalisisFacturasVentas-A TGT  (TGT61, base, fechas parametrizadas)
async def traer_facturacion_tgt(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """Facturación TGT61 (TGT), su propia data, crudo."""
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoExterno.TGT
    )
