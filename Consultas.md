# Reporte Ventas Industria — Consultas (Excel ↔ API)

Mapa **1:1** entre cada consulta del Excel y su cajón en la respuesta de la API.
Endpoint único: `GET /api/v1/reportes/ventas-industria?fecha_desde=...&fecha_hasta=...&access_token=...`

Cada consulta del Excel = un cajón independiente (para darle una tabla y comparar
1:1). Crudo, tal cual la API. Las columnas calculadas y la segmentación las arma
Marco en el Excel.

## Forma de la respuesta (15 cajones)

```json
{
  "ventas_cap_base":       [ ... ],   // AnalisisFacturasVentas (base, parametrizada)
  "ventas_cap_2023_1s":    [ ... ],   // AnalisisFacturasVentas 2023-1S (fija)
  "ventas_cap_2023_2s":    [ ... ],   // AnalisisFacturasVentas 2023-2S (fija)

  "facturacion_fgf_base":      [ ... ],   // AnalisisFacturasVentas-A (EMPRE01, base)
  "facturacion_fgf_2017_2022": [ ... ],   // AnalisisFacturasVentas-A 2017-2022 (EMPRE01, fija)
  "facturacion_dohler":        [ ... ],   // AnalisisFacturasVentas-A DTARG
  "facturacion_tucuman":       [ ... ],   // AnalisisFacturasVentas-A SA TT
  "facturacion_tgt":           [ ... ],   // AnalisisFacturasVentas-A TGT

  "contratos":             [ ... ],   // Contratos

  "stock_arg":             [ ... ],   // Stock-ARG
  "stock_ext":             [ ... ],   // Stock-EXT
  "stock_dt":              [ ... ],   // Stock-DT
  "despachos":             [ ... ],   // Despachos
  "analisis_type":         [ ... ],   // AnalisisType

  "producto_segmento":     [ ... ]    // Producto-Segmento
}
```

## 1 · ME real — APIVentascap (sin empresa)
| Consulta Excel | Empresa | Fechas | Cajón API |
|---|---|---|---|
| AnalisisFacturasVentas (base) | — | parametrizada | `ventas_cap_base` |
| AnalisisFacturasVentas 2023-1S | — | fija 2023-01-01 → 2023-06-30 | `ventas_cap_2023_1s` |
| AnalisisFacturasVentas 2023-2S | — | fija 2023-07-01 → 2023-12-31 | `ventas_cap_2023_2s` |
| AnalisisFacturasVentas 2017-2022 | — | — | ❌ archivo .xlsx, queda en Excel |

## 2 · MI real — APIAnalisisfacturacion (por empresa)
| Consulta Excel | Empresa | Fechas | Cajón API |
|---|---|---|---|
| AnalisisFacturasVentas-A (base) | EMPRE01 | parametrizada | `facturacion_fgf_base` |
| AnalisisFacturasVentas-A 2017-2022 | EMPRE01 | fija 2017-01-01 → 2022-12-31 | `facturacion_fgf_2017_2022` |
| AnalisisFacturasVentas-A DTARG | DOHLER63 | parametrizada | `facturacion_dohler` |
| AnalisisFacturasVentas-A SA TT | TUCUMANTRAPANI69 | parametrizada | `facturacion_tucuman` |
| AnalisisFacturasVentas-A TGT | TGT61 | parametrizada | `facturacion_tgt` |

## 3 · PPTO — APIContratosIndustria (sin empresa)
| Consulta Excel | Fechas | Cajón API |
|---|---|---|
| Contratos | parametrizada | `contratos` |
| PROYECCION COBROS | — | ❌ cálculo en Excel (desde contratos) |

## 4 · Stock
| Consulta Excel | API | Empresa | Fechas | Cajón API |
|---|---|---|---|---|
| Stock-ARG | APIStockProdIndustria | EMPRE01 | foto a hoy | `stock_arg` |
| Stock-EXT | APIStockProdIndustria | CAPACITACION43 | foto a hoy | `stock_ext` (filtro: excluye CLIENTE DESTINO/FINAL) |
| Stock-DT | APIStockProdIndustria | DOHLER63 | foto a hoy | `stock_dt` |
| Despachos | APIDespachosIndustria | — | parametrizada | `despachos` |
| AnalisisType | APIAnalisisLaboratorio | — | filtrado 9 tipos + dedup | `analisis_type` |
| Analisis-LOTE | APIAnalisisLaboratorio | — | — | ❌ intermedio, no expuesto |

## 5 · Referencia
| Consulta Excel | Origen | Cajón API |
|---|---|---|
| Producto-Segmento | tabla hardcodeada (219, sin fruta fresca) | `producto_segmento` |

## Fuera del alcance (en Excel, NO en API)
- `AnalisisFacturasVentas 2017-2022` → archivo .xlsx, queda en Excel.
- `PROYECCION COBROS` → se calcula en Excel desde `contratos`.
- `Analisis-LOTE` → solo se expone su versión filtrada `analisis_type`.
- `Agrupacion.xlsx` → del PPTO financiero (otro reporte).
