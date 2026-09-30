# Sistema de Auto-Download desde API Nauphilus

Sistema automatizado para descargar entrevistas directamente desde la API de Nauphilus, convertirlas a Excel y procesarlas con el sistema de asignación de LADAs.

## 🚀 Características

- **Descarga automática**: Se conecta a la API de Nauphilus y descarga entrevistas por mes
- **Conversión inteligente**: Convierte el JSON de la API al formato Excel esperado por el sistema
- **Procesamiento integrado**: Opcionalmente procesa automáticamente con el sistema LADA
- **Sin intervención manual**: Ya no necesitas descargar Excel manualmente del backoffice

## 📋 Requisitos

- Python 3.8+
- Credenciales de la API de Nauphilus
- Dependencias: `httpx`, `pandas`, `openpyxl`, `pyyaml`, `requests`

## 🔧 Instalación

1. **Instalar dependencias**:
```bash
pip install httpx pandas openpyxl pyyaml requests
```

O si usas el entorno virtual del proyecto:
```bash
venv/bin/pip install httpx
```

2. **Configurar credenciales**:

Edita el archivo `credentials.json` en la raíz del proyecto:

```json
{
  "id": "TELCEL",
  "nombre": "TELCEL",
  "base_url": "https://prod.nauphilus.com",
  "membership_id": 48,
  "endpoint_id": 1614,
  "username": "tu_usuario@nauphilusmail.com",
  "password": "tu_password",
  "deduplicar": false,
  "zoho_webhook": ""
}
```

**⚠️ Importante**: El archivo `credentials.json` está en `.gitignore` y NO debe subirse a GitHub.

## 🎯 Uso

### Opción 1: Solo Descargar y Convertir

Descarga un mes de la API y genera el Excel:

```bash
python3 src/auto_downloader.py --year 2026 --month 8
```

Esto generará: `data/input/entrevistas_2026_08.xlsx`

### Opción 2: Descargar y Procesar Automáticamente

Descarga, convierte y procesa todo en un solo comando:

```bash
python3 src/auto_downloader.py --year 2026 --month 8 --process
```

Esto:
1. Descarga las entrevistas desde la API
2. Convierte a Excel
3. Extrae LADAs de los teléfonos
4. Asigna estados
5. Asigna plazas
6. Genera reportes en `data/output/`

### Opción 3: Especificar Ruta de Salida

```bash
python3 src/auto_downloader.py --year 2026 --month 8 --output /ruta/custom.xlsx
```

## 📊 Flujo de Datos

```
API Nauphilus
    ↓
[Descarga JSON]
    ↓
[Conversión a DataFrame]
    ↓
[Excel con hoja 'data']
    ↓
[Procesamiento LADA] (opcional)
    ↓
[Reportes finales]
```

## 🔍 Estructura del Excel Generado

El Excel generado tiene una hoja llamada `data` con estas columnas:

| Columna | Descripción | Fuente API |
|---------|-------------|------------|
| `Clave` | ID único de la entrevista | `key` |
| `Asesor` | Nombre completo del asesor | `asesor.nombre + apellidos` |
| `Contactos` | Teléfono del cliente | `prospect.prospectContacts[0].contactMeans` |
| `Estatus` | Estado de la entrevista | `status.nombre` |
| `Resultado` | Resultado de evaluación | `result` |
| `Estrellas` | Calificación | `stars` |
| `LADA` | (Vacío, se asigna después) | - |
| `ESTADO` | (Vacío, se asigna después) | - |
| `PLAZA` | (Vacío, se asigna después) | - |
| `Fecha` | Fecha de creación | `createdDate` |

## 🏗️ Arquitectura

### Módulos Principales

1. **`src/api_client.py`**: Cliente HTTP para la API de Nauphilus
   - Maneja autenticación OAuth
   - Caché de token
   - Descarga por rango de fechas

2. **`src/json_to_excel_converter.py`**: Conversor JSON → Excel
   - Extrae datos del JSON anidado de la API
   - Genera DataFrame compatible con el sistema
   - Guarda Excel con formato correcto

3. **`src/auto_downloader.py`**: Orquestador principal
   - CLI interface
   - Coordina descarga + conversión + procesamiento
   - Validaciones y manejo de errores

### Integración con Sistema Existente

El auto-downloader genera Excel **100% compatible** con el sistema existente:
- Mismas columnas
- Mismos tipos de datos
- Misma hoja (`data`)
- Formato procesable por `src/excel_loader.py`

## 📝 Ejemplos de Uso

### Descargar múltiples meses

```bash
# Agosto 2026
python3 src/auto_downloader.py -y 2026 -m 8

# Septiembre 2026
python3 src/auto_downloader.py -y 2026 -m 9

# Octubre 2026
python3 src/auto_downloader.py -y 2026 -m 10
```

### Procesamiento batch con script

```bash
#!/bin/bash
# Script para descargar y procesar varios meses

for month in 8 9 10; do
    echo "Procesando 2026-$month..."
    python3 src/auto_downloader.py -y 2026 -m $month --process
    echo "---"
done
```

## 🐛 Troubleshooting

### Error: `httpx.ReadTimeout`

El mes tiene muchos registros. Esto es normal, el timeout está configurado a 5 minutos. El proceso continuará automáticamente.

### Error: `No hay datos para YYYY-MM`

La API no retornó datos para ese mes. Verifica:
- Las fechas (puede que el mes sea futuro)
- Los IDs de membership y endpoint en `credentials.json`
- Los permisos del usuario

### Error: `KeyError: 'nauphilus_api'`

El formato de `credentials.json` cambió. Asegúrate de que tenga las claves directamente en el root (ver sección Instalación).

## 🔐 Seguridad

- `credentials.json` está en `.gitignore` - NUNCA subas credenciales a GitHub
- Las credenciales se cargan solo en memoria
- El token OAuth se cachea temporalmente pero nunca se guarda a disco
- Los archivos de log no contienen credenciales

## 📈 Performance

- **1 día de agosto 2026**: ~573 registros, ~5 segundos
- **Mes completo de agosto 2026**: ~17,000 registros, ~2-3 minutos
- El cuello de botella es la API de Nauphilus, no el procesamiento local

## 🎓 Para Desarrolladores

### Testing

```bash
# Test del cliente API
python3 src/api_client.py

# Test del convertidor
python3 src/json_to_excel_converter.py

# Test de descarga de 1 día
python3 test_api_connection.py
```

### Agregar Nuevos Campos

Para agregar campos del JSON de la API al Excel:

1. Edita `src/json_to_excel_converter.py`
2. Modifica el método `convert_to_dataframe()`
3. Agrega la extracción del campo en el dict `row`
4. Actualiza `src/excel_loader.py` si es necesario

### Estructura del JSON de la API

Ver `data/cache/estructura_api_1dia_agosto2026.json` para ejemplos reales de la respuesta de la API.

## 📞 Soporte

Para problemas o dudas:
1. Revisa esta documentación
2. Verifica los logs en `data/cache/`
3. Ejecuta los scripts de test
4. Revisa `ARQUITECTURA_TECNICA.md` para más detalles del sistema

---

**Última actualización**: 30 de septiembre de 2026