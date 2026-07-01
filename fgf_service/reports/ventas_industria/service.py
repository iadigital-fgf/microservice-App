"""Orquestador del reporte VENTAS INDUSTRIA.

Junta TODAS las conexiones a Finnegans y devuelve un único dict con un cajón por
consulta del Excel (1:1). El Excel le pega una sola vez y cada tabla toma su
cajón. Esto es lo que se cachea (corrida 3am).
"""

import asyncio
import logging
from datetime import date

from fgf_service.reports.ventas_industria.secciones.me_real.ventas_cap import (
    traer_ventas_cap_base,
    traer_ventas_cap_2023_1s,
    traer_ventas_cap_2023_2s,
)
from fgf_service.reports.ventas_industria.secciones.mi_real.facturacion import (
    traer_facturacion_fgf_base,
    traer_facturacion_fgf_2017_2022,
    traer_facturacion_dohler,
    traer_facturacion_tucuman,
    traer_facturacion_tgt,
)
from fgf_service.reports.ventas_industria.secciones.ppto.contratos import (
    traer_contratos,
)
from fgf_service.reports.ventas_industria.secciones.stock.stock import (
    traer_stock_arg,
    traer_stock_ext,
    traer_stock_dt,
)
from fgf_service.reports.ventas_industria.secciones.stock.despachos import (
    traer_despachos,
)
from fgf_service.reports.ventas_industria.secciones.stock.laboratorio import (
    traer_analisis_type,
)
from fgf_service.core import producto_segmento

logger = logging.getLogger(__name__)

# Límite de llamadas SIMULTÁNEAS a Finnegans. Con las 14 a la vez el servidor se
# sobrecarga y las más lentas (stock_ext, facturacion_tgt) devuelven 500; de a
# pocas, todas responden bien.
_LIMITE = asyncio.Semaphore(6)


async def _seguro(coro, fallas: list) -> list:
    """Ejecuta una conexión con límite de concurrencia, tolerando fallas.

    Si falla (ej. un 500 por sobrecarga que agotó los reintentos), loguea, anota
    la falla en `fallas` y devuelve [] (cajón vacío) en vez de propagar — así una
    API caída NO tumba todo el reporte. `fallas` le sirve al caller para NO
    cachear una corrida incompleta (y reintentar en la próxima).
    """
    async with _LIMITE:
        try:
            return await coro
        except Exception as e:  # noqa: BLE001 — a propósito: cualquier falla -> cajón vacío
            logger.warning("Una conexión falló; se devuelve cajón vacío: %s", e)
            fallas.append(str(e))
            return []


async def traer_todo(
    fecha_desde: date, fecha_hasta: date, access_token: str
) -> tuple[dict, bool]:
    """Llama a todas las conexiones (en paralelo, limitado) y arma el JSON.

    Devuelve `(reporte, completo)`: `completo=False` si alguna conexión falló.
    En ese caso el caller NO debería cachear (para reintentar en la próxima).
    """
    fallas: list = []
    (
        ventas_cap_base,        # AnalisisFacturasVentas (base)
        ventas_cap_2023_1s,     # AnalisisFacturasVentas 2023-1S
        ventas_cap_2023_2s,     # AnalisisFacturasVentas 2023-2S
        facturacion_fgf_base,   # AnalisisFacturasVentas-A (EMPRE01 base)
        facturacion_fgf_2017_2022,  # AnalisisFacturasVentas-A 2017-2022
        facturacion_dohler,     # AnalisisFacturasVentas-A DTARG
        facturacion_tucuman,    # AnalisisFacturasVentas-A SA TT
        facturacion_tgt,        # AnalisisFacturasVentas-A TGT
        contratos,              # Contratos
        stock_arg,              # Stock-ARG
        stock_ext,              # Stock-EXT
        stock_dt,               # Stock-DT
        despachos,              # Despachos
        analisis_type,          # AnalisisType
    ) = await asyncio.gather(
        _seguro(traer_ventas_cap_base(fecha_desde, fecha_hasta, access_token), fallas),
        _seguro(traer_ventas_cap_2023_1s(access_token), fallas),
        _seguro(traer_ventas_cap_2023_2s(access_token), fallas),
        _seguro(traer_facturacion_fgf_base(fecha_desde, fecha_hasta, access_token), fallas),
        _seguro(traer_facturacion_fgf_2017_2022(access_token), fallas),
        _seguro(traer_facturacion_dohler(fecha_desde, fecha_hasta, access_token), fallas),
        _seguro(traer_facturacion_tucuman(fecha_desde, fecha_hasta, access_token), fallas),
        _seguro(traer_facturacion_tgt(fecha_desde, fecha_hasta, access_token), fallas),
        _seguro(traer_contratos(fecha_desde, fecha_hasta, access_token), fallas),
        _seguro(traer_stock_arg(access_token), fallas),
        _seguro(traer_stock_ext(access_token), fallas),
        _seguro(traer_stock_dt(access_token), fallas),
        _seguro(traer_despachos(fecha_desde, fecha_hasta, access_token), fallas),
        _seguro(traer_analisis_type(access_token), fallas),
    )

    reporte = {
        # ── ME real (VentasCap) ──
        "ventas_cap_base": ventas_cap_base,            # AnalisisFacturasVentas (base)
        "ventas_cap_2023_1s": ventas_cap_2023_1s,      # AnalisisFacturasVentas 2023-1S
        "ventas_cap_2023_2s": ventas_cap_2023_2s,      # AnalisisFacturasVentas 2023-2S
        # ── MI real (Facturación) ──
        "facturacion_fgf_base": facturacion_fgf_base,            # -A (EMPRE01 base)
        "facturacion_fgf_2017_2022": facturacion_fgf_2017_2022,  # -A 2017-2022
        "facturacion_dohler": facturacion_dohler,                # -A DTARG
        "facturacion_tucuman": facturacion_tucuman,              # -A SA TT
        "facturacion_tgt": facturacion_tgt,                      # -A TGT
        # ── PPTO ──
        "contratos": contratos,                        # Contratos
        # ── Stock ──
        "stock_arg": stock_arg,                        # Stock-ARG
        "stock_ext": stock_ext,                        # Stock-EXT
        "stock_dt": stock_dt,                          # Stock-DT
        "despachos": despachos,                        # Despachos
        "analisis_type": analisis_type,                # AnalisisType
        # ── Referencia (estática, mantenida por Marco) ──
        "producto_segmento": producto_segmento.tabla(),  # Producto-Segmento
    }
    return reporte, len(fallas) == 0
