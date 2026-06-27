"""ME REAL — Ventas Cap (exportación).

Reproduce las queries de VentasCap del Excel apilando:
- los HISTÓRICOS, con fechas FIJAS (tal cual el Excel): 2023-1S y 2023-2S.
- la BASE, con las fechas que se le pasan al endpoint (parametrizada).

Crudo, tal cual la API. El histórico 2017-2022 NO va acá: queda en el Excel
(es un archivo .xlsx, no la API).
"""

from datetime import date

from fgf_service.connectors.APIventas_cap import fetch_APIVentas_cap


async def traer_ventas_cap(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """VentasCap: 2023-1S + 2023-2S (fijos) + base (fechas pasadas), apilado."""
    filas: list[dict] = []

    # AnalisisFacturasVentas 2023-1S   (histórico, fechas FIJAS)
    filas += await fetch_APIVentas_cap(date(2023, 1, 1), date(2023, 6, 30), access_token)
    # AnalisisFacturasVentas 2023-2S   (histórico, fechas FIJAS)
    filas += await fetch_APIVentas_cap(date(2023, 7, 1), date(2023, 12, 31), access_token)
    # AnalisisFacturasVentas  (base, fechas parametrizadas)
    filas += await fetch_APIVentas_cap(fecha_desde, fecha_hasta, access_token)

    return filas
