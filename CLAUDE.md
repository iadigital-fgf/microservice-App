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

## Reporte ventas_industria — cálculos

Por familia (JUGO, ACEITE, FIBRA, PULPA — FAMILIA vacía = limón fresco, se excluye):
- VENTAS USD: suma de `totalfob` (APIVentasCap) / `fobtotal` (APIAnalisisFacturacion).
- VENTAS TN: suma de `cantidad`.
- PRECIO USD/TN: ventas_usd / ventas_tn.
- STOCK TN: `cantidad2` / 1000 (viene en kilos), sumando ARG + EXT + DT.

El reporte se divide en Mercado Externo y Mercado Interno.
Frecuencia de uso de Marco: semanal, acumulado desde 01/01 hasta la fecha.

## Pendientes

- Completar kpis.py (ventas, precio y stock por familia) y conectarlo al router.
- Redis + APScheduler (refresh diario 6am, acumulado 01/01 → hoy) — diferido.
- Presupuesto (viene de otra API) — diferido.
- Datos históricos 2025 — diferido.
- Front propio para Marco — diferido.

## Referencias

- Excel original de Marco: `C:\Users\Agustin Fernandez\Desktop\venta industria\VENTAS INDUSTRIA 03 06 2026.xlsm`
  (las conexiones Power Query adentro tienen los parámetros exactos que usa hoy).
