# Levantar proyecto

## flujo de archivos

1. connectors  → piden los datos crudos a Finnegans
2. service     → llama a los connectors y organiza los datos
3. kpis        → recibe los datos del service y hace los cálculos
4. router      → es la API de tu app, llama al service y devuelve el resultado a Power BI