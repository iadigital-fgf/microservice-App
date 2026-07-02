from fgf_service.core.finnegans import finnegans

#URL: /reports/APIAnalisisLaboratorio

async def fetch_APIAnalisis_laboratorio() -> list[dict]:
    """Llama a APIAnalisisLaboratorio y devuelve los registros crudos."""
    return await finnegans.get("APIAnalisisLaboratorio")
