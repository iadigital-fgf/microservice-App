# FGF Service — Microservicio Finnegans → Power BI

Microservicio FastAPI para FGF Trapani Group. Consume APIs del ERP Finnegans,
calcula KPIs y los expone para Power BI. Usuario final: Marco Velardez
(Responsable de Análisis y Planificación Financiera). El desarrollador (Agustín)
está aprendiendo: explicar los cambios en términos simples y siempre explicar
los cálculos.

## Regla de trabajo (CRÍTICA)

**Nunca editar código sin el "okey" explícito del usuario.**
Flujo: proponer → okey → editar → probar → corregir.

## Estructura

```
fgf_service/
├── core/          # config, cliente Finnegans, empresas.py (códigos y mapeo de mercados)
├── connectors/    # 1 archivo por API de Finnegans, devuelven list[dict] crudos
├── helpers/       # parsers.py — parse_finnegans (normaliza UPPERCASE → Pydantic)
└── reports/
    └── ventas_industria/   # 1 carpeta por reporte
        ├── schemas.py      # schemas Raw por API + ConsolidacionVentasIndustria
        ├── service.py      # orquesta llamadas (asyncio.gather) y separa mercados
        ├── kpis.py         # cálculos con pandas
        └── router.py       # endpoint FastAPI
```

Flujo de datos: connectors → service → kpis → router.

## Finnegans — particularidades

- Token: GET que devuelve un UUID; se pasa como query param `ACCESS_TOKEN`.
- Los nombres de parámetros llevan espacio: `PARAMWEB REPORT_FechaDesde` (formato dd-mm-YYYY).
- Los campos del JSON vienen en UPPERCASE → se normalizan con `parse_finnegans`.
- httpx async, timeout 120s. Una llamada completa al reporte tarda ~1.5 min (cache pendiente).
- **APIAnalisisFacturacion sin parámetro `empresa` devuelve TODAS las empresas juntas.**
  Por eso se hace 1 sola llamada sin empresa y se separa por mercado en Python
  (`separar_por_mercado` en service.py) usando el campo `EMPRESA` de cada registro
  y el dict `MERCADO_POR_EMPRESA` de core/empresas.py.
- Si aparece una empresa no mapeada, se descarta el registro y se loguea un warning
  → agregar el nombre exacto al dict.

## Empresas y mercados

Valores del campo `EMPRESA` en los registros (nombres exactos):
- `CAPACITACION` → externo (incluye ventas de TGT, confirmado: exportaciones en USD)
- `DOHLER-TRAPANI ARGENTINA S.A.` → externo
- `FGF TRAPANI S.A.` → interno
- `SA TUCUMAN TRAPANI` → interno
- Regla general (Marco): todas las S.A. / S.R.L. / S.A.S. son mercado interno, excepto TGT.

Parámetros `empresa` para otras APIs (códigos en core/empresas.py):
- APIVentasCap (mercado externo): `CAPACITACION43` (todo ME excepto fibra) + `DOHLER63` (fibra).
- APIStockProdIndustria: `EMPRE01` (ARG) + `CAPACITACION43` (EXT) + `DOHLER63` (DT).

## Reporte ventas_industria — arquitectura del cálculo

Flujo: connectors → service (trae datos) → detalle.py (traduce + apila) →
kpis.py (suma por segmento) → router.py (3 endpoints, formatea el final).

**Segmento** = familia comercial del reporte (ACEITES, CASCARAS, FIBRAS,
JUGOS CONCENTRADOS, JUGOS NFC, JUGOS TOP, OTROS). Se asigna en `core/segmentos.py`
con cadena: 1) tabla exacta producto→segmento (`core/productos.py`, generada del
Excel hoja Producto-Segmento), 2) familia+subfamilia, 3) SIN CLASIFICAR.
ACEITE DE SEMILLA va a ACEITES. FRUTA FRESCA y SIN CLASIFICAR se excluyen de KPIs.

**Reglas de negocio descubiertas (críticas):**
- **Parámetros API SIN espacio y fecha YYYY-MM-DD**: `PARAMWEBREPORT_Empresa`,
  `PARAMWEBREPORT_FechaDesde/Hasta`. Con espacio la API los IGNORA (no filtra
  empresa ni fecha). Fue la causa de fibras, fechas y stock triplicado.
- **Mercado por tipo de documento, NO por empresa**: si `transacconsubtiponombre`
  contiene "Exportación" → externo (usa `fobtotal`); si no → interno
  (usa `importemonsecundaria`). Una misma empresa factura export e interno.
