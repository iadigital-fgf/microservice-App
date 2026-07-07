# Instrucciones para continuar el proyecto

Bienvenido. Este documento explica, en palabras simples, qué es este proyecto,
cómo hacerlo andar y qué falta hacer. Leelo entero antes de tocar código.

---

## 1. Qué es esto

Es un **servicio intermediario** entre el sistema de gestión de la empresa
(el ERP **Finnegans**) y el Excel de reportes que usa **Marco Velardez**
(Análisis y Planificación Financiera).

La idea es simple:

```
Finnegans (ERP)  →  este servicio  →  Excel / Power BI de Marco
```

- El servicio le pide los datos a Finnegans (6 APIs distintas).
- Junta todo en **un solo paquete JSON con 15 "cajones"** (un cajón por cada
  consulta del Excel).
- El Excel le pega **una sola vez** al servicio y cada tabla toma su cajón.

**Regla más importante de todas: el servicio NO calcula nada.** Devuelve los
datos tal cual vienen de Finnegans ("crudos"). Todos los cálculos (toneladas,
precios, presupuesto, segmentación) los hace Marco del lado del Excel. Si
alguna vez parece buena idea calcular algo acá, NO: va del lado del Excel.

## 2. Cómo hacerlo andar en tu máquina

1. Cloná el repositorio y entrá a la carpeta.
2. Creá un entorno virtual de Python e instalá las dependencias:
   ```
   python -m venv .venv
   .venv\Scripts\activate        (en Windows)
   pip install -r requirements.txt
   ```
3. Creá un archivo **`.env`** en la raíz del proyecto con estas variables
   (pedile los valores a Agustín — son las credenciales para Finnegans):
   ```
   FINNEGANS_BASE_URL=...
   FINNEGANS_CLIENT_ID=...
   FINNEGANS_CLIENT_SECRET=...
   ```
   El `.env` NO se sube al repositorio (tiene secretos).
4. Levantá el servidor:
   ```
   uvicorn fgf_service.main:app --reload
   ```
   (`--reload` es SOLO para desarrollo; en producción va sin eso.)
5. Probá que anda: abrí `http://127.0.0.1:8000/health` → tiene que responder
   `{"status": "ok"}`. La documentación automática de los endpoints está en
   `http://127.0.0.1:8000/docs`.

## 3. Cómo pedir el reporte

```
GET /api/v1/reportes/ventas-industria?fecha_desde=2026-01-01&fecha_hasta=2026-12-31
```

- La **primera** llamada tarda ~1-2 minutos (le pide todo a Finnegans).
- Las siguientes salen **al instante**: el resultado queda guardado en memoria
  (el "cache").
- Sin fechas devuelve `{}` vacío — es a propósito (el Excel "sondea" la URL
  antes de pedir los datos de verdad).

**El cache se renueva solo** todos los días a las 3 de la mañana (un trabajo
programado que corre dentro de la app). También se puede forzar a mano:

```
GET /api/v1/reportes/ventas-industria/refresh
```

Detalle importante: si al renovar alguna conexión con Finnegans falla, el
cache **NO se pisa** — se queda el dato del día anterior. Preferimos datos de
ayer antes que cajones vacíos.

## 4. Cómo está organizado el código

```
fgf_service/
├── core/        → lo compartido: cliente de Finnegans (maneja el token solo),
│                  configuración, códigos de empresa
├── connectors/  → 1 archivo por API de Finnegans (traen los datos crudos)
├── reports/
│   └── ventas_industria/  → el reporte: endpoint, orquestador, cache,
│                            y secciones/ (1 función = 1 cajón)
└── main.py      → arranca la app y el trabajo de las 3am
```

El recorrido de un dato: `connector` (le pega a Finnegans) → `sección` (arma
el cajón) → `service.py` (junta los 15 cajones) → `router.py` (lo sirve y lo
cachea).

Dos detalles finos que ya están resueltos (no los toques sin motivo):

- **Token**: el servicio genera y renueva solo su token de Finnegans (con las
  credenciales del `.env`). El Excel no maneja tokens.
- **Semáforo**: las 14 conexiones a Finnegans NO se disparan todas juntas, van
  de a 6 por vez. Con todas juntas Finnegans se sobrecarga y devuelve error 500.

## 5. Cosas que parecen bugs pero NO lo son

- **`stock_ext` y `facturacion_tgt` vienen vacíos**: es normal. El origen no
  tiene datos para esos códigos (TGT no factura por esa API; ese depósito no
  tiene existencias). Ya se verificó contra Finnegans directo y contra las
  consultas de Marco.
- **El parámetro `access_token` en la URL se ignora**: se sigue aceptando solo
  para no romper el Excel actual de Marco.

## 6. Qué falta hacer (en orden)

1. **Pegar el botón "Traer datos frescos"** (macro VBA) en el Excel de Marco
   (hay que guardar el Excel como `.xlsm`).
2. **Decidir fechas fijas vs "año anterior"**: algunas consultas de Marco
   arrancan en fechas fijas (2023/2024) y el código usa "el año anterior al
   corte". Está documentado en `CLAUDE.md`, sección "Verificación contra las
   queries de Marco". Hay que decidir con Marco si se alinea.
3. **Cambiar las credenciales del `.env`** a las de la empresa (hoy son las
   personales de Agustín).
4. **Subir el servicio a Azure** siguiendo el plan (`Plan_Hosting_Azure.pdf`):
   App Service con "Always On", Redis para que el cache sobreviva reinicios,
   deploy automático y seguridad. Ya están hechas las etapas 1 (token propio)
   y 2 (refresco automático 3am).
5. **A futuro**: el objetivo final es mostrar el reporte en la **web**
   (recomendado: Power BI Service) y usar el Excel para **auditar** que los
   números coincidan. Y se van a sumar **más reportes** con el mismo molde —
   el paso a paso está en `CLAUDE.md`, sección "Cómo agregar un reporte nuevo".

## 7. Dónde leer más

- **`CLAUDE.md`** → el documento técnico principal: arquitectura, los 15
  cajones, parámetros exactos de cada API, historial de decisiones. Es la
  fuente de la verdad del proyecto.
- **`Consultas.md`** → el mapa consulta-del-Excel ↔ cajón-del-servicio.
- **`Plan_Hosting_Azure.pdf`** → el plan completo para llevarlo a producción.

## 8. Reglas de trabajo

- Antes de cambiar algo, **proponé el cambio y esperá el okey** (así venimos
  trabajando y evita sorpresas).
- Probá siempre contra Finnegans real antes de dar algo por terminado.
- Actualizá `CLAUDE.md` cuando cambies algo importante: el que venga después
  (como vos ahora) va a depender de que esté al día.
