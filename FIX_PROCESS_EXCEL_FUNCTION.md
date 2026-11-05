# Fix: Función process_excel() para Auto-Procesamiento

**Fecha**: 2 de octubre de 2026  
**Problema**: Error al usar `incremental_downloader.py --process`  
**Solución**: Refactorización de `src/main.py`

## 🐛 Problema Original

Al intentar usar el descargador incremental con auto-procesamiento:

```bash
lada/bin/python3 src/incremental_downloader.py --year 2026 --month 4 --process
```

Se obtenía el error:

```
ImportError: cannot import name 'process_excel' from 'main'
```

**Causa**: `incremental_downloader.py` intentaba importar una función `process_excel()` que no existía en `main.py`.

## ✅ Solución Implementada

### 1. Refactorización de `src/main.py`

Se creó la función `process_excel()` que encapsula toda la lógica de procesamiento:

```python
def process_excel(config: Config, excel_path: str) -> str:
    """
    Procesa un Excel con el sistema LADA completo
    
    Args:
        config: Objeto de configuración
        excel_path: Ruta al Excel de entrada
        
    Returns:
        Ruta al Excel procesado generado
    """
    # ... toda la lógica de procesamiento ...
    return str(output_path)
```

### 2. Nueva función `main()` simplificada

La función `main()` ahora solo maneja el CLI y delega el procesamiento:

```python
def main():
    """Punto de entrada CLI - Parsea argumentos y llama a process_excel()"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Pipeline de facturación mensual - Farmacias')
    parser.add_argument('--input', type=str, help='Ruta del Excel de entrada')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    config = Config(str(project_root))
    
    if args.input:
        config.set_input_excel(args.input)
    
    return process_excel(config, config.input_excel_path)
```

### 3. Fix en referencia a `config.base_path`

Corregido error al acceder a `config.project_root` (que no existía):

```python
# ❌ Antes (incorrecto)
project_root = Path(config.project_root)
output_dir = project_root / 'data' / 'output'

# ✅ Después (correcto)
output_dir = config.base_path / 'data' / 'output'
```

## 📊 Casos de Uso Soportados

### Caso 1: CLI Manual (sin cambios)

```bash
lada/bin/python3 src/main.py --input data/input/entrevistas_2026_04.xlsx
```

**Resultado**: Procesa el Excel y genera el archivo de salida.

### Caso 2: Descarga Incremental + Auto-Procesamiento (NUEVO)

```bash
lada/bin/python3 src/incremental_downloader.py --year 2026 --month 4 --process
```

**Resultado**: 
1. Descarga día por día (con checkpoint)
2. Convierte JSON → Excel
3. **Procesa automáticamente con sistema LADA**
4. Genera Excel procesado final

### Caso 3: Importación por otros módulos (NUEVO)

```python
from main import process_excel
from config import Config

config = Config('/path/to/project')
output_path = process_excel(config, 'data/input/mi_excel.xlsx')
print(f"Procesado: {output_path}")
```

## 🧪 Pruebas Realizadas

### Prueba 1: Procesamiento Manual (Abril 2026)
```bash
lada/bin/python3 src/main.py --input data/input/entrevistas_2026_04.xlsx
```

**Resultado**: ✅ Éxito
- 11,854 registros procesados
- Excel generado: `facturacion_procesada_20261002_113527.xlsx`
- Todas las hojas generadas correctamente
- Hoja dinámica con fórmulas agregada

### Prueba 2: Auto-Procesamiento (Septiembre 2026)
```bash
lada/bin/python3 src/incremental_downloader.py --year 2026 --month 9 --process
```

**Resultado**: ✅ En progreso
- Descarga día por día funcionando (7/30 días completados)
- Checkpoint guardándose correctamente
- Procesamiento automático pendiente al completar descarga

## 📝 Cambios en Archivos

### `src/main.py`

**Antes**: Una sola función `main()` con toda la lógica mezclada

**Después**: 
- `process_excel(config, excel_path)` - Lógica de procesamiento reutilizable
- `main()` - Punto de entrada CLI simplificado

**Líneas modificadas**: ~40 líneas refactorizadas

### `src/incremental_downloader.py`

**Sin cambios** - Ya estaba correctamente implementado, solo necesitaba que existiera `process_excel()` en `main.py`

## 🎯 Beneficios

1. **Modularidad**: La lógica de procesamiento es reutilizable
2. **Mantenibilidad**: Separación clara de responsabilidades
3. **Testabilidad**: Función `process_excel()` puede ser testeada independientemente
4. **Flujo automático**: Descarga + procesamiento en un solo comando
5. **Compatibilidad**: No rompe el uso CLI existente

## 🔄 Flujo Completo Automatizado

```
Usuario ejecuta:
  lada/bin/python3 src/incremental_downloader.py --year 2026 --month 4 --process

    ↓
[1] Descarga día por día
    ├─ Día 1: 342 registros
    ├─ Día 2: 298 registros
    ├─ ...
    └─ Día 30: 287 registros
    
    ↓
[2] Checkpoint automático cada día
    └─ Si falla, puede reanudar
    
    ↓
[3] Conversión JSON → Excel
    └─ entrevistas_2026_04.xlsx (11,854 registros)
    
    ↓
[4] Procesamiento LADA (process_excel)
    ├─ Resolver CONTACTO DIGITAL (99.5%)
    ├─ Generar reportes (Evaluadas, Activas, etc.)
    ├─ Auditoría de matching
    └─ Hojas dinámicas con fórmulas
    
    ↓
[5] Excel final generado
    └─ facturacion_procesada_YYYYMMDD_HHMMSS.xlsx
```

## 🚀 Próximos Pasos Recomendados

1. ✅ **Completado**: Función `process_excel()` implementada
2. ✅ **Completado**: Prueba con datos de abril 2026
3. ⏳ **En progreso**: Prueba completa con septiembre 2026
4. 📋 **Pendiente**: Documentar en README principal
5. 📋 **Pendiente**: Agregar tests unitarios para `process_excel()`

## 📚 Documentación Relacionada

- `README_INCREMENTAL_DOWNLOAD.md` - Sistema de descarga día por día
- `README_AUTO_DOWNLOAD.md` - Sistema de descarga automática original
- `ARQUITECTURA_TECNICA.md` - Arquitectura del sistema LADA

---

**Última actualización**: 2 de octubre de 2026, 11:36 AM