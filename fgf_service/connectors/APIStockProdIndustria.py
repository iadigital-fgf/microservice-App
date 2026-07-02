from fgf_service.core.finnegans import finnegans
from datetime import date
#URL: /reports/APIStockProdIndustria

async def fetch_APIStockProdIndustria(
    fecha_hasta: date, empresa: str
) -> list[dict]:
    """Llama a APIStockProdIndustria y devuelve los registros crudos."""
    return await finnegans.get(
        "APIStockProdIndustria",
        params={
            "PARAMWEBREPORT_Fecha": fecha_hasta.strftime("%Y-%m-%d"),
            "PARAMWEBREPORT_Empresa": empresa,
        },
    )
