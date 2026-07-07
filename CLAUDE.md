# FGF Service — Microservicio Finnegans → Excel / Power BI

Microservicio **FastAPI** para FGF Trapani Group (citrícola). Consume las APIs del
ERP **Finnegans** y las expone crudas para el reporte **VENTAS INDUSTRIA**.

Usuario final: **Marco Velardez** (Responsable de Análisis y Planificación
Financiera). Desarrollador: **Agustín** (está aprendiendo → explicar los cambios
en términos simples).

---

## Reglas de trabajo (CRÍTICAS — no borrar)

- **Nunca editar código sin el "okey" explícito del usuario.**
  Flujo: **proponer → okey → editar → probar → corregir.**
- **Responder en español**, explicaciones **cortas y simples** (no sobre-complicar,
  no irse por las ramas, no reabrir lo ya decidido).
- **Consultas crudas, cálculos aparte**: las consultas de Power Query en el Excel
  quedan CRUDAS (solo la data de la API). TODOS los cálculos (TN, precio,
  segmentación, filtros de documentos, PPTO) los hace Marco en el Excel (medidas
  DAX, tablas dinámicas, tablas manuales). El microservicio NO calcula nada.

---

## Arquitectura (IMPORTANTE — cambió respecto de la app vieja)

La versión anterior calculaba KPIs y separaba mercados en Python (`kpis.py`,
`detalle.py`, `armado.py`). **Eso se eliminó.** Ahora el servicio es un
**passthrough crudo**: le pega a todas las APIs de Finnegans y devuelve la data
**tal cual**, en un solo JSON con un "cajón" por consulta del Excel. Marco arma
los KPIs y la segmentación del lado del Excel.

```
fgf_service/
├── core/
│   ├── config.py              # settings (credenciales, URL base Finnegans)
│   ├── finnegans.py           # cliente httpx + manejo de token
│   ├── empresas.py            # códigos de empresa (EMPRE01, DOHLER63, ...)
│   └── producto_segmento.py   # tabla Producto-Segmento hardcodeada (219, sin fruta fresca)
├── connectors/                # 1 archivo por API de Finnegans → devuelven list[dict] crudos
│   ├── APIventas_cap.py
│   ├── APIanalisis_facturacion.py
│   ├── APIContratosIndustria.py
│   ├── APIStockProdIndustria.py
│   ├── APIDespachosIndustria.py
│   └── APIanalisis_laboratorio.py
├── cache/
│   └── redis.py               # cache Redis (Etapa 3 del hosting) — preparado, SIN usar
├── reports/
│   └── ventas_industria/
│       ├── router.py          # endpoints: reporte (cacheado) + /refresh
│       ├── service.py         # orquesta TODAS las conexiones (asyncio.gather) → arma el JSON
│       ├── cache_memoria.py   # cache en memoria (dict + candados), compartido
│       ├── refresh.py         # refrescar() (pisa el cache) + fechas_estandar()
│       └── secciones/         # 1 función por consulta del Excel (1:1)
│           ├── me_real/ventas_cap.py
│           ├── mi_real/facturacion.py
│           ├── ppto/contratos.py
│           └── stock/ (stock.py, despachos.py, laboratorio.py)
└── main.py                    # app FastAPI + job 3am (APScheduler)
```

Flujo: `connectors` → `secciones` (1 función = 1 cajón) → `service.py` (junta
todo) → `router.py` (endpoint + cache). El job 3am (`main.py`) y el `/refresh`
llaman a `refresh.refrescar()`, que recalcula y pisa el cache.

---

## Endpoint único

```
GET /api/v1/reportes/ventas-industria?fecha_desde=YYYY-MM-DD&fecha_hasta=YYYY-MM-DD
```

- Devuelve **UN JSON consolidado con 15 cajones** (ver `Consultas.md` para el mapa
  1:1 Excel ↔ cajón). El Excel le pega **una sola vez** y cada consulta toma su cajón.
- **Parámetros opcionales a propósito**: Power Query "sondea" la URL base sin
  parámetros para validar la fuente; sin las fechas se devuelve `{}` (si fueran
  obligatorios daría 422 y rompería la carga).
- **`access_token` ya NO hace falta** (token propio desde 2026-07-02): el servicio
  genera y renueva su token solo. El parámetro se sigue aceptando **pero se ignora**,
  para no romper el Excel actual de Marco hasta que actualice sus consultas.

