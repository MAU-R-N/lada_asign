"""
Módulo de carga de Excel - Lee las hojas necesarias con tipos correctos
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

class ExcelLoader:
    """Carga y prepara los datos del Excel de entrada"""
    
    def __init__(self, excel_path: Path, plazas_csv: Path = None):
        self.excel_path = excel_path
        # Catálogo de ladas ya NO se lee del Excel mensual (ver LadaMatcher)
        self.df_ladas = None
        self.df_asesores = None
        self.plazas_activas = None
        # Plazas activas congeladas en config/plazas_activas.csv (no del Excel)
        self.plazas_csv = plazas_csv or (Path(__file__).parent.parent / 'config' / 'plazas_activas.csv')
        
    def load_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, list]:
        """
        Carga todas las hojas necesarias
        Returns: (df_data, df_ladas, plazas_activas)
        """
        print(f"Cargando {self.excel_path}...")
        
        # Cargar data (hoja principal)
        self.df_data = pd.read_excel(
            self.excel_path,
            sheet_name='data',
            dtype={
                'Clave': str,
                'Asesor': str,
                'Contactos': str,
                'Estatus': str,
                'Resultado': str,
                'LADA': str,  # Como string para preservar ceros a la izquierda
                'ESTADO': str,
                'PLAZA': str
            }
        )
        
        # Convertir Estrellas a float (manejar nulos)
        if 'Estrellas' in self.df_data.columns:
            self.df_data['Estrellas'] = pd.to_numeric(
                self.df_data['Estrellas'], 
                errors='coerce'
            )
        
        # Plazas activas: leer desde full_asesor_estado.json (fuente dinámica del backoffice)
        # Este JSON se actualiza mensualmente reemplazando el archivo.
        # El CSV config/plazas_activas.csv es solo snapshot histórico de auditoría.
        from active_plazas import get_active_plazas_loader
        json_path = Path(__file__).parent.parent / 'full_asesor_estado.json'
        if not json_path.exists():
            raise FileNotFoundError(
                f"No se encontró el JSON de roles: {json_path}. "
                "Debe existir full_asesor_estado.json en la raíz del proyecto (fuente dinámica del backoffice)."
            )
        plazas_loader = get_active_plazas_loader(str(json_path))
        self.plazas_activas = sorted(list(plazas_loader.get_plazas_activas()))
        
        print(f"✓ Data: {len(self.df_data)} filas")
        print(f"✓ Plazas activas: {len(self.plazas_activas)} (desde full_asesor_estado.json)")
        
        return self.df_data, self.df_ladas, self.plazas_activas
    
    def get_diagnostico(self) -> Dict[str, any]:
        """Genera diagnóstico de valores únicos para validación"""
        if self.df_data is None:
            raise ValueError("Debe cargar los datos primero con load_all()")
        
        diag = {
            'total_filas': len(self.df_data),
            'estatus_unicos': sorted(self.df_data['Estatus'].unique().tolist()),
            'resultado_unicos': sorted(self.df_data['Resultado'].dropna().unique().tolist()),
            'asesor_unicos': sorted(self.df_data['Asesor'].unique().tolist()),
            'estrellas_min': self.df_data['Estrellas'].min(),
            'estrellas_max': self.df_data['Estrellas'].max(),
            'estrellas_nulos': self.df_data['Estrellas'].isna().sum(),
        }
        
        return diag

if __name__ == '__main__':
    # Test de carga
    from config import Config
    
    config = Config('..')
    loader = ExcelLoader(config.input_excel_path)
    df_data, df_ladas, plazas = loader.load_all()
    
    print("\n=== DIAGNÓSTICO ===")
    diag = loader.get_diagnostico()
    print(f"Total filas: {diag['total_filas']}")
    print(f"Estatus únicos: {diag['estatus_unicos']}")
    print(f"Estrellas: {diag['estrellas_min']} - {diag['estrellas_max']} (nulos: {diag['estrellas_nulos']})")
    print(f"\nAsesores únicos ({len(diag['asesor_unicos'])}):")
    for asesor in diag['asesor_unicos'][:10]:
        count = (df_data['Asesor'] == asesor).sum()
        print(f"  {asesor!r}: {count}")