"""Formateo visual de números para el reporte final (no para el detalle).

Convierte números a texto con separador de miles "." y decimal ","
(formato argentino). Se aplica como ÚLTIMO paso, después de todos los
cálculos, así no afecta ninguna suma.
"""

import math
from decimal import Decimal, ROUND_HALF_UP


def _formatear_numero(valor) -> str:
    """Redondea al entero más cercano (decimal <50 baja, >=50 sube) y
    formatea con separador de miles. 1234567.5 -> '1.234.568'. None/NaN -> '-'.
    """
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "-"
    entero = int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    # f-string da miles con ','; se cambia por '.'
    return f"{entero:,}".replace(",", ".")


def formatear_bloque(filas: list[dict], columnas: list[str]) -> list[dict]:
    """Devuelve las filas con las columnas indicadas formateadas como texto."""
    return [
        {
            k: (_formatear_numero(v) if k in columnas else v)
            for k, v in fila.items()
        }
        for fila in filas
    ]
