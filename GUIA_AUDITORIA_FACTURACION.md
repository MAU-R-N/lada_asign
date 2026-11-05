# 📊 Guía de Auditoría y Facturación

**Sistema de Asignación Automática de Plazas - Farmacias del Ahorro**  
**Versión**: 1.0  
**Fecha**: Octubre 2026

---

## 📑 Tabla de Contenido

1. [Vista General del Excel Procesado](#1-vista-general-del-excel-procesado)
2. [Auditoría de Asignaciones](#2-auditoría-de-asignaciones)
3. [Casos de Revisión Manual](#3-casos-de-revisión-manual)

---

### 📋 Hojas del Excel

| Hoja | Propósito | Uso |
|------|-----------|-----|
| **Data Enriquecida** | Datos completos con plazas calculadas | Auditoría detallada, edición manual |
| **Evaluadas** | Totales por plaza y estatus | Reporte para gerencia |
| **Activas** | Totales activas por avance (★) | Análisis de progreso |
| **Detalle Facturacion** | Consolidado evaluadas + activas | **Hoja principal para facturación** |
| **Resumen Dinámico** | Fórmulas dinámicas por plaza | Validación y análisis en tiempo real |
| **Revision Manual** | Casos que requieren revisión | Trabajo pendiente |
| **Auditoria Matching** | Verificación asesores vs JSON | Control de calidad |

### 🔄 Flujo de Trabajo Recomendado


   ↓
1. Verificar "Auditoria Matching" para ver casos contacto digital (calidad de asignaciones)
   ↓
2. ACTUALIZAR hoja de data enriquecida (corregir casos problemáticos)
   ↓
3. Validar "Detalle Facturacion" vs "Resumen Dinámico"
   ↓
4. Exportar reportes finales
```

---

## 2. Auditoría de Asignaciones



## 1. Casos de Revisión Manual

### 📋 Hoja "Revision Manual"

Esta hoja contiene casos que el sistema no pudo resolver automáticamente.

**Columnas Importantes:**

| Columna | Qué Revisar |
|---------|-------------|
| `Clave` | ID único de la entrevista |
| `Prospecto` | Nombre del candidato |
| `Asesor` | "CONTACTO DIGITAL" (casos CD no resueltos) |
| `Contactos` | Teléfonos proporcionados |
| `telefono_calculado` | Teléfono que el sistema extrajo |
| `lada_calculada` | LADA que el sistema detectó |
| `estado_calculado` | Estado inferido por LADA |
| `plaza_calculada` | Plaza asignada (puede estar vacía) |
| `metodo_asignacion` | Razón por la que está aquí |

### 🔍 Tipos de Casos Problemáticos

#### Tipo 1: `no_identificado`

**Problema:** No se pudo extraer un teléfono válido de la columna `Contactos`

**Ejemplos:**
- Contactos vacíos o con texto inválido
- Solo emails, sin teléfonos
- Formato no reconocido

**Acción:**
1. Revisar columna `Contactos` original
2. Si hay teléfono válido → Editar `telefono_calculado` manualmente
3. Buscar teléfono en otros sistemas (CRM, etc.)
4. Como último recurso → Asignar a plaza por defecto o ciudad del candidato

#### Tipo 2: `estado_sin_mapeo`

**Problema:** El estado inferido no tiene plaza configurada en `config/estado_a_plaza.yaml`

**Ejemplos:**
- LADA 664 (Tijuana) → Estado: BAJA CALIFORNIA → ¿Qué plaza?
- Estados con múltiples plazas necesitan configuración manual

**Acción:**
1. Verificar el estado en columna `estado_calculado`
2. Consultar con gerencia qué plaza corresponde
3. Editar `plaza_calculada` manualmente
4. Notificar a TI para actualizar configuración

#### Tipo 3: `directo_estado_inactiva`

**Problema:** La plaza calculada está inactiva según el JSON

**Acción:**
1. Verificar con RH si la plaza realmente está inactiva
2. Si es error del JSON → Actualizar JSON y reprocesar
3. Si la plaza está inactiva → Reasignar a plaza activa cercana

### ✏️ Cómo Corregir Casos de Revisión Manual

1. Abrir hoja **"Data Enriquecida"**
2. Buscar la `Clave` del caso problemático (Ctrl+F)
3. Editar las columnas calculadas (ver sección 4)
4. Una vez corregido, actualizar "Detalle Facturacion" manualmente o reprocesar

---

## 2. Edición de Data Enriquecida

### 📝 Columnas Editables vs Calculadas

#### ✅ Columnas Editables (Datos Originales)

Puedes editar estas sin problemas:

- `Clave`, `Prospecto`, `Asesor`, `Contactos`
- `Estatus`, `Estrellas`, `LADA` (original)
- Cualquier columna SIN el sufijo `_calculado/a`

#### ⚠️ Columnas Calculadas (Generadas por el Sistema)

**Puedes editarlas SOLO para correcciones manuales:**

| Columna | Propósito | Cuándo Editar |
|---------|-----------|---------------|
| `telefono_calculado` | Teléfono extraído | Si el sistema falló en extraerlo |
| `lada_calculada` | LADA detectada | Si es incorrecta (raro) |
| `estado_calculado` | Estado por LADA | Si la LADA es de frontera/ambigua |
| `plaza_calculada` | Plaza asignada | **Editar aquí para correcciones** |
| `metodo_asignacion` | Método usado | No editar (informativo) |

### ✏️ Proceso de Edición Manual

#### Caso de Uso 1: Cambiar Plaza Manualmente

**Situación:** El sistema asignó "CIUDAD DE MEXICO" pero debería ser "PUEBLA"

1. Buscar la fila por `Clave` o `Prospecto`
2. Localizar columna `plaza_calculada`
3. **Editar** el valor a `PUEBLA`
4. **Importante:** Usar el nombre exacto de la plaza (ver lista abajo)
5. Guardar Excel

#### Caso de Uso 2: Corregir Teléfono

**Situación:** `telefono_calculado` está vacío pero en `Contactos` hay un teléfono

1. Ver el teléfono en columna `Contactos`
   - Ejemplo: `"Juan: 5512345678, email@ejemplo.com"`
2. Editar `telefono_calculado` = `5512345678`
3. El sistema debería recalcular LADA/estado (o hazlo manual)
4. Editar `lada_calculada` = `55` (CDMX)
5. Editar `estado_calculado` = `CIUDAD DE MEXICO`
6. Editar `plaza_calculada` = `CIUDAD DE MEXICO`

#### Caso de Uso 3: Casos CONTACTO DIGITAL sin Resolver

**Situación:** Asesor = "CONTACTO DIGITAL", `plaza_calculada` vacía

1. Revisar `telefono_calculado` y `lada_calculada`
2. Si están presentes:
   - Buscar manualmente qué estado corresponde a esa LADA
   - Asignar `estado_calculado` y `plaza_calculada`
3. Si NO están presentes:
   - Intentar extraer teléfono de `Contactos`
   - O asignar plaza por ciudad del `Prospecto` si disponible
   - Como último recurso → Dejar para escalación

### 📋 Lista de Plazas Válidas (usar estos nombres exactos)

```
AGUASCALIENTES
BAJIO
CANCUN
CHIHUAHUA
CIUDAD DE MEXICO
CUERNAVACA
CULIACAN
GUADALAJARA
HERMOSILLO
LEON
MERIDA
MONTERREY
OAXACA
PUEBLA
QUERETARO
SALTILLO
SAN LUIS POTOSI
TAMPICO
TIJUANA
TOLUCA
TORREON
TUXTLA GUTIERREZ
VERACRUZ
VILLAHERMOSA
... (67 plazas totales, ver JSON completo)
```

### ⚠️ Advertencias Importantes

1. **NO editar en masa** sin verificar impacto
2. **NO cambiar** columnas originales del Excel base
3. **SÍ documentar** cambios manuales en un log aparte
4. **SÍ validar** que la plaza editada existe en el Resumen Dinámico
5. **Después de editar**, las hojas calculadas (Evaluadas, Activas, etc.) **NO se actualizan automáticamente**
   - Opción 1: Actualizar manualmente esas hojas
   - Opción 2: Reprocesar el Excel con el sistema

---

## 3. Validación: Detalle Facturación vs Resumen Dinámico

### 📊 Propósito de Cada Hoja

#### Hoja "Detalle Facturacion"

- **Qué es:** Tabla estática con totales por plaza
- **Cuándo se genera:** Al procesar el Excel (una sola vez)
- **Columnas:**
  - `plaza_calculada`: Nombre de la plaza
  - `EVALUADO`, `PARAMETRICO`, `REVISION ASESOR`: Desglose por estatus
  - `EVALUADAS`: Total evaluadas (suma de estatus)
  - `ACTIVAS >35★`: Activas con alto avance
  - `ACTIVAS <35★`: Activas con avance medio
  - `ACTIVAS 0★`: Activas sin avance
  - `ACTIVAS_TOTAL`: Total activas
- **Última fila:** `Total general` con sumas

#### Hoja "Resumen Dinámico"

- **Qué es:** Tabla con **fórmulas en vivo**
- **Se actualiza:** Automáticamente al editar Data Enriquecida
- **Ventaja:** Refleja cambios manuales en tiempo real
- **Columnas:** Similares a Detalle Facturación pero calculadas con COUNTIFS


