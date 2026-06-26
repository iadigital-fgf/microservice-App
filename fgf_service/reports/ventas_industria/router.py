"""Endpoints del reporte ventas industria.

La implementación vieja (KPIs/segmentación/armado) fue removida: ahora este
módulo expondrá el/los endpoint(s) de DATA CRUDA (todas las APIs de Finnegans
con sus columnas intactas), que se construyen en las próximas fases.

Por ahora es un stub vacío para que la app arranque sin la lógica vieja.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/reportes/ventas-industria", tags=["Ventas Industria"])
