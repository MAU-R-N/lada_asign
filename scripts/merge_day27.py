"""
Script para agregar los datos del día 27 manualmente al Excel de agosto
"""
import pandas as pd
from pathlib import Path
from datetime import datetime

def merge_day27():
    """Combina el Excel automático con el manual del día 27"""
    
    project_root = Path(__file__).parent.parent
    
    # Leer Excel automático (días 1-26, 28-31)
    auto_file = project_root / 'data' / 'input' / 'entrevistas_2026_08.xlsx'
    df_auto = pd.read_excel(auto_file, sheet_name='data')
    print(f"📥 Excel automático: {len(df_auto)} registros")
    
    # Leer Excel manual del día 27
    manual_file = project_root / 'auto_download_example' / 'Solicitudes_Farmah_27-08-2026.xlsx'
    df_manual = pd.read_excel(manual_file)
    print(f"📥 Excel manual día 27: {len(df_manual)} registros")
    
    # Mapear columnas del manual al formato automático
    df_manual_mapped = pd.DataFrame({
        'Clave': df_manual['Clave'],
        'Prospecto': df_manual['Prospecto'],  # Incluir prospecto del manual
        'Asesor': df_manual['Asesor'],
        'Contactos': df_manual['Contactos'],
        'Estatus': df_manual['Estatus'],
        'Resultado': df_manual['Resultado'],
        'Estrellas': df_manual['Estrellas'],
        'LADA': '',  # Se llenará después con el sistema
        'ESTADO': '',  # Se llenará después con el sistema
        'PLAZA': '',  # Se llenará después con el sistema
        'Fecha': '2026-08-27'  # Fecha del día 27
    })
    
    print(f"\n✓ Mapeadas {len(df_manual_mapped)} entradas del día 27")
    
    # Combinar ambos DataFrames
    df_combined = pd.concat([df_auto, df_manual_mapped], ignore_index=True)
    
    # Ordenar por fecha (opcional)
    df_combined['Fecha'] = pd.to_datetime(df_combined['Fecha'])
    df_combined = df_combined.sort_values('Fecha').reset_index(drop=True)
    
    print(f"\n✓ Total combinado: {len(df_combined)} registros")
    print(f"  - Automático: {len(df_auto)}")
    print(f"  - Manual día 27: {len(df_manual_mapped)}")
    print(f"  - Total: {len(df_combined)}")
    
    # Guardar Excel combinado
    output_file = project_root / 'data' / 'input' / 'entrevistas_2026_08_completo.xlsx'
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_combined.to_excel(writer, sheet_name='data', index=False)
    
    print(f"\n✅ Excel completo guardado: {output_file}")
    print(f"   Total registros: {len(df_combined)}")
    
    return output_file

if __name__ == '__main__':
    merge_day27()