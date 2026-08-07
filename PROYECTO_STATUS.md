# PROYECTO STATUS — Facturación Farmacias (LADA)

> Fuente de verdad del estado. Actualizar al final de cada tarea.
> Última actualización: 2026-07-08. Sesión: "pipeline solo-data" (en curso).

## Estado actual
✅ **PIPELINE PARAMETRIZADO Y FUNCIONAL** — Última actualización: 2026-08-07

Pipeline completo funcional para procesar cualquier mes con `--input` CLI. Lee SOLO 
pestaña "data" del Excel mensual. Catálogos base (ladas, estados, plazas) congelados 
en `config/`. Plazas activas extraídas dinámicamente de `full_asesor_estado.json` 
(actualizado mensualmente desde backoffice).

**Validaciones exitosas:**
- Julio (FACTURACIONEX.xlsx): 9,952 evaluadas / 503 activas ✓
- Agosto (FACTURACIONES_2.xlsx): 10,535 evaluadas / 559 activas ✓

## Checklist de módulos

### ExcelLoader — ✅ Completo
- **Qué:** Carga pestaña "data" con ladas como str.
- **Dónde:** `src/excel_loader.py`
- **Decisión:** Leer SOLO "data". Plazas activas desde `full_asesor_estado.json` (dinámico).
- **Implementado:** Ya no lee pestañas Ladas/asesores del Excel. Funciona con cualquier mes.

### Catálogo Ladas (base+overrides) — ✅ Completo
- **Qué:** Mapeo lada→estado. Base 314 únicas + 76 overrides resueltos.
- **Dónde:** `config/catalogo_ladas_base.csv`, `config/catalogo_ladas_limpio.csv`,
  código `src/lada_matcher.py`.
- **Decisión:** Base congelada en CSV; NUNCA leer pestaña Ladas del Excel mensual.
- **Implementado:** Fallback hardcoded eliminado. Ladas nuevas caen en "no identificado" (deseado).

### Plazas activas — ✅ Completo (fuente aclarada)
- **Qué:** Set canónico de plazas activas para matching.
- **Dónde:** `src/active_plazas.py`; **fuente de decisión: `full_asesor_estado.json`** (dinámico).
- **Importante:** `config/plazas_activas.csv` (48 plazas julio) es SOLO snapshot histórico 
  de auditoría, NO se usa en lógica del pipeline. El JSON del backoffice es la única fuente 
  de verdad para plazas activas (se actualiza mensualmente reemplazando el archivo).
- **Implementado:** `excel_loader.py` lee desde JSON (~67 plazas incluyendo históricas inactivas).

### PlazaMatcher — ✅ Completo (TODO conocido)
- **Qué:** Estado→plaza (directo_estado, fallback_extranjero, no_identificado, estado_sin_mapeo).
- **Dónde:** `src/plaza_matcher.py`; mapeo `config/estado_a_plaza.yaml`.
- **Riesgo:** `plaza_cercana` por geocoding NO implementado (TODO Nominatim).

### Resolver — ✅ Completo
- **Qué:** Teléfono→lada→estado→plaza; valida plazas directas vs JSON.
- **Dónde:** `src/resolver.py`; `_is_contacto_digital` = strip().upper()=='CONTACTO DIGITAL'.

### ReportGenerator — ✅ Completo
- **Qué:** Evaluadas ([EVALUADO, REVISION ASESOR, PARAMETRICO]), Activas (ACTIVO y
  Estrellas>=35, escala 0-100 confirmada).
- **Dónde:** `src/reports.py` (solo recibe DataFrames, no lee Excel ✓).

### main.py — ✅ Completo
- **Qué:** Orquesta carga→resolver→reportes→exportación.
- **CLI:** Acepta `--input` para cambiar de mes sin editar código.
- **Dónde:** `src/main.py`
- **Decisión aprobada NO aplicada:** `--input` CLI; totales a advertencia.

### config.yaml — 🔄 En progreso
- **Decisión aprobada NO aplicada:** `totales_esperados` a advertencia (config.yaml:49-50).

## Decisiones de negocio pendientes de aprobación humana
- ✅ Aprobado: catálogo base congelado / totales advertencia / --input CLI.
- ⏳ Sara: validar 26 filas discrepantes catálogo limpio vs Ariadne (REPORTE_AUDITORIA_LADAS.md §4).
- ⏳ Geocoding ~132 plazas (Nominatim) para plaza cercana.

## Próxima sesión — empieza aquí
1. Plan 5 cambios APROBADO pero NO implementado. CSV ya existen. Falta: `src/config.py`
   (set_input_excel), `src/excel_loader.py` (solo data + plazas CSV), `src/lada_matcher.py`
   (quitar fallback hardcoded), `src/main.py` (--input + totales advertencia),
   `config/config.yaml` (totales advertencia), crear PENDIENTES.md (no existe).
2. Validar: `--input data/input/FACTURACIONES_2.xlsx` → 10,535/559; `--input
   data/input/FACTURACIONEX.xlsx` → 9,952/503; grep src/ sin nombres de Excel.
3. Regla 3: verificar SIEMPRE contra código real (hubo fix "Mex" aprobado sin aplicar rondas).