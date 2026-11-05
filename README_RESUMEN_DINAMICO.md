# 📊 Hoja de Resumen Dinámico

## ¿Qué es?

La hoja **"Resumen Dinámico"** contiene fórmulas de Excel que se actualizan automáticamente cuando modificas manualmente la columna `plaza_calculada` en la hoja "Data Enriquecida".

## 🎯 Caso de Uso

Cuando necesites hacer correcciones manuales de plaza en casos específicos:

### Antes (Problema):
1. ✅ Procesas el Excel con el sistema
2. ❌ Encuentras un caso mal asignado en "Data Enriquecida"
3. ❌ Corriges manualmente la `plaza_calculada`
4. ❌ Las hojas de resumen (Detalle Facturacion, Evaluadas, Activas) **NO se actualizan**
5. ❌ Los totales quedan incorrectos

### Ahora (Solución):
1. ✅ Procesas el Excel con el sistema
2. ✅ El sistema genera automáticamente la hoja "Resumen Dinámico" con fórmulas
3. ✅ Corriges manualmente cualquier `plaza_calculada` en "Data Enriquecida"
4. ✅ La hoja "Resumen Dinámico" **se actualiza automáticamente** ⚡
5. ✅ Los totales siempre están correctos

## 📋 Estructura de la Hoja

```
Plaza                 EVALUADO  PARAMETRICO  REVISION ASESOR  Total EVALUADAS  ACTIVAS >35★  ACTIVAS 1-35★  ACTIVAS 0★  Total ACTIVAS
ACAPULCO GUERRERO     =COUNTIFS  =COUNTIFS    =COUNTIFS        =B3+C3+D3        =COUNTIFS     =COUNTIFS      =COUNTIFS   =F3+G3+H3
AGUASCALIENTES...     =COUNTIFS  =COUNTIFS    =COUNTIFS        =B4+C4+D4        =COUNTIFS     =COUNTIFS      =COUNTIFS   =F4+G4+H4
...
Total general         =SUM(B3:B53) =SUM(C3:C53) =SUM(D3:D53)   =SUM(E3:E53)     =SUM(F3:F53)  =SUM(G3:G53)   =SUM(H3:H53) =SUM(I3:I53)
```

### 📊 Categorías de Activas por Avance (Estrellas):

- **ACTIVAS >35★** (Alto avance): Entrevistas ACTIVAS con más de 35 estrellas
- **ACTIVAS 1-35★** (Medio avance): Entrevistas ACTIVAS con 1 a 35 estrellas
- **ACTIVAS 0★** (Sin avance): Entrevistas ACTIVAS con 0 estrellas
- **Total ACTIVAS**: Suma de las 3 categorías anteriores

## 🔧 Cómo Funciona

### Fórmulas por Plaza:
Cada plaza tiene fórmulas `COUNTIFS` que cuentan en "Data Enriquecida":

**EVALUADO:**
```excel
=COUNTIFS('Data Enriquecida'!$O:$O,"ACAPULCO GUERRERO",'Data Enriquecida'!$E:$E,"EVALUADO")
```

**PARAMETRICO:**
```excel
=COUNTIFS('Data Enriquecida'!$O:$O,"ACAPULCO GUERRERO",'Data Enriquecida'!$E:$E,"PARAMETRICO")
```

**REVISION ASESOR:**
```excel
=COUNTIFS('Data Enriquecida'!$O:$O,"ACAPULCO GUERRERO",'Data Enriquecida'!$E:$E,"REVISION ASESOR")
```

**Total EVALUADAS:**
```excel
=B3+C3+D3  (suma de las 3 columnas anteriores)
```

**ACTIVAS:**
```excel
=COUNTIFS('Data Enriquecida'!$O:$O,"ACAPULCO GUERRERO",'Data Enriquecida'!$E:$E,"ACTIVO",'Data Enriquecida'!$G:$G,">=30")
```

### Fórmulas de Totales:
```excel
Total EVALUADO:        =SUM(B3:B53)
Total PARAMETRICO:     =SUM(C3:C53)
Total REVISION ASESOR: =SUM(D3:D53)
Total EVALUADAS:       =SUM(E3:E53)
Total ACTIVAS:         =SUM(F3:F53)
```

## 📝 Ejemplo de Uso

### Paso 1: Procesar Datos
```bash
venv/bin/python3 src/main.py --input data/input/entrevistas_2026_08_completo.xlsx
```