### Cache (en memoria) + refresco (Etapa 2, 2026-07-03)

- Vive en `cache_memoria.py`. Clave = `(fecha_desde, fecha_hasta)`. La primera
  llamada calcula y guarda; las siguientes salen al instante. **Sin expiración**:
  los datos frescos entran **pisando** el cache (job 3am o `/refresh`), no por
  vencimiento. Reiniciar el servidor también lo limpia (queda vacío).
- **Fechas estándar** (`refresh.fechas_estandar()`): `1/1 → 31/12 del año actual`
  (2026-01-01 → 2026-12-31). Es el rango FIJO que comparten el job 3am y el Excel:
  misma clave todo el año → el Excel siempre encuentra el cache caliente. Cambia
  sola el 1 de enero. **Los datos viejos NO se piden con otras fechas: Marco filtra
  en el Excel** (los cajones ya traen el año anterior + históricos).
- **Job 3am** (APScheduler, registrado en `main.py`, id `refresh_3am`): todos los
  días a las 3:00 ejecuta `refrescar()` → recalcula TODO y pisa el cache. Con
  `misfire_grace_time=3600`. OJO: requiere el proceso vivo a las 3am (en Azure con
  Always On sí; en la PC de desarrollo solo si está prendida y uvicorn corriendo).
- **`GET /api/v1/reportes/ventas-industria/refresh`**: botón manual — misma función.
  Tarda ~76-100 seg y responde `{ok, cache_actualizado, duracion_seg, filas_por_cajon}`.
  Mientras corre, el cache viejo sigue sirviendo. Desde el Excel se dispara con el
  botón VBA "Traer datos frescos" (macro que llama al /refresh y después RefreshAll).
- **El refresh NO pisa el cache si la corrida vino incompleta** (alguna conexión
  falló): queda el dato anterior (Marco ve datos de ayer, nunca cajones vacíos).
  Igual que siempre: el GET normal tampoco cachea corridas incompletas.
- Probado 2026-07-03: `/refresh` 76 seg corrida completa; reporte con fechas
  estándar respondió en 427 ms desde el cache; job registrado en el log de arranque.

### Concurrencia limitada

Las 14 conexiones NO se disparan todas juntas: un **semáforo (6 a la vez)** limita
la concurrencia. Con las 14 en paralelo Finnegans se sobrecarga y las más lentas
(`stock_ext`, `facturacion_tgt`) devuelven 500 → llegaban vacías. De a pocas,
responden todas. (Ver `service.py`: `_LIMITE` y `_seguro`.)

---

## Los 15 cajones

| Cajón | API | Empresa | Fechas |
|---|---|---|---|
| `ventas_cap_base` | APIVentascap | — | **año anterior → corte** (ver nota) |
| `ventas_cap_2023_1s` | APIVentascap | — | fija 2023-01-01 → 2023-06-30 |
| `ventas_cap_2023_2s` | APIVentascap | — | fija 2023-07-01 → 2023-12-31 |
| `facturacion_fgf_base` | APIAnalisisfacturacion | EMPRE01 | **año anterior → corte** |
| `facturacion_fgf_2017_2022` | APIAnalisisfacturacion | EMPRE01 | fija 2017-2022 |
| `facturacion_dohler` | APIAnalisisfacturacion | DOHLER63 | parametrizada |
| `facturacion_tucuman` | APIAnalisisfacturacion | TUCUMANTRAPANI69 | **año anterior → corte** |
| `facturacion_tgt` | APIAnalisisfacturacion | TGT61 | parametrizada |
| `contratos` | APIContratosIndustria | — | **año anterior → corte** (PPTO) |
| `stock_arg` | APIStockProdIndustria | EMPRE01 | foto a hoy |
| `stock_ext` | APIStockProdIndustria | CAPACITACION43 | foto a hoy (excluye CLIENTE DESTINO/FINAL) |
| `stock_dt` | APIStockProdIndustria | DOHLER63 | foto a hoy |
| `despachos` | APIDespachosIndustria | — | parametrizada |
| `analisis_type` | APIAnalisisLaboratorio | — | filtrado 9 tipos + dedup |
| `producto_segmento` | tabla hardcodeada | — | estática |

