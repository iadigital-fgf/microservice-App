from datetime import date
from fgf_service.core.finnegans import finnegans

async def fetch_APIAnalisis_facturacion(
    fecha_desde: date, fecha_hasta: date, access_token: str, empresa: str | None = None
) -> list[dict]:
    """Llama a APIAnalisisFacturacion y devuelve los registros crudos.

    Sin `empresa` trae los registros de todas las empresas juntas.
    """
    params = {
        "PARAMWEBREPORT_FechaDesde": fecha_desde.strftime("%Y-%m-%d"),
        "PARAMWEBREPORT_FechaHasta": fecha_hasta.strftime("%Y-%m-%d"),
    }
    if empresa is not None:
        params["PARAMWEBREPORT_Empresa"] = empresa
    return await finnegans.get(
        "APIAnalisisFacturacion",
        access_token=access_token,
        params=params,
    )
