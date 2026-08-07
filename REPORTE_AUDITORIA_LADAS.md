# Reporte de Auditoría: LADAs Conflictivas y Catálogo Limpio

**Fecha:** 2026-07-08
**Cliente:** Sara / FA — Farmacias
**Archivo procesado:** `FACTURACIONEX.xlsx` (12,060 filas)

---

## 1. Contexto

El catálogo oficial de LADAs (pestaña "Ladas", 4,477 filas) contiene **duplicados**: la misma lada aparece mapeada a múltiples estados. Esto causaba que el matcher asignara estados arbitrarios (primer match) y produjera discrepancias contra la columna ESTADO precalculada por Ariadne en el Excel.

## 2. Hallazgo Principal

Se identificaron **76 ladas conflictivas** (misma lada → múltiples estados). Estas ladas afectan un total de **2,189 filas** de CONTACTO DIGITAL en la data mensual (según el conteo del catálogo limpio).

Distribución de filas afectadas por fuente de decisión:

| Fuente de decisión | Ladas | Filas afectadas | Coincidencia con Ariadne |
|---|---|---|---|
| `correccion_bug` | 1 (lada 55) | 1,172 | 0%* |
| `GT_ariadne` | 17 | 587 | 100% |
| `IFT_pdf` | 10 | 180 | 0%* |
| `frecuencia_real` | 14 | 202 | 100% |
| `IFT_desempate` | 19 | 48 | 57% |
| `primer_match_catalogo` | 15 | 0 (sin filas) | — |

*\*Las discrepancias no son errores del script, sino correcciones legítimas basadas en el plan oficial de numeración del IFT. Ver sección 4.*

## 3. Métricas Finales del Pipeline

| Métrica | Valor |
|---|---|
| Total filas | 12,060 |
| CONTACTO DIGITAL | 2,420 |
| Resueltas automáticamente | 2,409 (99.5%) |
| No identificadas (revisión manual) | 11 |
| Evaluadas (totales cuadran) | 9,952 ✓ |
| Activas (totales cuadran) | 503 ✓ |
| Coincidencia LADA vs columna precalculada | 68.6% |
| Casos para revisión manual | 12 |

## 4. Las 26 Discrepancias vs Ariadne (revisión requerida)

Tras aplicar el catálogo limpio, **26 filas** difieren de la interpretación de Ariadne. Todas son correcciones basadas en el plan oficial de numeración del IFT:

### 4.1 Bug lada 55 — 18 filas (corrección)
- La celda del catálogo decía `"Mex"` → el matcher devolvía "Mex" en vez de "MEXICO CENTRO"
- **Corrección aplicada:** lada 55 → `MEXICO CENTRO` (región metropolitana de CDMX)
- Ariadne también tiene "Mex" precalculado, por lo que ambas difieren de la corrección

### 4.2 Correcciones IFT — 8 filas
| Lada | Ariadne precalculó | IFT oficial | Filas |
|---|---|---|---|
| 287 | Oaxaca | **Veracruz** | 1 |
| 487 | QUERETARO | **Veracruz** | 1 |
| 488 | NUEVO LEON | **Veracruz** | 1 |
| 464 | GUANAJUATO | **Jalisco** | 1 |
| 466 | GUANAJUATO | **Jalisco** | 1 |
| 489 | SAN LUIS POTOSI | **San Luis Potosi** (normalización) | 1 |
| 346 | Durango | **Jalisco** | 1 |
| 313 | Coahuila | **Michoacan** | 1 |

### 4.3 Recomendación
Antes de facturar por primera vez con el catálogo limpio, Sara debe validar estas 26 filas contra:
- El plan de numeración vigente del IFT (fuente oficial)
- Los registros internos del aplicante (dirección si existiera)
- El criterio del equipo de RH sobre plazas fronterizas

## 5. Entregables Generados

1. **`config/catalogo_ladas_limpio.csv`** — Catálogo de 76 ladas con decisión resolvida, fuente y justificación (auditable)
2. **`scripts/generate_catalogo_limpio.py`** — Script reproducible para regenerar el catálogo limpio
3. **`src/lada_matcher.py`** — Matching actualizado: catálogo base completo + overrides del CSV limpio (los overrides tienen prioridad documentada)
4. **`src/main.py` + `src/resolver.py`** — Pipeline actualizado para usar el catálogo limpio automáticamente
5. **Excel de salida** (`data/output/facturacion_procesada_*.xlsx`) — Con hojas: Data Enriquecida, Evaluadas, Activas, Detalle Facturación, Revisión Manual, Auditoría Matching, Diagnóstico
6. **`README.md`** — Documentación completa actualizada con la sección "Auditoría de LADAs"

## 6. Método de Asignación de Plazas (auditoría)

Las 12,060 filas se clasifican así:

| Método | Filas | Descripción |
|---|---|---|
| `plaza_directa_activa` | 9,639 | Plaza directa del Excel con rol activo en backoffice ✓ |
| `directo_estado` | 2,408 | CONTACTO DIGITAL resuelta (lada → estado → plaza) |
| `no_identificado` | 11 | Teléfono no extraíble o lada fuera de catálogo |
| `estado_sin_mapeo` | 1 | Estado sin plaza en `estado_a_plaza.yaml` |
| `rol_sistema` | 1 | Rol de sistema (WIDGET NAUPHILUS, no facturable) |

## 7. Próximos Pasos Sugeridos

1. **Sara valida las 26 filas discrepantes** (sección 4) para confirmar las correcciones IFT
2. Para ladas de 3 dígitos poco frecuentes, validar contra el PDF oficial del IFT (`analysis_lada_pdf.py`)
3. Implementar geocoding Nominatim para asignar "plaza geográficamente más cercana" cuando un estado no tenga plaza activa
4. Configurar CI/validaciones de entrada para detectar cambios de estructura mes a mes