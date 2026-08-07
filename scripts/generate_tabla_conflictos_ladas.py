"""
Genera tabla consolidada de ladas conflictivas con propuesta de resolución.
Para revisión antes de aplicar el catálogo limpio.
"""
import pandas as pd
import sys
from pathlib import Path

# Añadir src al path (desde raíz del proyecto)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config import Config
from excel_loader import ExcelLoader
from phone_extractor import PhoneExtractor

# Mapeo manual del PDF (extraído de analysis_lada_pdf.py)
PDF_MAP = {
    "55": "Ciudad de México", "33": "Jalisco", "81": "Nuevo León",
    "442": "Querétaro", "614": "Chihuahua", "686": "Baja California",
    "656": "Chihuahua", "664": "Baja California", "999": "Yucatán",
    "983": "Quintana Roo", "951": "Oaxaca", "961": "Chiapas",
    "993": "Tabasco", "998": "Quintana Roo", "229": "Veracruz",
    "228": "Veracruz", "222": "Puebla", "722": "México",
    "771": "Hidalgo", "777": "Morelos", "744": "Guerrero",
    "871": "Coahuila", "322": "Jalisco", "753": "Guerrero",
    "833": "Tamaulipas", "378": "Jalisco", "232": "Veracruz",
    "287": "Oaxaca", "488": "San Luis Potosí", "487": "San Luis Potosí",
    "462": "Guanajuato", "464": "Guanajuato", "466": "Guanajuato",
    "615": "Baja California Sur", "736": "Guerrero", "757": "Guerrero",
    "427": "Querétaro"
}

