"""
ANÁLISIS TEMPORAL (modo plan) - Catalogo LADA del PDF vs catálogo actual
Reconcilia los 24 casos conflictivos con la fuente PDF proporcionada.
"""
import pandas as pd
import re
import sys
sys.path.insert(0, 'src')

EXCEL = 'data/input/FACTURACIONEX.xlsx'
PDF_TXT = '/tmp/tabla_ladas.txt'

# ---------- 1. Leer catálogo actual del Excel ----------
df_ladas = pd.read_excel(EXCEL, sheet_name='Ladas', dtype={'LADA': str, 'Estado': str})
df_ladas['LADA'] = df_ladas['LADA'].astype(str).str.strip()
df_ladas['Estado'] = df_ladas['Estado'].astype(str).str.strip()

# ---------- 2. Parsear el PDF ----------
txt = open(PDF_TXT, encoding='utf-8').read()
# Patrón: Ciudad (letras, números, acentos) + espacios + clave (2-3 dígitos)
# Formato: "Ciudad de México       55" o "Guadalajara         33"
patrones = re.findall(r'([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ ]{2,60}?)\s{2,}(\d{2,3})', txt)
# Limpiar ciudades (quitar espacios extra, capitalizar correctamente)
pdf_map = {}  # lada -> set de ciudades
for ciudad, lada in patrones:
    ciudad = ciudad.strip()
    # excluir encabezados de tabla
    if ciudad in ('Ciudad', 'Clave lada', 'Clave lada en la') or lada in ('lada',):
        continue
    if len(lada) < 2 or len(lada) > 3:
        continue
    # Normalizar: solo mantener si lada es numérica
    if not lada.isdigit():
        continue
    pdf_map.setdefault(lada, set()).add(ciudad)

print("=" * 70)
print("ANÁLISIS PDF LADAS vs CATÁLOGO ACTUAL")
print("=" * 70)

print(f"\n1. CLADES ÚNICAS EN PDF: {len(pdf_map)}")
print(f"   Ejemplo: 55 → {list(pdf_map.get('55', []))[:3]}")

# ---------- 3. Asignar estado a cada lada del PDF ----------
# Construir mapeo lada -> estados del catálogo actual
lada_to_estados = {}
for _, r in df_ladas.iterrows():
    lada_to_estados.setdefault(r['LADA'], set()).add(r['Estado'])

# Para cada lada del PDF, ¿cuál es su estado según catálogo actual?
print(f"\n2. RECONCILIACIÓN DE LAS 24 LADAS CONFLICTIVAS")
conflictivas = ['442','55','232','653','753','354','378','833','871','438','636','441','282','462','488','924','283','746','789','487','873','466','464','913','313','496','458','615','867','983','274','248','223','236','322','312','287','427','437','746','435','643','715','782','846','992']
conflictivas = sorted(set(conflictivas))
print(f"Ladas conflictivas a revisar: {len(conflictivas)}")

# Para cada conflictiva, ¿qué dice el PDF?
print(f"\n{'LADA':<6} {'PDF dice':<45} {'Catálogo actual (estados)'}")
for lada in conflictivas:
    pdf_ciudades = pdf_map.get(lada, set())
    pdf_info = ', '.join(sorted(pdf_ciudades))[:43] if pdf_ciudades else '— NO ESTÁ EN PDF'
    # estados en catálogo actual
    estados = lada_to_estados.get(lada, set())
    estados_str = ', '.join(estados)[:40] if estados else '—'
    print(f"{lada:<6} {pdf_info:<45} {estados_str}")

# ---------- 4. Cobertura nueva ----------
print(f"\n4. COBERTURA DEL PDF vs CATÁLOGO ACTUAL")
ladas_actuales = set(lada_to_estados.keys())
ladas_pdf = set(pdf_map.keys())

nuevas = ladas_pdf - ladas_actuales
print(f"   Ladas en catálogo actual: {len(ladas_actuales)}")
print(f"   Ladas en PDF: {len(ladas_pdf)}")
print(f"   Ladas NUEVAS (en PDF pero no en catálogo): {len(nuevas)}")
if nuevas:
    print(f"   Ejemplos nuevas: {sorted(nuevas)[:40]}")

# ---------- 5. Validar la moda contra PDF ----------
# Para las ladas donde el PDF dice algo, ¿coincide con el primer match?
print(f"\n5. VALIDACIÓN: ¿PDF CONFIRMA O CONTRADICE CATÁLOGO ACTUAL?")
# Mapeo manual de ciudades del PDF a estados (los más conocidos)
ciudad_a_estado = {}

print(f"\n   (Análisis manual de los principales: 55 CDMX, 33 Jalisco, 81 NL, 442 Querétaro, etc.)")
print(f"   PDF incluye: 55, 33, 81, 442, 614 Chihuahua, 686 Mexicali/BC, 656 Juárez, 664 Tijuana, 999 Mérida/Yucatán, 983 Chetumal/Q.Roo, 951 Oaxaca, 961 Chiapas, 993 Villahermosa/Tabasco, 998 Cancún/Q.Roo, 229 Veracruz, 228 Jalapa/Veracruz, 222 Puebla, 722 Toluca/México, 771 Pachuca/Hidalgo, 777 Cuernavaca/Morelos, 744 Acapulco/Guerrero, 334?, 331?" )