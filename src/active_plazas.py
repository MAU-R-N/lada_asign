"""
Carga y expone el set canónico de plazas activas desde el JSON de roles del backoffice.
Fuente de verdad: full_asesor_estado.json (roles ASESOR * con estatus Activo).
"""
import json
import re
from pathlib import Path
from typing import Set, Dict, Optional

class ActivePlazasLoader:
    """Carga plazas activas desde el JSON de roles del backoffice."""
    
    def __init__(self, json_path: str = 'full_asesor_estado.json'):
        """
        Args:
            json_path: Ruta al archivo JSON de roles (relativa a raíz del proyecto o absoluta).
        """
        self.json_path = Path(json_path)
        self._roles: Dict[str, Optional[str]] = {}  # rol -> estatus.nombre
        self._plazas_activas: Set[str] = set()
        self._loaded = False
    
    def load(self) -> None:
        """Carga el JSON y extrae roles ASESOR * recursivamente."""
        if self._loaded:
            return
        
        # Intentar rutas: actual, parent (si corremos desde src/)
        search_paths = [
            self.json_path,
            Path('..') / self.json_path,
        ]
        
        found_path = None
        for p in search_paths:
            if p.exists():
                found_path = p
                break
        
        if not found_path:
            raise FileNotFoundError(
                f"No se encontró el JSON de roles en: {self.json_path}\n"
                f"Rutas buscadas: {[str(p) for p in search_paths]}\n"
                "Asegúrate de que full_asesor_estado.json esté en la raíz del proyecto."
            )
        
        self.json_path = found_path
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extracción recursiva de roles
        for persona in data:
            self._walk_roles(persona)
        
        # Filtrar solo ASESOR * con estatus Activo y normalizar
        for rol, estatus in self._roles.items():
            if rol.startswith('ASESOR ') and estatus == 'Activo':
                plaza_norm = self._normalize_json_rol(rol)
                self._plazas_activas.add(plaza_norm)
        
        self._loaded = True
    
    def _walk_roles(self, node: dict) -> None:
        """Recursivamente extrae roles de un nodo (persona o rol dependiente)."""
        if not isinstance(node, dict):
            return
        
        # Capturar rol de este nodo
        rol = node.get('rol')
        if isinstance(rol, str) and rol:
            estatus_obj = node.get('estatus', {}) or {}
            estatus_nombre = estatus_obj.get('nombre') if isinstance(estatus_obj, dict) else None
            self._roles[rol] = estatus_nombre
        
        # Descender: primero dentro del dict 'rol' (si es dict), luego en rolesDependientes
        candidates = []
        rol_obj = node.get('rol')
        if isinstance(rol_obj, dict):
            candidates.append(rol_obj)
        candidates.extend(node.get('rolesDependientes', []) or [])
        
        for child in candidates:
            self._walk_roles(child)
    
    @staticmethod
    def _normalize_json_rol(rol: str) -> str:
        """Normaliza rol JSON: ASESOR ACAPULCO -> ACAPULCO."""
        return re.sub(r'^ASESOR\s+', '', rol.strip())
    
    def get_plazas_activas(self) -> Set[str]:
        """
        Retorna el set de plazas activas (normalizadas, sin prefijo ASESOR).
        
        Returns:
            Set de strings tipo {'ACAPULCO', 'MX CENTRO', 'MONTERREY ORIENTE', ...}
        """
        if not self._loaded:
            self.load()
        return self._plazas_activas.copy()
    
    def get_all_roles(self) -> Dict[str, Optional[str]]:
        """
        Retorna todos los roles extraídos del JSON (para debugging/auditoría).
        
        Returns:
            Dict {rol: estatus.nombre}
        """
        if not self._loaded:
            self.load()
        return self._roles.copy()
    
    def is_plaza_activa(self, plaza_normalizada: str) -> bool:
        """
        Verifica si una plaza (ya normalizada) está en el set de activas.
        
        Args:
            plaza_normalizada: Plaza sin prefijo ASESOR y sin sufijo de estado.
                              Ejemplo: 'ACAPULCO', 'MX CENTRO'
        
        Returns:
            True si la plaza está activa en el JSON.
        """
        if not self._loaded:
            self.load()
        return plaza_normalizada in self._plazas_activas

# Instancia global (singleton pattern, lazy-loaded)
_loader_instance: Optional[ActivePlazasLoader] = None

def get_active_plazas_loader(json_path: str = 'full_asesor_estado.json') -> ActivePlazasLoader:
    """
    Retorna la instancia singleton del loader de plazas activas.
    
    Args:
        json_path: Ruta al JSON de roles (solo se usa en primera llamada).
    
    Returns:
        ActivePlazasLoader instance (cargado lazy al primer uso).
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ActivePlazasLoader(json_path)
    return _loader_instance