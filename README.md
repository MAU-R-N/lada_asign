# Sistema de Facturación Automatizada - Farmacias

Sistema automatizado para procesar y calcular facturación mensual de entrevistas de evaluación de personal en Farmacias (cliente Sara/FA).

## Descripción del Problema

Cada mes se recibe un Excel con miles de "entrevistas" (aplicantes evaluados por asesores de RH). El sistema debe:

1. Calcular cuántas entrevistas evaluadas y activas corresponden a cada plaza (ciudad/sede)
2. Inferir la plaza para entrevistas de "CONTACTO DIGITAL" (sin plaza asignada) usando:
   - Número de teléfono del aplicante
   - LADA telefónica → Estado → Plaza más cercana

## Resultados

El sistema procesa exitosamente:
- **9,952 entrevistas evaluadas** (totales coinciden con valores esperados ✓)
- **503 entrevistas activas** (totales coinciden con valores esperados ✓)
- **2,420 registros de CONTACTO DIGITAL** (2409 resueltos automáticamente, 99.5%)
- **12 casos** requieren revisión manual (11 no identificados + 1 estado sin mapeo)

### Métricas de Calidad
- Resolución automática: 99.5% de casos CONTACTO DIGITAL
- Coincidencia LADA vs columna precalculada: 68.6% (explicado en sección Auditoría)
- Solo 12 casos necesitan revisión manual
- **LadaMatcher**: 390 ladas únicas (314 catálogo base + 76 overrides documentados)

### Auditoría de LADAs (recomendado leer)

El catálogo oficial de ladas tiene **duplicados**: la misma lada aparece en múltiples estados (ej. la lada 924 aparece en Oaxaca y Veracruz). La métrica de 68.6% de coincidencia LADA mide cuántas veces el script coincide con la **columna precalculada** del Excel (que es la interpretación de Ariadne, no la verdad absoluta).

Se creó un **catálogo limpio** (`config/catalogo_ladas_limpio.csv`) que resuelve las 76 ladas conflictivas con una decisión documentada:

| Fuente de decisión | Ladas | Descripción |
|---|---|---|
| `catalogo_base` | 314 | Sin conflicto, primer match del catálogo |
| `GT_ariadne` | 17 | Ground truth (frecuencia dominante según reporte de Ariadne) |
| `IFT_desempate` | 19 | Desempate con plan de numeración oficial del IFT |
| `IFT_pdf` | 10 | Decisión oficial IFT documentada en `analysis_lada_pdf.py` |
| `frecuencia_real` | 14 | Estado mayoritario en los datos reales (top 14 ladas) |
| `primer_match_catalogo` | 15 | Sin filas afectadas este mes, primer match |
| `correccion_bug` | 1 | Lada 55: "Mex" → MEXICO CENTRO (corrección de bug) |

**Resultado de auditoría**: Las 26 filas donde el catálogo limpio difiere de Ariadne son **correcciones legítimas** basadas en el plan de numeración del IFT (ej. lada 287 → Veracruz, no Oaxaca; lada 55 → MEXICO CENTRO, no "Mex"). Estas deben revisarse manualmente antes de facturar por primera vez.

## Estructura del Proyecto

```
LADA/
├── config/                         # Archivos de configuración
│   ├── config.yaml                # Configuración principal
│   ├── estado_a_plaza.yaml        # Mapeo Estado → Plaza
│   ├── overrides_plazas.yaml      # Coordenadas para geocoding
│   ├── asesor_normalization.yaml  # Normalización de plazas (estados, alias)
│   └── catalogo_ladas_limpio.csv  # 76 ladas conflictivas resueltas (auditable)
├── data/
│   ├── input/                     # Excel de entrada
│   │   └── FACTURACIONEX.xlsx
│   ├── cache/                     # Caché de geocoding (futuro)
│   └── output/                    # Excel procesado (generado)
├── src/                           # Código fuente
│   ├── config.py                 # Carga configuración
│   ├── excel_loader.py           # Carga Excel
│   ├── phone_extractor.py        # Extrae y normaliza teléfonos
│   ├── lada_matcher.py           # Matchea LADA → Estado (base + overrides)
│   ├── plaza_matcher.py          # Asigna Estado → Plaza
│   ├── geocoder.py               # Geocoding (placeholder)
│   ├── active_plazas.py          # Carga plazas activas desde JSON backoffice
│   ├── asesor_normalizer.py      # Normaliza nombres de plazas
│   ├── resolver.py               # Orquesta resolución y validación
│   ├── reports.py                # Genera reportes
│   └── main.py                   # Script principal
├── scripts/                       # Scripts de análisis y auditoría
│   ├── generate_catalogo_limpio.py    # Genera catalogo_ladas_limpio.csv
│   ├── generate_tabla_conflictos_ladas.py  # Identifica ladas duplicadas
│   └── desglose_ladas_pendientes.py  # Desglosa ladas pendientes por filas
├── full_asesor_estado.json        # Roles del backoffice (fuente de verdad)
├── requirements.txt              # Dependencias Python
└── README.md                     # Este archivo
```

