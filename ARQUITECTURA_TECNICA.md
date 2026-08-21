# ARQUITECTURA TÉCNICA — Sistema de Facturación Automatizada

> Documentación técnica completa: cada módulo, función y decisión de diseño explicada.

---

## TABLA DE CONTENIDOS

1. [Visión General del Sistema](#1-visión-general-del-sistema)
2. [Flujo de Datos End-to-End](#2-flujo-de-datos-end-to-end)
3. [Módulos del Sistema](#3-módulos-del-sistema)
4. [Catálogos y Fuentes de Datos](#4-catálogos-y-fuentes-de-datos)
5. [Decisiones de Diseño](#5-decisiones-de-diseño)
6. [Casos Especiales y Edge Cases](#6-casos-especiales-y-edge-cases)

---

## 1. VISIÓN GENERAL DEL SISTEMA

### 1.1 Problema de Negocio

**Cliente:** Sara/FA (Farmacias)  
**Necesidad:** Facturar mensualmente ~12,000 entrevistas de aplicantes evaluados por asesores de RH.

**Obstáculo:** ~2,500 entrevistas (20%) tienen `Asesor = "CONTACTO DIGITAL "`, lo que significa:
- No hay plaza física asignada (el asesor fue un bot/sistema digital)
- No se puede facturar directamente porque la facturación es por plaza
- Ariadne (analista de Sara) debe inferir manualmente la plaza revisando el teléfono del aplicante

**Solución:** Automatizar la inferencia de plaza desde el número de teléfono usando:
```
Teléfono → LADA → Estado → Plaza más cercana
```

### 1.2 Stack Tecnológico

```
Python 3.12
├── pandas + openpyxl (lectura/escritura Excel)
├── PyYAML (configuración)
├── geopy (geocoding Nominatim para distancias)
└── Sin dependencias externas pesadas (portable, sin API keys)
```

### 1.3 Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTRADA (por mes)                             │
├─────────────────────────────────────────────────────────────────┤
│ 1. Excel mensual (pestaña "data", ~12K filas)                   │
│ 2. full_asesor_estado.json (roles activos del backoffice)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  CATÁLOGOS ESTÁTICOS (config/)                   │
├─────────────────────────────────────────────────────────────────┤
│ • catalogo_ladas_base.csv (314 ladas únicas)                    │
│ • catalogo_ladas_limpio.csv (76 overrides resueltos)            │
│ • estado_a_plaza.yaml (mapeo estado→plaza directa)              │
│ • overrides_plazas.yaml (casos especiales)                      │
│ • asesor_normalization.yaml (normalización nombres asesores)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE (src/*.py)                           │
├─────────────────────────────────────────────────────────────────┤
│ ExcelLoader → ContactoDigitalResolver → ReportGenerator         │
│      ↓              ↓                         ↓                  │
│   Carga       PhoneExtractor          Evaluadas/Activas         │
│   datos       LadaMatcher                                        │
│               PlazaMatcher                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 SALIDA (data/output/)                            │
├─────────────────────────────────────────────────────────────────┤
│ Excel con 7 pestañas:                                            │
│ 1. Data Enriquecida (LADA/ESTADO/PLAZA calculados)              │
│ 2. Evaluadas por plaza                                           │
│ 3. Activas por plaza                                             │
│ 4. Detalle Facturacion                                           │
│ 5. Revision Manual                                               │
│ 6. Auditoria Matching                                            │
│ 7. Diagnostico                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. FLUJO DE DATOS END-TO-END

### 2.1 Paso 1: Carga de Datos (`src/excel_loader.py`)

**Responsabilidad:** Leer el Excel mensual y extraer plazas activas del JSON.

**Código clave:**
```python
class ExcelLoader:
    def load_all(self):
        # 1. Leer SOLO pestaña "data"
        self.df_data = pd.read_excel(
            self.excel_path,
            sheet_name='data',
            dtype={'Asesor': str, 'Contactos': str, ...}
        )
        
        # 2. Plazas activas desde JSON (dinámico)
        from active_plazas import get_active_plazas_loader
        plazas_loader = get_active_plazas_loader('full_asesor_estado.json')
        self.plazas_activas = sorted(list(plazas_loader.get_plazas_activas()))
```

**¿Por qué así?**
- **Solo "data":** Las pestañas Ladas/asesores cambian por mes y tienen inconsistencias. Los catálogos congelados en `config/` son más confiables.
- **JSON dinámico:** Las plazas activas cambian mensualmente (aperturas/cierres). El JSON del backoffice es la única fuente de verdad.
- **dtype explícito:** `LADA` como string preserva ceros a la izquierda (ej. "01" vs 1).

**Output:** DataFrame con ~12K filas + lista de plazas activas (~67).

---

### 2.2 Paso 2: Resolución de CONTACTO DIGITAL (`src/resolver.py`)

**Responsabilidad:** Para cada fila con `Asesor = "CONTACTO DIGITAL "`, inferir la plaza.

**Flujo interno:**
```python
class ContactoDigitalResolver:
    def resolve_all(self, df):
        # 1. Identificar filas CONTACTO DIGITAL
        mask = df['Asesor'].apply(self._is_contacto_digital)
        
        # 2. Para cada una, extraer teléfono → lada → estado → plaza
        for idx in df[mask].index:
            contactos = df.loc[idx, 'Contactos']
            
            # 2a. Extraer teléfono
            phone = self.phone_extractor.extract_phone(contactos)
            
            # 2b. Extraer lada
            lada_2, lada_3 = self.phone_extractor.extract_lada(phone)
            lada, estado = self.lada_matcher.match_lada(lada_2, lada_3)
            
            # 2c. Asignar plaza
            plaza, metodo = self.plaza_matcher.match_plaza(estado, lada)
            
            # 2d. Guardar en DataFrame
            df.loc[idx, 'lada_calculada'] = lada
            df.loc[idx, 'estado_calculado'] = estado
            df.loc[idx, 'plaza_calculada'] = plaza
            df.loc[idx, 'metodo_asignacion'] = metodo
```

**¿Por qué un resolver separado?**
- Encapsula la lógica compleja de inferencia
- Permite probar la lógica de forma aislada
- Separa responsabilidades: `ExcelLoader` solo carga, `Resolver` solo infiere

---

### 2.3 Paso 2a: Extracción de Teléfono (`src/phone_extractor.py`)

**Problema:** El campo `Contactos` es texto libre:
```
"MARIA LOPEZ Telefono Fijo: 755 140 07 96 Email: maria@gmail.com"
"JUAN PEREZ Telefono Fijo: 5623464466 Email: juan@hotmail.com"
"+52 663 207 2378"
```

**Solución:** Regex que busca 10 dígitos consecutivos (ignorando espacios):

```python
class PhoneExtractor:
    def extract_phone(self, contactos_raw: str) -> str:
        # 1. Limpiar: solo dígitos
        digits = re.sub(r'\D', '', contactos_raw)
        
        # 2. Tomar últimos 10 (descartar +52, 01, etc.)
        if len(digits) >= 10:
            return digits[-10:]
        return None
```

**¿Por qué últimos 10?**
- Números mexicanos tienen 10 dígitos (formato nacional)
- Si el usuario escribió +52 (código país) o 01 (prefijo), los descartamos
- Ejemplo: `+526632072378` → últimos 10 → `6632072378`

**Extracción de LADA:**
```python
def extract_lada(self, phone: str) -> Tuple[str, str]:
    # Lada de 2 dígitos: primeros 2
    lada_2 = phone[:2]
    
    # Lada de 3 dígitos: primeros 3
    lada_3 = phone[:3]
    
    return lada_2, lada_3
```

**¿Por qué 2 y 3 dígitos?**
- México tiene ladas de 2 dígitos (grandes ciudades: 33 Guadalajara, 55 CDMX)
- Y ladas de 3 dígitos (ciudades medianas/pequeñas: 755 Guerrero, 663 Baja California)
- El plan de numeración es "prefix-free": no hay colisión (ej. no existe lada 55 y 555)

---

### 2.4 Paso 2b: Matching de LADA (`src/lada_matcher.py`)

**Responsabilidad:** Cruzar lada contra el catálogo para obtener el estado.

**Estructura de datos:**
```python
class LadaMatcher:
    def __init__(self):
        # Catálogo BASE (config/catalogo_ladas_base.csv)
        # 314 ladas únicas, sin duplicados
        self.lada_to_estado = {
            '33': 'Jalisco',
            '55': 'CDMX',
            '755': 'Guerrero',
            ...
        }
        
        # OVERRIDES (config/catalogo_ladas_limpio.csv)
        # 76 ladas conflictivas con decisión documentada
        # Los overrides sobrescriben el catálogo base
```

**Lógica de matching:**
```python
def match_lada(self, lada_2: str, lada_3: str) -> Tuple[str, str]:
    # 1. Probar lada de 2 dígitos primero
    if lada_2 in self.lada_to_estado:
        return lada_2, self.lada_to_estado[lada_2]
    
    # 2. Si no, probar lada de 3 dígitos
    if lada_3 in self.lada_to_estado:
        return lada_3, self.lada_to_estado[lada_3]
    
    # 3. No hay match
    return None, None
```

**¿Por qué esta prioridad?**
- Ladas cortas (2 dígitos) son más comunes (ciudades grandes)
- Si existe lada 55, no puede existir 555 (prefix-free)
- Si no matchea ninguna, es número extranjero o lada nueva

**Fuentes del catálogo:**
- **IFT (Instituto Federal de Telecomunicaciones):** fuente oficial
- **GT Ariadne:** ladas que Ariadne corrigió manualmente en meses previos
- **Frecuencia real:** cuando hay conflicto, se elige la lada que aparece más en los datos

---

### 2.5 Paso 2c: Matching de Plaza (`src/plaza_matcher.py`)

**Responsabilidad:** Dado un estado, asignar la plaza correcta.

**Métodos de asignación:**

```python
class PlazaMatcher:
    def match_plaza(self, estado: str, lada: str) -> Tuple[str, str]:
        # Método 1: MAPEO DIRECTO (estado_a_plaza.yaml)
        if estado in self.estado_to_plaza:
            plaza = self.estado_to_plaza[estado]
            if plaza in self.plazas_activas:
                return plaza, 'directo_estado'
            else:
                return plaza, 'directo_estado_inactiva'
        
        # Método 2: OVERRIDE MANUAL (overrides_plazas.yaml)
        if lada in self.overrides:
            return self.overrides[lada], 'override_manual'
        
        # Método 3: PLAZA MÁS CERCANA (geocoding)
        plaza_cercana = self._find_closest_plaza(estado)
        return plaza_cercana, 'plaza_cercana'
        
        # Método 4: FALLBACK EXTRANJERO
        if lada is None:
            return self.config.fallback_extranjero, 'fallback_extranjero'
        
        # Método 5: NO IDENTIFICADO
        return 'NO IDENTIFICADO', 'no_identificado'
```

**¿Por qué esta jerarquía?**

1. **Mapeo directo:** Más rápido y confiable (estado → plaza, sin ambigüedad)
2. **Override manual:** Para casos especiales que Sara/Ariadne conocen mejor
3. **Plaza cercana:** Cuando el estado no tiene plaza activa, buscar la más cercana geográficamente
4. **Fallback extranjero:** Números +1, +34, etc. se asignan a una plaza fronteriza (configurable)
5. **No identificado:** Marcar para revisión manual

**Geocoding (plaza cercana):**
```python
def _find_closest_plaza(self, estado: str) -> str:
    # 1. Obtener coordenadas del estado (Nominatim cache)
    estado_coords = self.geocoder.get_coordinates(estado)
    
    # 2. Para cada plaza activa, calcular distancia haversine
    distancias = {}
    for plaza in self.plazas_activas:
        plaza_coords = self.geocoder.get_coordinates(plaza)
        distancia_km = haversine(estado_coords, plaza_coords)
        distancias[plaza] = distancia_km
    
    # 3. Retornar la plaza con menor distancia
    return min(distancias, key=distancias.get)
```

**¿Por qué haversine?**
- Fórmula precisa para distancias en esfera (Tierra)
- No requiere APIs externas (cálculo matemático puro)
- Cache en JSON local para no re-geocodificar cada corrida

---

### 2.6 Paso 3: Generación de Reportes (`src/reports.py`)

**Responsabilidad:** Producir las tablas de facturación (Evaluadas, Activas).

**Tabla Evaluadas:**
```python
class ReportGenerator:
    def generate_evaluadas(self, df_resolved):
        # 1. Filtrar por estatus: EVALUADO, REVISION ASESOR, PARAMETRICO
        mask = df_resolved['Estatus'].isin([
            'EVALUADO', 
            'REVISION ASESOR', 
            'PARAMETRICO'
        ])
        df_eval = df_resolved[mask]
        
        # 2. Agrupar por plaza y contar
        evaluadas = df_eval.groupby('plaza_calculada').size()
        
        # 3. Agregar total general
        evaluadas['Total general'] = evaluadas.sum()
        
        return evaluadas
```

**¿Por qué estos estatus?**
- Sara definió que "evaluado" = entrevista completada (aprobada o rechazada)
- Incluye revisiones pendientes porque ya pasaron por el sistema

**Tabla Activas:**
```python
def generate_activas(self, df_resolved):
    # 1. Filtrar: Estatus=ACTIVO Y Estrellas>=35
    mask = (
        (df_resolved['Estatus'] == 'ACTIVO') &
        (df_resolved['Estrellas'] >= 35)
    )
    df_act = df_resolved[mask]
    
    # 2. Agrupar y contar
    activas = df_act.groupby('plaza_calculada').size()
    
    return activas
```

**¿Por qué Estrellas >= 35?**
- El sistema de RH asigna estrellas de 0-100 como % de avance en el proceso
- 35% es el umbral que Sara define como "activa" (candidato con progreso real)
- Esto filtra aplicantes que solo llenaron el formulario inicial

---

## 3. MÓDULOS DEL SISTEMA

### 3.1 `src/config.py` — Configuración Central

**Propósito:** Cargar `config/config.yaml` y exponer parámetros.

```python
class Config:
    def __init__(self, project_root: str):
        # Cargar YAML
        config_path = Path(project_root) / 'config' / 'config.yaml'
        with open(config_path) as f:
            self.data = yaml.safe_load(f)
    
    def get(self, key_path: str, default=None):
        # Navegar dot notation: 'validaciones.totales_esperados.evaluadas'
        keys = key_path.split('.')
        value = self.data
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default
    
    def set_input_excel(self, path: str):
        # Permite override del Excel de entrada vía CLI
        self.input_excel_path = Path(path)
```

**¿Por qué YAML y no JSON/ENV?**
- YAML permite comentarios (documentar decisiones)
- Estructura jerárquica clara
- Más legible para humanos (Sara puede editarlo sin programar)

---

### 3.2 `src/active_plazas.py` — Extractor de Plazas Activas

**Propósito:** Leer `full_asesor_estado.json` y extraer roles ASESOR con estatus Activo.

**Estructura del JSON:**
```json
{
  "rol": "ASESOR ACAPULCO",
  "estatus": {"nombre": "Activo"},
  "rolesDependientes": [
    {
      "rol": "ASESOR MONTERREY",
      "estatus": {"nombre": "Activo"}
    }
  ]
}
```

**Código:**
```python
class ActivePlazasLoader:
    def load(self):
        with open(self.json_path) as f:
            data = json.load(f)
        
        # Recorrer recursivamente el árbol de roles
        self._walk_roles(data)
    
    def _walk_roles(self, node):
        # Si el rol empieza con "ASESOR" y tiene estatus Activo
        if node.get('rol', '').startswith('ASESOR'):
            estatus = node.get('estatus', {}).get('nombre')
            if estatus == 'Activo':
                # Normalizar: "ASESOR ACAPULCO" → "ACAPULCO"
                plaza = node['rol'].replace('ASESOR ', '').strip()
                self._plazas_activas.add(plaza)
        
        # Recursión en hijos
        for child in node.get('rolesDependientes', []):
            self._walk_roles(child)
```

**¿Por qué recursión?**
- El JSON tiene estructura de árbol (jerarquía de roles)
- Algunos asesores están anidados bajo supervisores
- La recursión garantiza que visitamos todos los nodos

---

### 3.3 `src/asesor_normalizer.py` — Normalización de Nombres

**Propósito:** Convertir nombres inconsistentes de asesores a formato estándar.

**Problema:**
```
"ACAPULCO GUERRERO "  (con espacio al final)
"ACAPULCO GUERRERO"   (sin espacio)
"Acapulco Guerrero"   (minúsculas)
```

**Solución:**
```python
class AsesorNormalizer:
    def __init__(self, normalization_yaml):
        # Cargar mapeo de normalizaciones
        self.normalization_map = yaml.safe_load(open(normalization_yaml))
    
    def normalize(self, asesor_raw: str) -> str:
        # 1. Limpiar espacios
        asesor = asesor_raw.strip().upper()
        
        # 2. Aplicar mapeo manual
        if asesor in self.normalization_map:
            return self.normalization_map[asesor]
        
        return asesor
```

**¿Por qué manual?**
- Fuzzy matching (distancia Levenshtein) es peligroso: puede unir plazas distintas
- El mapeo manual es explícito y auditable
- Sara puede agregar nuevas normalizaciones editando el YAML

---

### 3.4 `src/geocoder.py` — Cache de Coordenadas

**Propósito:** Obtener lat/long de plazas/estados sin hacer requests repetidos.

```python
class Geocoder:
    def __init__(self, cache_path):
        # Cargar cache existente
        if Path(cache_path).exists():
            self.cache = json.load(open(cache_path))
        else:
            self.cache = {}
    
    def get_coordinates(self, location: str) -> Tuple[float, float]:
        # 1. Buscar en cache
        if location in self.cache:
            return self.cache[location]
        
        # 2. Consultar Nominatim (con rate limit)
        time.sleep(1.0)  # Respetar rate limit
        geolocator = Nominatim(user_agent="LADA_Facturacion/1.0")
        result = geolocator.geocode(location + ", Mexico")
        
        if result:
            coords = (result.latitude, result.longitude)
            self.cache[location] = coords
            self._save_cache()
            return coords
        
        return None
```

**¿Por qué Nominatim y no Google Maps?**
- Nominatim es gratuito y sin API key (portable)
- Rate limit de 1 req/segundo es suficiente (solo se usa al setup)
- Cache local hace que corridas subsecuentes sean instantáneas

---

## 4. CATÁLOGOS Y FUENTES DE DATOS

### 4.1 `config/catalogo_ladas_base.csv`

**Formato:**
```csv
lada,estado
33,Jalisco
55,CDMX
755,Guerrero
```

**Origen:** Pestaña "Ladas" del Excel de julio (4,477 filas) → deduplicada a 314 ladas únicas.

**¿Por qué congelar?**
- Las ladas NO cambian por mes (plan de numeración nacional)
- La pestaña "Ladas" del Excel tiene duplicados y errores
- Mantener una fuente limpia y versionada en Git

---

### 4.2 `config/catalogo_ladas_limpio.csv`

**Formato:**
```csv
lada,estado,fuente
33,Jalisco,IFT_desempate
755,Guerrero,GT_ariadne
```

**Propósito:** Resolver conflictos donde una lada aparece con múltiples estados.

**Ejemplo de conflicto:**
```
Lada 999 → Yucatán (según IFT)
Lada 999 → Quintana Roo (según Excel de Sara)
```

**Decisión:** Crear override manual con `fuente` documentada (IFT, GT Ariadne, frecuencia real).

---

### 4.3 `config/estado_a_plaza.yaml`

**Formato:**
```yaml
Jalisco: GUADALAJARA JALISCO
CDMX: MX CENTRO
Guerrero: ACAPULCO GUERRERO
```

**Propósito:** Mapeo directo estado → plaza sin ambigüedad.

**¿Por qué YAML y no CSV?**
- Más legible para mapeos clave-valor
- Permite comentarios para documentar excepciones

---

### 4.4 `config/overrides_plazas.yaml`

**Formato:**
```yaml
# Casos especiales donde el estado NO determina la plaza
'755': 'ACAPULCO GUERRERO'  # Lada conflictiva, forzar Acapulco
'81': 'MONTERREY NORTE'      # Monterrey tiene 3 plazas, elegir norte
```

**Propósito:** Casos que Sara/Ariadne conocen mejor que la lógica genérica.

---

### 4.5 `config/asesor_normalization.yaml`

**Formato:**
```yaml
'ACAPULCO GUERRERO ': 'ACAPULCO GUERRERO'  # Quitar espacio final
'Mex Centro': 'MEXICO CENTRO'               # Corregir typo
```

**Propósito:** Estandarizar nombres de asesores que vienen inconsistentes.

---

### 4.6 `full_asesor_estado.json` (raíz del proyecto)

**Origen:** Exportación del backoffice de RH (sistema de Sara).

**Actualización:** Mensual — Sara reemplaza el archivo antes de correr el pipeline.

**¿Por qué JSON y no base de datos?**
- Portable: no requiere servidor de BD
- Versionable en Git (auditoría de cambios)
- Fácil de generar desde el backoffice (export JSON estándar)

---

## 5. DECISIONES DE DISEÑO

### 5.1 ¿Por qué separar catálogos del Excel mensual?

**Problema detectado:**
- El Excel de agosto NO tenía pestañas Ladas/asesores
- Las pestañas cambian de estructura entre meses
- Contienen errores y duplicados

**Solución:**
- Congelar catálogos una sola vez en `config/`
- El Excel mensual SOLO aporta la pestaña "data"
- Fuentes dinámicas (plazas activas) vienen del JSON, no del Excel

**Beneficio:**
- Pipeline robusto: funciona con cualquier Excel que tenga "data"
- Catálogos versionados y auditables en Git
- No rompe si Sara cambia el formato del Excel

---

### 5.2 ¿Por qué usar método de asignación como columna?

**Código:**
```python
df.loc[idx, 'metodo_asignacion'] = 'directo_estado'
# o 'plaza_cercana', 'override_manual', 'fallback_extranjero', 'no_identificado'
```

**Propósito:**
- Auditoría: Sara puede filtrar en Excel y ver cuáles plazas se asignaron por inferencia vs. mapeo directo
- Debug: Si hay un error, saber dónde falló la lógica
- Confianza: Diferenciar asignaciones confiables (directo) de inciertas (plaza cercana)

---

### 5.3 ¿Por qué totales esperados como advertencia y no bloqueo?

**Antes:**
```python
if total_eval != esperado_eval:
    raise ValueError("Totales no cuadran!")
```

**Ahora:**
```python
if total_eval != esperado_eval:
    print("⚠ Advertencia: Totales no cuadran")
    # Continuar ejecución
```

**Razón:**
- Los totales esperados son de OTRO mes (config.yaml tiene julio hardcoded)
- Al cambiar de mes, es NORMAL que no cuadren
- El bloqueo impedía usar el pipeline para meses nuevos
- La advertencia permite auditar sin frenar el proceso

---

### 5.4 ¿Por qué `--input` CLI en lugar de editar config.yaml?

**Antes:**
```bash
# Usuario edita config.yaml manualmente
paths:
  input_excel: "data/input/FACTURACIONES_2.xlsx"

# Luego corre
python src/main.py
```

**Ahora:**
```bash
# Usuario NO toca config.yaml
python src/main.py --input data/input/FACTURACIONES_2.xlsx
```

**Beneficio:**
- Más rápido (un comando vs. editar archivo)
- No requiere conocimiento de YAML
- No hay riesgo de romper config.yaml con typo
- Permite automatización (cron jobs, scripts batch)

---

### 5.5 ¿Por qué modular el código en clases?

**Alternativa naive:**
```python
# Todo en un solo script monolítico
df = pd.read_excel(...)
for idx, row in df.iterrows():
    if row['Asesor'] == 'CONTACTO DIGITAL':
        phone = extract_phone(row['Contactos'])
        lada = extract_lada(phone)
        estado = match_estado(lada)
        plaza = match_plaza(estado)
        df.loc[idx, 'plaza'] = plaza
```

**Problema:**
- Difícil de probar (no se pueden testear funciones aisladas)
- Difícil de debuggear (stack trace confuso)
- Difícil de extender (agregar nuevo método de asignación requiere reescribir todo)

**Solución: Clases con responsabilidad única**
```python
phone_extractor = PhoneExtractor()
lada_matcher = LadaMatcher()
plaza_matcher = PlazaMatcher()
resolver = ContactoDigitalResolver(phone_extractor, lada_matcher, plaza_matcher)
```

**Beneficio:**
- Cada clase tiene UN trabajo (Single Responsibility Principle)
- Fácil de testear: `test_phone_extractor.py` solo prueba extracción
- Fácil de debuggear: error en matching de lada → revisar solo `LadaMatcher`
- Fácil de extender: agregar nuevo método en `PlazaMatcher` sin tocar `PhoneExtractor`

---

## 6. CASOS ESPECIALES Y EDGE CASES

### 6.1 Números Extranjeros

**Caso:** `Contactos = "+1 415 555 0123"` (número de USA)

**Flujo:**
```python
# 1. PhoneExtractor detecta que no son 10 dígitos mexicanos
phone = None

# 2. LadaMatcher retorna None
lada, estado = None, None

# 3. PlazaMatcher aplica fallback
plaza = config.fallback_extranjero  # ej. "TIJUANA BAJA CALIFORNIA"
metodo = 'fallback_extranjero'
```

**¿Por qué Tijuana?**
- Es plaza fronteriza (aplicantes de USA probablemente viven cerca)
- Configurable en `config.yaml` (Sara puede cambiar a otra plaza)

---

### 6.2 Números sin Lada Identificada

**Caso:** Lada nueva que NO está en el catálogo (ej. lada recién asignada por IFT)

**Flujo:**
```python
# 1. PhoneExtractor extrae el teléfono correctamente
phone = "9991234567"

# 2. LadaMatcher no encuentra match
lada_2 = "99", lada_3 = "999"
# Ni "99" ni "999" están en el catálogo
lada, estado = None, None

# 3. PlazaMatcher marca como no identificado
plaza = 'NO IDENTIFICADO'
metodo = 'no_identificado'
```

**Manejo:**
- La fila aparece en la pestaña "Revision Manual" del Excel de salida
- Sara/Ariadne revisan manualmente y agregan la lada al catálogo para el mes siguiente

---

### 6.3 Estado sin Plaza Activa

**Caso:** `Estado = "Campeche"` pero NO hay plaza activa en Campeche ese mes

**Flujo:**
```python
# 1. LadaMatcher encuentra el estado
lada = "981", estado = "Campeche"

# 2. PlazaMatcher busca en estado_a_plaza.yaml
# Campeche → CAMPECHE (plaza directa)
# Pero CAMPECHE no está en plazas_activas (cerró esa plaza)

# 3. Buscar plaza más cercana geográficamente
plaza_cercana = geocoder.find_closest('Campeche', plazas_activas)
# Retorna "MERIDA YUCATAN" (plaza activa más cercana)
plaza = 'MERIDA YUCATAN'
metodo = 'plaza_cercana'
```

**Auditoría:**
- La columna `metodo_asignacion = 'plaza_cercana'` permite filtrar estos casos
- Sara puede revisar si la asignación tiene sentido geográficamente

---

### 6.4 Asesor = "CONTACTO DIGITAL " (con espacio)

**Problema:** El string NO es `"CONTACTO DIGITAL"` sino `"CONTACTO DIGITAL "` (espacio al final)

**Solución:**
```python
@staticmethod
def _is_contacto_digital(asesor: str) -> bool:
    # .strip() remueve espacios
    # .upper() normaliza mayúsculas
    return asesor.strip().upper() == 'CONTACTO DIGITAL'
```

**¿Por qué esta paranoia?**
- Excel permite espacios invisibles al final de celdas
- Un `==` directo fallaría silenciosamente
- `.strip().upper()` garantiza match robusto

---

### 6.5 Teléfono con Formato Inconsistente

**Casos reales:**
```
"755 140 07 96"           → espacios entre grupos
"7551400796"              → sin espacios
"+52 755 140 0796"        → código país
"01 755 140 0796"         → prefijo viejo
"Telefono Fijo: 755..."   → texto mezclado
```

**Solución universal:**
```python
def extract_phone(self, contactos_raw: str) -> str:
    # Paso 1: Quitar TODO lo que NO sea dígito
    digits = re.sub(r'\D', '', contactos_raw)
    # "755 140 07 96" → "7551400796"
    # "+52 755..." → "527551400796"
    
    # Paso 2: Tomar últimos 10 dígitos
    if len(digits) >= 10:
        return digits[-10:]  # "7551400796"
    
    return None
```

**¿Por qué funciona?**
- Regex `\D` (non-digit) elimina TODO excepto números
- Tomar últimos 10 descarta cualquier prefijo (+52, 01, etc.)
- Robusto contra cualquier formato que el usuario invente

---

### 6.6 Plaza Directa vs JSON de Asesores

**Problema:** El Excel tiene `Asesor = "MONTERREY"` pero el JSON tiene `"ASESOR MONTERREY NORTE"` y `"ASESOR MONTERREY SUR"`

**Validación:**
```python
# En resolver.py, después de procesar todas las filas:
def validate_direct_plazas(self, df):
    # Filas con plaza directa (no CONTACTO DIGITAL)
    mask_directo = ~df['Asesor'].str.contains('CONTACTO DIGITAL')
    
    for idx in df[mask_directo].index:
        plaza_excel = df.loc[idx, 'Asesor']
        plaza_normalizada = normalize(plaza_excel)
        
        # ¿Está en el JSON de plazas activas?
        if plaza_normalizada not in self.plazas_activas:
            # Marcar para auditoría
            df.loc[idx, 'auditoria_flag'] = 'plaza_no_en_json'
```

**Output:** Pestaña "Auditoria Matching" con casos que requieren verificación.

---

## 7. EJEMPLOS DE CÓDIGO REAL

### 7.1 Pipeline Completo (src/main.py simplificado)

```python
def main():
    # 1. Configuración
    config = Config('.')
    
    # 2. Cargar datos
    loader = ExcelLoader(config.input_excel_path)
    df_data, _, plazas_activas = loader.load_all()
    
    # 3. Resolver CONTACTO DIGITAL
    resolver = ContactoDigitalResolver(config, plazas_activas, None)
    df_resolved = resolver.resolve_all(df_data)
    
    # 4. Generar reportes
    generator = ReportGenerator(config)
    df_evaluadas = generator.generate_evaluadas(df_resolved)
    df_activas = generator.generate_activas(df_resolved)
    
    # 5. Exportar Excel
    with pd.ExcelWriter('output.xlsx') as writer:
        df_resolved.to_excel(writer, sheet_name='Data Enriquecida', index=False)
        df_evaluadas.to_excel(writer, sheet_name='Evaluadas', index=False)
        df_activas.to_excel(writer, sheet_name='Activas', index=False)
    
    print("✓ Procesamiento completado")
```

---

### 7.2 Test Unitario (ejemplo conceptual)

```python
import pytest
from phone_extractor import PhoneExtractor

def test_extract_phone_with_spaces():
    extractor = PhoneExtractor()
    contactos = "MARIA LOPEZ Telefono Fijo: 755 140 07 96 Email: m@gmail.com"
    
    phone = extractor.extract_phone(contactos)
    
    assert phone == "7551400796"

def test_extract_phone_with_country_code():
    extractor = PhoneExtractor()
    contactos = "+52 663 207 2378"
    
    phone = extractor.extract_phone(contactos)
    
    assert phone == "6632072378"  # Sin +52

def test_extract_lada():
    extractor = PhoneExtractor()
    phone = "6632072378"
    
    lada_2, lada_3 = extractor.extract_lada(phone)
    
    assert lada_2 == "66"
    assert lada_3 == "663"
```

---

## 8. FLUJO DE TRABAJO MENSUAL

### 8.1 Checklist para Sara/Operador

1. **Obtener inputs del mes:**
   ```bash
   # Descargar desde el sistema de RH
   - Excel mensual (ej. FACTURACIONES_SEPTIEMBRE.xlsx)
   - full_asesor_estado.json (roles activos actualizados)
   ```

2. **Colocar archivos:**
   ```
   data/input/FACTURACIONES_SEPTIEMBRE.xlsx
   full_asesor_estado.json (raíz del proyecto, reemplazar el anterior)
   ```

3. **Ejecutar pipeline:**
   ```bash
   venv/bin/python src/main.py --input data/input/FACTURACIONES_SEPTIEMBRE.xlsx
   ```

4. **Revisar output:**
   ```bash
   # Abrir el Excel generado
   data/output/facturacion_procesada_YYYYMMDD_HHMMSS.xlsx
   
   # Revisar pestaña "Revision Manual" (casos no identificados)
   # Revisar pestaña "Auditoria Matching" (validación plazas)
   ```

5. **Casos especiales:**
   - Si hay ladas nuevas: agregar a `config/catalogo_ladas_base.csv`
   - Si hay plazas nuevas con nombre ambiguo: agregar override a `config/overrides_plazas.yaml`
   - Si hay asesores con nombres inconsistentes: agregar a `config/asesor_normalization.yaml`

6. **Facturar:**
   - Usar totales de las pestañas "Evaluadas" y "Activas"
   - Generar factura por plaza

---

## 9. TROUBLESHOOTING

### 9.1 "No module named 'src'"

**Error:**
```
ModuleNotFoundError: No module named 'src'
```

**Causa:** Python no encuentra el módulo `src/`

**Solución:**
```bash
# Opción 1: Correr desde la raíz del proyecto
cd /ruta/al/proyecto
python src/main.py --input data/input/archivo.xlsx

# Opción 2: Usar venv (recomendado)
venv/bin/python src/main.py --input data/input/archivo.xlsx
```

---

### 9.2 "Worksheet named 'data' not found"

**Causa:** El Excel NO tiene una pestaña llamada "data"

**Solución:**
1. Abrir el Excel en Excel/LibreOffice
2. Verificar que existe una pestaña llamada exactamente "data" (minúsculas)
3. Si la pestaña tiene otro nombre, renombrarla a "data"

---

### 9.3 Totales no cuadran con Ariadne

**Causa:** Los totales esperados en `config.yaml` son de OTRO mes

**Solución:**
1. Ignorar la advertencia (es normal al cambiar de mes)
2. O actualizar `config.yaml` con los totales del mes actual:
   ```yaml
   validaciones:
     totales_esperados:
       evaluadas: 10535  # Actualizar con el total real del mes
       activas: 559
   ```

---

## 10. MEJORAS FUTURAS

### 10.1 Geocoding Batch

**Problema actual:** Geocoding de ~132 plazas es lento (1 req/segundo)

**Mejora propuesta:**
```python
# Usar batch geocoding de Nominatim
# O pre-cachear todas las plazas en el setup inicial
```

---

### 10.2 Dashboard Web

**Propuesta:** Crear interfaz web simple con Flask/Streamlit para que Sara:
- Suba el Excel directamente desde el navegador
- Vea el progreso en tiempo real
- Descargue el Excel procesado
- No requiere tocar la línea de comandos

---

### 10.3 Notificaciones Automáticas

**Propuesta:** Email automático al terminar el procesamiento con:
- Resumen de totales
- Link al Excel de salida
- Alertas de casos que requieren revisión manual

---

## APÉNDICE: GLOSARIO

- **LADA:** Código de área telefónico (ej. 33 para Guadalajara)
- **Plaza:** Sucursal física de Farmacias donde trabaja un asesor
- **Asesor:** Reclutador de RH que evalúa aplicantes
- **CONTACTO DIGITAL:** Asesor virtual (bot/sistema) que no tiene plaza física
- **Evaluada:** Entrevista completada (aprobada o rechazada)
- **Activa:** Aplicante con progreso ≥35% en el proceso de selección
- **Override:** Excepción manual que sobrescribe la lógica genérica
- **Geocoding:** Convertir nombre de lugar a coordenadas lat/long
- **Haversine:** Fórmula para calcular distancia entre dos puntos en la Tierra

---

**Fin de la documentación técnica.**

Para preguntas o dudas, revisar el código fuente en `src/` (está comentado línea por línea).
