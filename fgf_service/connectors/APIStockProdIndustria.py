from fgf_service.core.finnegans import finnegans
from datetime import date
#URL: /reports/APIStockProdIndustria

async def fetch_APIStockProdIndustria(
    fecha_hasta: date, access_token: str, empresa: str
) -> list[dict]:
    """Llama a APIStockProdIndustria y devuelve los registros crudos."""
    return await finnegans.get(
        "APIStockProdIndustria",
        access_token=access_token,
        params={
            "PARAMWEB REPORT_Fecha": fecha_hasta.strftime("%d-%m-%Y"),
            "PARAMWEB REPORT_Empresa": empresa,
        },
    )