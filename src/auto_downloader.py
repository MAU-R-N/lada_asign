"""
Auto-Downloader: Descarga automática desde API, conversión a Excel y procesamiento
"""
from pathlib import Path
from datetime import datetime
import sys

# Importar módulos del sistema
from api_client import NauphilusAPIClient, load_credentials
from json_to_excel_converter import JSONToExcelConverter

class AutoDownloader:
    """Orquestador de descarga automática y procesamiento"""
    
    def __init__(self, config: dict = None):
        """
        Inicializa el auto-downloader
        
        Args:
            config: Configuración de la API (si es None, la carga automáticamente)
        """
        self.config = config or load_credentials()
        self.api_client = NauphilusAPIClient(self.config)
        self.converter = JSONToExcelConverter()
        self.project_root = Path(__file__).parent.parent
    
    def download_and_convert_month(self, year: int, month: int, output_path: Path = None) -> Path:
        """
        Descarga un mes completo de la API y lo convierte a Excel
        
        Args:
            year: Año (ej: 2026)
            month: Mes (1-12)
            output_path: Ruta del Excel de salida (opcional, por defecto data/input/)
            
        Returns:
            Path del archivo Excel creado
        """
        print("=" * 80)
        print(f"AUTO-DOWNLOAD: {year}-{month:02d}")
        print("=" * 80)
        
        # 1. Descargar desde API
        print(f"\n[1/3] Descargando entrevistas desde API...")
        entrevistas = self.api_client.fetch_mes_completo(year, month)
        
        if not entrevistas:
            print(f"\n⚠ No hay datos para {year}-{month:02d}")
            return None
        
        print(f"\n✓ Descargados {len(entrevistas)} registros")
        
        # 2. Convertir a DataFrame
        print(f"\n[2/3] Convirtiendo a formato Excel...")
        df = self.converter.convert_to_dataframe(entrevistas)
        print(f"✓ DataFrame creado: {len(df)} filas x {len(df.columns)} columnas")
        
        # 3. Guardar Excel
        if output_path is None:
            output_path = self.project_root / 'data' / 'input' / f'entrevistas_{year}_{month:02d}.xlsx'
        
        print(f"\n[3/3] Guardando Excel...")
        self.converter.save_to_excel(df, output_path)
        
        print(f"\n{'=' * 80}")
        print(f"✓ COMPLETADO")
        print(f"{'=' * 80}")
        print(f"Archivo generado: {output_path}")
        print(f"Total registros: {len(df)}")
        
        return output_path
    
    def download_and_process_month(self, year: int, month: int) -> dict:
        """
        Descarga, convierte y procesa un mes completo automáticamente
        
        Args:
            year: Año (ej: 2026)
            month: Mes (1-12)
            
        Returns:
            Diccionario con resultados del procesamiento
        """
        # Descargar y convertir
        excel_path = self.download_and_convert_month(year, month)
        
        if not excel_path:
            return {'error': 'No hay datos para procesar'}
        
        # Procesar con el sistema principal
        print(f"\n{'=' * 80}")
        print("PROCESANDO CON SISTEMA LADA")
        print('=' * 80)
        
        from main import process_excel
        from config import Config
        
        config = Config(self.project_root)
        # Actualizar la ruta del Excel en config
        config.input_excel_path = excel_path
        
        resultados = process_excel(config, excel_path)
        
        return resultados

def cli_interface():
    """Interfaz de línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Auto-Downloader: Descarga automática desde API Nauphilus'
    )
    parser.add_argument(
        '--year', '-y',
        type=int,
        required=True,
        help='Año a descargar (ej: 2026)'
    )
    parser.add_argument(
        '--month', '-m',
        type=int,
        required=True,
        help='Mes a descargar (1-12)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Ruta del Excel de salida (opcional)'
    )
    parser.add_argument(
        '--process',
        action='store_true',
        help='Procesar automáticamente con el sistema LADA'
    )
    
    args = parser.parse_args()
    
    # Validaciones
    if not (1 <= args.month <= 12):
        print("❌ Error: El mes debe estar entre 1 y 12")
        sys.exit(1)
    
    if args.year < 2020 or args.year > 2030:
        print("❌ Error: Año fuera de rango razonable")
        sys.exit(1)
    
    # Ejecutar
    try:
        downloader = AutoDownloader()
        
        if args.process:
            # Descargar y procesar
            resultados = downloader.download_and_process_month(args.year, args.month)
            
            if 'error' in resultados:
                print(f"\n❌ Error: {resultados['error']}")
                sys.exit(1)
            
            print("\n✅ Proceso completado exitosamente")
        else:
            # Solo descargar y convertir
            output_path = Path(args.output) if args.output else None
            excel_path = downloader.download_and_convert_month(args.year, args.month, output_path)
            
            if not excel_path:
                print(f"\n❌ No se pudo generar el Excel")
                sys.exit(1)
            
            print(f"\n✅ Excel generado: {excel_path}")
            print("\nPara procesarlo con el sistema LADA, ejecuta:")
            print(f"  python3 src/main.py")
            print("O descarga con procesamiento automático:")
            print(f"  python3 src/auto_downloader.py -y {args.year} -m {args.month} --process")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    cli_interface()