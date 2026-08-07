"""
ANÁLISIS 2: matching fino JSON (sin prefijo) vs data (sin sufijo de estado).
Cuantifica cuántos matchean tras doble normalización y lista overrides necesarios.
"""
import json, re, pandas as pd
from collections import defaultdict

EXCEL = 'data/input/FACTURACIONEX.xlsx'
import os
if not os.path.exists(EXCEL):
    EXCEL = 'FACTURACIONEX.xlsx'
JSON_FILE = 'full_asesor_estado.json'

with open(JSON_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ---------- Extraer roles recursivo ----------
roles = {}
def walk(node):
    if not isinstance(node, dict):
        return
    r = node.get('rol')
    if isinstance(r, str) and r:
        est = node.get('estatus', {}) or {}
        roles.setdefault(r, est.get('nombre'))
    cand = []
    rr = node.get('rol')
    if isinstance(rr, dict):
        cand.append(rr)
    cand.extend(node.get('rolesDependientes', []) or [])
    for h in cand:
        walk(h)
for p in data:
    walk(p)
roles_asesor = {r: s for r, s in roles.items() if r.startswith('ASESOR ')}
print(f"Roles 'ASESOR *' en JSON: {len(roles_asesor)}")
for r in sorted(roles_asesor):
    print(f"   {r!r}")

# ---------- data Asesor ----------
df = pd.read_excel(EXCEL, sheet_name='data', dtype={'Asesor': str})
asesores = sorted(df['Asesor'].dropna().str.strip().unique().tolist())
asesores = [a for a in asesores if a != 'CONTACTO DIGITAL']
print(f"\nAsesores en data (excl CONTACTO DIGITAL): {len(asesores)}")
for a in asesores:
    print(f"   {a!r}")

# ---------- Normalización doble ----------
ESTADOS_MX = {
    'AGUASCALIENTES','BAJA CALIFORNIA','BAJA CALIFORNIA SUR','CAMPECHE','CHIAPAS',
    'CHIHUAHUA','COAHUILA','COLIMA','DURANGO','GUANAJUATO','GUERRERO','HIDALGO',
    'JALISCO','MICHOACAN','MORELOS','NAYARIT','NUEVO LEON','OAXACA','PUEBLA',
    'QUERETARO','QUINTANA ROO','SAN LUIS POTOSI','SINALOA','SONORA','TABASCO',
    'TAMAULIPAS','TLAXCALA','VERACRUZ','YUCATAN','ZACATECAS','ESTADO DE MEXICO',
}
# Estados multi-palabra primero (para que el regex las consuma como unidad)
ESTADOS_MX_MULTI = sorted([e for e in ESTADOS_MX if ' ' in e], key=len, reverse=True)
ESTADOS_MX_SIMPLE = [e for e in ESTADOS_MX if ' ' not in e]

ALIAS_CIUDAD = {
    # data (ciudad extraída) -> json (tras quitar prefijo)
    'POZA RICA': 'POZARICA',
    'PUEBLA FORANEAS': 'PUEBLA FOR',
    'TUXTLA FORANEAS': 'TUXTLA FOR',
    'TOLUCA FORANEAS': 'TOLUCA FOR',
    'QUERETARO FORANEAS': 'QUERETARO FOR',
    'MEXICO CENTRO': 'MX CENTRO',
    'MEXICO NORTE': 'MXNTE',
    'MEXICO ORIENTE': 'MXOTE',
    'MEXICO SUR': 'MX SUR',
    'NUEVO LEON': 'NUEVO LEON',  # ciudad == estado, queda igual
    'XALAPA': 'XALAPA',
}

def norm_json(r):
    """ASESOR ACAPULCO -> ACAPULCO"""
    return re.sub(r'^ASESOR\s+', '', r.strip())

def norm_data(a):
    """ACAPULCO GUERRERO -> ACAPULCO (quita sufijo de estado)"""
    a = a.strip()
    # quitar estado multi-palabra primero
    for e in ESTADOS_MX_MULTI:
        if a.endswith(' ' + e):
            ciudad = a[:-(len(e) + 1)]
            return ALIAS_CIUDAD.get(ciudad, ciudad)
    # quitar estado simple
    partes = a.split()
    if len(partes) > 1 and partes[-1] in ESTADOS_MX_SIMPLE:
        ciudad = ' '.join(partes[:-1])
        return ALIAS_CIUDAD.get(ciudad, ciudad)
    return ALIAS_CIUDAD.get(a, a)

json_norm = {r: norm_json(r) for r in roles_asesor}
json_norm_set = set(json_norm.values())
data_norm = {a: norm_data(a) for a in asesores}

print("\n" + "=" * 80)
print("MATCHING CON DOBLE NORMALIZACIÓN")
print("=" * 80)
matched = []
solo_data = []
for a in asesores:
    nd = data_norm[a]
    if nd in json_norm_set:
        matched.append((a, nd))
    else:
        solo_data.append((a, nd))

print(f"MATCHEAN: {len(matched)}/{len(asesores)}")
print(f"NO MATCHEAN: {len(solo_data)}/{len(asesores)}")

print("\n--- MATCHES (data -> json) ---")
for a, nd in sorted(matched):
    print(f"   {a!r}  ->  {nd!r}")

print("\n--- NO MATCHES (data -> ciudad extraída, comparado con json disponible) ---")
for a, nd in sorted(solo_data):
    print(f"   {a!r}  ->  {nd!r}")
    print(f"        JSON similares: {[v for v in sorted(json_norm_set) if v[:4] == nd[:4] or nd[:4] in v]}")

print("\n--- ROLES JSON sin correspondencia en data ---")
for jn in sorted(json_norm_set - set(data_norm.values())):
    print(f"   {jn!r}")