from datetime import date

from fgf_service.connectors.finnegans import finnegans


async def fetch_ventas_cap(fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Llama a APIVentasCap y devuelve los registros crudos."""
    return await finnegans.get(
        "/reports/APIVentascap",
        params={
            "PARAMWEB REPORT_FechaDesde": fecha_desde.strftime("%d/%m/%Y"),
            "PARAMWEB REPORT_FechaHasta": fecha_hasta.strftime("%d/%m/%Y"),
        },
    )