## Fuente de Verdad: Plazas Activas

El sistema utiliza **`full_asesor_estado.json`** como fuente canónica de plazas activas. Este archivo contiene los roles del backoffice de Farmacias.

### ¿Por qué es importante?

- **Validación automática**: El sistema valida que todas las plazas directas del Excel coincidan con roles activos en el backoffice.
- **Auditoría de discrepancias**: Genera reporte "Auditoria Matching" que identifica plazas en el Excel sin rol activo en el JSON.
- **Consistencia mes a mes**: Evita facturar plazas desactivadas o con nombres desactualizados.

### Flujo de validación

1. **Carga del JSON**: `src/active_plazas.py` extrae roles tipo "ASESOR {PLAZA}" con estatus "Activo"
2. **Normalización**: `src/asesor_normalizer.py` normaliza nombres (recorta estados, aplica alias)
   - Configuración en `config/asesor_normalization.yaml`
3. **Clasificación en resolver.py**:
   - `plaza_directa_activa`: Plaza del Excel matchea con rol activo en JSON ✓
   - `plaza_directa_sin_rol_json`: Plaza del Excel sin rol en JSON (revisar)
   - `rol_sistema`: Rol no facturable (ej: WIDGET NAUPHILUS)
   - `directo_estado`, `no_identificado`, etc.: Otros métodos de asignación

### Actualización mensual

Antes de procesar un nuevo mes:
1. Solicitar a TI el export actualizado de roles: `full_asesor_estado.json`
2. Reemplazar el archivo en la raíz del proyecto
3. Ejecutar el pipeline - el sistema validará automáticamente

El reporte "Auditoria Matching" en el Excel de salida muestra:
- Asesores únicos del Excel
- Si matchean con JSON (`match_json`: Sí / No (revisar))
- Conteo de filas por asesor

**Resultado actual**: 47 asesores únicos, 100% con match en JSON (0 discrepancias).

## Instalación

### Requisitos
- Python 3.8+
- pip

### Pasos

1. Clonar el repositorio:
```bash
git clone <repo-url>
cd LADA
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Colocar el Excel de entrada en `data/input/FACTURACIONEX.xlsx`

## Uso

### Ejecución básica

```bash
cd src
python3 main.py
```

El script genera un Excel en `data/output/facturacion_procesada_YYYYMMDD_HHMMSS.xlsx` con:
- **Data Enriquecida**: Datos originales + columnas calculadas (teléfono, lada, estado, plaza, método)
- **Evaluadas**: Conteo por plaza
- **Activas**: Conteo por plaza
- **Detalle Facturación**: Evaluadas + Activas por plaza
- **Revisión Manual**: Casos que requieren revisión (extranjeros, no identificados)
- **Diagnóstico**: Métricas del proceso

### Pruebas de módulos individuales

Cada módulo incluye tests ejecutables:

```bash
cd src

# Test de carga de configuración
python3 config.py

# Test de carga de Excel
python3 excel_loader.py

# Test de extracción de teléfonos
python3 phone_extractor.py

# Test de matching de ladas
python3 lada_matcher.py

# Test de asignación de plazas
python3 plaza_matcher.py

# Test de resolución completa
python3 resolver.py

