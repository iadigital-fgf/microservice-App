"""STOCK — Laboratorio (AnalisisType).

Replica la query AnalisisType del Excel: toma APIAnalisisLaboratorio, filtra a
9 tipos de análisis puntuales y dedup por (LOTE, COD_ANA, COD_FINN, NOMBRE).
Es la versión filtrada de Analisis-LOTE (la misma data, pero solo los tipos que
usa el reporte) → mucho más liviana.
"""

from fgf_service.connectors.APIanalisis_laboratorio import fetch_APIAnalisis_laboratorio

# Tipos de análisis que deja pasar la query AnalisisType.
_TIPOS_ANALISIS = {
    "ACIDITY PERCENT, pH 8,1", "COLOR a*", "COLOR b*", "COLOR L*",
    "GPL", "pH (at 8º Bx)", "PULP", "RATIO CORRECTED", "TYPE",
}


def _dedup(filas: list[dict], claves: tuple) -> list[dict]:
    """Una fila por combinación de `claves` — la primera que aparece."""
    visto: set = set()
    unicas: list[dict] = []
    for fila in filas:
        clave = tuple(fila.get(c) for c in claves)
        if clave in visto:
            continue
        visto.add(clave)
        unicas.append(fila)
    return unicas


# AnalisisType
async def traer_analisis_type(access_token: str) -> list[dict]:
    """APIAnalisisLaboratorio filtrada a 9 tipos + dedup (igual que AnalisisType)."""
    crudo = await fetch_APIAnalisis_laboratorio(access_token)
    filtrado = [f for f in crudo if f.get("NOMBRE") in _TIPOS_ANALISIS]
    return _dedup(filtrado, ("LOTE", "COD_ANA", "COD_FINN", "NOMBRE"))
