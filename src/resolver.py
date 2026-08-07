"""
Módulo resolver - Orquesta el proceso completo de resolución de CONTACTO DIGITAL
y validación de plazas directas contra el backoffice.
"""
import pandas as pd
from typing import Dict, List
from config import Config
from phone_extractor import PhoneExtractor
from lada_matcher import LadaMatcher
from plaza_matcher import PlazaMatcher
from active_plazas import get_active_plazas_loader
from asesor_normalizer import get_asesor_normalizer

class ContactoDigitalResolver:
    """Resuelve las filas de CONTACTO DIGITAL a plazas"""
    
    def __init__(self, config: Config, plazas_activas: list, df_ladas: pd.DataFrame = None):
        """
        Inicializa el resolver
        
        Args:
            config: Objeto de configuración
            plazas_activas: Lista de plazas activas
            df_ladas: DataFrame del catálogo base (opcional). Si None, se carga solo.
        """
        self.config = config
        self.phone_extractor = PhoneExtractor()
        self.lada_matcher = LadaMatcher(df_ladas)  # Catálogo base + overrides limpios
        self.plaza_matcher = PlazaMatcher(config, plazas_activas)
        
        # Cargar validadores de plazas activas y normalizador
        self.active_plazas_loader = get_active_plazas_loader()
        self.active_plazas_loader.load()
        self.asesor_normalizer = get_asesor_normalizer()
        self.asesor_normalizer.load()
        
        print("✓ ContactoDigitalResolver inicializado")
        print(f"  Plazas activas en JSON: {len(self.active_plazas_loader.get_plazas_activas())}")
    
    def resolve_row(self, contactos: str) -> Dict[str, any]:
        """
        Resuelve una fila de CONTACTO DIGITAL
        
        Args:
            contactos: Campo Contactos de la fila
            
        Returns:
            Dict con: telefono, lada, estado, plaza, metodo_asignacion
        """
        result = {
            'telefono_calculado': None,
            'lada_calculada': None,
            'estado_calculado': None,
            'plaza_calculada': None,
            'metodo_asignacion': 'no_identificado'
        }
        
        # 1. Extraer teléfono
        phone = self.phone_extractor.extract_phone(contactos)
        if not phone:
            return result
        
        result['telefono_calculado'] = phone
        
        # 2. Extraer lada y matchear estado
        lada_2, lada_3 = self.phone_extractor.extract_lada(phone)
        lada_matched, estado = self.lada_matcher.match_lada(lada_2, lada_3)
        
        if not lada_matched:
            # No se identificó la lada
            return result
        
        result['lada_calculada'] = lada_matched
        result['estado_calculado'] = estado
        
        # 3. Asignar plaza
        plaza, metodo = self.plaza_matcher.assign_plaza(estado)
        result['plaza_calculada'] = plaza
        result['metodo_asignacion'] = metodo
        
        return result
    
    @staticmethod
    def _is_contacto_digital(asesor) -> bool:
        """Detecta filas de CONTACTO DIGITAL tolerando espacios y mayúsculas."""
        return str(asesor).strip().upper() == 'CONTACTO DIGITAL'

    def resolve_all(self, df_data: pd.DataFrame) -> pd.DataFrame:
        """
        Resuelve todas las filas de CONTACTO DIGITAL en el DataFrame
        
        Args:
            df_data: DataFrame completo
            
        Returns:
            DataFrame con columnas adicionales de resolución
        """
        print("\nResolviendo CONTACTO DIGITAL...")
        
        # Identificar filas de CONTACTO DIGITAL (tolerando espacios/mayúsculas)
        mask_cd = df_data['Asesor'].apply(self._is_contacto_digital)
        cd_count = mask_cd.sum()
        
        print(f"  Filas CONTACTO DIGITAL: {cd_count}")
        
        # Crear columnas nuevas
        df_data['telefono_calculado'] = None
        df_data['lada_calculada'] = None
        df_data['estado_calculado'] = None
        df_data['plaza_calculada'] = None
        df_data['metodo_asignacion'] = None
        
        # Resolver cada fila de CONTACTO DIGITAL
        resolved = 0
        for idx in df_data[mask_cd].index:
            contactos = df_data.at[idx, 'Contactos']
            result = self.resolve_row(contactos)
            
            df_data.at[idx, 'telefono_calculado'] = result['telefono_calculado']
            df_data.at[idx, 'lada_calculada'] = result['lada_calculada']
            df_data.at[idx, 'estado_calculado'] = result['estado_calculado']
            df_data.at[idx, 'plaza_calculada'] = result['plaza_calculada']
            df_data.at[idx, 'metodo_asignacion'] = result['metodo_asignacion']
            
            if result['plaza_calculada'] and result['plaza_calculada'] != self.config.no_identificado_label:
                resolved += 1
        
        print(f"  Resueltas: {resolved}/{cd_count} ({100*resolved/cd_count:.1f}%)")
        
        # Para filas normales, validar contra JSON y clasificar
        mask_normal = ~mask_cd
        print(f"\n  Validando {mask_normal.sum()} plazas directas contra JSON...")
        
        for idx in df_data[mask_normal].index:
            asesor = df_data.at[idx, 'Asesor']
            asesor_norm = self.asesor_normalizer.normalize(asesor)
            
            # Clasificar método de asignación
            if asesor_norm == '__SISTEMA__':
                # Rol de sistema (WIDGET NAUPHILUS) - no facturable
                df_data.at[idx, 'plaza_calculada'] = asesor
                df_data.at[idx, 'metodo_asignacion'] = 'rol_sistema'
            elif self.active_plazas_loader.is_plaza_activa(asesor_norm):
                # Plaza directa con rol activo en JSON
                df_data.at[idx, 'plaza_calculada'] = asesor
                df_data.at[idx, 'metodo_asignacion'] = 'plaza_directa_activa'
            else:
                # Plaza directa SIN rol en JSON - revisar (pero cuenta en totales)
                df_data.at[idx, 'plaza_calculada'] = asesor
                df_data.at[idx, 'metodo_asignacion'] = 'plaza_directa_sin_rol_json'
        
        # Reporte de clasificación
        metodos = df_data['metodo_asignacion'].value_counts()
        print(f"\n  Clasificación de filas:")
        for metodo, count in metodos.items():
            print(f"    {metodo}: {count}")
        
        return df_data

if __name__ == '__main__':
    # Test
    from excel_loader import ExcelLoader
    
    config = Config('..')
    loader = ExcelLoader(config.input_excel_path)
    df_data, df_ladas, plazas = loader.load_all()
    
    resolver = ContactoDigitalResolver(config, plazas, df_ladas)
    df_resolved = resolver.resolve_all(df_data.copy())
    
    print("\n=== VALIDACIÓN ===")
    
    # Comparar lada_calculada vs LADA precalculada
    mask_cd = df_resolved['Asesor'].apply(ContactoDigitalResolver._is_contacto_digital)
    cd_resolved = df_resolved[mask_cd]
    
    # Solo donde ambas existen
    mask_both = cd_resolved['lada_calculada'].notna() & cd_resolved['LADA'].notna()
    comparables = cd_resolved[mask_both]
    
    if len(comparables) > 0:
        matches = (comparables['lada_calculada'].astype(str) == comparables['LADA'].astype(str)).sum()
        pct = 100 * matches / len(comparables)
        print(f"Coincidencia LADA: {matches}/{len(comparables)} ({pct:.1f}%)")
    
    # Mostrar distribución de métodos
    print("\nMétodos de asignación:")
    print(df_resolved['metodo_asignacion'].value_counts())