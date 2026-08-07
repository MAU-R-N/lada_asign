"""
Módulo de configuración - Carga archivos YAML y provee acceso a parámetros
"""
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Clase para manejar la configuración del proyecto"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.config = self._load_yaml("config/config.yaml")
        self.estado_plaza = self._load_yaml("config/estado_a_plaza.yaml")
        self.overrides_plazas = self._load_yaml("config/overrides_plazas.yaml")
        self._input_excel_override = None
    
    def _load_yaml(self, rel_path: str) -> Dict[str, Any]:
        """Carga un archivo YAML"""
        file_path = self.base_path / rel_path
        if not file_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de configuración: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key_path: str, default=None):
        """
        Obtiene un valor de configuración usando notación de punto
        Ej: config.get('paths.input_excel')
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set_input_excel(self, path: str) -> None:
        """
        Sobreescribe la ruta del Excel de entrada (usado por --input CLI).
        No modifica el config.yaml para que cada mes se pase por argumento.
        """
        self._input_excel_override = str(path)

    def get_estado_to_plaza(self, estado: str) -> str:
        """Obtiene la plaza correspondiente a un estado"""
        return self.estado_plaza.get('estado_plaza', {}).get(estado)
    
    def get_plaza_override(self, plaza: str) -> Dict[str, Any]:
        """Obtiene las coordenadas override para una plaza"""
        return self.overrides_plazas.get('overrides', {}).get(plaza)
    
    @property
    def input_excel_path(self) -> Path:
        """Ruta del Excel de entrada (override CLI si existe, si no YAML)"""
        if self._input_excel_override:
            path = Path(self._input_excel_override)
            if not path.is_absolute():
                path = self.base_path / path
            return path
        return self.base_path / self.get('paths.input_excel')
    
    @property
    def geocoding_cache_path(self) -> Path:
        """Ruta del cache de geocoding"""
        return self.base_path / self.get('paths.geocoding_cache')
    
    @property
    def evaluadas_estatus(self) -> list:
        """Lista de estatus considerados como evaluadas"""
        return self.get('clasificacion.evaluadas_estatus', [])
    
    @property
    def activas_estatus(self) -> str:
        """Estatus para activas"""
        return self.get('clasificacion.activas_estatus', 'ACTIVO')
    
    @property
    def activas_umbral(self) -> float:
        """Umbral de estrellas para activas"""
        return self.get('clasificacion.activas_umbral_estrellas', 35)
    
    @property
    def fallback_extranjero(self) -> str:
        """Plaza por defecto para números extranjeros"""
        return self.get('plaza_assignment.fallback_extranjero', 'MEXICALI BAJA CALIFORNIA ')
    
    @property
    def no_identificado_label(self) -> str:
        """Label para números no identificados"""
        return self.get('plaza_assignment.no_identificado_label', 'NO IDENTIFICADO')

if __name__ == '__main__':
    # Test de carga de configuración
    config = Config('..')
    print("✓ Config cargado")
    print(f"  Input: {config.input_excel_path}")
    print(f"  Evaluadas estatus: {config.evaluadas_estatus}")
    print(f"  Activas umbral: {config.activas_umbral}")
    print(f"  Fallback extranjero: {config.fallback_extranjero}")
    print(f"  Estados en mapeo: {len(config.estado_plaza.get('estado_plaza', {}))}")
    print(f"  Overrides: {len(config.overrides_plazas.get('overrides', {}))}")