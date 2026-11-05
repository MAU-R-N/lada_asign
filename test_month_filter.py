#!/usr/bin/env python3
"""
Script de prueba para verificar el filtrado por mes
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from datetime import datetime
from api_client import NauphilusAPIClient, load_credentials
from json_to_excel_converter import JSONToExcelConverter
import pandas as pd

print("=" * 80)
print("TEST: Filtrado por Mes")
print("=" * 80)

# Cargar configuración
config = load_credentials()
client = NauphilusAPIClient(config)
converter = JSONToExcelConverter()

print("\n1. Descargando 2 días de octubre 2026...")
all_records = []
for dia in [1, 2]:
    fecha = datetime(2026, 10, dia)
    print(f"   Día {dia}...", end=' ')
    registros = client.fetch_entrevistas(fecha, fecha)
    all_records.extend(registros)
    print(f"{len(registros)} registros")

print(f"\n✓ Total descargado: {len(all_records)} registros")

# Convertir a DataFrame
print("\n2. Convirtiendo a DataFrame con columnas Año/Mes...")
df = converter.convert_to_dataframe(all_records)

print(f"✓ DataFrame creado: {len(df)} filas")
print(f"✓ Columnas: {list(df.columns)}")

# Verificar columnas Año/Mes
if 'Año' in df.columns and 'Mes' in df.columns:
    print("\n3. ✓ Columnas Año/Mes presentes")
    
    # Distribución por mes
    month_dist = df['Mes'].value_counts().sort_index()
    print("\n   Distribución por mes:")
    for mes, count in month_dist.items():
        print(f"      Mes {int(mes):02d}: {count} registros")
    
    # Simular contaminación: agregar un registro de septiembre
    print("\n4. Simulando contaminación (agregando registro de septiembre)...")
    fake_row = df.iloc[0].copy()
    fake_row['Año'] = 2026
    fake_row['Mes'] = 9
    fake_row['Clave'] = 'FAKE_SEPT'
    df = pd.concat([df, pd.DataFrame([fake_row])], ignore_index=True)
    
    print(f"✓ Dataset contaminado: {len(df)} registros")
    
    # Nueva distribución
    month_dist = df['Mes'].value_counts().sort_index()
    print("\n   Nueva distribución:")
    for mes, count in month_dist.items():
        print(f"      Mes {int(mes):02d}: {count} registros")
else:
    print("\n3. ✗ ERROR: Columnas Año/Mes NO encontradas")
    sys.exit(1)

# Guardar Excel de prueba
output_path = Path('data/input/entrevistas_2026_10_test.xlsx')
print(f"\n5. Guardando Excel de prueba...")
converter.save_to_excel(df, output_path)

print("\n6. Ahora procesar con main.py para ver el filtrado en acción:")
print(f"   lada/bin/python3 src/main.py --input {output_path}")

print("\n" + "=" * 80)
print("✓ Test completado - Archivo listo para probar filtrado")
print("=" * 80)