"""MI REAL — Análisis Facturación (mercado interno).

Cada empresa es una conexión separada y trae SOLO su propia data (no se apila
el histórico de otra empresa). Las EMPRESAS quedan fijas; las fechas:
- el HISTÓRICO (solo EMPRE01: 2017-2022) va con fechas FIJAS (tal cual el Excel).
- la BASE va con las fechas que se le pasan al endpoint (parametrizada).

Crudo, tal cual la API.
"""

from datetime import date

from fgf_service.connectors.APIanalisis_facturacion import fetch_APIAnalisis_facturacion
from fgf_service.core.empresas import MercadoExterno, MercadoInterno


async def traer_facturacion_fgf(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """EMPRE01 (FGF): histórico 2017-2022 (fijo) + base (fechas pasadas)."""
    filas: list[dict] = []
    # AnalisisFacturasVentas-A 2017-2022   (histórico, fechas FIJAS)
    filas += await fetch_APIAnalisis_facturacion(
        date(2017, 1, 1), date(2022, 12, 31), access_token,
        empresa=MercadoInterno.FGF_TRAPANI,
    )
    # AnalisisFacturasVentas-A  (base, fechas parametrizadas)
    filas += await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoInterno.FGF_TRAPANI
    )
    return filas


async def traer_facturacion_dohler(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """DOHLER63 (Dohler): su propia data (base, fechas parametrizadas)."""
    # AnalisisFacturasVentas-A DTARG
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoExterno.DOHLER
    )


async def traer_facturacion_tucuman(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """TUCUMANTRAPANI69 (SA TT): su propia data (base, fechas parametrizadas)."""
    # AnalisisFacturasVentas-A SA TT
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoInterno.TUCUMAN_TRAPANI
    )


async def traer_facturacion_tgt(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """TGT61 (TGT): su propia data (base, fechas parametrizadas)."""
    # AnalisisFacturasVentas-A TGT
    return await fetch_APIAnalisis_facturacion(
        fecha_desde, fecha_hasta, access_token, empresa=MercadoExterno.TGT
    )
