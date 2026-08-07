"""
ANÁLISIS TEMPORAL 2 (modo plan) - Causa raíz REAL del 68.6% coincidencia LADA
La coincidencia de LADA no cambia con moda vs primer match → el problema está en
la extracción teléfono→lada, no en la selección de estado.
Este script analiza QUÉ tipo de discrepancia tienen las filas que fallan.
"""
import pandas as pd
from collections import Counter

EXCEL = 'data/input/FACTURACIONEX.xlsx'
import sys
sys.path.insert(0, 'src')
from phone_extractor import PhoneExtractor

print("=" * 70)
print("ANÁLISIS 2: ¿POR QUÉ LA COINCIDENCIA DE LADA ES SOLO 69.7%?")
print("=" * 70)

# ---------- 1. Cargar datos ----------
df_ladas = pd.read_excel(EXCEL, sheet_name='Ladas', dtype={'LADA': str, 'Estado': str})
df_ladas['LADA'] = df_ladas['LADA'].astype(str).str.strip()
df_ladas['Estado'] = df_ladas['Estado'].astype(str).str.strip()

df_data = pd.read_excel(EXCEL, sheet_name='data', dtype={
    'Asesor': str, 'Contactos': str, 'LADA': str, 'ESTADO': str, 'PLAZA': str
})
df_data['LADA'] = df_data['LADA'].astype(str).str.strip()
df_data['ESTADO'] = df_data['ESTADO'].astype(str).str.strip()

mask_cd = df_data['Asesor'] == 'CONTACTO DIGITAL '
cd = df_data[mask_cd].copy()

# Catálogo de ladas (todas las ladas válidas del catálogo, 2 y 3 dígitos)
ladas_catalogo = set(df_ladas['LADA'].unique())
ladas_2d = {l for l in ladas_catalogo if len(l) == 2}
ladas_3d = {l for l in ladas_catalogo if len(l) == 3}

print(f"Ladas en catálogo: {len(ladas_catalogo)} (2d: {len(ladas_2d)}, 3d: {len(ladas_3d)})")
print(f"CONTACTO DIGITAL: {len(cd)}")

# ---------- 2. Replicar pipeline: extraer teléfono → lada efectiva ----------
extractor = PhoneExtractor()

def resolve_lada_efectiva(contactos):
    """Replica la lógica del pipeline: extraer teléfono, probar lada 2d, luego 3d"""
    phone = extractor.extract_phone(contactos)
    if not phone:
        return None, None
    l2, l3 = extractor.extract_lada(phone)
    if l2 in ladas_2d or l2 in ladas_3d:
        return phone, l2
    elif l3 in ladas_catalogo:
        return phone, l3
    return phone, None

resultados = []
for _, row in cd.iterrows():
    contactos = row['Contactos']
    lada_precalc = row['LADA'] if pd.notna(row['LADA']) and row['LADA'] != 'nan' else None
    
    phone, lada_efectiva = resolve_lada_efectiva(contactos)
    
    if lada_efectiva is None:
        resultados.append({'tipo': 'sin_lada_catalogo', 'contactos': contactos, 'phone': phone, 
                          'lada_precalc': lada_precalc, 'lada_efectiva': lada_efectiva})
        continue
    
    if lada_precalc and lada_efectiva == lada_precalc:
        resultados.append({'tipo': 'COINCIDE', 'contactos': contactos, 'phone': phone,
                          'lada_precalc': lada_precalc, 'lada_efectiva': lada_efectiva})
    elif not lada_precalc:
        resultados.append({'tipo': 'sin_precalc', 'contactos': contactos, 'phone': phone,
                          'lada_precalc': lada_precalc, 'lada_efectiva': lada_efectiva})
    else:
        resultados.append({'tipo': 'DISCREPA', 'contactos': contactos, 'phone': phone,
                          'lada_precalc': lada_precalc, 'lada_efectiva': lada_efectiva})

df_res = pd.DataFrame(resultados)
print(f"\nDistribución de resultados:")
print(df_res['tipo'].value_counts().to_string())

# ---------- 3. Analizar las DISCREPANCIAS ----------
disc = df_res[df_res['tipo'] == 'DISCREPA'].copy()
print(f"\n3. ANÁLISIS DE DISCREPANCIAS ({len(disc)} filas)")
print(f"   Lada efectiva (del teléfono) vs LADA precalculada:")

# Tipos de discrepancia
disc['calc_len'] = disc['lada_efectiva'].str.len()
disc['precalc_len'] = disc['lada_precalc'].str.len()
disc['misma_lada_3d'] = disc['lada_efectiva'].str[:3] == disc['lada_precalc'].str[:3]
disc['misma_lada_2d'] = disc['lada_efectiva'].str[:2] == disc['lada_precalc'].str[:2]

print(f"   - Ambas 2 dígitos pero diferentes: {((disc['calc_len']==2)&(disc['precalc_len']==2)&(~disc['misma_lada_2d'])).sum()}")
print(f"   - Ambas 3 dígitos pero diferentes: {((disc['calc_len']==3)&(disc['precalc_len']==3)&(~disc['misma_lada_3d'])).sum()}")
print(f"   - Calculada 2d, precalculada 3d: {((disc['calc_len']==2)&(disc['precalc_len']==3)).sum()}")
print(f"   - Calculada 3d, precalculada 2d: {((disc['calc_len']==3)&(disc['precalc_len']==2)).sum()}")
print(f"   - Comparten primeros 3 dígitos (solo difieren formato): {disc['misma_lada_3d'].sum()}")

