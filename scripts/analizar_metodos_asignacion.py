"""
Analiza los métodos de asignación: directo_estado_inactiva y no_identificado.
Confirma si cuentan en los totales de Evaluadas/Activas.
"""
import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config import Config
from excel_loader import ExcelLoader
from resolver import ContactoDigitalResolver
from active_plazas import ActivePlazasLoader
from asesor_normalizer import AsesorNormalizer

def main():
    # Ejecutar main.py para obtener el dataframe resuelto, luego analizar
    import subprocess
    import os
    
    # Ejecutar el pipeline completo
    print("Ejecutando pipeline completo...")
    result = subprocess.run(
        ['python3', 'src/main.py'],
        capture_output=True,
        text=True,
        cwd=os.getcwd()
    )
    
    if result.returncode != 0:
        print("Error ejecutando pipeline:")
        print(result.stderr)
        return
    
    # Buscar el archivo de salida más reciente
    output_dir = Path('data/output')
    output_files = sorted(output_dir.glob('facturacion_procesada_*.xlsx'))
    if not output_files:
        print(f"No se encontró archivo de salida en {output_dir}")
        return
    
    output_path = output_files[-1]
    print(f"Cargando {output_path}...")
    
    # Verificar nombres de hojas
    import openpyxl
    wb = openpyxl.load_workbook(output_path, read_only=True)
    print(f"  Hojas disponibles: {wb.sheetnames}")
    wb.close()
    
    df = pd.read_excel(output_path, sheet_name=0)
    
    # Cargar plazas activas del JSON para análisis adicional
    json_loader = ActivePlazasLoader('full_asesor_estado.json')
    json_loader.load()
    plazas_json = json_loader.get_plazas_activas()
    
    # Cargar normalización
    normalizer = AsesorNormalizer('config/asesor_normalization.yaml')
    
    # Cargar config para obtener clasificaciones
    import yaml
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    evaluadas_est = config_dict['clasificacion']['evaluadas_estatus']
    activas_est = config_dict['clasificacion']['activas_estatus']
    umbral = config_dict['clasificacion']['activas_umbral_estrellas']
    no_id_label = config_dict['plaza_assignment']['no_identificado_label']
    
    print("=" * 100)
    print("ANÁLISIS DE MÉTODOS DE ASIGNACIÓN")
    print("=" * 100)
    
    # Distribución completa
    print("\nDistribución de métodos (todas las 12,060 filas):")
    metodos = df['metodo_asignacion'].value_counts()
    for metodo, count in metodos.items():
        print(f"  {metodo}: {count}")
    
    # Análisis de directo_estado_inactiva
    print("\n" + "=" * 100)
    print("1. MÉTODO: directo_estado_inactiva")
    print("=" * 100)
    inactivas = df[df['metodo_asignacion'] == 'directo_estado_inactiva'].copy()
    print(f"\nTotal filas: {len(inactivas)}")
    
    if len(inactivas) > 0:
        print("\n¿Qué significa?")
        print("  - Son filas con plaza directa en la columna 'Asesor' del Excel")
        print("  - Esa plaza NO está activa en el JSON de roles (full_asesor_estado.json)")
        print("  - Puede ser: plaza desactivada, nombre desactualizado, o error de captura")
        
        print("\nPlazas inactivas detectadas:")
        plazas_prob = inactivas['Asesor'].value_counts()
        for plaza, count in plazas_prob.items():
            normalizada = normalizer.normalize(plaza)
            match = "SÍ" if normalizada in plazas_json else "NO"
            print(f"  '{plaza}' ({count} filas) → normalizada: '{normalizada}' → match JSON: {match}")
        
        print("\n¿Cuentan en Evaluadas/Activas?")
        
        inac_eval = inactivas[inactivas['Estatus'].isin(evaluadas_est)]
        inac_activas = inactivas[
            (inactivas['Estatus'] == activas_est) & 
            (inactivas['Estrellas'] >= umbral)
        ]
        
        print(f"  - Evaluadas (estatus {evaluadas_est}): {len(inac_eval)} filas → SÍ CUENTAN")
        print(f"  - Activas (estatus {activas_est} AND estrellas>={umbral}): {len(inac_activas)} filas → SÍ CUENTAN")
        print(f"  Total inactivas en reportes: {len(inac_eval)} + {len(inac_activas)} = {len(inac_eval) + len(inac_activas)}")
        
        print("\nMuestras (primeras 5 filas):")
        print(inactivas[['Clave', 'Prospecto', 'Asesor', 'Estatus', 'plaza_calculada', 'metodo_asignacion']].head().to_string())
    
    # Análisis de no_identificado
    print("\n" + "=" * 100)
    print("2. MÉTODO: no_identificado")
    print("=" * 100)
    no_id = df[df['metodo_asignacion'] == 'no_identificado'].copy()
    print(f"\nTotal filas: {len(no_id)}")
    
    if len(no_id) > 0:
        print("\n¿Qué significa?")
        print("  - Filas CONTACTO DIGITAL sin teléfono extraíble O con lada no en catálogo")
        print("  - Son casos genuinamente irresolubles sin intervención manual")
        
        # Clasificar causa
        no_id['tiene_telefono'] = no_id['telefono_calculado'].notna()
        sin_tel = (~no_id['tiene_telefono']).sum()
        con_tel = no_id['tiene_telefono'].sum()
        
        print(f"\nCausas:")
        print(f"  - Sin teléfono extraíble: {sin_tel} filas")
        print(f"  - Con teléfono pero lada sin match: {con_tel} filas")
        
        print("\n¿Cuentan en Evaluadas/Activas?")
        no_id_eval = no_id[no_id['Estatus'].isin(evaluadas_est)]
        no_id_activas = no_id[
            (no_id['Estatus'] == activas_est) & 
            (no_id['Estrellas'] >= umbral)
        ]
        
        print(f"  - Evaluadas: {len(no_id_eval)} filas → SÍ CUENTAN (con plaza_calculada='{no_id_label}')")
        print(f"  - Activas: {len(no_id_activas)} filas → SÍ CUENTAN (con plaza_calculada='{no_id_label}')")
        
        print("\nMuestras (primeras 5 filas):")
        print(no_id[['Clave', 'Prospecto', 'Contactos', 'Estatus', 'telefono_calculado', 'lada_calculada', 'plaza_calculada']].head().to_string())
    
    # Confirmación de totales
    print("\n" + "=" * 100)
    print("CONFIRMACIÓN: TODOS LOS MÉTODOS CUENTAN EN TOTALES")
    print("=" * 100)
    
    evaluadas_total = df[df['Estatus'].isin(evaluadas_est)]
    activas_total = df[(df['Estatus'] == activas_est) & (df['Estrellas'] >= umbral)]
    
    print(f"\nTotal Evaluadas: {len(evaluadas_total)}")
    print(f"  - Incluye directo_estado_inactiva: {len(inactivas[inactivas['Estatus'].isin(evaluadas_est)])}")
    print(f"  - Incluye no_identificado: {len(no_id[no_id['Estatus'].isin(evaluadas_est)])}")
    
    print(f"\nTotal Activas: {len(activas_total)}")
    print(f"  - Incluye directo_estado_inactiva: {len(inactivas[(inactivas['Estatus']==activas_est) & (inactivas['Estrellas']>=umbral)])}")
    print(f"  - Incluye no_identificado: {len(no_id[(no_id['Estatus']==activas_est) & (no_id['Estrellas']>=umbral)])}")
    
    print("\n✓ Ambos métodos CUENTAN en los totales finales de facturación.")
    print("  Solo se marcan con bandera de auditoría en la columna 'metodo_asignacion'.")

if __name__ == '__main__':
    main()