"""
Normalización de data.Asesor para matching contra roles JSON del backoffice.
Recorta sufijos de estado y aplica alias/overrides desde config/asesor_normalization.yaml
"""
import yaml
from pathlib import Path
from typing import Optional

class AsesorNormalizer:
    """Normaliza valores de data.Asesor para comparación con roles JSON."""
    
    def __init__(self, config_path: str = 'config/asesor_normalization.yaml'):
        self.config_path = Path(config_path)
        self._estados_mx: list[str] = []
        self._alias: dict[str, str] = {}
        self._overrides: dict[str, str] = {}
        self._loaded = False
    
    def load(self) -> None:
        """Carga la configuración desde YAML."""
        if self._loaded:
            return
        
        # Intentar rutas: actual, parent (si corremos desde src/)
        search_paths = [
            self.config_path,
            Path('..') / self.config_path,
        ]
        
        found_path = None
        for p in search_paths:
            if p.exists():
                found_path = p
                break
        
        if not found_path:
            raise FileNotFoundError(
                f"No se encontró config de normalización: {self.config_path}\n"
                f"Rutas buscadas: {[str(p) for p in search_paths]}"
            )
        
        self.config_path = found_path
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Estados ya vienen ordenados multi-palabra primero en el YAML
        self._estados_mx = config.get('estados_mx', [])
        self._alias = config.get('alias_ciudad', {})
        self._overrides = config.get('overrides', {})
        self._loaded = True
    
    def normalize(self, asesor: str) -> str:
        """
        Normaliza un valor de data.Asesor.
        
        Pasos:
        1. Trim y uppercase
        2. Aplicar overrides si existe
        3. Recortar sufijo de estado (multi-palabra primero)
        4. Aplicar alias de ciudad si existe
        
        Args:
            asesor: Valor raw de data.Asesor (ej: "ACAPULCO GUERRERO")
        
        Returns:
            Plaza normalizada (ej: "ACAPULCO") o marker especial ("__SISTEMA__")
        """
        if not self._loaded:
            self.load()
        
        asesor = asesor.strip().upper()
        
        # Overrides directos (casos especiales que no siguen patrón)
        if asesor in self._overrides:
            return self._overrides[asesor]
        
        # Recortar sufijo de estado (multi-palabra primero, luego simple)
        ciudad = self._recortar_estado(asesor)
        
        # Aplicar alias de ciudad si existe
        return self._alias.get(ciudad, ciudad)
    
    def _recortar_estado(self, asesor: str) -> str:
        """Recorta sufijo de estado del asesor (CIUDAD ESTADO → CIUDAD)."""
        # Estados multi-palabra primero (ya ordenados en YAML)
        for estado in self._estados_mx:
            if asesor.endswith(' ' + estado):
                return asesor[:-(len(estado) + 1)]
        
        # Si no matcheó, el asesor podría ser ciudad == estado (no hay sufijo)
        # o un caso no catalogado → retornar tal cual
        return asesor

# Instancia singleton
_normalizer_instance: Optional[AsesorNormalizer] = None

def get_asesor_normalizer(config_path: str = 'config/asesor_normalization.yaml') -> AsesorNormalizer:
    """
    Retorna la instancia singleton del normalizador.
    
    Args:
        config_path: Ruta al YAML de configuración (solo primera llamada).
    
    Returns:
        AsesorNormalizer instance (lazy-loaded).
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = AsesorNormalizer(config_path)
    return _normalizer_instance