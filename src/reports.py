"""
Mรณdulo de reportes - Genera las tablas de evaluadas, activas y comparaciรณn
"""
import pandas as pd
from typing import Dict, Tuple
from config import Config

class ReportGenerator:
    """Genera los reportes de facturaciรณn"""
    
    def __init__(self, config: Config):
        """
        Inicializa el generador de reportes
        
        Args:
            config: Objeto de configuraciรณn
        """
        self.config = config
        self.evaluadas_estatus = config.evaluadas_estatus
        self.activas_estatus = config.activas_estatus
        self.activas_umbral = config.activas_umbral
        
        print("โ�� ReportGenerator inicializado")
    
    def generate_evaluadas(self, df_data: pd.DataFrame) -> pd.DataFrame:
        """
        Genera reporte de entrevistas evaluadas por plaza
        
        Args:
            df_data: DataFrame con datos resueltos
            
        Returns:
            DataFrame con columnas: Plaza, Count
        """
        # Filtrar por estatus de evaluadas
        mask = df_data['Estatus'].isin(self.evaluadas_estatus)
        df_eval = df_data[mask]
        
        # Agrupar por plaza_calculada
        report = df_eval.groupby('plaza_calculada').size().reset_index(name='EVALUADAS')
        report = report.sort_values('plaza_calculada')
        
        # Agregar total
        total = pd.DataFrame([{
            'plaza_calculada': 'Total general',
            'EVALUADAS': len(df_eval)
        }])
        report = pd.concat([report, total], ignore_index=True)
        
        return report
    
    def generate_activas(self, df_data: pd.DataFrame) -> pd.DataFrame:
        """
        Genera reporte de entrevistas activas por plaza
        
        Args:
            df_data: DataFrame con datos resueltos
            
        Returns:
            DataFrame con columnas: Plaza, Count
        """
        # Filtrar por estatus activo Y estrellas >= umbral
        mask = (df_data['Estatus'] == self.activas_estatus) & \
               (df_data['Estrellas'] >= self.activas_umbral)
        df_act = df_data[mask]
        
        # Agrupar por plaza_calculada
        report = df_act.groupby('plaza_calculada').size().reset_index(name='ACTIVAS')
        report = report.sort_values('plaza_calculada')
        
        # Agregar total
        total = pd.DataFrame([{
            'plaza_calculada': 'Total general',
            'ACTIVAS': len(df_act)
        }])
        report = pd.concat([report, total], ignore_index=True)
        
        return report
    
    def generate_detalle_facturacion(self, df_evaluadas: pd.DataFrame, 
                                    df_activas: pd.DataFrame) -> pd.DataFrame:
        """
        Genera detalle de facturaciรณn combinando evaluadas y activas
        
        Args:
            df_evaluadas: Reporte de evaluadas
            df_activas: Reporte de activas
            
        Returns:
            DataFrame con evaluadas y activas por plaza
        """
        # Merge de evaluadas y activas
        report = pd.merge(
            df_evaluadas, 
            df_activas, 
            on='plaza_calculada', 
            how='outer'
        ).fillna(0)
        
        # Convertir a int
        report['EVALUADAS'] = report['EVALUADAS'].astype(int)
        report['ACTIVAS'] = report['ACTIVAS'].astype(int)
        
        # Ordenar (Total general al final)
        mask_total = report['plaza_calculada'] == 'Total general'
        report_plazas = report[~mask_total].sort_values('plaza_calculada')
        report_total = report[mask_total]
        report = pd.concat([report_plazas, report_total], ignore_index=True)
        
        return report
    
    def generate_comparacion(self, df_calculado: pd.DataFrame, 
                            df_ariadne: pd.DataFrame) -> pd.DataFrame:
        """
        Genera comparaciรณn entre lo calculado y lo reportado por Ariadne
        
        Args:
            df_calculado: Detalle de facturaciรณn calculado
            df_ariadne: Detalle de Ariadne del Excel original
            
        Returns:
            DataFrame de comparaciรณn
        """
        # Leer detalle de Ariadne del Excel (TODO: implementar lectura)
        # Por ahora retornar df_calculado con columnas adicionales
        
        comp = df_calculado.copy()
        comp['EVALUADAS_ARIADNE'] = None
        comp['ACTIVAS_ARIADNE'] = None
        comp['DIFF_EVALUADAS'] = None
        comp['DIFF_ACTIVAS'] = None
        
        return comp
    
    def generate_revision_manual(self, df_data: pd.DataFrame) -> pd.DataFrame:
        """
        Genera reporte de casos que requieren revisiรณn manual
        
        Args:
            df_data: DataFrame con datos resueltos
            
        Returns:
            DataFrame con casos dudosos
        """
        # Casos para revisar: no_identificado, estado_sin_mapeo, fallback_extranjero
        metodos_revisar = ['no_identificado', 'estado_sin_mapeo', 
                          'fallback_extranjero', 'directo_estado_inactiva']
        
        mask = df_data['metodo_asignacion'].isin(metodos_revisar)
        df_revisar = df_data[mask][[
            'Clave', 'Prospecto', 'Asesor', 'Contactos', 'Estatus',
            'telefono_calculado', 'lada_calculada', 'estado_calculado',
            'plaza_calculada', 'metodo_asignacion'
        ]].copy()
        
        return df_revisar
    
    def generate_auditoria_matching(self, df_data: pd.DataFrame) -> pd.DataFrame:
        """
        Genera reporte de auditoría de matching: plazas directas vs roles JSON.
        
        Agrupa por Asesor original, muestra su plaza normalizada, si matchea con JSON,
        y el conteo de filas. Útil para que Sara revise discrepancias.
        
        Args:
            df_data: DataFrame con datos resueltos (debe tener columna metodo_asignacion)
        
        Returns:
            DataFrame con columnas: Asesor, plaza_normalizada, match_json, metodo, filas
        """
        # Solo plazas directas (excluir CONTACTO DIGITAL y roles de sistema)
        mask = (df_data['Asesor'].apply(lambda x: str(x).strip().upper() != 'CONTACTO DIGITAL')) & \
               (df_data['metodo_asignacion'] != 'rol_sistema')
        df_directas = df_data[mask].copy()
        
        # Agrupar por Asesor y metodo_asignacion
        agg = df_directas.groupby(['Asesor', 'metodo_asignacion']).size().reset_index(name='filas')
        
        # Clasificar match_json
        agg['match_json'] = agg['metodo_asignacion'].apply(
            lambda x: 'Sí' if x == 'plaza_directa_activa' else 'No (revisar)'
        )
        
        # Reordenar columnas
        agg = agg[['Asesor', 'match_json', 'metodo_asignacion', 'filas']]
        agg = agg.sort_values(['match_json', 'Asesor'])
        
        return agg

