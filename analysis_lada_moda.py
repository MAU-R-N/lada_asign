"""
ANÁLISIS TEMPORAL (modo plan) - Validar hipótesis de la moda en catálogo de ladas
No modifica nada, solo analiza.
"""
import pandas as pd
from collections import Counter

EXCEL = 'data/input/FACTURACIONEX.xlsx'

print("=" * 70)
print("ANÁLISIS: CONFLICTO DE LADAS Y VALIDACIÓN DE MODA vs GROUND TRUTH")
print("=" * 70)

# ---------- 1. Cargar catálogo de ladas ----------
df_ladas = pd.read_excel(EXCEL, sheet_name='Ladas', dtype={'LADA': str, 'Estado': str})
df_ladas['LADA'] = df_ladas['LADA'].astype(str).str.strip()
df_ladas['Estado'] = df_ladas['Estado'].astype(str).str.strip()

# Quitar filas sin lada o estado
df_ladas_valid = df_ladas[df_ladas['LADA'].notna() & df_ladas['LADA'].astype(str).str.isdigit() & df_ladas['Estado'].notna() & (df_ladas['Estado'] != 'nan')].copy()
df_ladas_valid['LADA'] = df_ladas_valid['LADA'].str.zfill(3) if False else df_ladas_valid['LADA']

print(f"\n1. CATÁLOGO LADAS")
print(f"   Total filas: {len(df_ladas)}")
print(f"   Filas válidas (lada+estado): {len(df_ladas_valid)}")
print(f"   Ladas únicas: {df_ladas_valid['LADA'].nunique()}")

# ---------- 2. Conflictos por lada ----------
# Agrupar: para cada lada, cuántos estados distintos
grupos = df_ladas_valid.groupby('LADA')['Estado'].agg(
    n_filas='count',
    n_estados_distintos='nunique',
    estados=lambda x: list(x.value_counts().items())[:5]  # top 5 estados con conteo
).reset_index()

con_flia_duplicada = grupos[grupos['n_estados_distintos'] == 1]
con_conflicto = grupos[grupos['n_estados_distintos'] > 1]

print(f"\n2. CONFLICTOS EN CATÁLOGO")
print(f"   Ladas sin conflicto (1 solo estado, solo filas duplicadas): {len(con_flia_duplicada)} ({100*len(con_flia_duplicada)/len(grupos):.1f}%)")
print(f"   Ladas CON conflicto real (2+ estados distintos): {len(con_conflicto)} ({100*len(con_conflicto)/len(grupos):.1f}%)")

print(f"\n   --- Top 15 ladas con conflicto ---")
print(f"   {'LADA':<8} {'#filas':<7} {'#estados':<9} {'Estados (frecuencia)'}")
for _, r in con_conflicto.sort_values('n_estados_distintos', ascending=False).head(15).iterrows():
    estados_str = ', '.join([f"{e}({c})" for e, c in r['estados']])
    print(f"   {r['LADA']:<8} {r['n_filas']:<7} {r['n_estados_distintos']:<9} {estados_str}")

# ---------- 3. Construir mapeo por MODA y por PRIMER MATCH ----------
def build_mapa(df, metodo='moda'):
    mapa = {}
    for lada, g in df.groupby('LADA'):
        if metodo == 'moda':
            # Estado más frecuente (moda); si empate, el primero en orden de aparición
            counts = g['Estado'].value_counts()
            mapa[lada] = counts.index[0]
        else:
            # Primer match (comportamiento actual)
            mapa[lada] = g['Estado'].iloc[0]
    return mapa

mapa_moda = build_mapa(df_ladas_valid, 'moda')
mapa_primer = build_mapa(df_ladas_valid, 'primer')

# Verificar cuántas ladas cambian de estado entre moda y primer match
cambios = {k: (mapa_primer[k], mapa_moda[k]) for k in mapa_moda if mapa_primer[k] != mapa_moda[k]}
print(f"\n3. MAPEO MODA vs PRIMER MATCH")
print(f"   Ladas donde moda y primer match coinciden: {len(mapa_moda) - len(cambios)}/{len(mapa_moda)}")
print(f"   Ladas donde moda CAMBIA el estado: {len(cambios)}")