**Reglas de fechas:**
- **Históricos** (`2023_1s`, `2023_2s`, `2017_2022`) → fechas **FIJAS**, tal cual.
- **Resto** → **parametrizadas** desde el Excel (solo se pasan las fechas; las
  empresas quedan fijas en el código).
- **`ventas_cap_base`, `contratos`, `facturacion_fgf_base` y `facturacion_tucuman`**
  → arrancan el **1/1 del año anterior al corte** (`fecha_hasta.year - 1`), NO desde
  `fecha_desde`. Motivo: hay que traer el año previo completo (real 2025 de ME y de
  MI, y los contratos de PPTO que se cargan el año anterior). Se ajusta solo cuando
  cambie el año.

**Fuera del alcance (queda en el Excel, NO en la API):** `AnalisisFacturasVentas
2017-2022` (archivo .xlsx), `PROYECCION COBROS` (se calcula desde `contratos`),
`Analisis-LOTE` (solo se expone su versión filtrada `analisis_type`).

---

## APIs por sección — parámetros y valores fijos

Detalle de **qué API usa cada sección** del reporte, **qué parámetros** manda cada
API y **cuáles van con valor fijo**. Todas las APIs llevan siempre `ACCESS_TOKEN`
(el token lo genera el propio servicio — ver "Token propio"). Ojo con los nombres
de parámetros: no son todos iguales.

### ME real (exportación) → `APIVentascap`
Parámetros: `PARAMWEBREPORT_FechaDesde`, `PARAMWEBREPORT_FechaHasta`,
`PARAMWEBREPORT_Empresa`, `ACCESS_TOKEN`.
**Empresa: siempre vacía** (se manda sin empresa → trae toda la exportación; el
campo `EMPRESA` de los registros viene como `CAPACITACION`).

| Cajón | FechaDesde | FechaHasta | Empresa |
|---|---|---|---|
| `ventas_cap_base` | 1/1 del año anterior al corte (`fecha_hasta.year-1`) | parametrizada | — |
| `ventas_cap_2023_1s` | **fija** 2023-01-01 | **fija** 2023-06-30 | — |
| `ventas_cap_2023_2s` | **fija** 2023-07-01 | **fija** 2023-12-31 | — |

### MI real (facturación) → `APIAnalisisFacturacion`
Parámetros: `PARAMWEBREPORT_FechaDesde`, `PARAMWEBREPORT_FechaHasta`,
`PARAMWEBREPORT_Empresa`, `ACCESS_TOKEN`.
**Una llamada por empresa** (empresa fija en cada cajón; cada una trae lo suyo).

| Cajón | Empresa (fija) | FechaDesde | FechaHasta |
|---|---|---|---|
| `facturacion_fgf_base` | `EMPRE01` | 1/1 del año anterior al corte (`fecha_hasta.year-1`) | parametrizada |
| `facturacion_fgf_2017_2022` | `EMPRE01` | **fija** 2017-01-01 | **fija** 2022-12-31 |
| `facturacion_dohler` | `DOHLER63` | parametrizada | parametrizada |
| `facturacion_tucuman` | `TUCUMANTRAPANI69` | 1/1 del año anterior al corte (`fecha_hasta.year-1`) | parametrizada |
| `facturacion_tgt` | `TGT61` | parametrizada | parametrizada |

> Nota: `facturacion_fgf_base` y `facturacion_tucuman` (mercado interno) arrancan el
> año anterior para traer el MI real del año previo (ej. 2025). Esto deja **2023-2024
> sin traer** en el MI; si hicieran falta, pasar a inicio fijo 2023-01-01.

> ⚠️ `facturacion_tgt` (`TGT61`) devuelve **0 filas** — TGT no factura por esta API;
> sus ventas están en `APIVentascap`. Ver "Errores conocidos / pendientes".

### PPTO → `APIContratosIndustria`
Parámetros: `PARAMWEBREPORT_FechaDesde`, `PARAMWEBREPORT_FechaHasta`, `ACCESS_TOKEN`.
**Sin empresa.**

| Cajón | FechaDesde | FechaHasta |
|---|---|---|
| `contratos` | 1/1 del año anterior al corte (`fecha_hasta.year-1`) | parametrizada |