if __name__ == '__main__':
    # Test
    from excel_loader import ExcelLoader
    from resolver import ContactoDigitalResolver
    
    config = Config('..')
    loader = ExcelLoader(config.input_excel_path)
    df_data, df_ladas, plazas = loader.load_all()
    
    resolver = ContactoDigitalResolver(config, df_ladas, plazas)
    df_resolved = resolver.resolve_all(df_data.copy())
    
    generator = ReportGenerator(config)
    
    print("\n=== GENERANDO REPORTES ===\n")
    
    df_evaluadas = generator.generate_evaluadas(df_resolved)
    print(f"Evaluadas: {len(df_evaluadas)-1} plazas")
    print(f"Total: {df_evaluadas[df_evaluadas['plaza_calculada']=='Total general']['EVALUADAS'].values[0]}")
    
    df_activas = generator.generate_activas(df_resolved)
    print(f"\nActivas: {len(df_activas)-1} plazas")
    print(f"Total: {df_activas[df_activas['plaza_calculada']=='Total general']['ACTIVAS'].values[0]}")
    
    df_detalle = generator.generate_detalle_facturacion(df_evaluadas, df_activas)
    print(f"\nDetalle facturaciรณn: {len(df_detalle)} filas")
    
    df_revision = generator.generate_revision_manual(df_resolved)
    print(f"\nCasos para revisiรณn manual: {len(df_revision)}")