if cambios:
    print(f"\n   --- Cambios de estado (primer_match → moda) ---")
    for lada, (antes, despues) in list(cambios.items())[:20]:
        # contexto: cuántas filas tenía cada estado
        sub = df_ladas_valid[df_ladas_valid['LADA'] == lada]
        ctx = ', '.join([f"{e}({c})" for e, c in sub['Estado'].value_counts().items()])
        print(f"   Lada {lada:<6}: {antes} → {despues}   [catálogo: {ctx}]")

# ---------- 4. Validar contra ground truth (filas CONTACTO DIGITAL con LADA precalculada) ----------
print(f"\n4. VALIDACIÓN CONTRA GROUND TRUTH (data precalculada)")

df_data = pd.read_excel(EXCEL, sheet_name='data', dtype={
    'Asesor': str, 'Contactos': str, 'LADA': str, 'ESTADO': str, 'PLAZA': str
})
df_data['LADA'] = df_data['LADA'].astype(str).str.strip()
df_data['ESTADO'] = df_data['ESTADO'].astype(str).str.strip()

# Filtrar CONTACTO DIGITAL con LADA y ESTADO precalculados
mask_cd = df_data['Asesor'] == 'CONTACTO DIGITAL '
cd = df_data[mask_cd].copy()
cd_gt = cd[cd['LADA'].notna() & (cd['LADA'] != 'nan') & cd['ESTADO'].notna() & (cd['ESTADO'] != 'nan')].copy()

print(f"   CONTACTO DIGITAL total: {len(cd)}")
print(f"   Con LADA+ESTADO precalculados (ground truth): {len(cd_gt)}")

# Función para evaluar coincidencia de ESTADO
def evaluar_estado(filas, mapa, nombre):
    correctos = 0
    total = 0
    for _, row in filas.iterrows():
        lada = row['LADA']
        estado_gt = row['ESTADO']
        # Normalizar ESTADO del catálogo: el catálogo puede tener "Morelia, Mich" vs "MORELIA MICH"
        estado_pred = mapa.get(lada)
        if estado_pred is None:
            continue
        total += 1
        if estado_pred == estado_gt:
            correctos += 1
    pct = 100 * correctos / total if total else 0
    print(f"   {nombre:<28}: {correctos}/{total} ({pct:.1f}%)")
    return pct

# Evaluar por LADA primero, luego por ESTADO
def evaluar_lada(filas, mapa, nombre):
    """Coincidencia de lada ENCONTRADA en catálogo (como el pipeline actual)"""
    correctos = 0
    total = 0
    for _, row in filas.iterrows():
        lada = row['LADA']
        if lada in mapa:
            total += 1
            correctos += 1  # la lada existe en el catálogo
        else:
            total += 1
    pct = 100 * correctos / total if total else 0
    print(f"   {nombre:<28}: {correctos}/{total} ({pct:.1f}%)")
    return pct

# Nota: el pipeline actual compara LADA_calculada == LADA_precalculada.
# Para la moda el criterio equivalente es: ¿la moda de esa lada da el mismo estado que ESTADO precalculado?
print(f"\n   --- Coincidencia de ESTADO predicho vs ESTADO ground truth ---")
pct_primer = evaluar_estado(cd_gt, mapa_primer, "Primer match (actual)")
pct_moda = evaluar_estado(cd_gt, mapa_moda, "Moda (propuesto)")

# También: coincidencia de LADA (como reporta el pipeline actual)
print(f"\n   --- Coincidencia de LADA (criterio actual del pipeline) ---")
# El pipeline actual: lada_calculada (del teléfono) vs LADA precalculada
# Para CD donde el teléfono se extrae, la lada del teléfono debe matchear la LADA precalculada
from src.phone_extractor import PhoneExtractor
extractor = PhoneExtractor()
def lada_del_telefono(contactos):
    phone = extractor.extract_phone(contactos)
    if not phone:
        return None
    l2, l3 = extractor.extract_lada(phone)
    return l3  # la lada más específica encontrada se resuelve en el matcher