### Stock (existencias) → `APIStockProdIndustria`
Parámetros: `PARAMWEBREPORT_Fecha` (**una sola fecha**, no rango),
`PARAMWEBREPORT_Empresa`, `ACCESS_TOKEN`.
**Fecha: siempre `date.today()`** — la API es una foto a hoy, no acepta histórico.

| Cajón | Empresa (fija) | Filtro extra (en código) |
|---|---|---|
| `stock_arg` | `EMPRE01` | — |
| `stock_ext` | `CAPACITACION43` | excluye `DEPOSITO` ∈ {CLIENTE DESTINO, CLIENTE FINAL} |
| `stock_dt` | `DOHLER63` | — |

> ⚠️ `stock_ext` (`CAPACITACION43`) devuelve **0 filas** — ese depósito no tiene
> existencias en Finnegans. Ver "Errores conocidos / pendientes".

### Stock (despachos) → `APIDespachosIndustria`
Parámetros: `PARAMWEBREPORT_fechaDesde`, `PARAMWEBREPORT_fechaHasta`, `ACCESS_TOKEN`.
**Sin empresa.** ⚠️ Ojo: acá los parámetros de fecha van en **minúscula** (`fechaDesde`
/`fechaHasta`), a diferencia del resto de las APIs (`FechaDesde`/`FechaHasta`).

| Cajón | fechaDesde | fechaHasta |
|---|---|---|
| `despachos` | parametrizada | parametrizada |

### Stock (laboratorio) → `APIAnalisisLaboratorio`
Parámetros: **solo `ACCESS_TOKEN`** (sin fechas ni empresa — trae todo).

| Cajón | Filtro extra (en código) |
|---|---|
| `analisis_type` | deja 9 tipos de `NOMBRE` + dedup por (LOTE, COD_ANA, COD_FINN, NOMBRE) |

Los 9 tipos: `ACIDITY PERCENT, pH 8,1`, `COLOR a*`, `COLOR b*`, `COLOR L*`, `GPL`,
`pH (at 8º Bx)`, `PULP`, `RATIO CORRECTED`, `TYPE`.

### Referencia → sin API
| Cajón | Origen |
|---|---|
| `producto_segmento` | tabla hardcodeada en `core/producto_segmento.py` (219 filas, sin fruta fresca) |

---

## Verificación contra las queries de Marco (2026-07, Excel terminado)

Se compararon **las 14 queries reales de Marco** (Power Query, en
`Desktop\venta industria\{ME y MI, PPTO, STOCK}\*.txt`) contra el código, para
confirmar que **cada consulta llama a la empresa correcta**.

### Empresas — TODAS coinciden ✅

| Consulta de Marco | API | Empresa (Marco = código) |
|---|---|---|
| AnalisisFacturasVentas (base) | VentasCap | *(sin empresa)* |
| AnalisisFacturasVentas 2023-1S / 2S | VentasCap | *(sin empresa)* |
| AnalisisFacturasVentas-A (base) | Facturación | `EMPRE01` |
| AnalisisFacturasVentas-A 2017-2022 | Facturación | `EMPRE01` |
| AnalisisFacturasVentas-A DTARG | Facturación | `DOHLER63` |
| AnalisisFacturasVentas-A SA TT | Facturación | `TUCUMANTRAPANI69` |
| AnalisisFacturasVentas-A TGT | Facturación | `TGT61` |
| Contratos | Contratos | *(sin empresa)* |
| Stock-ARG | Stock | `EMPRE01` |
| Stock-EXT | Stock | `CAPACITACION43` |
| Stock-DT | Stock | `DOHLER63` |
| Despachos | Despachos | *(sin empresa)* |
| AnalisisType | Laboratorio | *(sin empresa)* |

**Confirmaciones clave:**
- `TGT61` (facturación) y `CAPACITACION43` (stock ext) son **exactamente** los
  códigos que usa Marco → los cajones vienen **vacíos porque el ORIGEN no tiene
  datos**, NO por código equivocado. (TGT no factura por esta API; su venta es
  exportación en VentasCap. El depósito CAPACITACION43 hoy no tiene existencias.)
- **Despachos**: Marco declara `Empre1="EMPRE01"` pero **NO lo usa** en la llamada
  (solo manda fechas) → va sin empresa, igual que el código.
