from datetime import date
from fgf_service.core.finnegans import finnegans


async def fetch_APIContratosIndustria(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """Llama a APIContratosIndustria y devuelve los contratos crudos.

    Es la fuente del PRESUPUESTO: los contratos marcados como
    DESCRIPCION="PPTO ME/MI {año}" son los objetivos de venta.
    Toma rango de fechas (sin empresa), igual que la API de facturación.
    """
    return await finnegans.get(
        "APIContratosIndustria",
        access_token=access_token,
        params={
            "PARAMWEBREPORT_FechaDesde": fecha_desde.strftime("%Y-%m-%d"),
            "PARAMWEBREPORT_FechaHasta": fecha_hasta.strftime("%Y-%m-%d"),
        },
    )
