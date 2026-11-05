# 🔍 Filtrado Automático por Mes

## Problema Identificado

Al descargar datos de la API, se descubrió que **la API devuelve registros de otros meses** junto con los del mes solicitado.

**Ejemplo real:**
- Solicitando octubre 2026 (días 1-2)
- API devolvió:
  - ✅ 540 registros de octubre 2026
  - ❌ 1 registro de mayo 2026
  - ❌ 2 registros de junio 2026
  - ❌ 22 registros de septiembre 2026

Esto contamina la facturación del mes al incluir entrevistas que no pertenecen al período.

---

## Solución Implementada

### 1. **Columnas Año/Mes en la Conversión JSON→Excel**

**Archivo:** `src/json_to_excel_converter.py`

Al convertir de JSON a Excel, ahora se extraen y agregan dos columnas:
- `Año`: Año de la fecha de creación
- `Mes`: Mes de la fecha de creación (1-12)

```python
# Extraer año y mes para filtrado posterior
anio = fecha.year if fecha else None
mes = fecha.month if fecha else None

row = {
    ...
    'Fecha': fecha,
    'Año': anio,
    'Mes': mes
}
```

### 2. **Filtrado Automático en el Procesamiento**

**Archivo:** `src/main.py`

Al procesar el Excel, el sistema:

1. **Detecta el mes objetivo**
   - Cuenta registros por mes
   - El mes con más registros es el objetivo

2. **Identifica registros de otros meses**
   - Compara Año/Mes de cada registro
   - Separa los que no pertenecen al mes objetivo

3. **Filtra y reporta**
   - Excluye automáticamente registros de otros meses
   - Muestra en consola cuántos se excluyeron y de qué meses

**Salida en consola:**
```
============================================================
FILTRADO POR MES
============================================================
Distribución de registros por mes:
  Mes 05: 1 registros
  Mes 06: 2 registros
  Mes 09: 23 registros
  Mes 10: 540 registros

✓ Mes objetivo detectado: 2026-10

⚠️  Excluyendo 26 registros de otros meses:
   - 2025-06: 1 registros
   - 2026-05: 1 registros
   - 2026-06: 1 registros
   - 2026-09: 23 registros
✓ Dataset filtrado: 540 registros del mes objetivo
```

---

## Compatibilidad

### ✅ Archivos Descargados con API
Los archivos generados por:
- `src/incremental_downloader.py`
- `src/auto_downloader.py`
- `src/json_to_excel_converter.py`

**Tienen las columnas Año/Mes** → Se filtran automáticamente

### ✅ Archivos Manuales (Legacy)
Los archivos creados manualmente o con versiones antiguas:
- `data/input/entrevistas_2026_04.xlsx`
- `data/input/FACTURACIONES_2.xlsx`

**NO tienen Año/Mes** → Se procesan normalmente sin filtrado

**Mensaje en consola:**
```
ℹ️  Columnas Año/Mes no encontradas - asumiendo dataset manual (sin filtrado)
```

---

## Beneficios

### 1. **Limpieza Automática**
- No requiere revisión manual
- Elimina registros arrastrados de otros meses
- Facturación precisa del mes solicitado

### 2. **Transparencia Total**
- Muestra distribución de registros por mes
- Reporta cuántos se excluyeron y de qué meses
- Permite auditar el filtrado

### 3. **Sin Cambios Manuales**
- El sistema detecta y filtra automáticamente
- No necesitas editar el Excel manualmente
- Funciona en cada procesamiento

### 4. **Retrocompatible**
- Archivos antiguos sin Año/Mes siguen funcionando
- No rompe el flujo existente
- Adopción gradual

---

## Pruebas

### Test Automático

Ejecutar:
```bash
lada/bin/python3 test_month_filter.py
```

Este script:
1. Descarga 2 días de octubre 2026
2. Verifica que tenga columnas Año/Mes
3. Detecta registros de otros meses (los hay!)
4. Simula contaminación adicional
5. Guarda Excel de prueba
6. Instruye cómo procesarlo