- **`AnalisisFacturasVentas 2017-2022`** (de ME/VentasCap) sale de un **archivo Excel**
  (`\\192.168.168.18\...\Ventas cap 2017-2022.xlsx`), NO de la API → queda en el Excel.
  En cambio **`AnalisisFacturasVentas-A 2017-2022`** (de MI/Facturación) SÍ sale de la
  API (`EMPRE01`, 2017-01-01→2022-12-31) → es nuestro cajón `facturacion_fgf_2017_2022`.
- En el Excel, cada query base **appendea** su histórico (VentasCap base + 2023-1S +
  2023-2S + 2017-2022 xlsx; Facturación base + 2017-2022). Nosotros los mantenemos como
  **cajones separados** y Marco los une en el Excel.

### Fechas de inicio — DIFIEREN ⚠️ (pendiente de decisión)

Marco usa **inicios FIJOS**; el código quedó con lógica "año anterior". Diferencias:

| Cajón | Inicio Marco (query) | Inicio código actual | Hueco |
|---|---|---|---|
| `ventas_cap_base` | **2024-01-01** (fijo) | `fecha_hasta.year-1` → 2025-01-01 | falta **2024** |
| `facturacion_fgf_base` | **2023-01-01** (fijo) | `fecha_hasta.year-1` → 2025-01-01 | falta **2023-2024** |
| `facturacion_tucuman` | **2023-01-01** (fijo) | `fecha_hasta.year-1` → 2025-01-01 | falta **2023-2024** |
| `despachos` | **2024-01-01** (fijo) | parametrizada (del Excel) | según el Excel |
| `facturacion_dohler` | 2026-01-01 (fijo) | parametrizada | ~igual (año actual) |
| `contratos` | celda `FECHADESDE01` (parametrizada) | `fecha_hasta.year-1` → 2025-01-01 | según la celda |

**Decisión pendiente:** para replicar a Marco tal cual convendría pasar esos inicios
a **fijos** (`ventas_cap_base`→2024-01-01; `facturacion_fgf_base` y `facturacion_tucuman`
→2023-01-01). Hoy están con "año anterior" (elección de Agustín, "de última lo cambiamos").

### Token (referencia, NO usar credenciales de Marco)

Cada query de Marco **genera su propio token** vía
`GET .../BSA/api/oauth/token?grant_type=client_credentials&client_id=…&client_secret=…`
(las credenciales son **de Marco**; no se usan desde el servicio — ver regla). Sirve
para saber que el endpoint de auth existe y su formato, de cara al pendiente de manejar
el token del lado del servicio.

---

## Finnegans — particularidades

- **Token propio (implementado 2026-07-02)**: el servicio genera y renueva su
  token solo — el Excel ya no lo manda. Cómo funciona (`core/finnegans.py`):
  - GET a `FINNEGANS_TOKEN_URL` (`https://api.finneg.com/api/oauth/token`) con
    `grant_type=client_credentials` + `client_id`/`client_secret` del `.env`
    (variables `FINNEGANS_CLIENT_ID` / `FINNEGANS_CLIENT_SECRET`; hoy son las
    credenciales de Agustín — el cuerpo de la respuesta ES el token, un UUID).
  - El token vive **en memoria** en el cliente (NO en el `.env`: vence). Se pide
    la primera vez que hace falta y todas las llamadas lo reusan.
  - Si Finnegans devuelve **401/403** (token vencido), se pide uno nuevo y se
    reintenta la llamada (a lo sumo una renovación por request). Un **candado**
    evita que las 14 conexiones en paralelo pidan 14 tokens: una pide, el resto reusa.
  - Probado 2026-07-02 contra Finnegans real: token OK, reuso OK, llamada a
    `stock_dt` OK (36 filas). Pendiente menor: verificar qué código devuelve
    Finnegans REALMENTE cuando el token vence (se asumió 401/403).
- **Parámetros SIN espacio y fecha `YYYY-MM-DD`**: `PARAMWEBREPORT_Empresa`,
  `PARAMWEBREPORT_FechaDesde/Hasta`. Con espacio la API los **ignora**.
- Los campos del JSON vienen en **UPPERCASE** (`TOTALFOB`, `EMPRESA`, ...); se
  devuelven tal cual (crudo).
- `APIVentascap` se llama **sin empresa**; `APIAnalisisfacturacion` se llama **una
  vez por empresa** (cada empresa trae lo suyo, sin apilar entre empresas).

---

## Empresas (códigos en `core/empresas.py`)

