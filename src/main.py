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

def main():
    """Proceso principal de facturación"""
    import argparse
    
    # Parsear argumentos CLI
    parser = argparse.ArgumentParser(description='Pipeline de facturación mensual - Farmacias')
    parser.add_argument('--input', type=str, help='Ruta del Excel de entrada (ej: data/input/FACTURACIONES_2.xlsx). Si no se provee, usa config.yaml')
    args = parser.parse_args()
    
    print("=" * 60)
    print("SISTEMA DE FACTURACIÓN AUTOMATIZADA - FARMACIAS")
    print("=" * 60)
    
    # 1. Cargar configuración (usar directorio del proyecto, no src/)
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    config = Config(str(project_root))
    
    # Si se provee --input, sobreescribir la ruta del Excel de entrada
    if args.input:
        config.set_input_excel(args.input)
        print(f"✓ Excel de entrada (CLI): {config.input_excel_path}")
    else:
        print(f"✓ Excel de entrada (config.yaml): {config.input_excel_path}")
    
    # 2. Cargar datos
    loader = ExcelLoader(config.input_excel_path)
    df_data, df_ladas, plazas_activas = loader.load_all()
    
    # 3. Diagnóstico inicial
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO INICIAL")
    print("=" * 60)
    diag = loader.get_diagnostico()
    print(f"Total filas: {diag['total_filas']}")
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
    total_act = df_activas[df_activas['plaza_calculada']=='Total general']['ACTIVAS'].values[0]
    sin_match_json = df_auditoria[df_auditoria['match_json'] == 'No (revisar)']['filas'].sum() if len(df_auditoria) > 0 else 0
    
    print(f"✓ Evaluadas: {total_eval}")
    print(f"✓ Activas: {total_act}")
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
    output_dir = project_root / 'data' / 'output'
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
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)
    
    return output_path

if __name__ == '__main__':
    try:
        output_path = main()
        print(f"\n✓ Archivo generado exitosamente: {output_path}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()