### Verificación Manual

```bash
# Procesar el archivo de prueba
lada/bin/python3 src/main.py --input data/input/entrevistas_2026_10_test.xlsx

# Ver sección "FILTRADO POR MES" en la salida
```

---

## Casos de Uso

### Caso 1: Descarga Mensual Normal

```bash
# Descargar septiembre 2026
lada/bin/python3 -c "
from src.incremental_downloader import IncrementalDownloader
downloader = IncrementalDownloader()
downloader.download_month_incremental(2026, 9)
"

# Procesar (filtrado automático)
lada/bin/python3 src/main.py --input data/input/entrevistas_2026_09.xlsx
```

**Resultado:** Solo registros de septiembre en la facturación

### Caso 2: Archivo Manual (sin Año/Mes)

```bash
# Procesar archivo antiguo
lada/bin/python3 src/main.py --input data/input/FACTURACIONES_2.xlsx
```

**Resultado:** Se procesa normalmente sin filtrado (compatible)

### Caso 3: Verificar Contaminación

Después de descargar un mes, verificar si la API devolvió registros de otros meses:

```python
import pandas as pd

df = pd.read_excel('data/input/entrevistas_2026_10.xlsx', sheet_name='data')

if 'Mes' in df.columns:
    print("Distribución por mes:")
    print(df['Mes'].value_counts().sort_index())
else:
    print("Archivo sin columna Mes (manual)")
```

---

## Mejoras Futuras (Opcional)

### Opción 1: Guardar Registros Excluidos

Agregar una hoja en el Excel de salida con los registros excluidos para auditoría:

```python
if len(df_otros_meses) > 0:
    df_otros_meses.to_excel(writer, sheet_name='Excluidos Otros Meses', index=False)
```

### Opción 2: Alerta si Excluidos > Threshold

Si se excluyen demasiados registros (ej. >5%), alertar:

```python
pct_excluidos = len(df_otros_meses) / len(df_data_original) * 100
if pct_excluidos > 5:
    print(f"⚠️  ALERTA: {pct_excluidos:.1f}% de registros excluidos")
    print("   Revisar si la API tiene problemas")
```

### Opción 3: Configuración de Filtrado

Agregar en `config/config.yaml`:

```yaml
filtrado_mes:
  habilitado: true
  guardar_excluidos: true
  alerta_threshold_pct: 5.0
```

---

## Preguntas Frecuentes

### ¿Por qué la API devuelve registros de otros meses?

Posibles causas:
- Fechas de modificación vs creación
- Bug en el backend de la API
- Registros que se actualizan después de su creación

El filtrado resuelve esto independientemente de la causa.

### ¿Se pierden datos importantes?

No. Los registros excluidos **no pertenecen al mes que estás facturando**. Aparecerán en sus respectivos meses cuando los descargues.

### ¿Qué pasa si descargo todo el año?

Si descargas enero-diciembre en un solo archivo, el sistema:
1. Detectará que hay múltiples meses
2. Elegirá el mes con MÁS registros como objetivo
3. Filtrará el resto

**Recomendación:** Descarga y procesa mes por mes para mejor control.

### ¿Funciona con archivos .xlsx manuales?

Sí, pero solo si tienen columnas Año/Mes. Los archivos manuales antiguos se procesan sin filtrado (comportamiento anterior).

---

## Resumen

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Registros de otros meses** | ❌ Se incluían en la facturación | ✅ Se excluyen automáticamente |
| **Visibilidad** | ❌ No se sabía que existían | ✅ Se reportan claramente |
| **Acción requerida** | ❌ Revisión y limpieza manual | ✅ Automático |
| **Compatibilidad** | ✅ Solo archivos nuevos | ✅ Archivos nuevos Y antiguos |
| **Auditoría** | ❌ Difícil de rastrear | ✅ Log completo en consola |

---

**Fecha de implementación:** Octubre 2026  
**Versión:** 1.0  
**Archivos modificados:**
- `src/json_to_excel_converter.py`
- `src/main.py`
- `test_month_filter.py` (nuevo)