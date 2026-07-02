"""STOCK — Stock por depósito.

Foto del stock a HOY (la API no acepta fecha histórica). Una conexión por
empresa, igual que el Excel. Se replica TAL CUAL la query (incluido el filtro
de EXT): se prioriza lo que hace la consulta del Excel.
"""

from datetime import date

from fgf_service.connectors.APIStockProdIndustria import fetch_APIStockProdIndustria
from fgf_service.core.empresas import Stock

# Depósitos que NO son stock propio: la mercadería ya está en poder del cliente.
# La query Stock-EXT del Excel los excluye, así que replicamos ese filtro.
_DEPOSITOS_CLIENTE = {"CLIENTE DESTINO", "CLIENTE FINAL"}


# Stock-ARG
async def traer_stock_arg() -> list[dict]:
    """APIStockProdIndustria — EMPRE01 (Argentina), foto a hoy."""
    return await fetch_APIStockProdIndustria(date.today(), empresa=Stock.ARG)


# Stock-EXT
async def traer_stock_ext() -> list[dict]:
    """APIStockProdIndustria — CAPACITACION43 (Exterior), foto a hoy.

    FILTRO (igual que la query Stock-EXT): se excluyen las filas cuyo DEPOSITO
    es 'CLIENTE DESTINO' o 'CLIENTE FINAL' (stock ya entregado al cliente).
    """
    filas = await fetch_APIStockProdIndustria(date.today(), empresa=Stock.EXT)
    return [f for f in filas if f.get("DEPOSITO") not in _DEPOSITOS_CLIENTE]


# Stock-DT
async def traer_stock_dt() -> list[dict]:
    """APIStockProdIndustria — DOHLER63 (Dohler), foto a hoy."""
    return await fetch_APIStockProdIndustria(date.today(), empresa=Stock.DT)
