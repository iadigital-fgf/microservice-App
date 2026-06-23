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

## Reporte ventas_industria — arquitectura

Flujo: connectors → `service.py` (trae datos de Finnegans) → `detalle.py`
(traduce cada API al idioma común + apila + clasifica mercado/segmento) →
`kpis.py` (suma por segmento) → `armado.py` (comparación año anterior +
estructura sectorizada) → `router.py` (solo endpoints).

Carpetas: `core/` (empresas, segmentos, productos, finnegans, config — dominio
compartido), `connectors/` (1 archivo por API), `helpers/` (genéricos: parsers),
`reports/ventas_industria/` (TODO lo específico de este reporte).

**Respuesta del reporte** (3 mercados, cada uno sectorizado):
```
mercado_externo / mercado_interno / total:
  anio_actual:   [{segmento, ventas_usd, ventas_tn, precio_usd_tn, stock_tn}]
  anio_anterior: [{segmento, ventas_real_usd, precio_fob_real, var_usd, var_precio}]
```
Año anterior = mismo período −1 año (derivado solo, `armado.menos_un_anio`).
VAR = actual/anterior (ratio). El año anterior NO lleva ventas_tn ni stock_tn.

**Segmento** = familia comercial (ACEITES, CASCARAS, FIBRAS, JUGOS CONCENTRADOS,
JUGOS NFC, JUGOS TOP, OTROS). `core/segmentos.py`: 1) familia Finnegans en
FAMILIAS_OTROS (ESENCIA/TERPENO/etc) → OTROS (gana sobre la tabla de Marco que
los tiene mal), 2) tabla producto→segmento (`core/productos.py`), 3) familia+
subfamilia, 4) SIN CLASIFICAR. FRUTA FRESCA y SIN CLASIFICAR se excluyen de KPIs.

**Reglas de negocio descubiertas (críticas):**
- **Parámetros API SIN espacio y fecha YYYY-MM-DD** (`PARAMWEBREPORT_Empresa`,
  `PARAMWEBREPORT_FechaDesde/Hasta`). Con espacio la API los IGNORA → causaba
  fibras/fechas/stock mal.
- **Mercado por tipo de documento** (`transacconsubtiponombre`): "Exportación" →
  externo (`fobtotal`); "Mercado Interno"/"(MI" → interno (`importemonsecundaria`);
  cualquier otra cosa → "otro" (intercompany, líquido producto, otras empresas →
  fuera de KPIs). "todo lo que no es export = interno" era demasiado amplio.
- **VentasCap se llama SIN empresa**; **Dohler** necesita llamada dedicada
  `empresa=DOHLER63` (se sacan las filas Dohler de la general para no duplicar).
- **ME**: USD y TN de VentasCap, EXCEPTO fibras → USD de Dohler, TN de VentasCap.
- **MI**: no-fibra = FGF TRAPANI S.A. (clientes externos); FIBRAS = Dohler.
- **Intercompany**: venta a empresa del grupo (`es_cliente_del_grupo`) → excluida.
  EXCEPCIÓN Dohler: sus ventas SÍ cuentan (la fibra se vende desde Dohler, incluso
  a FGF). Ojo: "Dohler Trapani ARGENTINA" es del grupo; "Dohler NETHERLANDS" no.
- **Dohler = fibra**: TODO lo de Dohler es FIBRAS (ventas, costos/gastos negativos
  que restan, e incluso una línea de jugo). Así cierra el neto de Marco (163.659).
  Y Dohler-no-export → interno (incluye docs "Liquido Producto").
- **Notas de crédito**: en USD netean (negativas, se incluyen); en TN NO cuentan
  (0). Detectadas por "nota de cr" en el doc.
- **TN** = `cantidadstock2`/1000 si `unidadstock2`=="Kilos".
- División de precio usa `np.nan` (no `pd.NA`) para `.round()` cuando TN=0.
- API devuelve NÚMEROS (no texto). El formato visual va en el consumidor
  (Excel formato de celda, front `toLocaleString`, Power BI locale).

## Estado de validación (al 2026-06-19, contra Excel 03/06, `fecha_hasta=2026-06-03`)

- **Mercado Externo: VALIDADO** los 6 segmentos (USD, TN, precio).
- **Mercado Interno: casi validado.** Dan bien: ACEITES, CASCARAS, JUGOS TOP,
  OTROS, JUGOS NFC (este último: nuestro número es el correcto, Marco omitió 2
  ventas). Faltan: JUGOS CONCENTRADOS (−13k) y FIBRAS MI (+58k, en investigación
  —ver Pendientes—; NO es fecha).

