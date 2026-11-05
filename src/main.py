"""
Script principal - Orquesta el proceso completo de facturación
"""
import pandas as pd
from datetime import datetime
from pathlib import Path
from config import Config
from excel_loader import ExcelLoader
from resolver import ContactoDigitalResolver
from reports import ReportGenerator

def process_excel(config: Config, excel_path: str) -> str:
    """
    Procesa un Excel con el sistema LADA completo
    
    Args:
        config: Objeto de configuración
        excel_path: Ruta al Excel de entrada
        
    Returns:
        Ruta al Excel procesado generado
    """
    print("=" * 60)
    print("SISTEMA DE FACTURACIÓN AUTOMATIZADA - FARMACIAS")
    print("=" * 60)
    print(f"✓ Excel de entrada: {excel_path}")
    
    # 2. Cargar datos
    loader = ExcelLoader(config.input_excel_path)
    df_data, df_ladas, plazas_activas = loader.load_all()
    
    # 2.5. Filtrar por mes objetivo (excluir registros de otros meses)
    print("\n" + "=" * 60)
    print("FILTRADO POR MES")
    print("=" * 60)
    
    # Detectar si hay columnas Año/Mes (de descarga automática)
    if 'Año' in df_data.columns and 'Mes' in df_data.columns:
        # Contar registros por mes
        df_con_mes = df_data[df_data['Mes'].notna()]
        
        if len(df_con_mes) > 0:
            month_counts = df_con_mes['Mes'].value_counts().sort_index()
            print("Distribución de registros por mes:")
            for mes, count in month_counts.items():
                print(f"  Mes {int(mes):02d}: {count} registros")
            
            # Mes objetivo = mes con más registros
            target_month = month_counts.idxmax()
            target_year = df_con_mes[df_con_mes['Mes'] == target_month]['Año'].mode()[0]
            
            print(f"\n✓ Mes objetivo detectado: {int(target_year)}-{int(target_month):02d}")
            
            # Filtrar registros de otros meses
            mask_mes_correcto = (df_data['Año'] == target_year) & (df_data['Mes'] == target_month)
            df_otros_meses = df_data[~mask_mes_correcto & df_data['Mes'].notna()]
            
            if len(df_otros_meses) > 0:
                print(f"\n⚠️  Excluyendo {len(df_otros_meses)} registros de otros meses:")
                otros_meses_counts = df_otros_meses.groupby(['Año', 'Mes']).size()
                for (anio, mes), count in otros_meses_counts.items():
                    print(f"   - {int(anio)}-{int(mes):02d}: {count} registros")
                
                # Filtrar
                df_data = df_data[mask_mes_correcto | df_data['Mes'].isna()]
                print(f"✓ Dataset filtrado: {len(df_data)} registros del mes objetivo")
            else:
                print("✓ No hay registros de otros meses - dataset limpio")
        else:
            print("⚠️  No se detectaron fechas válidas - procesando todos los registros")
    else:
        print("ℹ️  Columnas Año/Mes no encontradas - asumiendo dataset manual (sin filtrado)")
    
    # 3. Diagnóstico inicial
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO INICIAL")
    print("=" * 60)
    diag = loader.get_diagnostico()
    print(f"Total filas: {len(df_data)}")
    print(f"Estatus únicos: {diag['estatus_unicos']}")
    print(f"Asesor 'CONTACTO DIGITAL ' (tolera espacios): {df_data['Asesor'].apply(ContactoDigitalResolver._is_contacto_digital).sum()}")
    print(f"Estrellas rango: {diag['estrellas_min']:.0f} - {diag['estrellas_max']:.0f}")
    
    # 4. Resolver CONTACTO DIGITAL (usa catálogo limpio automáticamente)
    print("\n" + "=" * 60)
    print("RESOLVIENDO CONTACTO DIGITAL")
    print("=" * 60)
    resolver = ContactoDigitalResolver(config, plazas_activas, df_ladas)
    df_resolved = resolver.resolve_all(df_data.copy())
    
    # 5. Validar coincidencia de ladas
    print("\n" + "=" * 60)
    print("VALIDACIÓN LADA")
    print("=" * 60)
    mask_cd = df_resolved['Asesor'].apply(ContactoDigitalResolver._is_contacto_digital)
    cd_resolved = df_resolved[mask_cd]
    mask_both = cd_resolved['lada_calculada'].notna() & cd_resolved['LADA'].notna()
    comparables = cd_resolved[mask_both]
    
    if len(comparables) > 0:
        matches = (comparables['lada_calculada'].astype(str) == comparables['LADA'].astype(str)).sum()
        pct_lada = 100 * matches / len(comparables)
        print(f"Coincidencia LADA: {matches}/{len(comparables)} ({pct_lada:.1f}%)")
        
        if pct_lada < config.get('validaciones.min_coincidencia_lada_percent', 95):
            print(f"⚠ Advertencia: Coincidencia por debajo del {config.get('validaciones.min_coincidencia_lada_percent')}% esperado")
    
    # 6. Generar reportes
    print("\n" + "=" * 60)
    print("GENERANDO REPORTES")
    print("=" * 60)
    generator = ReportGenerator(config)
    
    df_evaluadas = generator.generate_evaluadas(df_resolved)
    df_activas = generator.generate_activas(df_resolved)
    df_detalle = generator.generate_detalle_facturacion(df_evaluadas, df_activas)
    df_revision = generator.generate_revision_manual(df_resolved)
    df_auditoria = generator.generate_auditoria_matching(df_resolved)
    
    total_eval = df_evaluadas[df_evaluadas['plaza_calculada']=='Total general']['EVALUADAS'].values[0]
    total_act_alto = df_activas[df_activas['plaza_calculada']=='Total general']['ACTIVAS >35★'].values[0]
    total_act_medio = df_activas[df_activas['plaza_calculada']=='Total general']['ACTIVAS <35★'].values[0]
    total_act_sin = df_activas[df_activas['plaza_calculada']=='Total general']['ACTIVAS 0★'].values[0]
    total_act = df_activas[df_activas['plaza_calculada']=='Total general']['ACTIVAS_TOTAL'].values[0]
    sin_match_json = df_auditoria[df_auditoria['match_json'] == 'No (revisar)']['filas'].sum() if len(df_auditoria) > 0 else 0
    
    print(f"✓ Evaluadas: {total_eval}")
    print(f"✓ Activas: {total_act}")
    print(f"  - ACTIVAS >35★: {total_act_alto}")
    print(f"  - ACTIVAS <35★: {total_act_medio}")
    print(f"  - ACTIVAS 0★: {total_act_sin}")
    print(f"✓ Casos para revisión: {len(df_revision)}")
    print(f"✓ Asesores auditados: {len(df_auditoria)} ({sin_match_json} filas sin match JSON)")
    
    # 7. Validar totales esperados
    print("\n" + "=" * 60)
    print("VALIDACIÓN TOTALES")
    print("=" * 60)
    esperado_eval = config.get('validaciones.totales_esperados.evaluadas')
    esperado_act = config.get('validaciones.totales_esperados.activas')
    
    eval_ok = (total_eval == esperado_eval)
    act_ok = (total_act == esperado_act)
    
    status_eval = "✓" if eval_ok else "✗"
    status_act = "✓" if act_ok else "✗"
    
    print(f"{status_eval} Evaluadas: {total_eval} {'==' if eval_ok else '!='} {esperado_eval} (esperado)")
    print(f"{status_act} Activas: {total_act} {'==' if act_ok else '!='} {esperado_act} (esperado)")
    
    if not (eval_ok and act_ok):
        print("\n⚠ Advertencia: Los totales no cuadran con los esperados")
    
    # 8. Exportar Excel
    print("\n" + "=" * 60)
    print("EXPORTANDO RESULTADOS")
    print("=" * 60)
    
    # Crear directorio de salida
    output_dir = config.base_path / 'data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Nombre del archivo con fecha
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f'facturacion_procesada_{fecha}.xlsx'
    
    # Escribir Excel con múltiples hojas
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Data enriquecida
        df_resolved.to_excel(writer, sheet_name='Data Enriquecida', index=False)
        
        # Evaluadas
        df_evaluadas.to_excel(writer, sheet_name='Evaluadas', index=False)
        
        # Activas
        df_activas.to_excel(writer, sheet_name='Activas', index=False)
        
        # Detalle de facturación
        df_detalle.to_excel(writer, sheet_name='Detalle Facturacion', index=False)
        
        # Revisión manual
        if len(df_revision) > 0:
            df_revision.to_excel(writer, sheet_name='Revision Manual', index=False)
        
        # Auditoría de matching (plazas directas vs JSON)
        if len(df_auditoria) > 0:
            df_auditoria.to_excel(writer, sheet_name='Auditoria Matching', index=False)
        
        # Diagnóstico
        diag_data = {
            'Métrica': [
                'Total filas',
                'CONTACTO DIGITAL',
                'Resueltas',
                'Evaluadas total',
                'Activas total',
                'Coincidencia LADA %',
                'Casos revisión manual'
            ],
            'Valor': [
                len(df_data),
                df_data['Asesor'].apply(ContactoDigitalResolver._is_contacto_digital).sum(),
                (df_resolved['metodo_asignacion'] == 'directo_estado').sum(),
                total_eval,
                total_act,
                f"{pct_lada:.1f}%" if len(comparables) > 0 else 'N/A',
                len(df_revision)
            ]
        }
        pd.DataFrame(diag_data).to_excel(writer, sheet_name='Diagnostico', index=False)
    
    print(f"✓ Excel exportado: {output_path}")
    
    # Agregar hoja dinámica con fórmulas
    print("\nAgregando hoja con fórmulas dinámicas...")
    try:
        from dynamic_reports import add_dynamic_reports_to_excel
        add_dynamic_reports_to_excel(output_path)
    except Exception as e:
        print(f"⚠ No se pudo agregar hoja dinámica: {e}")
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)
    
    return str(output_path)

def main():
    """Punto de entrada CLI - Parsea argumentos y llama a process_excel()"""
    import argparse
    import sys
    
    # Parsear argumentos CLI
    parser = argparse.ArgumentParser(description='Pipeline de facturación mensual - Farmacias')
    parser.add_argument('--input', type=str, help='Ruta del Excel de entrada (ej: data/input/FACTURACIONES_2.xlsx). Si no se provee, usa config.yaml')
    args = parser.parse_args()
    
    # Cargar configuración
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    config = Config(str(project_root))
    
    # Si se provee --input, sobreescribir la ruta del Excel de entrada
    if args.input:
        config.set_input_excel(args.input)
    
    # Procesar Excel
    return process_excel(config, config.input_excel_path)

if __name__ == '__main__':
    try:
        output_path = main()
        print(f"\n✓ Archivo generado exitosamente: {output_path}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
