"""
Descargador Incremental: Descarga día por día con checkpoint para reanudar
"""
from pathlib import Path
from datetime import datetime, timedelta
import json
import pandas as pd
from typing import Optional

from api_client import NauphilusAPIClient, load_credentials
from json_to_excel_converter import JSONToExcelConverter

class IncrementalDownloader:
    """Descargador incremental con checkpoint y reinicio automático"""
    
    def __init__(self, config: dict = None):
        """
        Inicializa el downloader incremental
        
        Args:
            config: Configuración de la API (si es None, la carga automáticamente)
        """
        self.config = config or load_credentials()
        self.api_client = NauphilusAPIClient(self.config)
        self.converter = JSONToExcelConverter()
        self.project_root = Path(__file__).parent.parent
        self.checkpoint_path = self.project_root / 'data' / 'cache' / 'download_checkpoint.json'
    
    def _load_checkpoint(self) -> Optional[dict]:
        """Carga el checkpoint si existe"""
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, 'r') as f:
                return json.load(f)
        return None
    
    def _save_checkpoint(self, checkpoint: dict):
        """Guarda el checkpoint"""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def _delete_checkpoint(self):
        """Elimina el checkpoint cuando se completa la descarga"""
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
            print("✓ Checkpoint eliminado (descarga completa)")
    
    def download_month_incremental(
        self,
        year: int,
        month: int,
        output_path: Path = None
    ) -> Path:
        """
        Descarga un mes completo día por día, con checkpoint para reanudar
        
        Args:
            year: Año (ej: 2026)
            month: Mes (1-12)
            output_path: Ruta del Excel de salida (opcional)
            
        Returns:
            Path del archivo Excel creado
        """
        from calendar import monthrange
        
        if output_path is None:
            output_path = self.project_root / 'data' / 'input' / f'entrevistas_{year}_{month:02d}.xlsx'
        
        # Determinar días del mes
        ultimo_dia_num = monthrange(year, month)[1]
        
        # Verificar checkpoint
        checkpoint = self._load_checkpoint()
        
        if checkpoint and checkpoint.get('year') == year and checkpoint.get('month') == month:
            print("=" * 80)
            print("📋 CHECKPOINT ENCONTRADO - Reanudando descarga...")
            print("=" * 80)
            dia_inicio = checkpoint['ultimo_dia_completado'] + 1
            all_records = checkpoint['registros_acumulados']
            print(f"✓ Ya descargados: {len(all_records)} registros (días 1-{checkpoint['ultimo_dia_completado']})")
            print(f"⏩ Reanudando desde día {dia_inicio}")
        else:
            print("=" * 80)
            print(f"📥 DESCARGA INCREMENTAL: {year}-{month:02d}")
            print("=" * 80)
            dia_inicio = 1
            all_records = []
        
        # Descargar día por día
        for dia in range(dia_inicio, ultimo_dia_num + 1):
            fecha = datetime(year, month, dia)
            fecha_str = fecha.strftime("%d-%m-%Y")
            
            print(f"\n[{dia}/{ultimo_dia_num}] Descargando {fecha_str}...", end=' ')
            
            try:
                # Descargar día completo (mismo día como inicio y fin)
                registros_dia = self.api_client.fetch_entrevistas(fecha, fecha)
                
                if registros_dia:
                    all_records.extend(registros_dia)
                    print(f"✓ {len(registros_dia)} registros (Total: {len(all_records)})")
                else:
                    print("○ Sin registros")
                
                # Guardar checkpoint después de cada día
                checkpoint = {
                    'year': year,
                    'month': month,
                    'ultimo_dia_completado': dia,
                    'registros_acumulados': all_records,
                    'timestamp': datetime.now().isoformat()
                }
                self._save_checkpoint(checkpoint)
                
            except Exception as e:
                # Si es 404, tratar como día sin datos y continuar
                if '404' in str(e):
                    print(f"○ Sin datos (404)")
                    # Guardar checkpoint para este día vacío
                    checkpoint = {
                        'year': year,
                        'month': month,
                        'ultimo_dia_completado': dia,
                        'registros_acumulados': all_records,
                        'timestamp': datetime.now().isoformat()
                    }
                    self._save_checkpoint(checkpoint)
                else:
                    # Otros errores sí deben detener el proceso
                    print(f"❌ Error: {e}")
                    print(f"\n⚠️  Checkpoint guardado en día {dia-1}")
                    print(f"   Para reanudar, ejecuta el mismo comando de nuevo")
                    raise
        
        # Convertir a Excel
        print(f"\n{'=' * 80}")
        print(f"✓ Descarga completa: {len(all_records)} registros totales")
        print(f"{'=' * 80}")
        
        if not all_records:
            print(f"\n⚠️  No hay datos para {year}-{month:02d}")
            self._delete_checkpoint()
            return None
        
        print(f"\n[Final] Convirtiendo a Excel...")
        df = self.converter.convert_to_dataframe(all_records)
        print(f"✓ DataFrame creado: {len(df)} filas x {len(df.columns)} columnas")
        
        print(f"\n[Final] Guardando Excel...")
        self.converter.save_to_excel(df, output_path)
        
        # Eliminar checkpoint al completar exitosamente
        self._delete_checkpoint()
        
        print(f"\n{'=' * 80}")
        print(f"✅ COMPLETADO EXITOSAMENTE")
        print(f"{'=' * 80}")
        print(f"Archivo: {output_path}")
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
        # Descargar y convertir incrementalmente
        excel_path = self.download_month_incremental(year, month)
        
        if not excel_path:
            return {'error': 'No hay datos para procesar'}
        
        # Procesar con el sistema principal
        print(f"\n{'=' * 80}")
        print("PROCESANDO CON SISTEMA LADA")
        print('=' * 80)
        
        from main import process_excel
        from config import Config
        
        config = Config(self.project_root)
        config.input_excel_path = excel_path
        
        resultados = process_excel(config, excel_path)
        
        return resultados

def cli_interface():
    """Interfaz de línea de comandos"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='Descargador Incremental: Descarga día por día con checkpoint'
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
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reiniciar descarga (eliminar checkpoint)'
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
        downloader = IncrementalDownloader()
        
        # Opción para resetear checkpoint
        if args.reset:
            if downloader.checkpoint_path.exists():
                downloader._delete_checkpoint()
                print("✓ Checkpoint eliminado. La descarga comenzará desde el día 1.")
            else:
                print("○ No hay checkpoint para eliminar.")
            sys.exit(0)
        
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
            excel_path = downloader.download_month_incremental(args.year, args.month, output_path)
            
            if not excel_path:
                print(f"\n❌ No se pudo generar el Excel")
                sys.exit(1)
            
            print(f"\n✅ Excel generado: {excel_path}")
            print("\nPara procesarlo con el sistema LADA, ejecuta:")
            print(f"  venv/bin/python3 src/main.py")
            print("O descarga con procesamiento automático:")
            print(f"  venv/bin/python3 src/incremental_downloader.py -y {args.year} -m {args.month} --process")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Descarga interrumpida por el usuario")
        print("   Checkpoint guardado. Para reanudar, ejecuta el mismo comando de nuevo")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Si la descarga se interrumpió, el checkpoint fue guardado.")
        print("   Para reanudar, ejecuta el mismo comando de nuevo")
        sys.exit(1)

if __name__ == '__main__':
    cli_interface()