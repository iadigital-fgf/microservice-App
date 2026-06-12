# Levantar proyecto

## flujo de archivos

1. connectors  → piden los datos crudos a Finnegans
2. service     → llama a los connectors y organiza los datos
3. kpis        → recibe los datos del service y hace los cálculos
4. router      → es la API de tu app, llama al service y devuelve el resultado a Power BI

# El camino de los datos — Reporte Ventas Industria

---------FLUJO--------

## Paso 1 — Pedir los datos crudos (`connectors/`)

El microservicio hace 5 llamadas en paralelo a Finnegans:

- **APIVentasCap** (sin empresa) → todas las ventas de exportación (facturas y notas de crédito)
- **APIAnalisisFacturacion** (sin empresa) → toda la facturación de todas las empresas del grupo
- **APIStockProdIndustria** × 3 (ARG, EXT, DT) → la existencia de mercadería en cada depósito

Cada llamada devuelve miles de registros: una fila por ítem facturado o por lote en stock.

## Paso 2 — Limpiar y enriquecer (`helpers/` + `service.py`)

Los datos crudos no se pueden usar directo; hay que prepararlos:

- **Normalizar**: Finnegans manda los campos en MAYÚSCULAS; se pasan a minúsculas
  y se validan (parser + schemas).
- **Separar mercados**: en facturación, cada registro dice su EMPRESA.
  Los de FGF Trapani son mercado interno; los de Dohler se usan para las fibras
  (su FOB es venta externa, su importe en USD es venta interna).
- **Calcular toneladas**: si la unidad es "Kilos", la cantidad se divide por 1000.
- **Asignar familia del reporte (segmento)**: con FAMILIA + SUBFAMILIA de cada registro
  se decide si es ACEITES, JUGOS CONCENTRADOS, JUGOS NFC, JUGOS TOP, CASCARAS,
  FIBRAS u OTROS.

## Paso 3 — Calcular los KPIs (`kpis.py`)

Recién acá se suman números, siempre **agrupando por familia**:

- **Ventas ME**: USD = suma de `totalfob` (VentasCap) + fibras desde facturación Dohler.
  TN = suma de toneladas.
- **Ventas MI**: USD = suma de `importemonsecundaria` (facturación local convertida a USD)
  de FGF Trapani + fibras Dohler. TN ídem.
- **Precio USD/TN**: división de los dos anteriores (cálculo derivado, no se suma nada nuevo).
- **Stock TN**: toneladas por familia, sumando los 3 depósitos.

## Paso 4 — Armar el reporte (`router.py`)

Se juntan las tres piezas en la estructura final: por cada familia, una fila con sus
4 KPIs, en tres bloques (**Mercado Externo**, **Mercado Interno**, **Total** = suma
de ambos). Eso es lo que el endpoint le devuelve a Power BI.

## Pendiente

- **Presupuesto**: Excel manual del área comercial (sin API). Cuando se encare,
  será una fuente más en el paso 1 y las columnas VENTAS PPTO USD y Real vs PPTO
  en el paso 4.

> Clave del diseño: cada paso vive en una carpeta distinta
> (`connectors` → `helpers`/`service` → `kpis` → `router`).
> Cuando un número dé raro, se sabe en qué paso del camino buscar.