from datetime import date

from fgf_service.core.finnegans import finnegans

async def fetch_APIVentas_cap(
    fecha_desde: date, fecha_hasta: date, access_token: str, empresa: str | None = None
) -> list[dict]:
    """Llama a APIVentasCap y devuelve los registros crudos."""
    return await finnegans.get(
        "APIVentascap",
        access_token=access_token,
        params={
            "PARAMWEBREPORT_FechaDesde": fecha_desde.strftime("%Y-%m-%d"),
            "PARAMWEBREPORT_FechaHasta": fecha_hasta.strftime("%Y-%m-%d"),
            "PARAMWEBREPORT_Empresa": empresa if empresa else None,
        },
    )
