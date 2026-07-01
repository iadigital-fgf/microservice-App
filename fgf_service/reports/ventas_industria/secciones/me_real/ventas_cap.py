"""ME REAL — Ventas Cap (exportación).

Cada consulta del Excel = una función = un cajón (1:1):
- AnalisisFacturasVentas         → base, fechas parametrizadas
- AnalisisFacturasVentas 2023-1S → histórico, fechas FIJAS
- AnalisisFacturasVentas 2023-2S → histórico, fechas FIJAS

Crudo, tal cual la API. El histórico 2017-2022 queda en el Excel (es un .xlsx,
no la API).
"""

from datetime import date

from fgf_service.connectors.APIventas_cap import fetch_APIVentas_cap


# AnalisisFacturasVentas  (base; arranca el año ANTERIOR, ver nota)
async def traer_ventas_cap_base(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """VentasCap base, crudo.

    Igual que contratos (PPTO): para poder armar "Exportación real 2025" hay que
    traer también el año anterior, así que se arranca el 1/1 del año previo al
    corte (NO desde fecha_desde). La fórmula se ajusta sola: cuando el corte pase
    a 2027, arranca en 2026. Esto puede cambiar más adelante (lo iremos viendo).
    """
    inicio = date(fecha_hasta.year - 1, 1, 1)  # corte 2026 -> 2025-01-01
    return await fetch_APIVentas_cap(inicio, fecha_hasta, access_token)


# AnalisisFacturasVentas 2023-1S  (histórico, fechas FIJAS)
async def traer_ventas_cap_2023_1s(access_token: str) -> list[dict]:
    """VentasCap 2023-01-01 → 2023-06-30 (fijo), crudo."""
    return await fetch_APIVentas_cap(date(2023, 1, 1), date(2023, 6, 30), access_token)


# AnalisisFacturasVentas 2023-2S  (histórico, fechas FIJAS)
async def traer_ventas_cap_2023_2s(access_token: str) -> list[dict]:
    """VentasCap 2023-07-01 → 2023-12-31 (fijo), crudo."""
    return await fetch_APIVentas_cap(date(2023, 7, 1), date(2023, 12, 31), access_token)
