from datetime import date
from fgf_service.core.finnegans import finnegans

async def fetch_APIAnalisis_facturacion(
    fecha_desde: date, fecha_hasta: date, access_token: str, empresa: str | None = None
) -> list[dict]:
    """Llama a APIAnalisisFacturacion y devuelve los registros crudos.

    Sin `empresa` trae los registros de todas las empresas juntas.
    """
    params = {
        "PARAMWEB REPORT_FechaDesde": fecha_desde.strftime("%d-%m-%Y"),
        "PARAMWEB REPORT_FechaHasta": fecha_hasta.strftime("%d-%m-%Y"),
    }
    if empresa is not None:
        params["PARAMWEB REPORT_Empresa"] = empresa
    return await finnegans.get(
        "APIAnalisisFacturacion",
        access_token=access_token,
        params=params,
    )
