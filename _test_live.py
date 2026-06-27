import asyncio, httpx
from datetime import date
from fgf_service.reports.ventas_industria.service import traer_todo

TOKEN_URL = ("https://api.finneg.com/api/oauth/token?grant_type=client_credentials"
             "&client_id=a6d4fd3c62bafd6fc9a4102838ea1b8e"
             "&client_secret=6b740b66886a42246a11ad4031cbd2c2")

async def main():
    async with httpx.AsyncClient(timeout=60) as c:
        token = (await c.get(TOKEN_URL)).text.strip().strip('"')
    # contratos/despachos usan este rango; ventas/facturacion traen su histórico fijo
    data = await traer_todo(date(2026,1,1), date(2026,1,31), token)
    print("CAJONES:", len(data))
    for cajon, filas in data.items():
        cols = len(filas[0]) if filas else 0
        print(f"  {cajon:22s} filas={len(filas):7d}  columnas={cols}")

asyncio.run(main())
