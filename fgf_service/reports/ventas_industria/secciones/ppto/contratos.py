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
    """Filas de APIContratosIndustria tal cual la API (crudo).

    PPTO: los contratos del presupuesto se cargan durante el año ANTERIOR, así
    que se traen desde el 1/1 del año previo al corte (NO desde fecha_desde),
    para no perderlos. El fecha_desde principal se ignora solo en esta sección.
    """
    inicio_ppto = date(fecha_hasta.year - 1, 1, 1)  # corte 2026 -> 2025-01-01
    return await fetch_APIContratosIndustria(inicio_ppto, fecha_hasta, access_token)