def evaluar_coincidencia_lada(filas, mapa, nombre):
    """Coincidencia: lada del teléfono que existe en catálogo Y matchea a estado precalculado"""
    correctos_lada = 0
    correctos_estado = 0
    total = 0
    for _, row in filas.iterrows():
        contactos = row['Contactos']
        phone = extractor.extract_phone(contactos)
        if not phone:
            continue
        l2, l3 = extractor.extract_lada(phone)
        # resolver lada como el pipeline: probar 2, luego 3
        lada_efectiva = None
        if l2 in mapa:
            lada_efectiva = l2
        elif l3 in mapa:
            lada_efectiva = l3
        
        if lada_efectiva is None:
            continue
        total += 1
        if lada_efectiva == row['LADA']:
            correctos_lada += 1
        if mapa.get(lada_efectiva) == row['ESTADO']:
            correctos_estado += 1
    pct_l = 100*correctos_lada/total if total else 0
    pct_e = 100*correctos_estado/total if total else 0
    print(f"   {nombre:<28}: LADA {correctos_lada}/{total} ({pct_l:.1f}%) | ESTADO {correctos_estado}/{total} ({pct_e:.1f}%)")
    return pct_l, pct_e

print(f"\n   --- Replicación exacta del pipeline: teléfono→lada→estado vs ground truth ---")
_ = evaluar_coincidencia_lada(cd_gt, mapa_primer, "Primer match (actual)")
_ = evaluar_coincidencia_lada(cd_gt, mapa_moda, "Moda (propuesto)")

# ---------- 5. Casos donde la MODA falla vs ground truth ----------
print(f"\n5. CASOS DONDE LA MODA FALLA vs GROUND TRUTH")
fallos_moda = []
for _, row in cd_gt.iterrows():
    lada = row['LADA']
    estado_gt = row['ESTADO']
    if lada in mapa_moda and mapa_moda[lada] != estado_gt:
        fallos_moda.append({
            'LADA': lada,
            'ESTADO_GT': estado_gt,
            'MODA': mapa_moda[lada],
            'PRIMER': mapa_primer.get(lada),
            # contexto catálogo
            'catálogo': dict(df_ladas_valid[df_ladas_valid['LADA']==lada]['Estado'].value_counts().items())
        })

print(f"   Filas ground truth donde la moda NO coincide con ESTADO precalculado: {len(fallos_moda)}")
print(f"   Ladas involucradas: {len(set(f['LADA'] for f in fallos_moda))}")

from collections import defaultdict
por_lada = defaultdict(lambda: {'gt_estados': Counter(), 'n': 0})
for f in fallos_moda:
    por_lada[f['LADA']]['gt_estados'][f['ESTADO_GT']] += 1
    por_lada[f['LADA']]['n'] += 1

print(f"\n   --- Detalle por lada problemática ---")
for lada, info in sorted(por_lada.items(), key=lambda x: -x[1]['n'])[:30]:
    cat = ', '.join([f"{e}({c})" for e, c in df_ladas_valid[df_ladas_valid['LADA']==lada]['Estado'].value_counts().items()])
    gt = ', '.join([f"{e}({c})" for e, c in info['gt_estados'].items()])
    moda = mapa_moda.get(lada)
    print(f"   Lada {lada:<6}: MODA={moda} | GT esperado={gt} | catálogo=[{cat}]")

# Resumen impacto en % de coincidencia LADA del pipeline
print(f"\n6. RESUMEN ANTES/DESPUÉS")
print(f"   Coincidencia ESTADO con primer match: {pct_primer:.1f}%")
print(f"   Coincidencia ESTADO con moda:         {pct_moda:.1f}%")
print(f"   (porcentajes sobre {len(cd_gt)} filas ground truth)")