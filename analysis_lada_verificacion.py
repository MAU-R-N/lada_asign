"""
ANÁLISIS TEMPORAL 3 (modo plan) - Verificación final de causa raíz
1. ¿Están las ladas 3d específicas (331,332,333,334,686,614,553...) en el catálogo?
2. Textos completos de los ~17 casos no resolubles
3. Recalcular % coincidencia si resolvemos por ESTADO (no por LADA textual)
"""
import pandas as pd
import sys
sys.path.insert(0, 'src')
from phone_extractor import PhoneExtractor

EXCEL = 'data/input/FACTURACIONEX.xlsx'

df_ladas = pd.read_excel(EXCEL, sheet_name='Ladas', dtype={'LADA': str, 'Estado': str})
df_ladas['LADA'] = df_ladas['LADA'].astype(str).str.strip()
df_ladas['Estado'] = df_ladas['Estado'].astype(str).str.strip()

df_data = pd.read_excel(EXCEL, sheet_name='data', dtype={
    'Asesor': str, 'Contactos': str, 'LADA': str, 'ESTADO': str, 'PLAZA': str
})
df_data['LADA'] = df_data['LADA'].astype(str).str.strip()
df_data['ESTADO'] = df_data['ESTADO'].astype(str).str.strip()

ladas_catalogo = set(df_ladas['LADA'].unique())
ladas_2d = {l for l in ladas_catalogo if len(l) == 2}
ladas_3d = {l for l in ladas_catalogo if len(l) == 3}

print("=" * 70)
print("VERIFICACIÓN 3: ¿LAS LADAS 3d DE ARIADNE ESTÁN EN EL CATÁLOGO?")
print("=" * 70)

# 1. Ladas precalculadas únicas en data (CD)
cd = df_data[df_data['Asesor'] == 'CONTACTO DIGITAL '].copy()
ladas_precalc_unicas = sorted(cd['LADA'].dropna().astype(str).unique())

# Separar: cuáles existen en catálogo, cuáles no
en_catalogo = [l for l in ladas_precalc_unicas if l in ladas_catalogo]
no_en_catalogo = [l for l in ladas_precalc_unicas if l not in ladas_catalogo]

print(f"\n1. LADAS PRECALCULADAS ÚNICAS EN DATA (CD): {len(ladas_precalc_unicas)}")
print(f"   En catálogo Ladas: {len(en_catalogo)}")
print(f"   NO en catálogo: {len(no_en_catalogo)}")

print(f"\n   --- Ladas precalc que NO están en el catálogo ({len(no_en_catalogo)}) ---")
print(no_en_catalogo)

# 2. Verificar ladas específicas del ejemplo
print(f"\n2. ¿EXISTEN EN CATÁLOGO LAS LADAS 3d DEL EJEMPLO?")
for lada in ['331','332','333','334','686','614','553','911','973','351']:
    en_cat = lada in ladas_catalogo
    # buscar si existe alguna lada similar
    if not en_cat:
        sub = df_ladas[df_ladas['LADA'].str.startswith(lada[:2])]
        estados = sub['Estado'].unique().tolist()
        print(f"   Lada {lada}: {'✓ EN CATÁLOGO' if en_cat else '✗ NO está'} (similares {lada[:2]}*: {estados})")
    else:
        estados = df_ladas[df_ladas['LADA']==lada]['Estado'].unique().tolist()
        print(f"   Lada {lada}: ✓ EN CATÁLOGO → {estados}")

# 3. Cuántas filas CD tienen lada precalc que NO está en el catálogo
cd_no_cat = cd[~cd['LADA'].isin(ladas_catalogo)]
print(f"\n3. FILAS CD con lada precalc NO en catálogo: {len(cd_no_cat)} de {len(cd)} ({100*len(cd_no_cat)/len(cd):.1f}%)")

# 4. Para esas filas, ¿el ESTADO precalculado está en el estado que da la lada 2d?
extractor = PhoneExtractor()
print(f"\n4. PARA FILAS CON LADA PRECALC FUERA DE CATÁLOGO:")
print(f"   ¿Qué estado precalculó Ariadne vs qué estado daría la lada 2d del teléfono?")

def lada_2d_de_telefono(contactos):
    phone = extractor.extract_phone(contactos)
    if not phone:
        return None, None
    l2, l3 = extractor.extract_lada(phone)
    return l2, l3

# Mapeo lada -> estados
lada_to_estados = {}
for _, r in df_ladas.iterrows():
    lada_to_estados.setdefault(r['LADA'], set()).add(r['Estado'])

conteo_mismo_estado = 0
conteo_diff = 0
conteo_sin_tel = 0
for _, row in cd_no_cat.iterrows():
    l2, l3 = lada_2d_de_telefono(row['Contactos'])
    estado_gt = row['ESTADO']
    # estado de la lada 2d si existe
    if l2 and l2 in lada_to_estados:
        estados_2d = lada_to_estados[l2]
        # normalizar comparación: ver si algún estado 2d coincide parcialmente
        match = any(estado_gt in e or e in estado_gt for e in estados_2d)
        if match:
            conteo_mismo_estado += 1
        else:
            conteo_diff += 1
    else:
        conteo_sin_tel += 1

print(f"   - Estado precalc coincide (por substring) con estado de lada 2d: {conteo_mismo_estado}")
print(f"   - Estado precalc NO coincide: {conteo_diff}")
print(f"   - Sin teléfono extraíble: {conteo_sin_tel}")

# Mostrar ejemplos de los no coincidentes
print(f"\n   --- Ejemplos donde la lada precalc NO está en catálogo y estado difiere ---")
count = 0
for _, row in cd_no_cat.iterrows():
    l2, l3 = lada_2d_de_telefono(row['Contactos'])
    if not l2:
        continue
    estado_gt = row['ESTADO']
    if l2 not in lada_to_estados:
        continue
    estados_2d = lada_to_estados[l2]
    match = any(estado_gt in e or e in estado_gt for e in estados_2d)
    if not match:
        print(f"   ** LADA precalc={row['LADA']} ESTADO={estado_gt} | tel 2d={l2} estados_2d={list(estados_2d)}")
        print(f"      Contacto: {row['Contactos'][:130]}")
        count += 1
        if count >= 10:
            break

# 5. CONCLUSIÓN: impacto real en ESTADO
print(f"\n5. COINCIDENCIA REAL DE ESTADO (lo que importa para facturación):")
print(f"   El pipeline actual reporta ESTADO 2394/2409 = 99.4%")
print(f"   ~15 casos restantes (0.6%) son ladas precalc fuera de catálogo con estado distinto")