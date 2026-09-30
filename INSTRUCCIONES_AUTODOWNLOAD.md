# Instrucciones para Configurar Auto-Download

## Paso 1: Crear archivo de credenciales

1. **Copia el archivo de ejemplo:**
   ```bash
   cp credentials.json.example credentials.json
   ```

2. **Edita `credentials.json` con las credenciales reales:**
   ```json
   {
     "nauphilus_api": {
       "username": "TU_USUARIO_REAL",
       "password": "TU_PASSWORD_REAL",
       "base_url": "https://URL_REAL_DE_LA_API",
       "membership_id": "ID_MEMBERSHIP_REAL",
       "endpoint_id": "ID_ENDPOINT_REAL"
     }
   }
   ```

   **Valores a completar:**
   - `username`: Tu usuario de la API de Nauphilus
   - `password`: Tu contraseña de la API
   - `base_url`: URL base de la API (ej: `https://api.nauphilus.com` o similar)
   - `membership_id`: ID del membership de Farmacias
   - `endpoint_id`: ID del endpoint específico

3. **El archivo `credentials.json` está en `.gitignore`** - No se subirá al repositorio por seguridad.

## Paso 2: Instalar dependencias

Si aún no has instalado las dependencias:

```bash
pip install httpx
```

O instalar todas las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

## Paso 3: Probar la conexión (IMPORTANTE)

Ejecuta el script de prueba para descubrir la estructura de la API:

```bash
python3 test_api_connection.py
```

**Este script hará lo siguiente:**
1. Conectará con la API usando tus credenciales
2. Descargará los datos de **OCTUBRE 2026**
3. Mostrará la estructura del JSON que retorna la API
4. Guardará los primeros 5 registros en `data/cache/estructura_api_octubre2026.json`
5. Sugerirá el mapeo de campos JSON → Excel

**Output esperado:**
```
================================================================================
PRUEBA DE CONEXIÓN API - DESCUBRIMIENTO DE ESTRUCTURA
================================================================================

1. Cargando credenciales...
   ✓ Base URL: https://api.nauphilus.com
   ✓ Username: tu_usuario
   ✓ Membership ID: 12345
   ✓ Endpoint ID: 67890

2. Creando cliente API...
   ✓ Cliente inicializado

3. Descargando datos de OCTUBRE 2026...
Obteniendo nuevo token OAuth...
✓ Token obtenido (válido por 3600s)

Descargando mes completo: 2026-10
Rango: 2026-10-01 a 2026-10-31
Descargando desde: 2026-10-01 00:00:00
             hasta: 2026-10-31 23:59:59
URL: https://api.nauphilus.com/memberships/12345/core/creditApp/getSolitudesByTime/67890/2026-10-01 00:00:00/2026-10-31 23:59:59
✓ Descargados 1234 registros

✓ ÉXITO: Descargados 1234 registros

✓ Primeros 5 registros guardados en: data/cache/estructura_api_octubre2026.json

================================================================================
ESTRUCTURA DEL PRIMER REGISTRO:
================================================================================
{
  "clave": "...",
  "prospecto": "...",
  ...
}

================================================================================
ANÁLISIS DE CAMPOS:
================================================================================
...
```

## Paso 4: Verificar la estructura

Una vez que el script se ejecute exitosamente:

1. **Revisa el archivo generado:**
   ```bash
   cat data/cache/estructura_api_octubre2026.json
   ```

2. **Verifica el mapeo sugerido** en la salida del script

3. **Comparte la estructura conmigo** si hay campos que no coinciden con el Excel esperado

## Paso 5: Siguiente fase

Una vez confirmada la estructura de la API, crearemos:
- `src/json_to_excel_converter.py` - Para convertir JSON → Excel con el mapeo correcto
- `src/auto_downloader.py` - Para orquestar la descarga automática
- Modificaremos `src/main.py` - Para integrar el auto-download

## Solución de Problemas

### Error: "No se encontró credentials.json"
- Asegúrate de haber creado el archivo `credentials.json` en la raíz del proyecto
- Verifica que el nombre del archivo sea exactamente `credentials.json` (sin `.example`)

### Error de autenticación (401, 403)
- Verifica que el username y password sean correctos
- Confirma que la URL base sea la correcta
- Verifica que el usuario tenga permisos para acceder a la API

### Error: "No module named 'httpx'"
```bash
pip install httpx
```

### La API no retorna datos
- Verifica que haya datos disponibles para octubre 2026
- Confirma los IDs de membership y endpoint
- Prueba con otro mes (ej: agosto 2026) modificando el script

### Otros errores
- Revisa el traceback completo que imprime el script
- Verifica tu conexión a internet
- Confirma que la URL de la API sea accesible

## Notas de Seguridad

- **NUNCA** subas `credentials.json` al repositorio
- El archivo está en `.gitignore` por defecto
- Si necesitas compartir credenciales, hazlo por un canal seguro (no por chat/email)
- Considera usar variables de entorno en producción