Esto genera:
- ✅ `data/output/facturacion_procesada_YYYYMMDD_HHMMSS.xlsx`
- ✅ Con hoja "Resumen Dinámico" incluida automáticamente

### Paso 2: Abrir Excel y Revisar

Abre el archivo generado y navega a la hoja "Data Enriquecida".

### Paso 3: Hacer Correcciones Manuales

Si encuentras un caso mal asignado:

**Antes:**
```
Clave             plaza_calculada              Estatus
FARMAH20260093521 MEXICALI BAJA CALIFORNIA    EVALUADO  ❌ Incorrecto
```

**Después:**
```
Clave             plaza_calculada                     Estatus
FARMAH20260093521 MEXICO CENTRO ESTADO DE MEXICO     EVALUADO  ✅ Corregido
```

### Paso 4: Ver Actualización Automática

Ve a la hoja "Resumen Dinámico":
- ✅ La fila "MEXICALI BAJA CALIFORNIA" disminuye en 1
- ✅ La fila "MEXICO CENTRO ESTADO DE MEXICO" aumenta en 1
- ✅ Los totales se recalculan automáticamente

## ⚠️ Notas Importantes

### Columnas de Referencia en "Data Enriquecida":
- **Columna O**: `plaza_calculada`
- **Columna E**: `Estatus`
- **Columna G**: `Estrellas`

### Hojas Estáticas vs Dinámicas:

| Hoja | Tipo | Se Actualiza |
|------|------|--------------|
| Data Enriquecida | Editable | ✏️ Editas aquí |
| **Resumen Dinámico** | **Dinámico** | **✅ Se actualiza automático** |
| Detalle Facturacion | Estático | ❌ Valores fijos |
| Evaluadas | Estático | ❌ Valores fijos |
| Activas | Estático | ❌ Valores fijos |

### Recomendación:
- Usa **"Resumen Dinámico"** como tu fuente de verdad después de hacer correcciones manuales
- Las hojas estáticas reflejan el procesamiento inicial automático

## 🚀 Para Procesar Nuevos Meses

La hoja dinámica se genera automáticamente:

```bash
# Septiembre 2026
venv/bin/python3 src/main.py --input data/input/entrevistas_2026_09.xlsx

# Octubre 2026
venv/bin/python3 src/main.py --input data/input/entrevistas_2026_10.xlsx
```

Cada archivo generado incluirá su propia hoja "Resumen Dinámico".

## 🛠️ Agregar Hoja Dinámica a Excel Existente

Si ya tienes un Excel procesado sin la hoja dinámica:

```bash
venv/bin/python3 src/dynamic_reports.py data/output/tu_archivo.xlsx
```

Esto agregará la hoja "Resumen Dinámico" al archivo existente.

## 📊 Formato Visual

La hoja incluye:
- ✅ **Nota en rojo** en la primera fila explicando que es dinámica
- ✅ **Encabezados en negrita**
- ✅ **Fila de totales en negrita**
- ✅ **Anchos de columna ajustados** para legibilidad
- ✅ **51 plazas únicas** del proceso agosto 2026

## ✨ Ventajas

1. **Correcciones sin reprocesar**: Edita casos individuales sin ejecutar todo el pipeline
2. **Totales siempre correctos**: Las fórmulas garantizan precisión
3. **Auditoría transparente**: Puedes ver exactamente qué cuenta cada fórmula
4. **Compatible con Excel**: Funciona en Excel, LibreOffice, Google Sheets
5. **Automático**: Se genera sin pasos adicionales

## 🔍 Troubleshooting

### Las fórmulas muestran #REF!
- ✅ Verifica que la hoja "Data Enriquecida" existe
- ✅ Verifica que las columnas O (plaza_calculada), E (Estatus), G (Estrellas) existen

### Los totales no coinciden con "Detalle Facturacion"
- ✅ Normal si hiciste correcciones manuales
- ✅ "Resumen Dinámico" refleja el estado actual
- ✅ "Detalle Facturacion" refleja el procesamiento inicial

### Quiero regenerar la hoja dinámica
```bash
venv/bin/python3 src/dynamic_reports.py data/output/tu_archivo.xlsx
```

Esto eliminará y recreará la hoja "Resumen Dinámico".

---

**💡 Tip**: Después de hacer correcciones manuales, usa "Resumen Dinámico" como tu reporte oficial ya que siempre está actualizado.