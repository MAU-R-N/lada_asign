"""
Módulo de carga de Excel - Lee las hojas necesarias con tipos correctos
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

class ExcelLoader:
    """Carga y prepara los datos del Excel de entrada"""
    
    def __init__(self, excel_path: Path):
        self.excel_path = excel_path
        self.df_data = None
        self.df_ladas = None
        self.df_asesores = None
        self.plazas_activas = None
        
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
        
        # Cargar catálogo de ladas
        self.df_ladas = pd.read_excel(
            self.excel_path,
            sheet_name='Ladas',
            dtype={
                'LADA': str,  # Como string
                'Ubicación': str,
                'Estado': str,
                'PLAZAS': str
            }
        )
        
        # Normalizar columna LADA (asegurar formato consistente)
        if 'LADA' in self.df_ladas.columns:
            # Convertir a string y rellenar con ceros a la izquierda
            self.df_ladas['LADA'] = self.df_ladas['LADA'].astype(str).str.strip()
        
        # Cargar asesores para obtener plazas activas
        self.df_asesores = pd.read_excel(
            self.excel_path,
            sheet_name='asesores'
        )
        
        # Extraer lista de plazas activas de la columna PLAZAS del catálogo
        plazas_col = self.df_ladas['PLAZAS'].dropna()
        self.plazas_activas = sorted(plazas_col.unique().tolist())
        
        print(f"✓ Data: {len(self.df_data)} filas")
        print(f"✓ Ladas: {len(self.df_ladas)} entradas")
        print(f"✓ Plazas activas: {len(self.plazas_activas)}")
        
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