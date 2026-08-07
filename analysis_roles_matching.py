"""
ANÁLISIS DE MATCHING: full_asesor_estado.json (roles backoffice) vs data["Asesor"]
Propósito: determinar si quitar prefijo "ASESOR " + normalizar es suficiente para
match 1-a-1, y definir el criterio de "plaza activa" por estatus.
"""
import json, re, pandas as pd
from collections import defaultdict

EXCEL = 'data/input/FACTURACIONEX.xlsx'
JSON_FILE = 'full_asesor_estado.json'

import os
if not os.path.exists(EXCEL):
    EXCEL = 'FACTURACIONEX.xlsx'
if not os.path.exists(EXCEL):
    raise FileNotFoundError(f"No se encontró el Excel en data/input/ ni en la raíz: {EXCEL}")
if not os.path.exists(JSON_FILE):
    raise FileNotFoundError(f"No se encontró el JSON: {JSON_FILE}")

# ---------- 1. Cargar JSON y extraer TODOS los roles (recursivo) ----------
with open(JSON_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

roles = {}  # rol -> set(estatus)
rol_origen = defaultdict(list)  # rol -> de dónde viene (principal/dependiente)

def walk(node, es_dependiente=False):
    if not isinstance(node, dict):
        return
    rol_nombre = node.get('rol')
    if isinstance(rol_nombre, str) and rol_nombre:
        est = node.get('estatus', {})
        nombre_est = est.get('nombre') if isinstance(est, dict) else None
        roles.setdefault(rol_nombre, set()).add(nombre_est)
        rol_origen[rol_nombre].append('dependiente' if es_dependiente else 'principal')
    # Descender: primero dentro del dict 'rol' (si es dict), luego en rolesDependientes
    candidates = []
    r = node.get('rol')
    if isinstance(r, dict):
        candidates.append(r)
    candidates.extend(node.get('rolesDependientes', []) or [])
    for hijo in candidates:
        walk(hijo, es_dependiente=True)

for persona in data:
    walk(persona)

# ---------- 2. Cargar data["Asesor"] ----------
df_data = pd.read_excel(EXCEL, sheet_name='data', dtype={'Asesor': str, 'PLAZA': str})
asesores = sorted(df_data['Asesor'].dropna().str.strip().unique().tolist())
asesores_norm = [a for a in asesores if a != 'CONTACTO DIGITAL']

# ---------- 3. Normalizar para matching ----------
def norm(s):
    if not s:
        return ''
    s = s.upper().strip()
    s = re.sub(r'^ASESOR\s+', '', s)  # quitar prefijo
    s = re.sub(r'\s+', ' ', s)         # colapsar espacios
    return s.strip()

roles_norm = {r: norm(r) for r in roles}
asesores_norm_set = {norm(a) for a in asesores_norm}

# ---------- 4. Reporte ----------
print("=" * 80)
print(f"1. TOTALES")
print("=" * 80)
print(f"Roles únicos en JSON (todos, principal+dependiente): {len(roles)}")
print(f"Asesores únicos en data (excl. CONTACTO DIGITAL): {len(asesores_norm)}")
print(f"Personas en JSON: {len(data)}")

print("\n" + "=" * 80)
print("2. VALORES ÚNICOS DE estatus.nombre EN TODO EL JSON")
print("=" * 80)
todos_estatus = set()
for r, ss in roles.items():
    todos_estatus.update(ss)
for s in sorted(todos_estatus, key=str):
    print(f"   - {s!r}")

print("\n" + "=" * 80)
print("3. MATCHING NORMALIZADO (quitar 'ASESOR ' + trim + colapsar)")
print("=" * 80)
norm_roles = {norm(r) for r in roles}
norm_asesores = {norm(a) for a in asesores_norm}

matched_roles = norm_roles & norm_asesores
solo_json = sorted(norm_roles - norm_asesores)
solo_data = sorted(norm_asesores - norm_roles)

print(f"Roles JSON normalizados que matchean con data: {len(matched_roles)}")
print(f"En JSON pero NO en data: {len(solo_json)}")
print(f"En data pero NO en JSON: {len(solo_data)}")

print("\n--- EN DATA PERO NO EN JSON (con conteo de filas) ---")
conteo = df_data[df_data['Asesor'] != 'CONTACTO DIGITAL ']['Asesor'].str.strip().value_counts()
for a in solo_data:
    # encontrar el asesor original que normaliza a este valor
    orig = [x for x in asesores_norm if norm(x) == a]
    print(f"   {a!r}  <- orígenes: {orig}  (filas: {conteo.get(orig[0], '?') if orig else '?'})")

print("\n--- EN JSON PERO NO EN DATA (con estatus) ---")
for r in solo_json:
    orig_roles = [r0 for r0, n in roles_norm.items() if n == r]
    estats = set()
    for o in orig_roles:
        estats.update(roles[o])
    print(f"   {r!r}  (estatus: {sorted(map(str, estats))})")

print("\n" + "=" * 80)
print("4. ROLES NO-ASESOR EN JSON (para filtrar ruido)")
print("=" * 80)
no_asesor = sorted([r for r in roles if not r.startswith('ASESOR')])
print(f"Roles que NO empiezan con 'ASESOR': {len(no_asesor)}")
for r in no_asesor:
    print(f"   {r!r}")

print("\n" + "=" * 80)
print("5. ASESORES EN DATA COMPARADOS CONTRA ROLES JSON (con st 'ASESOR')")
print("=" * 80)
# Solo roles que empiezan con ASESOR
roles_asesor = {r for r in roles if r.startswith('ASESOR')}
norm_roles_asesor = {norm(r) for r in roles_asesor}
matched_asesor = norm_roles_asesor & norm_asesores
solo_json_asesor = sorted(norm_roles_asesor - norm_asesores)
solo_data_asesor = sorted(norm_asesores - norm_roles_asesor)
print(f"Roles 'ASESOR *' en JSON: {len(roles_asesor)}")
print(f"  Matchean con data: {len(matched_asesor)}")
print(f"  Solo JSON: {len(solo_json_asesor)}")
print(f"  Solo data: {len(solo_data_asesor)}")