# Test de generación de reportes
python3 reports.py
```

## Cómo Funciona

### Pipeline de Procesamiento

1. **Carga de datos** (`excel_loader.py`)
   - Lee pestañas: data, Ladas, asesores
   - Normaliza tipos de datos (string para LADAs, float para Estrellas)
   - Extrae lista de plazas activas del mes

2. **Resolución de CONTACTO DIGITAL** (`resolver.py`)
   - Identifica filas con `Asesor == "CONTACTO DIGITAL "`
   - Para cada fila:
     - Extrae teléfono del campo `Contactos` (regex)
     - Normaliza a 10 dígitos (elimina código de país)
     - Extrae LADA (2 o 3 dígitos)
     - Matchea LADA → Estado (catálogo)
     - Asigna Estado → Plaza (mapeo configurable)

3. **Generación de reportes** (`reports.py`)
   - **Evaluadas**: Filtra por `Estatus` en ['EVALUADO', 'REVISION ASESOR', 'PARAMETRICO']
   - **Activas**: Filtra por `Estatus == 'ACTIVO'` AND `Estrellas >= 35`
   - Agrupa por plaza y suma
   - Identifica casos para revisión manual

### Extracción de Teléfonos

El módulo `phone_extractor.py` usa dos estrategias:

1. **Buscar después de "Telefono Fijo:"** (principal)
   ```python
   Telefono Fijo: 7552403032 Email: correo@gmail.com
   → 7552403032
   ```

2. **Fallback**: Buscar cualquier secuencia de 10+ dígitos
   - Toma últimos 10 dígitos (elimina +52, 52, 01 automáticamente)

### Matching de LADA

El `lada_matcher.py` prueba primero 2 dígitos, luego 3:
- **Lada 2 dígitos**: 33 (Jalisco), 55 (CDMX), 81 (Nuevo León)
- **Lada 3 dígitos**: 755 (Guerrero), 999 (Yucatán), 664 (Baja California)

**Nota sobre coincidencia 68.6%**: El catálogo de ladas tiene duplicados (misma lada en diferentes estados). Se resolvieron las **76 ladas conflictivas** con un catálogo limpio (`config/catalogo_ladas_limpio.csv`) que documenta la decisión y su fuente (GT Ariadne, IFT, frecuencia real). El 68.6% mide la coincidencia contra la columna precalculada del Excel, que es la interpretación de Ariadne, no la verdad absoluta. Ver sección "Auditoría de LADAs".

### Asignación de Plazas

El `plaza_matcher.py` usa la siguiente lógica:

1. **Match directo**: Estado tiene plaza en `estado_a_plaza.yaml`
2. **Plaza inactiva**: Plaza del estado no está activa este mes (marcar para revisión)
3. **Estado sin mapeo**: Usar fallback (configurable, default: MEXICALI)
4. **TODO**: Plaza geográficamente cercana (requiere geocoding)

## Configuración

### `config/config.yaml`

Parámetros principales:
```yaml
paths:
  input_excel: "../data/input/FACTURACIONEX.xlsx"

clasificacion:
  evaluadas_estatus: ["EVALUADO", "REVISION ASESOR", "PARAMETRICO"]
  activas_estatus: "ACTIVO"
  activas_umbral_estrellas: 35

plaza_assignment:
  fallback_extranjero: "MEXICALI BAJA CALIFORNIA "
  no_identificado_label: "NO IDENTIFICADO"

validaciones:
  totales_esperados:
    evaluadas: 9952
    activas: 503
  min_coincidencia_lada_percent: 95.0
```

### `config/estado_a_plaza.yaml`

Mapeo Estado → Plaza activa:
```yaml
estado_plaza:
  "Aguascalientes": "AGUASCALIENTES AGUASCALIENTES "
  "Baja California": "MEXICALI BAJA CALIFORNIA "
  "Jalisco": "GUADALAJARA JALISCO "
  # ... 44 estados
```

### `config/overrides_plazas.yaml`

Coordenadas para plazas con nombres ambiguos (geocoding):
```yaml
overrides:
  "MEXICO CENTRO ESTADO DE MEXICO ":
    lat: 19.4326
    lon: -99.1332
    nota: "Ciudad de México, centro"
  # ... 13 overrides
