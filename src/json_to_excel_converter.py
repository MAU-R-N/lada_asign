"""
Convertidor de JSON de API Nauphilus a Excel compatible con el sistema
"""
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class JSONToExcelConverter:
    """Convierte entrevistas de la API a formato Excel del sistema"""
    
    def __init__(self):
        pass
    
    def _extract_telefono(self, prospect: dict) -> str:
        """
        Extrae el primer teléfono del contacto
        
        Args:
            prospect: Dict con datos del prospecto
            
        Returns:
            Teléfono como string o vacío
        """
        try:
            contacts = prospect.get('prospectContacts', [])
            if not contacts:
                return ''
            
            contact = contacts[0]
            contact_means = contact.get('contactMeans', [])
            
            for medio in contact_means:
                medio_contacto = medio.get('medioContacto', {})
                nombre = medio_contacto.get('nombre', '').lower()
                
                # Buscar teléfonos (fijo o celular)
                if 'telefono' in nombre or 'celular' in nombre:
                    return str(medio.get('dato', ''))
            
            return ''
        except:
            return ''
    
    def _extract_asesor_nombre(self, asesor: dict) -> str:
        """
        Extrae el nombre completo del asesor
        
        Args:
            asesor: Dict con datos del asesor
            
        Returns:
            Nombre completo como string
        """
        if not asesor:
            return ''
        
        nombre = asesor.get('nombre', '')
        apellido_p = asesor.get('apellidoP', '')
        apellido_m = asesor.get('apellidoM', '')
        
        partes = [p for p in [nombre, apellido_p, apellido_m] if p]
        return ' '.join(partes)
    
    def _timestamp_to_datetime(self, timestamp_ms: int) -> datetime:
        """
        Convierte timestamp en milisegundos a datetime
        
        Args:
            timestamp_ms: Timestamp en milisegundos
            
        Returns:
            datetime object
        """
        if not timestamp_ms:
            return None
        return datetime.fromtimestamp(timestamp_ms / 1000.0)
    
    def convert_to_dataframe(self, entrevistas: List[dict]) -> pd.DataFrame:
        """
        Convierte lista de entrevistas de la API a DataFrame
        
        Args:
            entrevistas: Lista de diccionarios desde la API
            
        Returns:
            DataFrame con columnas: Clave, Asesor, Contactos, Estatus, Resultado, 
                                   Estrellas, LADA, ESTADO, PLAZA, Fecha
        """
        rows = []
        
        for entrevista in entrevistas:
            # Extraer datos básicos
            clave = entrevista.get('key', '')
            
            # Asesor
            asesor_dict = entrevista.get('asesor', {})
            asesor = self._extract_asesor_nombre(asesor_dict)
            
            # Contactos (teléfono)
            prospect = entrevista.get('prospect', {})
            contactos = self._extract_telefono(prospect)
            
            # Estatus
            status_dict = entrevista.get('status', {})
            estatus = status_dict.get('nombre', '') if status_dict else ''
            
            # Resultado
            resultado = entrevista.get('result', '')
            
            # Estrellas
            stars_str = entrevista.get('stars', '0')
            try:
                estrellas = float(stars_str) if stars_str else 0.0
            except:
                estrellas = 0.0
            
            # Fecha de creación
            created_date_ms = entrevista.get('createdDate')
            fecha = self._timestamp_to_datetime(created_date_ms)
            
            # LADA, ESTADO, PLAZA se dejan vacíos - el sistema los asignará
            row = {
                'Clave': clave,
                'Asesor': asesor,
                'Contactos': contactos,
                'Estatus': estatus,
                'Resultado': resultado,
                'Estrellas': estrellas,
                'LADA': '',  # Se asignará por phone_extractor
                'ESTADO': '',  # Se asignará por lada_matcher
                'PLAZA': '',  # Se asignará por plaza_matcher
                'Fecha': fecha
            }
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Asegurar tipos correctos
        df['Clave'] = df['Clave'].astype(str)
        df['Asesor'] = df['Asesor'].astype(str)
        df['Contactos'] = df['Contactos'].astype(str)
        df['Estatus'] = df['Estatus'].astype(str)
        df['Resultado'] = df['Resultado'].astype(str)
        df['Estrellas'] = pd.to_numeric(df['Estrellas'], errors='coerce')
        df['LADA'] = df['LADA'].astype(str)
        df['ESTADO'] = df['ESTADO'].astype(str)
        df['PLAZA'] = df['PLAZA'].astype(str)
        
        return df
    
    def save_to_excel(self, df: pd.DataFrame, output_path: Path):
        """
        Guarda DataFrame a Excel con formato correcto
        
        Args:
            df: DataFrame con los datos
            output_path: Ruta del archivo Excel de salida
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='data', index=False)
        
        print(f"✓ Excel guardado: {output_path}")
        print(f"  Filas: {len(df)}")
        print(f"  Columnas: {list(df.columns)}")

if __name__ == '__main__':
    # Test de conversión con los datos de prueba
    import json
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from api_client import NauphilusAPIClient, load_credentials
    from datetime import datetime
    
    print("=" * 80)
    print("TEST: Conversión JSON → Excel")
    print("=" * 80)
    
    # Cargar configuración
    config = load_credentials()
    client = NauphilusAPIClient(config)
    
    # Descargar 1 día de agosto para test
    print("\n1. Descargando 1 día de agosto...")
    fecha_inicio = datetime(2026, 8, 1, 0, 0, 0)
    fecha_fin = datetime(2026, 8, 1, 23, 59, 59)
    entrevistas = client.fetch_entrevistas(fecha_inicio, fecha_fin)
    print(f"   ✓ {len(entrevistas)} registros descargados")
    
    # Convertir a DataFrame
    print("\n2. Convirtiendo a DataFrame...")
    converter = JSONToExcelConverter()
    df = converter.convert_to_dataframe(entrevistas)
    print(f"   ✓ DataFrame creado: {len(df)} filas x {len(df.columns)} columnas")
    
    # Mostrar muestra
    print("\n3. Muestra de datos:")
    print(df.head(3).to_string())
    
    # Guardar Excel de prueba
    output_path = Path('data/cache/test_converted_1dia_agosto.xlsx')
    print(f"\n4. Guardando a Excel...")
    converter.save_to_excel(df, output_path)
    
    print("\n" + "=" * 80)
    print("✓ Test completado")
    print("=" * 80)