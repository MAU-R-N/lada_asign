"""
ANÁLISIS TEMPORAL FINAL (modo plan) - Tabla de 24 casos conflictivos
Reconcilia: lada → estados en conflicto (catálogo actual) → qué dice el PDF → 
plaza activa de Farmacias por estado → recomendación PROPUESTA (no aplicada).
"""
import pandas as pd
import re

EXCEL = 'data/input/FACTURACIONEX.xlsx'

# ---------- 1. Cargar datos ----------
df_ladas = pd.read_excel(EXCEL, sheet_name='Ladas', dtype={'LADA': str, 'Estado': str, 'PLAZAS': str})
df_ladas['LADA'] = df_ladas['LADA'].astype(str).str.strip()
df_ladas['Estado'] = df_ladas['Estado'].astype(str).str.strip()

df_data = pd.read_excel(EXCEL, sheet_name='data', dtype={
    'Asesor': str, 'LADA': str, 'ESTADO': str, 'PLAZA': str
})
df_data['LADA'] = df_data['LADA'].astype(str).str.strip()
df_data['ESTADO'] = df_data['ESTADO'].astype(str).str.strip()
cd = df_data[df_data['Asesor'] == 'CONTACTO DIGITAL '].copy()

# ---------- 2. Parsear PDF ----------
txt = open('/tmp/tabla_ladas.txt', encoding='utf-8').read()
patrones = re.findall(r'([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ ]{2,60}?)\s{2,}(\d{2,3})', txt)
pdf_map = {}
for ciudad, lada in patrones:
    ciudad = ciudad.strip()
    if ciudad in ('Ciudad', 'Clave lada', 'Clave lada en la') or not lada.isdigit():
        continue
    pdf_map.setdefault(lada, set()).add(ciudad)

# ---------- 3. Ladas conflictivas (con más de un estado en catálogo) ----------
grupos = df_ladas.groupby('LADA')['Estado'].agg(
    n_filas='count',
    n_estados='nunique',
    estados=lambda x: list(dict(x.value_counts()).items())
).reset_index()
conflictivas = grupos[grupos['n_estados'] > 1].sort_values('n_filas', ascending=False)

# ---------- 4. Plazas activas del mes (columna PLAZAS del catálogo) ----------
plazas_activas = df_ladas['PLAZAS'].dropna().astype(str).str.strip()
plazas_activas = plazas_activas[plazas_activas != 'nan'].unique()
print(f"Plazas activas encontradas en columna PLAZAS: {len(plazas_activas)}")

# ---------- 5. Mapeo estado → plaza (config) ----------
estado_plaza = {
    "Aguascalientes": "AGUASCALIENTES AGUASCALIENTES ",
    "Baja California": "BAJA CALIFORNIA SUR BAJA CALIFORNIA SUR ",
    "Baja California Sur": "BAJA CALIFORNIA SUR BAJA CALIFORNIA SUR ",
    "B.C.S": "BAJA CALIFORNIA SUR BAJA CALIFORNIA SUR ",
    "Chiapas": "TAPACHULA CHIAPAS ",
    "Chihuahua": "CHIHUAHUA CHIHUAHUA ",
    "Chih": "CHIHUAHUA CHIHUAHUA ",
    "Coahuila": "SALTILLO COAHUILA ",
    "Durango": "DURANGO DURANGO ",
    "Estado de Mexico": "MEXICO CENTRO ESTADO DE MEXICO ",
    "Mex": "MEXICO CENTRO ESTADO DE MEXICO ",  # CORREGIDO: antes decía MEXICALI
    "GUANAJUATO": "CELAYA GUANAJUATO ",
    "Guerrero": "ACAPULCO GUERRERO ",
    "Hidalgo": "PACHUCA HIDALGO ",
    "Jalisco": "GUADALAJARA JALISCO ",
    "Jal": "GUADALAJARA JALISCO ",
    "Leon Guanajuato": "LEON GUANAJUATO ",
    "MERIDA YUCATAN": "MERIDA YUCATAN ",
    "MEXICO CENTRO": "MEXICO CENTRO ESTADO DE MEXICO ",
    "MORELIA MICH": "MORELIA MICHOACAN ",
    "MICHOACAN": "MORELIA MICHOACAN ",
    "Morelos": "CUAUTLA MORELOS ",
    "NUEVO LEON": "MONTERREY ORIENTE NUEVO LEON ",
    "Nayarit": "TEPIC NAYARIT ",
    "Oaxaca": "OAXACA OAXACA ",
    "Puebla": "PUEBLA FORANEAS PUEBLA FORANEAS ",
    "Puebla foraneas": "PUEBLA FORANEAS PUEBLA FORANEAS ",
    "QUERETARO": "QUERETARO QUERETARO ",
    "Quintana Roo": "CANCUN QUINTANA ROO ",
    "Q. Roo": "CANCUN QUINTANA ROO ",
    "San Luis Potosi": "SAN LUIS POTOSI SAN LUIS POTOSI ",
    "SAN LUIS POTOSI SAN LUIS POTOSI": "SAN LUIS POTOSI SAN LUIS POTOSI ",
    "Sinaloa": "CULIACAN SINALOA ",
    "Sonora": "HERMOSILLO SONORA ",
    "Tabasco": "TABASCO TABASCO ",
    "Tamaulipas": "MATAMOROS TAMAULIPAS ",
    "Tamps": "MATAMOROS TAMAULIPAS ",
    "Veracruz": "COATZACOALCOS VERACRUZ ",
    "Yucatan": "MERIDA YUCATAN ",
    "Zacatecas": "ZACATECAS ZACATECAS ",
    "zac.": "ZACATECAS ZACATECAS ",
}

# Conteo de ground truth: para cada lada, qué ESTADO usó Ariadne en data
gt_conteo = cd.groupby(['LADA', 'ESTADO']).size().reset_index(name='n_gt')

# ---------- 6. Construir tabla final ----------
print("=" * 120)
print("TABLA DE 24 LADAS CONFLICTIVAS — PROPUESTA PARA REVISIÓN (SIN APLICAR)")
print("=" * 120)

for _, r in conflictivas.iterrows():
    lada = r['LADA']
    estados_cat = [e for e, c in r['estados']]
    
    # Estado más usado por Ariadne en ground truth
    gt_lada = gt_conteo[gt_conteo['LADA'] == lada].sort_values('n_gt', ascending=False)
    gt_info = "; ".join([f"{e} ({int(n)})" for e, n in zip(gt_lada['ESTADO'], gt_lada['n_gt'])]) if len(gt_lada) else "sin datos GT"
    
    # Qué dice el PDF (si aplica)
    pdf_ciudades = pdf_map.get(lada, set())
    pdf_info = ", ".join(sorted(pdf_ciudades)) if pdf_ciudades else "—"
    
    print(f"\nLADA {lada}")
    print(f"  Estados en catálogo: {', '.join(estados_cat)}")
    print(f"  GROUND TRUTH (Ariadne): {gt_info}")
    print(f"  PDF dice (ciudades): {pdf_info}")

print("\n\n" + "=" * 120)
print("ANÁLISIS DE COBERTURA PDF vs CATÁLOGO")
print("=" * 120)
ladas_actuales = set(grupos['LADA'])
ladas_pdf = set(pdf_map.keys())
nuevas = ladas_pdf - ladas_actuales
print(f"Ladas en catálogo actual: {len(ladas_actuales)}")
print(f"Ladas en PDF: {len(ladas_pdf)}")
print(f"Ladas del PDF NO cubiertas por catálogo: {len(nuevas)}")
print(f"  → {sorted(nuevas)}")