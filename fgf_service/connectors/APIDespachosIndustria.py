from datetime import date

from fgf_service.core.finnegans import finnegans


async def fetch_APIDespachosIndustria(
    fecha_desde: date, fecha_hasta: date
) -> list[dict]:
    """Llama a APIDespachosIndustria (despachos/embarques) y devuelve crudo.

    Toma rango de fechas (sin empresa), igual que la query del Excel.
    """
    return await finnegans.get(
        "APIDespachosIndustria",
        params={
            "PARAMWEBREPORT_fechaDesde": fecha_desde.strftime("%Y-%m-%d"),
            "PARAMWEBREPORT_fechaHasta": fecha_hasta.strftime("%Y-%m-%d"),
        },
    )