# Ejemplos de discrepancia: misma zona pero formato distinto (2 vs 3 dígitos)
print(f"\n   --- Ejemplos: calculada 2d vs precalculada 3d (formato largo) ---")
subset = disc[(disc['calc_len']==2)&(disc['precalc_len']==3)].head(8)
for _, r in subset.iterrows():
    print(f"   Tel: {r['phone']} → calc: {r['lada_efectiva']} | precalc: {r['lada_precalc']} | {r['contactos'][:80]}")

print(f"\n   --- Ejemplos: calculada 3d vs precalculada 2d (formato corto) ---")
subset = disc[(disc['calc_len']==3)&(disc['precalc_len']==2)].head(8)
for _, r in subset.iterrows():
    print(f"   Tel: {r['phone']} → calc: {r['lada_efectiva']} | precalc: {r['lada_precalc']} | {r['contactos'][:80]}")

print(f"\n   --- Ejemplos: mismas longitud pero ladas realmente diferentes ---")
subset = disc[(disc['calc_len']==disc['precalc_len'])&(~disc['misma_lada_2d'])].head(10)
for _, r in subset.iterrows():
    print(f"   Tel: {r['phone']} → calc: {r['lada_efectiva']} | precalc: {r['lada_precalc']} | {r['contactos'][:80]}")

# ---------- 4. Verificar: si el pipeline usara SIEMPRE lada de 3 dígitos ----------
# La pregunta clave: ¿la LADA precalculada es SIEMPRE la lada de 3 dígitos del teléfono?
print(f"\n4. ¿QUÉ SUCEDERÍA SI SIEMPRE USAMOS LADA DE 3 DÍGITOS (existente en catálogo)?")

def resolve_lada_siempre_3d(contactos):
    phone = extractor.extract_phone(contactos)
    if not phone:
        return None, None
    l2, l3 = extractor.extract_lada(phone)
    if l3 in ladas_catalogo:
        return phone, l3
    elif l2 in ladas_catalogo:
        return phone, l2
    return phone, None

correctos_3d = 0
total_3d = 0
for _, row in cd.iterrows():
    lada_precalc = row['LADA'] if pd.notna(row['LADA']) and row['LADA'] != 'nan' else None
    if not lada_precalc:
        continue
    phone, lada = resolve_lada_siempre_3d(row['Contactos'])
    if lada is None:
        continue
    total_3d += 1
    if lada == lada_precalc:
        correctos_3d += 1

pct_3d = 100 * correctos_3d / total_3d if total_3d else 0
print(f"   Con lada de 3 dígitos primero: {correctos_3d}/{total_3d} ({pct_3d:.1f}%)")

# Comparar: usando exactamente el teléfono como está
print(f"\n5. ¿CUÁNTAS DISCREPANCAS SON POR ORDEN 2d-vs-3d vs OTRAS CAUSAS?")
# Si tomamos la lada precalculada del teléfono directamente:
# el teléfono tiene 10 dígitos. Los primeros 2 = lada corta, primeros 3 = lada larga.
# La LADA precalculada debe ser UNA de esas dos.
resolubles_por_orden = 0
no_resolubles = 0
for _, r in disc.iterrows():
    phone = r['phone']
    if not phone:
        no_resolubles += 1
        continue
    l2, l3 = extractor.extract_lada(phone)
    if l2 == r['lada_precalc'] or l3 == r['lada_precalc']:
        resolubles_por_orden += 1
    else:
        no_resolubles += 1

print(f"   Discrepancias donde la lada precalculada SÍ está en el teléfono (solo problema de orden 2d/3d): {resolubles_por_orden}/{len(disc)} ({100*resolubles_por_orden/len(disc):.1f}%)")
print(f"   Discrepancias donde la lada precalculada NO está en el teléfono extraído: {no_resolubles}/{len(disc)} ({100*no_resolubles/len(disc):.1f}%)")

# Muestra de no resolubles
print(f"\n   --- Ejemplos NO resolubles (lada precalculada no está en el teléfono) ---")
count_nr = 0
for _, r in disc.iterrows():
    phone = r['phone']
    l2, l3 = extractor.extract_lada(phone) if phone else (None, None)
    if l2 != r['lada_precalc'] and l3 != r['lada_precalc']:
        print(f"   Tel: {r['phone']} → calc: {r['lada_efectiva']} | precalc: {r['lada_precalc']}")
        print(f"   Contacto: {r['contactos'][:110]}")
        count_nr += 1
        if count_nr >= 12:
            break

# ---------- 6. Impacto esperado del fix de orden 3d-primero ----------
print(f"\n6. IMPACTO ESPERADO CON FIX (probar 3 dígitos primero, luego 2)")
corregir_formato = 0
for _, r in disc.iterrows():
    phone = r['phone']
    l2, l3 = extractor.extract_lada(phone) if phone else (None, None)
    # si la precalculada es la de 3 dígitos y la efectiva fue la de 2
    if l3 == r['lada_precalc'] and l3 in ladas_catalogo:
        corregir_formato += 1

print(f"   Discrepancias corregibles cambiando el orden (usar 3d primero): {corregir_formato}")
print(f"   Perfecto proyectado: {df_res['tipo'].value_counts().get('COINCIDE',0) + corregir_formato}/{len(df_res) - df_res['tipo'].value_counts().get('sin_precalc',0) - df_res['tipo'].value_counts().get('sin_lada_catalogo',0)}")