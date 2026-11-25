# Planificación y optimización de la producción

Documentos HTML de planificación económica con **Leontief** (input-output), **Kantorovich** (programación lineal, valoraciones duales, juegos completos) y el **método del taller** (takt, balanceo, Johnson, camino crítico).

| Documento | Generador | Contenido |
|---|---|---|
| `planificacion_turismo.html` | `build_html.py` (`modelo.py`) | Turismo medio de principio a fin |
| `planificacion_integral.html` | `build_plan.py` (`modelo_plan.py`, `procesos.py`) | Coches, autobuses y tranvías autónomos para una ciudad de 735.000 habitantes |
| `planificacion_ordenadores.html` | `build_ordenadores.py` (`modelo_ordenadores.py`) | PC de oficina, PC gaming y centro de datos de 50 MW 24/7/365 |
| `planificacion_viviendas.html` | `build_viviendas.py` (`modelo_viviendas.py`) | 1.000.000 de viviendas y comedores comunales |
| `planificacion_viviendas_balance.html` | `build_viviendas_balance.py` (`balance_viviendas.py`) | Necesidades frente a la producción industrial nacional 2025 (INE) |

## Regenerar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install numpy scipy
python build_ordenadores.py   # o cualquier otro build_*.py
```

Los datos técnicos son ilustrativos (órdenes de magnitud del sector). `datos/ine_2025_construccion.json` es un extracto de la Encuesta Industrial Anual de Productos del INE.
