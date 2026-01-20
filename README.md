# RiskGuard - Aplicativo para Gestion de Riesgos Ciberneticos (ITIZ3301)

**RiskGuard** es un aplicativo web (Flask + SQLite) para automatizar una metodologia de gestion de riesgos ciberneticos.

## Modulos
- **Activos**: inventario, clasificacion, valor CID (C/I/D) y calculo automatico de impacto.
- **Catalogos**: amenazas, vulnerabilidades y controles.
- **Riesgos**: escenarios (activo + amenaza + vulnerabilidad), calculo de riesgo inherente y categoria.
- **Tratamiento**: estrategia (mitigar/transferir/aceptar/evitar), controles propuestos (ref. ISO/IEC 27002:2022), responsable, plazo y estado.
- **Riesgo residual**: recalculo posterior a controles y comparacion antes vs despues.
- **Comunicacion**: observaciones, recomendaciones y generacion de reporte PDF.
- **Monitoreo**: panel con KPIs y seguimiento de riesgos/controles.

## Requisitos
- Python 3.10+ (recomendado)

## Instalacion

```bash
cd RiskGuard
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecucion

```bash
cd app
python app.py
```

Luego abrir: http://127.0.0.1:5000

## Datos de ejemplo (opcional)

```bash
cd app
python seed.py
python app.py
```

## Reporte PDF
- Menu "Reportes" -> descarga "Registro de riesgos (PDF)".

## Notas
- El sistema es un MVP academico; no incluye login.
- La referencia a ISO/IEC 27002:2022 se maneja como un campo de texto en cada control (codigo/nombre), para que el grupo lo alinee con los controles que seleccione.

## Estructura del proyecto
- `app/` codigo fuente del aplicativo
- `docs/` manual de usuario y documento tecnico
- `exports/` carpeta de salida (PDFs generados)
