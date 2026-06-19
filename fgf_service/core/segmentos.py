"""Traducción de la clasificación de Finnegans (FAMILIA + SUBFAMILIA)
a las familias comerciales del reporte directorio (segmentos).

Mapeo descubierto en el Excel de stock de Marco (columna SEGMENTO 2).
"""

# (familia, subfamilia) → segmento
SEGMENTO_POR_FAMILIA_SUBFAMILIA = {
    ("ACEITE", "CONCENTRADO"): "ACEITES",
    ("ACEITE", "ESCENCIAL"): "ACEITES",  # sic: así está escrito en Finnegans
    ("CASCARA", "PROCESO A"): "CASCARAS",
    ("FIBRA", "CF-1"): "FIBRAS",
    ("FIBRA", "LF-19"): "FIBRAS",
    ("JUGO", "CLARIFICADO"): "JUGOS CONCENTRADOS",
    ("JUGO", "NFC"): "JUGOS NFC",
    ("JUGO", "TURBIO"): "JUGOS TOP",
    ("JUGO", "POLVO"): "OTROS",
}

# Familias que van enteras a OTROS, sin importar la subfamilia
FAMILIAS_OTROS = {
    "CERA",
    "DESTILADO",
    "ESENCIA",
    "EXTRACTO",
    "PULPA",
    "TERPENO",
}

SIN_CLASIFICAR = "SIN CLASIFICAR"

# Segmentos que existen en el detalle pero NO entran a los KPIs de ventas:
# la fruta fresca es otro negocio (este reporte es solo industria) y lo
# sin clasificar se excluye hasta que se le escriba su regla.
SEGMENTOS_EXCLUIDOS_KPIS = {"FRUTA FRESCA", SIN_CLASIFICAR}

def asignar_segmento(
    familia: str | None,
    subfamilia: str | None,
    producto: str | None = None,
) -> str:
    """Devuelve el segmento comercial de un registro.

    Cadena, de más autoritativa a más general:
    1. Familia de Finnegans en FAMILIAS_OTROS → OTROS (gana sobre la tabla:
       la tabla de Marco tiene mal cargados productos como ESENCIA y TERPENO
       en ACEITE; la familia de Finnegans es la fuente real).
    2. Por nombre de producto exacto (la tabla oficial Producto-Segmento).
    3. Por familia + subfamilia fabril (el mapeo del Excel de stock).
    4. SIN CLASIFICAR, para que el registro no se pierda y quede visible.
    """
    # Import acá adentro para evitar import circular y porque la tabla es grande
    from fgf_service.core.productos import SEGMENTO_POR_PRODUCTO

    producto = (producto or "").strip().upper()
    familia = (familia or "").strip().upper()
    subfamilia = (subfamilia or "").strip().upper()

    # 1) familia de Finnegans que va a OTROS (prioridad sobre la tabla)
    if familia in FAMILIAS_OTROS:
        return "OTROS"

    # 2) por producto (clasificación oficial)
    segmento = SEGMENTO_POR_PRODUCTO.get(producto)
    if segmento:
        return segmento

    # 3) por familia + subfamilia fabril
    segmento = SEGMENTO_POR_FAMILIA_SUBFAMILIA.get((familia, subfamilia))
    if segmento:
        return segmento

    # 4) red de seguridad
    return SIN_CLASIFICAR