```

## Clasificación de Entrevistas

### Evaluadas
Contabiliza entrevistas con estatus:
- EVALUADO
- REVISION ASESOR
- PARAMETRICO

### Activas
Contabiliza entrevistas que cumplen:
- `Estatus == "ACTIVO"`
- `Estrellas >= 35`

**Nota**: La columna Estrellas tiene rango 0-96, no es porcentaje. El umbral de 35 está configurado en `config.yaml`.

## Casos Especiales

### Números Extranjeros
- Ladas no mexicanas se asignan a plaza del norte (configurable)
- Default: MEXICALI BAJA CALIFORNIA
- Se marcan con método `fallback_extranjero`

### No Identificados
- Teléfonos no extraíbles o ladas no en catálogo
- Se marcan como "NO IDENTIFICADO"
- Aparecen en hoja "Revision Manual" del Excel de salida

### Plazas Inactivas
- Estado tiene plaza pero no está activa este mes
- Se asigna la plaza del mapeo (marcar para revisión)
- Método: `directo_estado_inactiva`

## Mejoras Futuras (TODOs)

### Alta Prioridad
1. ✅ **Optimizar matching de ladas (COMPLETADO)**
   - Catálogo limpio de 76 ladas conflictivas documentadas
   - Decisiones basadas en GT de Ariadne, IFT y frecuencia real
   - Archivo: `config/catalogo_ladas_limpio.csv`

2. **Implementar geocoding completo**
   - Generar coordenadas automáticas con Nominatim
   - Calcular plaza más cercana geográficamente
   - Cache de resultados en CSV

### Media Prioridad
3. ✅ **Comparación con reporte de Ariadne (COMPLETADO)**
   - Auditoría de las 76 ladas conflictivas vs columna ESTADO precalculada
   - 26 filas difieren: todas son correcciones IFT legítimas documentadas
   - Visible en sección "Auditoría de LADAs" y hoja "Revision Manual"

4. **Validación de datos de entrada**
   - Detectar cambios en estructura del Excel
   - Alertar sobre valores inesperados
   - Sugerir ajustes en configuración

5. **Interfaz gráfica (opcional)**
   - GUI para ejecutar sin terminal
   - Selector de archivos
   - Vista previa de resultados

### Baja Prioridad
6. **Tests unitarios**
   - pytest para cada módulo
   - Cobertura de código
   - Tests de integración

7. **Logging avanzado**
   - Logs a archivo
   - Niveles de verbosidad
   - Auditoría completa del proceso

## Preguntas Frecuentes

**P: ¿Por qué la coincidencia de lada es 68.6% y no 95%+?**
R: El catálogo de ladas tiene duplicados (misma lada mapeada a diferentes estados). Se creó un catálogo limpio que resuelve los 76 casos conflictivos con decisiones documentadas (GT Ariadne, IFT, frecuencia real). El 68.6% mide coincidencia contra la columna precalculada del Excel (interpretación de Ariadne). Las 26 discrepancias restantes son correcciones IFT legítimas listadas para revisión manual.

**P: ¿Cómo se manejan los números con espacios o formato inconsistente?**
R: El extractor normaliza eliminando todo lo que no sea dígito, luego toma los últimos 10 dígitos (descarta códigos de país automáticamente).

**P: ¿Qué pasa si una plaza cambia de nombre entre meses?**
R: Actualizar `config/estado_a_plaza.yaml` con el nuevo nombre. El sistema usa la lista de plazas activas de la columna PLAZAS del Excel de entrada.

**P: ¿Cómo agrego una nueva plaza o estado?**
R: Editar `config/estado_a_plaza.yaml` agregando la línea correspondiente. Si tiene nombre ambiguo, agregar coordenadas en `config/overrides_plazas.yaml`.

**P: ¿El sistema funciona para otros clientes o solo Farmacias?**
R: La lógica es específica para Farmacias pero el código es modular y reutilizable. Requeriría ajustar:
- Nombres de columnas en `excel_loader.py`
- Criterios de clasificación en `config.yaml`
- Mapeo de plazas

## Mantenimiento Mensual

1. Colocar nuevo Excel en `data/input/`
2. Actualizar `config.yaml` con totales esperados (si se conocen)
3. Ejecutar: `cd src && python3 main.py`
4. Revisar hoja "Revision Manual" en Excel de salida
5. Validar totales en hoja "Diagnostico"
6. Si hay plazas nuevas/cambios, actualizar `estado_a_plaza.yaml`

## Contribuir

Este proyecto está estructurado para facilitar mantenimiento y extensión:
- Código modular (cada módulo una responsabilidad)
- Configuración externa (sin hardcodear valores)
- Tests ejecutables en cada módulo
- Documentación en código y README

Para agregar funcionalidad:
1. Crear nuevo módulo en `src/`
2. Agregar test ejecutable (`if __name__ == '__main__'`)
3. Integrar en `main.py` o módulo correspondiente
4. Actualizar README

## Licencia

Este es un proyecto interno para automatización de procesos de facturación.

## Contacto

Desarrollado para Sara/FA - Cliente Farmacias
Automatización de proceso de facturación mensual de entrevistas