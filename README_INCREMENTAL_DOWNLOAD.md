# Descargador Incremental - Sistema Día por Día con Checkpoint

Sistema robusto de descarga automática que descarga mes por mes, día por día, con checkpoint para reanudar en caso de interrupciones.

## 🎯 ¿Por Qué Día por Día?

### Ventajas sobre descarga completa del mes:

1. **Resistente a fallos**: Si la conexión falla o hay un error, solo se pierde el día actual
2. **Reinicio automático**: Continúa desde donde quedó sin re-descargar datos
3. **Progress tracking**: Ves exactamente cuántos días y registros llevas
4. **Menor carga en la API**: Solicitudes más pequeñas y manejables
5. **Interrumpible**: Puedes detener (Ctrl+C) y reanudar cuando quieras

## 🚀 Uso Básico

### Descargar un mes completo

```bash
venv/bin/python3 src/incremental_downloader.py --year 2026 --month 8
```

Esto descarga agosto 2026 día por día, mostrando progreso:

```
📥 DESCARGA INCREMENTAL: 2026-08
================================================================================

[1/31] Descargando 01-08-2026... ✓ 342 registros (Total: 342)
[2/31] Descargando 02-08-2026... ✓ 298 registros (Total: 640)
[3/31] Descargando 03-08-2026... ✓ 315 registros (Total: 955)
...
[31/31] Descargando 31-08-2026... ✓ 287 registros (Total: 9854)

================================================================================
✓ Descarga completa: 9854 registros totales
================================================================================
```

### Descargar y procesar automáticamente

```bash
venv/bin/python3 src/incremental_downloader.py --year 2026 --month 8 --process
```

Descarga día por día Y procesa con el sistema LADA automáticamente.

### Reanudar descarga interrumpida

Si el proceso se interrumpe (error, Ctrl+C, etc.), simplemente ejecuta el mismo comando:

```bash
venv/bin/python3 src/incremental_downloader.py --year 2026 --month 8
```

Continuará desde donde quedó:

```
📋 CHECKPOINT ENCONTRADO - Reanudando descarga...
================================================================================
✓ Ya descargados: 5262 registros (días 1-15)
⏩ Reanudando desde día 16

[16/31] Descargando 16-08-2026... ✓ 301 registros (Total: 5563)
[17/31] Descargando 17-08-2026... ✓ 289 registros (Total: 5852)
...
```

### Reiniciar descarga desde cero

Si quieres borrar el checkpoint y empezar de nuevo:

```bash
venv/bin/python3 src/incremental_downloader.py --year 2026 --month 8 --reset
```

## 📋 Sistema de Checkpoint

### ¿Qué es el checkpoint?

Es un archivo JSON (`data/cache/download_checkpoint.json`) que guarda:
- Año y mes que se está descargando
- Último día completado exitosamente
- Todos los registros acumulados hasta ahora
- Timestamp de la última actualización

### ¿Cuándo se guarda?

- Automáticamente después de cada día completado
- Antes de lanzar cualquier error
- Al interrumpir con Ctrl+C

### ¿Cuándo se elimina?

- Automáticamente al completar el mes exitosamente
- Manualmente con `--reset`

### Verificar progreso actual

```bash
# Ver día actual y registros acumulados
cat data/cache/download_checkpoint.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Mes: {d[\"year\"]}-{d[\"month\"]:02d}')
print(f'Progreso: Día {d[\"ultimo_dia_completado\"]}/31')
print(f'Registros: {len(d[\"registros_acumulados\"])}')
"
```

## 🔧 Configuración

Usa el mismo `credentials.json` que el sistema principal:

```json
{
  "id": "FARMAH",
  "nombre": "Farmacias del ahorro",
  "base_url": "https://prod.nauphilus.com",
  "membership_id": 57,
  "endpoint_id": 1612,
  "username": "reporteFA@nauphilus.com",
  "password": "tu_password",
  "deduplicar": true,
  "zoho_webhook": ""
}
```

## 📊 Ejemplos de Uso

### Caso 1: Descargar agosto completo

```bash
venv/bin/python3 src/incremental_downloader.py -y 2026 -m 8
```

### Caso 2: Se interrumpió a mitad - reanudar

```bash
# El mismo comando - detecta el checkpoint automáticamente
venv/bin/python3 src/incremental_downloader.py -y 2026 -m 8
```

### Caso 3: Descargar múltiples meses

```bash
#!/bin/bash
for month in 8 9 10; do
  echo "Descargando mes $month..."
  venv/bin/python3 src/incremental_downloader.py -y 2026 -m $month
  echo "---"
done
```

### Caso 4: Monitorear progreso en tiempo real

Terminal 1:
```bash
venv/bin/python3 src/incremental_downloader.py -y 2026 -m 8
```

