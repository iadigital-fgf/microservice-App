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
- Formato final (solo endpoint reporte): entero (regla 50) + miles con punto.
  El detalle queda numérico (Marco lo formatea en Excel).

## Estado de validación (al 2026-06-16, contra Excel 03/06)

Mercado Externo USD: ACEITES, CASCARAS, FIBRAS, JUGOS CONCENTRADOS, JUGOS NFC
dan EXACTO. Falta JUGOS TOP (da 266k vs 420k esperado).

## Pendientes (próxima sesión, en orden)

1. **JUGOS TOP**: gap de ~154k. Filas existentes están bien (positivas,
   clasificadas, sin NC). Faltan filas → cruzar qué productos cuenta Marco
   como "JUGO LIMON TOP" que nosotros no.
2. **TN finas**: dan un poco altas (ACEITES, CASCARAS, CONC, NFC). Causa
   probable: notas de crédito. La fórmula TN es idéntica a Marco; revisar signos/NC.
3. **Mercado Interno**: validar contra Excel (hay un OTROS de ~1,8M que se cuela).
4. **Stock**: filtrar por estado "disponible" (campos estadocalidad/estadocomex);
   Marco cuenta solo lo vendible + warrant activo.
- Redis + APScheduler (refresh diario 6am) — diferido.
- Presupuesto (Excel manual del área comercial, NO viene de API) — diferido.
- Datos históricos 2025 — diferido.
- Front propio para Marco — diferido (Excel de depuración sobre /detalle alcanza).

## Referencias

- Excel original de Marco: `C:\Users\Agustin Fernandez\Desktop\venta industria\VENTAS INDUSTRIA 03 06 2026.xlsm`
  (las conexiones Power Query adentro tienen los parámetros exactos que usa hoy).
