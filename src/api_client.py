"""
Cliente HTTP para descargar entrevistas desde la API de Nauphilus
Adaptado de auto_download_example/auth.py y fetcher.py
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional
import json
from pathlib import Path

class NauphilusAPIClient:
    """Cliente para la API de Nauphilus con autenticación OAuth"""
    
    def __init__(self, config: dict):
        """
        Inicializa el cliente con configuración
        
        Args:
            config: Diccionario con username, password, base_url, membership_id, endpoint_id
        """
        self.base_url = config['base_url']
        self.username = config['username']
        self.password = config['password']
        self.membership_id = config['membership_id']
        self.endpoint_id = config['endpoint_id']
        self._token_cache: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    def _get_token(self) -> str:
        """
        Obtiene token OAuth (con caché)
        Si el token existe y no ha expirado, lo reutiliza.
        """
        ahora = datetime.utcnow()
        
        if self._token_cache and self._token_expiry and ahora < self._token_expiry:
            print(f"✓ Usando token cacheado (expira en {(self._token_expiry - ahora).seconds}s)")
            return self._token_cache
        
        print("Obteniendo nuevo token OAuth...")
        
        response = httpx.post(
            f"{self.base_url}/auth/oauth/token",
            headers={"Authorization": "Basic TkFVUEhJTFVTOnNlY3JldA=="},
            data={
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
            },
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        
        self._token_cache = data["access_token"]
        self._token_expiry = ahora + timedelta(seconds=data["expires_in"] - 60)
        
        print(f"✓ Token obtenido (válido por {data['expires_in']}s)")
        return self._token_cache
    
    def fetch_entrevistas(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        """
        Descarga entrevistas para un rango de fechas
        
        Args:
            fecha_inicio: Fecha y hora de inicio (inclusiva)
            fecha_fin: Fecha y hora de fin (inclusiva)
            
        Returns:
            Lista de diccionarios con entrevistas
        """
        token = self._get_token()
        
        # Formato con horas como en el ejemplo original
        fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d %H:%M:%S")
        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d %H:%M:%S")
        
        # Construir URL - httpx maneja el encoding automáticamente
        base_url_path = (
            f"{self.base_url}/memberships/{self.membership_id}/core/creditApp"
            f"/getSolitudesByTime/{self.endpoint_id}"
        )
        
        url = f"{base_url_path}/{fecha_inicio_str}/{fecha_fin_str}"
        
        print(f"Descargando desde: {fecha_inicio_str}")
        print(f"             hasta: {fecha_fin_str}")
        print(f"URL: {url}")
        
        response = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=300.0  # 5 minutos para meses con muchos datos
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Descargados {len(data)} registros")
        
        return data
    
    def fetch_mes_completo(self, año: int, mes: int) -> list[dict]:
        """
        Descarga todas las entrevistas de un mes completo
        
        Args:
            año: Año (ej: 2026)
            mes: Mes (1-12)
            
        Returns:
            Lista de diccionarios con entrevistas del mes
        """
        from calendar import monthrange
        
        primer_dia = datetime(año, mes, 1, 0, 0, 0)
        ultimo_dia_num = monthrange(año, mes)[1]
        ultimo_dia = datetime(año, mes, ultimo_dia_num, 23, 59, 59)
        
        print(f"\nDescargando mes completo: {año}-{mes:02d}")
        print(f"Rango: {primer_dia.date()} a {ultimo_dia.date()}")
        
        return self.fetch_entrevistas(primer_dia, ultimo_dia)

def load_credentials(credentials_path: Path = None) -> dict:
    """
    Carga credenciales desde credentials.json
    
    Args:
        credentials_path: Ruta al archivo de credenciales (opcional)
        
    Returns:
        Diccionario con configuración de la API
    """
    if credentials_path is None:
        credentials_path = Path(__file__).parent.parent / 'credentials.json'
    
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"No se encontró {credentials_path}. "
            "Copia credentials.json.example a credentials.json y completa los valores."
        )
    
    with open(credentials_path) as f:
        creds = json.load(f)
    
    # Soportar ambos formatos: con wrapper 'nauphilus_api' o directo
    if 'nauphilus_api' in creds:
        return creds['nauphilus_api']
    else:
        # Formato directo con las credenciales en el root
        return creds

if __name__ == '__main__':
    # Test del cliente
    print("=" * 60)
    print("TEST: API CLIENT")
    print("=" * 60)
    
    try:
        config = load_credentials()
        print(f"✓ Credenciales cargadas")
        print(f"  Base URL: {config['base_url']}")
        print(f"  Username: {config['username']}")
        
        client = NauphilusAPIClient(config)
        
        # Descargar octubre 2026 como test
        print("\nDescargando octubre 2026...")
        entrevistas = client.fetch_mes_completo(2026, 10)
        
        print(f"\n✓ Descargados {len(entrevistas)} registros")
        
        if entrevistas:
            print("\nPrimera entrevista (estructura):")
            print(json.dumps(entrevistas[0], indent=2, ensure_ascii=False))
            
            print("\nCampos disponibles:")
            for key in entrevistas[0].keys():
                print(f"  - {key}")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()