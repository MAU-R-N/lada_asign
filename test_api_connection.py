"""
Script de prueba para conectar con la API y descubrir la estructura de datos
Ejecutar después de crear credentials.json con valores reales
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from api_client import NauphilusAPIClient, load_credentials
import json

def main():
    print("=" * 80)
    print("PRUEBA DE CONEXIÓN API - DESCUBRIMIENTO DE ESTRUCTURA")
    print("=" * 80)
    
    try:
        # Cargar credenciales
        print("\n1. Cargando credenciales...")
        config = load_credentials()
        print(f"   ✓ Base URL: {config['base_url']}")
        print(f"   ✓ Username: {config['username']}")
        print(f"   ✓ Membership ID: {config['membership_id']}")
        print(f"   ✓ Endpoint ID: {config['endpoint_id']}")
        
        # Crear cliente
        print("\n2. Creando cliente API...")
        client = NauphilusAPIClient(config)
        print("   ✓ Cliente inicializado")
        
        # Descargar octubre 2026
        print("\n3. Descargando datos de OCTUBRE 2026...")
        entrevistas = client.fetch_mes_completo(2026, 10)
        
        print(f"\n✓ ÉXITO: Descargados {len(entrevistas)} registros")
        
        if entrevistas:
            # Guardar estructura completa para análisis
            output_file = Path('data/cache/estructura_api_octubre2026.json')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(entrevistas[:5], f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Primeros 5 registros guardados en: {output_file}")
            
            # Mostrar estructura del primer registro
            print("\n" + "=" * 80)
            print("ESTRUCTURA DEL PRIMER REGISTRO:")
            print("=" * 80)
            print(json.dumps(entrevistas[0], indent=2, ensure_ascii=False))
            
            # Análisis de campos
            print("\n" + "=" * 80)
            print("ANÁLISIS DE CAMPOS:")
            print("=" * 80)
            
            campos = list(entrevistas[0].keys())
            print(f"\nTotal de campos: {len(campos)}")
            print("\nLista de campos disponibles:")
            for i, campo in enumerate(campos, 1):
                valor = entrevistas[0][campo]
                tipo = type(valor).__name__
                print(f"  {i:2d}. {campo:30s} (tipo: {tipo})")
            
            # Mapeo sugerido Excel → JSON
            print("\n" + "=" * 80)
            print("MAPEO SUGERIDO (Excel → JSON):")
            print("=" * 80)
            
            mapeo_excel = {
                'Clave': ['clave', 'id', 'folio', 'codigo'],
                'Prospecto': ['prospecto', 'nombre', 'nombre_completo', 'nombreCompleto'],
                'Asesor': ['asesor', 'plaza', 'plaza_asignada', 'plazaAsignada'],
                'Contactos': ['contactos', 'telefono', 'email'],
                'Producto': ['producto', 'tipo_producto', 'tipoProducto'],
                'Ultima Mod.': ['ultima_modificacion', 'fecha', 'fecha_actualizacion'],
                'Estatus': ['estatus', 'status', 'estado'],
                'Resultado': ['resultado', 'resultado_evaluacion'],
                'Estrellas': ['estrellas', 'calificacion', 'rating', 'score'],
                'LADA': ['lada', 'codigo_lada', 'codigoLada'],
                'ESTADO': ['estado', 'entidad', 'estado_republica'],
                'PLAZA': ['plaza', 'plaza_normalizada'],
            }
            
            for excel_col, posibles_json in mapeo_excel.items():
                encontrado = None
                for posible in posibles_json:
                    if posible in campos:
                        encontrado = posible
                        break
                
                if encontrado:
                    print(f"  {excel_col:15s} → {encontrado} ✓")
                else:
                    print(f"  {excel_col:15s} → {posibles_json[0]} (NO ENCONTRADO)")
            
            print("\n" + "=" * 80)
            print("SIGUIENTE PASO:")
            print("=" * 80)
            print("Revisa el archivo estructura_api_octubre2026.json")
            print("Ajusta el mapeo en json_to_excel_converter.py según los campos reales")
            
        else:
            print("\n⚠ Advertencia: La API no retornó registros para octubre 2026")
            print("Verifica:")
            print("  - Las fechas (puede que no haya datos para ese mes)")
            print("  - Los IDs de membership y endpoint")
            print("  - Los permisos del usuario")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nPASOS PARA SOLUCIONAR:")
        print("1. Copia credentials.json.example a credentials.json")
        print("2. Edita credentials.json con las credenciales reales")
        print("3. Ejecuta este script nuevamente")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nVERIFICA:")
        print("  - Credenciales correctas en credentials.json")
        print("  - URL de la API correcta")
        print("  - Conexión a internet")
        print("  - IDs de membership y endpoint válidos")

if __name__ == '__main__':
    main()