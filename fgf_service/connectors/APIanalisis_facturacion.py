from datetime import date
from fgf_service.core.finnegans import finnegans

async def fetch_APIAnalisis_facturacion(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> list[dict]:
    """Llama a APIAnalisisFacturacion y devuelve los registros crudos."""
    return await finnegans.get(
        "APIAnalisisFacturacion",
        access_token=access_token,
        params={
            "PARAMWEB REPORT_FechaDesde": fecha_desde.strftime("%d-%m-%Y"),
            "PARAMWEB REPORT_FechaHasta": fecha_hasta.strftime("%d-%m-%Y"),
        },
    )