**Quirks del reporte de Marco** (nuestro número es más correcto; confirmar con él):
- ESENCIA/TERPENO: su tabla los pone en ACEITE, Finnegans dice ESENCIA/TERPENO
  → nosotros OTROS. Su reporte es inconsistente (USD en ACEITES, TN no).
- FIBRAS ME: nuestro 683.928 vs 683.538 — su hoja de fibra está refrescada solo
  hasta mayo; nuestro número (incluye 1-3 jun) está más actualizado.

## Pendientes (próxima sesión)

Diferencias finas del MI 2026:
1. **JUGOS NFC MI** — RESUELTO: **nuestro número es el correcto**. Marco no
   contempló 2 ventas en su reporte; el cálculo nuestro está bien.
2. **JUGOS CONCENTRADOS MI** — gap −13k (96.677 vs 109.370). A revisar con el detalle.
3. **FIBRAS MI** — nuestro ~221.669 vs 163.659 de Marco (+58k). Investigación hecha:
   - Confirmado que **NUESTRO número netea bien**: todos los rows de Dohler tienen
     EMPRESA="DOHLER-TRAPANI ARGENTINA S.A." (incluidos NC y costos negativos), así
     que `es_dohler` los agarra y restan correctamente.
   - Datos crudos de Marco (hoja `AnalisisFacturasVentas-A DTARG`): interno 2026 =
     **163.659 exacto**, meses Ene/Mar/Abr/May (sin Feb ni Jun). Por DOCUMENTO:
     Factura MI 174.257 + Liquido Producto 28.686 − NC 39.284 = 163.659.
   - **NO es fecha**: se corrió con `fecha_hasta=2026-05-31` y SIGUE sin dar (~221k).
   - **Falta investigar**: por qué nuestra llamada DOHLER63 en vivo (a 31/05) suma
     más que la hoja DTARG de Marco (163.659). Sospechas a chequear: (a) doble conteo
     —los rows de Dohler podrían venir en la llamada general Y en la dedicada, revisar
     el dedup en service.py—; (b) la dinámica DTARG de Marco filtra algo que nosotros
     no (¿FAMILIA=FIBRA, excluye la línea de jugo o ciertos docs?); (c) nuestra llamada
     trae más registros que su snapshot. Comparar el detalle FIBRAS interno (fuente
     Dohler) fila por fila contra la hoja DTARG.
   - Aparte: administración anotó una venta de JUGO como FIBRA (dato mal cargado en
     Finnegans). Con "todo Dohler = fibra" ese jugo entra igual (como en Marco).

Otros pendientes:
4. **Stock**: filtrar por estado "disponible" (estadocalidad/estadocomex); Marco
   cuenta solo lo vendible + warrant activo.
5. **Cache (Redis + scheduler)**: clave para escalar/velocidad. El año anterior es
   histórico (no cambia) → ideal para cachear. Hoy el reporte trae 2 años en vivo
   (lento, ~3 min). Diferido pero importante.
6. Presupuesto (Excel manual, no API), históricos guardados, front propio — diferidos.

## ACLARACIONES (confirmado con Marco / hallazgos manuales)

- **ESENCIA y TERPENO → OTROS, CONFIRMADO**: Marco confirmó que son **derivados
  del aceite** y van clasificados en OTROS (no en ACEITES). Nuestra clasificación
  ya es la correcta. (Antes era "quirk a confirmar"; ya está confirmado.)
- **Hay 3 tipos de llamada a APIAnalisisFacturacion** según `empresa`:
  `DOHLER63`, `EMPRE01` (FGF Trapani) y `TGT61`. Importante: detectar bien dónde
  se usa cada una (hoy usamos la general sin empresa + la dedicada DOHLER63).
- **Charlas con marco**: "Los movimientos intercompany entre dohler y fgf si cuentan en el reporte."

## Cómo verificar un KPI a mano (para Agustín)

El detalle ES la materia prima del KPI. En Excel → Datos → Power Query → Nuevo
origen → Web → URL de `/detalle/ventas` (con access_token) → "En la tabla" →
expandir columnas → usd/tn como Número decimal → Cerrar y cargar → Tabla dinámica.
OJO: el detalle tiene TODAS las filas; para igualar un KPI hay que filtrar con la
receta (ej. ME = mercado externo + fuente APIVentasCap).

## Referencias

- Excel original de Marco: `C:\Users\Agustin Fernandez\Desktop\venta industria\VENTAS INDUSTRIA 03 06 2026.xlsm`
  (las conexiones Power Query adentro tienen los parámetros exactos que usa hoy).


DOBLE CLICK EN OTROS