- **VentasCap se llama SIN empresa** (1 sola vez, trae todas las exportaciones).
- **Dohler (fibras) necesita llamada dedicada** `empresa=DOHLER63`; la llamada
  general no trae sus exportaciones. Se sacan las filas Dohler de la general
  para no duplicar.
- **ME**: USD y TN de VentasCap, EXCEPTO fibras → USD de Dohler, TN de VentasCap.
- **MI**: solo FGF TRAPANI S.A. + fibras Dohler.
- **TN** = `cantidadstock2`/1000 si `unidadstock2`=="Kilos".
- **Notas de crédito**: en USD netean (vienen negativas, se incluyen); en TN
  NO cuentan (devuelven 0). Se detectan por `transacconsubtiponombre` que
  contiene "nota de cr". (`_es_nota_credito` / `_toneladas` en detalle.py.)
- División de precio usa `np.nan` (no `pd.NA`) para soportar `.round()` cuando TN=0.
- Formato final (solo endpoint reporte): entero (regla 50) + miles con punto.
  El detalle queda numérico (Marco lo formatea en Excel).

## Estado de validación (al 2026-06-17, contra Excel 03/06)

**Mercado Externo: VALIDADO (USD, TN y precio) en ACEITES, CASCARAS, FIBRAS,
JUGOS CONCENTRADOS, JUGOS NFC.** Único pendiente del ME: JUGOS TOP.

## Estado ME: VALIDADO (al 2026-06-18)

Los 6 segmentos del ME dan exacto con `fecha_hasta=2026-06-03` (la fecha del Excel
de Marco). JUGOS TOP era un tema de fecha de corte (el 03/06 hubo ventas de Top
que el 02/06 no incluía), no un bug. Único matiz: ESENCIA y TERPENO ahora van a
OTROS (su familia real en Finnegans), no a ACEITES. Esto hace que ACEITES USD
(~4.827.862) y OTROS difieran del reporte ACTUAL de Marco, que tiene esos productos
mal clasificados como ACEITE en su tabla Producto-Segmento.

## Pendientes (próxima sesión, en orden)

1. **CONFIRMAR CON MARCO** (bloqueante para cerrar ME al 100%): su tabla
   Producto-Segmento clasifica ESENCIA y TERPENO como ACEITE, pero Finnegans
   (campo FAMILIA) dice ESENCIA/TERPENO. Nosotros ya los pusimos en OTROS
   (correcto). Marco debe corregir su tabla (esos productos → OTROS) para que su
   reporte coincida con el nuestro en ACEITES USD y OTROS. Su reporte hoy es
   inconsistente (USD los cuenta en ACEITES, TN no).
2. **FIBRAS** residuo chico: USD 683.928 vs 683.538 (−390). Revisar si es NC o
   una fila de borde.
3. **Mercado Interno**: validar contra Excel. Bug conocido: OTROS da ~1,8M porque
   se cuelan líneas que NO son productos (anticipos, gastos, fletes, descuentos,
   demurrage). Fix propuesto (NO aplicado aún): excluir de KPIs los conceptos
   no-producto detectándolos por palabras en el nombre (Gasto, Anticipo, Servicio,
   Flete, Recupero, Reembolso, Descuento, Demurrage, Bonific, Comisión).
4. **Stock**: filtrar por estado "disponible" (campos estadocalidad/estadocomex);
   Marco cuenta solo lo vendible + warrant activo.

## Cómo verificar un KPI a mano (para Agustín)

El detalle ES la materia prima del KPI. Para comprobar cualquier número:
en Excel → Datos → Power Query → Nuevo origen → Web → pegar la URL de
`/detalle/ventas` (con access_token) → "En la tabla" → expandir columnas →
poner usd/tn como Número decimal → Cerrar y cargar → Tabla dinámica
(segmento en Filas, usd en Valores). OJO: el detalle tiene TODAS las filas;
para igualar un KPI hay que filtrar con la misma receta (ej. ME = mercado
externo + fuente APIVentasCap).
- Redis + APScheduler (refresh diario 6am) — diferido.
- Presupuesto (Excel manual del área comercial, NO viene de API) — diferido.
- Datos históricos 2025 — diferido.
- Front propio para Marco — diferido (Excel de depuración sobre /detalle alcanza).

## Referencias

- Excel original de Marco: `C:\Users\Agustin Fernandez\Desktop\venta industria\VENTAS INDUSTRIA 03 06 2026.xlsm`
  (las conexiones Power Query adentro tienen los parámetros exactos que usa hoy).