def main():
    # Cargar data directamente
    input_path = Path('data/input/FACTURACIONEX.xlsx')
    loader = ExcelLoader(input_path)
    df_data, df_ladas, plazas = loader.load_all()
    
    print("Cargando datos...")
    print(f"  Total filas en data: {len(df_data)}")
    print(f"  Total entradas en catálogo Ladas: {len(df_ladas)}")
    
    # Identificar ladas con conflictos (múltiples estados)
    ladas_cat = df_ladas.groupby('LADA')['Estado'].apply(
        lambda x: sorted(x.dropna().unique())
    ).to_dict()
    conflictos = {k: v for k, v in ladas_cat.items() if len(v) > 1}
    
    print(f"\nLadas conflictivas detectadas: {len(conflictos)}")
    
    # Extraer ladas de los teléfonos en data para contar filas afectadas
    extractor = PhoneExtractor()
    df_data['tel_temp'] = df_data['Contactos'].apply(
        lambda x: extractor.extract_phone(str(x))
    )
    df_data['lada_temp_2'] = df_data['tel_temp'].apply(
        lambda x: x[:2] if pd.notna(x) and len(str(x)) >= 10 else None
    )
    df_data['lada_temp_3'] = df_data['tel_temp'].apply(
        lambda x: x[:3] if pd.notna(x) and len(str(x)) >= 10 else None
    )
    
    # Ground truth de Ariadne (columna ESTADO precalculada en filas CONTACTO DIGITAL)
    mask_cd = df_data['Asesor'] == 'CONTACTO DIGITAL '
    cd_gt = df_data[mask_cd & df_data['ESTADO'].notna()].copy()
    
    print(f"Filas CONTACTO DIGITAL con ESTADO precalculado (GT): {len(cd_gt)}")
    
    # Procesar cada lada conflictiva
    resultados = []
    for lada, estados in sorted(conflictos.items()):
        # Conteo de filas afectadas (cualquier fila con esa lada)
        mask_2 = df_data['lada_temp_2'] == lada
        mask_3 = df_data['lada_temp_3'] == lada
        filas_afectadas = (mask_2 | mask_3).sum()
        
        # Ground truth de Ariadne (qué estado usó Sara/Ariadne para esa lada)
        if 'LADA' in cd_gt.columns:
            cd_lada = cd_gt[cd_gt['LADA'] == lada]
            if len(cd_lada) > 0:
                gt_estados = cd_lada['ESTADO'].value_counts()
                gt_str = f"{gt_estados.index[0]} ({gt_estados.iloc[0]} filas)"
                gt_principal = gt_estados.index[0]
                gt_count = gt_estados.iloc[0]
            else:
                gt_str = "sin datos GT"
                gt_principal = None
                gt_count = 0
        else:
            gt_str = "sin datos GT"
            gt_principal = None
            gt_count = 0
        
        # PDF
        pdf_str = PDF_MAP.get(lada, "—")
        
        # Decidir fuente y estado final según reglas de prioridad
        if lada == "55" and "Mex" in estados:
            # Bug conocido: "Mex" debe ser MEXICO CENTRO
            fuente = "correccion_bug"
            estado_final = "MEXICO CENTRO"
            justificacion = "Bug config: 'Mex' → MEXICO CENTRO (lada 55 es CDMX)"
        elif gt_count >= 2:
            # Ground truth de Ariadne con al menos 2 filas
            fuente = "frecuencia_ariadne"
            estado_final = gt_principal
            justificacion = f"Ariadne usó {gt_principal} en {gt_count} casos"
        elif pdf_str != "—":
            # PDF tiene referencia
            fuente = "PDF"
            estado_final = pdf_str
            justificacion = f"PDF oficial indica {pdf_str}"
        else:
            # Sin información confiable → pendiente revisión manual
            fuente = "pendiente_sara"
            estado_final = estados[0]  # Primer estado del catálogo por defecto
            justificacion = f"Sin GT ni PDF, usando {estados[0]} (revisar)"
        
        resultados.append({
            'lada': lada,
            'estados_conflicto': ', '.join(estados),
            'gt_ariadne': gt_str,
            'pdf': pdf_str,
            'fuente_propuesta': fuente,
            'estado_final': estado_final,
            'justificacion': justificacion,
            'filas_afectadas': filas_afectadas
        })
    
    # Convertir a DataFrame
    df_res = pd.DataFrame(resultados)
    
    # Mostrar tabla
    print("\n" + "=" * 140)
    print("TABLA CONSOLIDADA: LADAS CONFLICTIVAS CON PROPUESTA DE RESOLUCIÓN")
    print("=" * 140)
    print(df_res.to_string(index=False, max_colwidth=50))
    
    # Resumen
    print("\n" + "=" * 140)
    print("RESUMEN")
    print("=" * 140)
    print(f"Total ladas conflictivas: {len(df_res)}")
    print(f"  - Con corrección de bug 'Mex': {(df_res['fuente_propuesta']=='correccion_bug').sum()}")
    print(f"  - Con GT Ariadne (>=2 filas): {(df_res['fuente_propuesta']=='frecuencia_ariadne').sum()}")
    print(f"  - Con referencia PDF: {(df_res['fuente_propuesta']=='PDF').sum()}")
    print(f"  - Pendientes revisión Sara: {(df_res['fuente_propuesta']=='pendiente_sara').sum()}")
    print(f"\nTotal filas potencialmente afectadas: {df_res['filas_afectadas'].sum()}")
    
    # Casos pendientes Sara (los que requieren decisión manual)
    pendientes = df_res[df_res['fuente_propuesta'] == 'pendiente_sara']
    if len(pendientes) > 0:
        print(f"\n⚠️  {len(pendientes)} CASOS REQUIEREN REVISIÓN MANUAL:")
        for _, row in pendientes.iterrows():
            print(f"  LADA {row['lada']}: {row['estados_conflicto']} → propuesta: {row['estado_final']}")
            print(f"    Justificación: {row['justificacion']}")
    
    # Exportar CSV para revisión
    output_csv = 'data/cache/ladas_conflictivas_propuesta.csv'
    df_res.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n✓ Tabla exportada a: {output_csv}")
    print("  Revisar antes de aplicar el catálogo limpio.")

if __name__ == '__main__':
    main()