- `EMPRE01` → FGF Trapani (mercado interno)
- `DOHLER63` → Dohler-Trapani Argentina
- `TUCUMANTRAPANI69` → SA Tucumán Trapani
- `TGT61` → TGT (exportaciones)
- `CAPACITACION43` → stock externo

---

## Lo que hace Marco del lado del Excel

- **Modelo de datos** (Power Pivot): relaciones entre tablas (varios-a-uno).
- **Tabla dinámica intermedia** de depuración: para ver en detalle qué producto es
  cada fila (prioridad del Excel además de reflejar el reporte).
- **Tabla de segmentación manual** (`Segmentacion_Manual`): reclasifica productos
  fuera de las consultas (ej. aceite de semilla y terpeno → OTROS). No se toca la
  consulta; si se refresca, la tabla manual sobrevive.
- **Cálculos**: TN, precio, ventas por segmento → medidas DAX / SUMAR.SI.CONJUNTO /
  dinámicas. Ventas de industria = documentos "Proforma Cliente Industria" (la fruta
  fresca / Empaque queda excluida: al filtrar por Segmento, Empaque queda en blanco).

---

## Errores conocidos / pendientes

- **`stock_ext` y `facturacion_tgt` vienen vacíos — RESUELTO (no es bug)**: el
  ORIGEN no tiene datos para esos códigos. Confirmado httpx directo a Finnegans y
  contra las queries de Marco: `TGT61` no factura por `APIAnalisisFacturacion` (0
  filas en 2023-2026; TGT vende por VentasCap), y el depósito `CAPACITACION43` no
  tiene existencias hoy. Los códigos son los MISMOS que usa Marco → correctos. (El
  semáforo y el "no cachear corridas incompletas" quedan igual como robustez, pero
  no eran la causa.)
- **Token del Excel expira — RESUELTO (2026-07-02)**: el servicio maneja su propio
  token (Etapa 1 del plan de hosting). Ver "Token propio" en "Finnegans —
  particularidades". Queda verificar el código real de "token vencido" (se asumió
  401/403) y, más adelante, pasar a credenciales de la empresa (hoy usa las de Agustín).
- **Fechas de inicio vs Marco**: `ventas_cap_base`, `facturacion_fgf_base` y
  `facturacion_tucuman` usan "año anterior"; Marco usa inicios fijos (2024/2023).
  Ver "Verificación contra las queries de Marco". Decidir si alinear.

---

## Plan de producción — hosting en Azure (hoja de ruta)

Objetivo: el servicio vive en Azure, **a las 3am se refresca solo** y el Excel/Power BI
pide los datos al instante, **sin intervención manual** (ni tokens ni botones).
PDF completo del plan: **`Plan_Hosting_Azure.pdf`** (en la raíz).

**Piezas elegidas (las más convenientes, costo no es limitante):**
- **Azure App Service** (Linux, Python) con **“Always On”** + **una sola instancia** →
  el hosting; el proceso no se apaga (para el job 3am y el cache).
- **Manejo de token propio** en el servicio (genera y renueva su token con client_id/
  secret de la empresa) → saca el token del Excel, que se vencía.
- **Programador 3am** dentro de la app (**APScheduler**) → deja el cache caliente. Sin
  tecnología aparte.
- **Azure Cache for Redis** → el cache sobrevive reinicios y deploys (hoy `cache/redis.py`
  está preparado, sin usar).
- **Azure Key Vault** (secretos), **GitHub Actions** (deploy automático),
  **Application Insights** (logs + alertas si el 3am falla), **API key / IP allowlist**
  (que solo el Excel/Power BI entren).

**Etapas:** 0) preparar repo → 1) token propio → 2) reloj 3am + `/refresh` →
3) Redis → 4) crear infra Azure → 5) CI/CD GitHub → 6) seguridad + pruebas.

**Para arrancar se necesita:** (1) credenciales de la empresa (client_id/secret) — de
Agustín, **no las de Marco**; (2) acceso a la cuenta de Azure. **Primer paso: Etapa 1
(token propio)** — sin eso el 3am no puede autenticarse.

---

## Estado / progreso (último avance: 2026-07-03)

