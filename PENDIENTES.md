# PENDIENTES - Pipeline de Facturación Farmacias

**Estado actual**: ✅ PIPELINE FUNCIONAL PARA CUALQUIER MES

**Última actualización**: 2026-08-07

---

## ✅ COMPLETADO

### Infraestructura Base
- ✅ Pipeline completo funcional (extracción, matching, reportes)
- ✅ Catálogos congelados en `config/`:
  - `catalogo_ladas_base.csv` (314 ladas únicas, fuente estática)
  - `catalogo_ladas_limpio.csv` (76 overrides resueltos)
  - `plazas_activas.csv` (48 plazas julio, SOLO snapshot histórico/auditoría)
  - `asesor_normalization.yaml` (nombres de asesores normalizados)
  - `estado_a_plaza.yaml` (mapeo estado→plaza directa)
  - `overrides_plazas.yaml` (casos especiales de asignación)
- ✅ **Fuente dinámica de plazas activas**: `full_asesor_estado.json` (backoffice, actualizado mensualmente)

### Parametrización Mensual
- ✅ `--input` CLI: permite cambiar de mes sin editar código
- ✅ Pipeline lee SOLO pestaña "data" del Excel (no requiere Ladas/asesores)
- ✅ Totales esperados convertidos a advertencia (no bloqueo)
- ✅ Validaciones exitosas:
  - Julio (FACTURACIONEX.xlsx): 9,952 evaluadas / 503 activas ✓
  - Agosto (FACTURACIONES_2.xlsx): 10,535 evaluadas / 559 activas ✓

### Resolución de CONTACTO DIGITAL
- ✅ Extracción de teléfono con regex robusto
- ✅ Matching de ladas 2/3 dígitos contra catálogo limpio
- ✅ Asignación de plaza por estado (directo) o cercanía geográfica
- ✅ Tasa de resolución: ~99.5% de filas CONTACTO DIGITAL

### Auditoría y Calidad
- ✅ Reporte de métodos de asignación (directo, cercanía, fallback)
- ✅ Validación de plazas directas vs JSON de asesores
- ✅ Pestaña "Revisión Manual" para casos no identificados
- ✅ Pestaña "Auditoría Matching" para verificar consistencia JSON

---

## 🔧 MEJORAS PENDIENTES (Prioridad Media)

### Coincidencia de Ladas
**Problema**: Coincidencia LADA calculada vs precalculada ~61-68% (esperado ≥95%)

**Causa raíz probable**: Las columnas LADA/ESTADO/PLAZA precalculadas en el Excel 
de entrada pueden tener errores o usar un catálogo distinto al nuestro.

**Acciones sugeridas**:
1. Auditar muestra de discrepancias (script `analysis_lada_*.py` ya creados)
2. Si nuestro catálogo es correcto (IFT + GT Ariadne), documentar que la columna
   LADA precalculada del Excel no es ground truth confiable
3. Considerar ignorar esa columna en futuras validaciones

### Geocoding y Plazas Cercanas
**Estado actual**: El código usa distancia haversine con lat/long cacheadas en JSON

**Mejoras posibles**:
- Regenerar cache de coordenadas con Nominatim si hay plazas nuevas
- Validar que overrides manuales en `overrides_plazas.yaml` siguen vigentes

### Documentación
- [ ] README con instrucciones de uso mensual
- [ ] Guía de troubleshooting para errores comunes
- [ ] Documentar flujo de decisión de catálogos (base → overrides → estado → plaza)

---

## 📝 NOTAS TÉCNICAS

### Uso Mensual
```bash
# Activar venv (primera vez)
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Procesar nuevo mes
venv/bin/python src/main.py --input data/input/FACTURACIONES_SEPTIEMBRE.xlsx
```

### Estructura de Catálogos
- `config/catalogo_ladas_base.csv`: 314 ladas únicas (solo necesarias, sin duplicados)
- `config/catalogo_ladas_limpio.csv`: 76 overrides para ladas conflictivas (decisión documentada)
- Los overrides tienen prioridad sobre el catálogo base

### Archivos de Entrada Requeridos
**Excel mensual** (parametrizable con `--input`):
- Pestaña "data" con columnas: Clave, Asesor, Contactos, Estatus, Resultado, Estrellas
- NO requiere pestañas Ladas/asesores (catálogos congelados en config/)

**JSON de roles** (actualizado mensualmente):
- `full_asesor_estado.json` en raíz del proyecto
- Fuente de verdad para plazas activas (se extrae automáticamente)
- Reemplazar este archivo cada mes con la exportación del backoffice

---

## 🚨 ISSUES CONOCIDOS

### Advertencias Esperadas
- ⚠️ Coincidencia LADA <95%: esperado hasta resolver auditoría de catálogos
- ⚠️ Totales != esperados: normal al cambiar de mes (actualizar config.yaml manualmente si se desea)

### Limitaciones
- PlazaMatcher usa todas las plazas del JSON (~67 incluyendo históricas inactivas)
- El filtro de plazas activas se aplica en `active_plazas.py` extrayendo solo roles con estatus Activo
- Estados sin plaza activa usan plaza más cercana (puede no ser óptimo para estados grandes)

---

## 📚 DOCUMENTOS DE REFERENCIA

- `PROYECTO_STATUS.md`: Fuente de verdad del estado actual
- `REPORTE_AUDITORIA_LADAS.md`: Análisis detallado de conflictos de ladas
- `config/config.yaml`: Parámetros editables del pipeline
- `README.md`: Documentación de alto nivel (pendiente actualización)

---

**Contacto**: Para dudas sobre el pipeline, revisar código en `src/` (modular y comentado)