Terminal 2:
```bash
# Ver progreso cada 5 segundos
watch -n 5 "cat data/cache/download_checkpoint.json | python3 -c '
import json, sys
d = json.load(sys.stdin)
print(f\"Día {d[\\\"ultimo_dia_completado\\\"]}/31\")
print(f\"Registros: {len(d[\\\"registros_acumulados\\\"])}\")
'"
```

## ⚙️ Opciones de CLI

```
usage: incremental_downloader.py [-h] --year YEAR --month MONTH [--output OUTPUT] [--process] [--reset]

Descargador Incremental: Descarga día por día con checkpoint

options:
  -h, --help            show this help message and exit
  --year YEAR, -y YEAR  Año a descargar (ej: 2026)
  --month MONTH, -m MONTH
                        Mes a descargar (1-12)
  --output OUTPUT, -o OUTPUT
                        Ruta del Excel de salida (opcional)
  --process             Procesar automáticamente con el sistema LADA
  --reset               Reiniciar descarga (eliminar checkpoint)
```

## 🔍 Detalles Técnicos

### Flujo de Ejecución

```
Inicio
  ↓
¿Existe checkpoint?
  ├─ Sí → Cargar checkpoint
  │        Reanudar desde día N+1
  │
  └─ No → Empezar desde día 1
         all_records = []
  ↓
Por cada día del mes:
  ├─ Descargar día completo (fecha_inicio = fecha_fin)
  ├─ Agregar registros a all_records
  ├─ Guardar checkpoint con progreso actualizado
  └─ Continuar al siguiente día
  ↓
¿Completados todos los días?
  ├─ Sí → Convertir a Excel
  │        Eliminar checkpoint
  │        ✅ COMPLETADO
  │
  └─ No (error) → Checkpoint guardado
                  💡 Re-ejecutar para reanudar
```

### Formato del Checkpoint

```json
{
  "year": 2026,
  "month": 8,
  "ultimo_dia_completado": 15,
  "registros_acumulados": [
    {
      "id": 673925,
      "key": "FARMAH20260081952",
      "status": {...},
      "asesor": {...},
      ...
    },
    ...
  ],
  "timestamp": "2026-09-30T16:52:30.123456"
}
```

### Manejo de Errores

| Tipo de Error | Comportamiento |
|---------------|----------------|
| Red (timeout, 500, etc.) | Guarda checkpoint, muestra error, sale |
| Ctrl+C | Guarda checkpoint, mensaje amigable, exit 130 |
| Disco lleno | Guarda checkpoint si es posible, sale |
| Cualquier otro | Guarda checkpoint, traceback, exit 1 |

En todos los casos, re-ejecutar el mismo comando reanuda la descarga.

## 🐛 Troubleshooting

### "Server error 500"

La API rechazó la solicitud. Posibles causas:
- IDs incorrectos en credentials.json (membership_id, endpoint_id)
- Token expirado (se renueva automáticamente)
- Fecha inválida

**Solución**: Verifica credentials.json y re-ejecuta.

### Checkpoint corrupto

Si el archivo checkpoint está dañado:

```bash
rm data/cache/download_checkpoint.json
venv/bin/python3 src/incremental_downloader.py -y 2026 -m 8
```

Volverá a descargar desde el día 1.

### Descarga muy lenta

Es normal, la API puede ser lenta. El sistema es paciente y retomará si se interrumpe.

### ¿Cómo saber si sigue ejecutándose?

```bash
ps aux | grep incremental_downloader.py
```

O verifica que el checkpoint se actualice:

```bash
stat data/cache/download_checkpoint.json
```

## 📈 Performance

- **Tiempo por día**: ~1-2 segundos
- **Mes completo (31 días)**: ~1-2 minutos
- **Registros típicos por mes**: ~8,000-12,000

## 🔐 Seguridad

- Checkpoint contiene datos completos de entrevistas
- Se guarda en `data/cache/` (incluido en .gitignore)
- Se elimina automáticamente al completar
- NO contiene credenciales

## 🎓 Comparación con auto_downloader.py

| Feature | auto_downloader | incremental_downloader |
|---------|----------------|----------------------|
| Descarga completa | ✓ Mes entero | ✓ Día por día |
| Checkpoint | ✗ No | ✓ Sí |
| Reinicio | ✗ Desde cero | ✓ Continúa |
| Progreso visible | ✗ No | ✓ Sí |
| Interrumpible | ✗ Pierde todo | ✓ Guarda estado |
| Recomendado para | Meses pequeños | **Producción** |

**Recomendación**: Usa `incremental_downloader.py` para todos los casos de uso en producción.

---

**Última actualización**: 30 de septiembre de 2026