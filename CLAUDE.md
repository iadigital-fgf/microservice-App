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
│   ├── APIAnalisisfacturacion.py
│   ├── APIContratosIndustria.py
│   ├── APIStockProdIndustria.py
│   ├── APIDespachosIndustria.py
│   └── APIAnalisisLaboratorio.py
└── reports/
    └── ventas_industria/
        ├── router.py          # UN endpoint + cache en memoria
        ├── service.py         # orquesta TODAS las conexiones (asyncio.gather) → arma el JSON
        └── secciones/         # 1 función por consulta del Excel (1:1)
            ├── me_real/ventas_cap.py
            ├── mi_real/facturacion.py
            ├── ppto/contratos.py
            └── stock/ (stock.py, despachos.py, laboratorio.py)
```

Flujo: `connectors` → `secciones` (1 función = 1 cajón) → `service.py` (junta
todo) → `router.py` (endpoint + cache).

---

## Endpoint único

```
GET /api/v1/reportes/ventas-industria?fecha_desde=YYYY-MM-DD&fecha_hasta=YYYY-MM-DD&access_token=...
```

- Devuelve **UN JSON consolidado con 15 cajones** (ver `Consultas.md` para el mapa
  1:1 Excel ↔ cajón). El Excel le pega **una sola vez** y cada consulta toma su cajón.
- **Parámetros opcionales a propósito**: Power Query "sondea" la URL base sin
  parámetros para validar la fuente; sin los tres datos se devuelve `{}` (si fueran
  obligatorios daría 422 y rompería la carga).

### Cache (en memoria)

- Clave = `(fecha_desde, fecha_hasta)`. La primera llamada calcula y guarda; las
  siguientes salen al instante. **Sin expiración**: para datos frescos se **reinicia
  el servidor** (eso limpia el cache).
- Un **candado** (`asyncio.Lock`) evita que, cuando el Excel dispara las tablas casi
  a la vez con el cache vacío, se le pegue muchas veces a Finnegans: una sola calcula
  y las demás esperan ese resultado.
- **No se cachea una corrida incompleta**: si alguna conexión falló, el resultado NO
  se guarda, así la próxima llamada reintenta (evita que una corrida degradada quede
  pegada devolviendo cajones vacíos).

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
| `facturacion_fgf_base` | APIAnalisisfacturacion | EMPRE01 | parametrizada |
| `facturacion_fgf_2017_2022` | APIAnalisisfacturacion | EMPRE01 | fija 2017-2022 |
| `facturacion_dohler` | APIAnalisisfacturacion | DOHLER63 | parametrizada |
| `facturacion_tucuman` | APIAnalisisfacturacion | TUCUMANTRAPANI69 | parametrizada |
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
- **`ventas_cap_base` y `contratos`** → arrancan el **1/1 del año anterior al corte**
  (`fecha_hasta.year - 1`), NO desde `fecha_desde`. Motivo: hay que traer el año
  previo completo (para "Exportación real 2025" y para los contratos de PPTO, que se
  cargan durante el año anterior). Se ajusta solo cuando cambie el año.

**Fuera del alcance (queda en el Excel, NO en la API):** `AnalisisFacturasVentas
2017-2022` (archivo .xlsx), `PROYECCION COBROS` (se calcula desde `contratos`),
`Analisis-LOTE` (solo se expone su versión filtrada `analisis_type`).

---

## APIs por sección — parámetros y valores fijos

Detalle de **qué API usa cada sección** del reporte, **qué parámetros** manda cada
API y **cuáles van con valor fijo**. Todas las APIs llevan siempre `ACCESS_TOKEN`
(el token lo pasa el Excel). Ojo con los nombres de parámetros: no son todos iguales.

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
| `facturacion_fgf_base` | `EMPRE01` | parametrizada | parametrizada |
| `facturacion_fgf_2017_2022` | `EMPRE01` | **fija** 2017-01-01 | **fija** 2022-12-31 |
| `facturacion_dohler` | `DOHLER63` | parametrizada | parametrizada |
| `facturacion_tucuman` | `TUCUMANTRAPANI69` | parametrizada | parametrizada |
| `facturacion_tgt` | `TGT61` | parametrizada | parametrizada |

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

## Finnegans — particularidades

- **Token**: GET a la API de auth (client_id / client_secret) devuelve un **UUID**
  que se pasa como query param `ACCESS_TOKEN`. **Expira** → hay que renovarlo.
  (Hoy en el Excel el token está hardcodeado; manejarlo del lado del servicio es un
  pendiente.)
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

- **`stock_ext` y `facturacion_tgt` llegaban vacíos**: causa = sobrecarga de
  Finnegans al disparar las 14 juntas + el cache guardaba la corrida degradada.
  Mitigado con el **semáforo (6)** + **no cachear corridas incompletas**. Si vuelve
  a pasar, reiniciar el server para limpiar el cache y probar de nuevo.
- **Token del Excel expira**: pendiente manejar el token del lado del servicio.

---

## Estado / progreso (último avance: 2026-06-30)

**Hecho:**
- Pivot completo a **crudo passthrough** (15 cajones). Sacada la app vieja (KPIs,
  detalle, armado, separación de mercados).
- **Cache** en memoria + candado; **no cachea corridas incompletas**; **semáforo (6)**
  para no sobrecargar Finnegans (arreglo de `stock_ext` / `facturacion_tgt` vacíos).
- **`contratos`** y **`ventas_cap_base`** → arrancan el 1/1 del año anterior al corte
  (`fecha_hasta.year - 1`), para PPTO y "Exportación real 2025".
- **CLAUDE.md** reescrito (este archivo) reflejando la arquitectura nueva.

**Pendiente (próxima sesión):**
1. **Probar `ventas_cap_base`** tras reiniciar uvicorn: confirmar que trae desde
   2025-01-01 (y que el fix de `stock_ext` / `facturacion_tgt` quedó).
2. **Completar sección PPTO exportación** (columna "VENTAS PPTO USD", desde
   `contratos` filtrado por el PPTO ME del año). Marco puede pasar su Excel de
   referencia.
3. **VENTAS TN de MI real** (quedó en curso).
4. **Manejo del token** del lado del servicio (hoy hardcodeado en el Excel, expira).

## Referencias

- Mapa completo Excel ↔ API: **`Consultas.md`** (en la raíz).
- Excel original de Marco:
  `C:\Users\Agustin Fernandez\Desktop\venta industria\VENTAS INDUSTRIA 03 06 2026.xlsm`
  (las conexiones Power Query adentro tienen los parámetros exactos que usa hoy).

## Pendiente 

- **APIStockProdIndustria** con **CAPACITACION43** -> No trae registros con herramientas externas.

