"""
Módulo de geocoding - Placeholder para geocoding de plazas
Por ahora usa solo el mapeo directo estado→plaza
"""
import csv
from pathlib import Path
from typing import Optional, Dict, Tuple
import time

class Geocoder:
    """Geocoder simplificado que usa overrides y mapeo directo"""
    
    def __init__(self, config, cache_path: Path):
        """
        Inicializa el geocoder
        
        Args:
            config: Objeto de configuración
            cache_path: Ruta al archivo de cache
        """
        self.config = config
        self.cache_path = cache_path
        self.cache = self._load_cache()
        self.overrides = config.overrides_plazas.get('overrides', {})
        
        print(f"✓ Geocoder inicializado con {len(self.overrides)} overrides")
    
    def _load_cache(self) -> Dict[str, Tuple[float, float]]:
        """Carga el cache de geocoding desde CSV"""
        cache = {}
        if self.cache_path.exists():
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cache[row['plaza']] = (float(row['lat']), float(row['lon']))
        return cache
    
    def _save_cache(self):
        """Guarda el cache de geocoding"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['plaza', 'lat', 'lon'])
            writer.writeheader()
            for plaza, (lat, lon) in self.cache.items():
                writer.writerow({'plaza': plaza, 'lat': lat, 'lon': lon})
    
    def get_coordinates(self, plaza: str) -> Optional[Tuple[float, float]]:
        """
        Obtiene las coordenadas de una plaza
        
        Args:
            plaza: Nombre de la plaza
            
        Returns:
            (lat, lon) o None si no se encuentra
        """
        # Primero buscar en overrides
        override = self.overrides.get(plaza)
        if override:
            return (override['lat'], override['lon'])
        
        # Luego en cache
        if plaza in self.cache:
            return self.cache[plaza]
        
        # TODO: Implementar llamada a Nominatim si no está en cache
        # Por ahora retornar None (no implementar geocoding real hasta validar el resto)
        return None
    
    def find_nearest_plaza(self, estado: str, plazas_activas: list) -> Optional[str]:
        """
        Encuentra la plaza activa más cercana geográficamente
        
        Args:
            estado: Estado del que buscar plaza cercana
            plazas_activas: Lista de plazas activas
            
        Returns:
            Plaza más cercana o None
        """
        # TODO: Implementar búsqueda geográfica real
        # Por ahora retornar None (usar fallback en plaza_matcher)
        return None

if __name__ == '__main__':
    # Test básico
    from config import Config
    
    config = Config('..')
    geocoder = Geocoder(config, config.geocoding_cache_path)
    
    print("\n=== TEST GEOCODER ===\n")
    
    # Probar algunos overrides
    plazas_test = [
        "MEXICO CENTRO ESTADO DE MEXICO ",
        "MONTERREY ORIENTE NUEVO LEON ",
        "ACAPULCO GUERRERO ",
    ]
    
    for plaza in plazas_test:
        coords = geocoder.get_coordinates(plaza)
        if coords:
            print(f"✓ {plaza}: {coords}")
        else:
            print(f"✗ {plaza}: No encontrado")