**Hecho:**
- **Etapa 2 del plan de hosting: JOB 3AM + /REFRESH (2026-07-03)** ✅ — el cache
  ahora se refresca solo: job diario 3:00 (`refresh_3am` en `main.py`) + endpoint
  manual `GET .../ventas-industria/refresh`. Ambos llaman a `refresh.refrescar()`:
  recalcula con las **fechas estándar** (1/1 → 31/12 del año actual, mismas que el
  Excel) y pisa el cache SOLO si la corrida vino completa. Cache movido a módulo
  propio (`cache_memoria.py`). Probado: refresh 76 seg, reporte desde cache 427 ms.
  Del lado del Excel: botón VBA "Traer datos frescos" (llama /refresh + RefreshAll)
  — pendiente de pegar en el Excel de Marco (requiere guardarlo como .xlsm).
- **Excel conectado al microservicio — debugging (2026-07-03)**: dos errores del
  Excel de Agustín resueltos (no eran del servicio): (1) un paso "Convertido en
  tabla" (`Record.ToTable`) de más en `APIConsolidacion` rompía los 14 cajones
  ("column of the table wasn't found"); (2) editar el paso Origen con "Editar
  configuración" borra `RelativePath`/`Query` → 404 a la raíz. Regla: las fechas
  se cambian SOLO editando `FechaDesde`/`FechaHasta` en el Editor avanzado, y
  `APIConsolidacion` debe terminar `in Origen` (devuelve un RECORD, no tabla).
- **Etapa 1 del plan de hosting: TOKEN PROPIO (2026-07-02)** ✅ — el servicio genera
  y renueva su token solo; el Excel ya no necesita mandarlo (el parámetro
  `access_token` se acepta pero se ignora, para no romper el Excel de Marco).
  Cambios: `config.py` (+3 settings), `finnegans.py` (token en memoria + renovación
  ante 401/403 + candado), y se sacó `access_token` de toda la cadena (connectors,
  secciones, service, router). Credenciales en `.env` (hoy las de Agustín; pasar a
  las de la empresa cuando estén). Probado contra Finnegans real: token + reuso +
  llamada OK.
- Pivot completo a **crudo passthrough** (15 cajones). Sacada la app vieja.
- **Cache** en memoria + candado; **no cachea corridas incompletas**; **semáforo (6)**
  (robustez; NO era la causa de las tablas vacías).
- **Fechas “año anterior”** (`fecha_hasta.year-1`) en `contratos`, `ventas_cap_base`,
  `facturacion_fgf_base` y `facturacion_tucuman` (para traer el real del año previo).
- **Router** arreglado: `traer_todo` devuelve `(reporte, completo)`; el 500 quedó resuelto.
- **Tablas vacías (`stock_ext`, `facturacion_tgt`) — diagnosticadas**: el ORIGEN no
  tiene datos; los códigos (`CAPACITACION43`, `TGT61`) son los MISMOS que usa Marco.
- **Excel de Marco verificado**: las 14 queries llaman a la empresa correcta (ver
  "Verificación contra las queries de Marco"). Excel terminado.
- **CLAUDE.md** documentado (APIs por sección, verificación, plan de hosting).
- **Plan de hosting** en PDF (`Plan_Hosting_Azure.pdf`).

**Pendiente (próxima sesión):**
1. **Pegar el botón VBA "Traer datos frescos"** en el Excel (guardarlo como .xlsm).
2. Decidir **fechas fijas vs año anterior** (ver "Verificación…"; quedó en pausa).
3. Cambiar a **credenciales de la empresa** en el `.env` cuando estén (hoy las de Agustín).
4. Seguir el plan de hosting (etapas 3→6: Redis, Azure, CI/CD, seguridad).
   Recordar: en producción uvicorn va SIN `--reload` (en dev, un reload a las 3am
   mataría el job; y cada reload limpia el cache).

## Referencias

- Mapa completo Excel ↔ API: **`Consultas.md`** (en la raíz).
- Excel original de Marco:
  `C:\Users\Agustin Fernandez\Desktop\venta industria\VENTAS INDUSTRIA 03 06 2026.xlsm`
  (las conexiones Power Query adentro tienen los parámetros exactos que usa hoy).

## Pendiente 

- **APIStockProdIndustria con CAPACITACION43** → RESUELTO: no trae registros porque
  ese depósito no tiene existencias en el origen (mismo código que usa Marco). Ver
  "Verificación contra las queries de Marco" y "Errores conocidos".

