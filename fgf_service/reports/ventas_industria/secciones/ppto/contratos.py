"""PPTO — Contratos.

Trae los datos de APIContratosIndustria (SIN empresa) por rango de fechas,
tal cual los devuelve Finnegans (claves en MAYÚSCULA). SIN cálculos agregados:
los del presupuesto y la proyección de cobros (cuotas por CONDICIONPAGO) los
arma Marco en su Excel.
"""

from datetime import date

from fgf_service.connectors.APIContratosIndustria import fetch_APIContratosIndustria


# Contratos
async def traer_contratos(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """Filas de APIContratosIndustria tal cual la API (crudo)."""
    return await fetch_APIContratosIndustria(fecha_desde, fecha_hasta, access_token)
