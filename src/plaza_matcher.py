"""
Módulo de asignación de plazas - Asigna plaza a partir del estado
"""
from typing import Optional, Tuple
from config import Config

class PlazaMatcher:
    """Asigna plaza a partir del estado usando el mapeo configurado"""
    
    def __init__(self, config: Config, plazas_activas: list):
        """
        Inicializa el matcher
        
        Args:
            config: Objeto de configuración
            plazas_activas: Lista de plazas activas del mes
        """
        self.config = config
        self.plazas_activas = set(plazas_activas)
        self.fallback_extranjero = config.fallback_extranjero
        self.no_identificado = config.no_identificado_label
        
        print(f"✓ PlazaMatcher inicializado con {len(self.plazas_activas)} plazas activas")
    
    def assign_plaza(self, estado: Optional[str]) -> Tuple[Optional[str], str]:
        """
        Asigna plaza a partir del estado
        
        Args:
            estado: Estado obtenido del catálogo de ladas
            
        Returns:
            (plaza, metodo) donde metodo puede ser:
            - 'directo_estado': Plaza asignada directamente del estado
            - 'fallback_extranjero': Número extranjero, plaza del norte
            - 'no_identificado': No se pudo identificar lada
            - 'plaza_cercana': Plaza geográficamente cercana (TODO: geocoding)
        """
        # Caso 1: No hay estado (no se identificó lada)
        if not estado:
            return self.no_identificado, 'no_identificado'
        
        # Caso 2: Buscar plaza directa del estado en el mapeo
        plaza = self.config.get_estado_to_plaza(estado)
        
        if plaza:
            # Verificar si la plaza está activa este mes
            if plaza in self.plazas_activas:
                return plaza, 'directo_estado'
            else:
                # La plaza del estado no está activa, buscar cercana
                # TODO: Implementar geocoding para plaza cercana
                # Por ahora, retornar la plaza del mapeo aunque no esté activa
                return plaza, 'directo_estado_inactiva'
        
        # Caso 3: Estado no tiene plaza en el mapeo
        # TODO: Implementar búsqueda de plaza cercana por geocoding
        # Por ahora, retornar fallback para estados sin mapeo
        return self.fallback_extranjero, 'estado_sin_mapeo'
    
    def assign_plaza_extranjero(self) -> Tuple[str, str]:
        """Asigna la plaza por defecto para números extranjeros"""
        return self.fallback_extranjero, 'fallback_extranjero'

if __name__ == '__main__':
    # Test con datos reales
    import pandas as pd
    from excel_loader import ExcelLoader
    from phone_extractor import PhoneExtractor
    from lada_matcher import LadaMatcher
    
    config = Config('..')
    loader = ExcelLoader(config.input_excel_path)
    df_data, df_ladas, plazas = loader.load_all()
    
    matcher_lada = LadaMatcher(df_ladas)
    matcher_plaza = PlazaMatcher(config, plazas)
    extractor = PhoneExtractor()
    
    # Probar con filas de CONTACTO DIGITAL
    cd_rows = df_data[df_data['Asesor'] == 'CONTACTO DIGITAL '].head(20)
    
    print("\n=== TEST PLAZA MATCHER ===\n")
    coincidencias = 0
    for idx, row in cd_rows.iterrows():
        phone = extractor.extract_phone(row['Contactos'])
        if phone:
            lada_2, lada_3 = extractor.extract_lada(phone)
            lada_matched, estado = matcher_lada.match_lada(lada_2, lada_3)
            plaza, metodo = matcher_plaza.assign_plaza(estado)
            
            # Comparar con PLAZA precalculada
            plaza_precalc = str(row['PLAZA']).strip() if pd.notna(row['PLAZA']) else None
            
            match = (plaza == plaza_precalc)
            if match:
                coincidencias += 1
            
            status = "✓" if match else "✗"
            print(f"{status} Estado: {estado:30} → Plaza: {plaza}")
            print(f"   Método: {metodo} | Esperado: {plaza_precalc}")
            print()
    
    print(f"Coincidencias plaza: {coincidencias}/{len(cd_rows)}")
