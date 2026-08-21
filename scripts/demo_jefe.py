#!/usr/bin/env python3
"""
Demo en vivo para jefatura — Procesa julio y agosto mostrando el problema resuelto
Sin argumentos, un solo comando: python3 scripts/demo_jefe.py
"""
import sys
from pathlib import Path

# Agregar src/ al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

import pandas as pd
from config import Config
from excel_loader import ExcelLoader
from resolver import ContactoDigitalResolver
from reports import ReportGenerator

def separador(titulo="", ancho=80):
    """Imprime separador visual"""
    if titulo:
        pad = (ancho - len(titulo) - 2) // 2
        print("\n" + "=" * pad + f" {titulo} " + "=" * pad)
    else:
        print("=" * ancho)

def anonimizar_nombre(contactos_raw: str) -> str:
    """Extrae y anonimiza el nombre (solo iniciales)"""
    # Contactos típico: "NOMBRE APELLIDO Telefono Fijo: 7552403032 Email: correo@gmail.com"
    partes = contactos_raw.split()
    if len(partes) >= 2:
        return f"{partes[0][0]}. {partes[1][0]}."
    return "N/A"

def procesar_mes(mes_nombre: str, excel_path: Path, config: Config, esperado_eval: int, esperado_act: int):
    """Procesa un mes y retorna estadísticas para el demo"""
    print(f"\n{'─' * 80}")
    print(f"📅 PROCESANDO: {mes_nombre}")
    print(f"   Archivo: {excel_path.name}")
    print(f"{'─' * 80}")
    
    # 1. Cargar datos
    loader = ExcelLoader(excel_path)
    df_data, _, plazas_activas = loader.load_all()
    
    # 2. Identificar CONTACTO DIGITAL
    mask_cd = df_data['Asesor'].apply(ContactoDigitalResolver._is_contacto_digital)
    total_cd = mask_cd.sum()
    
    separador("PROBLEMA DETECTADO")
    print(f"❌ {total_cd:,} filas tienen Asesor = 'CONTACTO DIGITAL'")
    print(f"   → Sin plaza asignada, no se pueden facturar directamente")
    print(f"   → Solución: inferir plaza desde el teléfono del aplicante")
    
    # 3. Resolver CONTACTO DIGITAL
    resolver = ContactoDigitalResolver(config, plazas_activas, None)
    df_resolved = resolver.resolve_all(df_data.copy())
    
    # 4. Obtener 3 ejemplos reales
    ejemplos = df_resolved[mask_cd].head(3)
    
    separador("EJEMPLOS DE RESOLUCIÓN (3 casos reales)")
    print(f"\n{'Aplicante':<15} {'Teléfono Original':<25} {'LADA':<6} {'Estado':<20} {'Plaza Asignada':<30}")
    print("─" * 110)
    
    for idx, row in ejemplos.iterrows():
        nombre = anonimizar_nombre(row['Contactos'])
        # Extraer teléfono del texto original (sin clean)
        tel_raw = row['Contactos'].split('Telefono Fijo:')[1].split()[0] if 'Telefono Fijo:' in row['Contactos'] else 'N/A'
        lada = row.get('lada_calculada', 'N/A')
        estado = row.get('estado_calculado', 'N/A')
        plaza = row.get('plaza_calculada', 'N/A')
        
        print(f"{nombre:<15} {tel_raw:<25} {lada:<6} {estado:<20} {plaza:<30}")
    
    # 5. Generar reportes
    generator = ReportGenerator(config)
    df_evaluadas = generator.generate_evaluadas(df_resolved)
    df_activas = generator.generate_activas(df_resolved)
    
    total_eval_calculado = df_evaluadas[df_evaluadas['plaza_calculada']=='Total general']['EVALUADAS'].values[0]
    total_act_calculado = df_activas[df_activas['plaza_calculada']=='Total general']['ACTIVAS'].values[0]
    
    separador("TOTALES CALCULADOS POR EL SISTEMA")
    print(f"\n{'Métrica':<30} {'Total':<10}")
    print("─" * 40)
    print(f"{'Evaluadas':<30} {total_eval_calculado:>10,}")
    print(f"{'Activas (Estrellas ≥35)':<30} {total_act_calculado:>10,}")
    
    # 6. Totales esperados (de Ariadne/Sara) pasados como parámetro
    
    separador("TOTALES REPORTADOS POR ARIADNE/SARA")
    print(f"\n{'Métrica':<30} {'Total':<10}")
    print("─" * 40)
    print(f"{'Evaluadas':<30} {esperado_eval:>10,}")
    print(f"{'Activas':<30} {esperado_act:>10,}")
    
    # 7. Comparar
    separador("VALIDACIÓN")
    eval_match = (total_eval_calculado == esperado_eval)
    act_match = (total_act_calculado == esperado_act)
    
    if eval_match and act_match:
        print("\n✅ ¡COINCIDENCIA PERFECTA!")
        print("   Los totales calculados automáticamente coinciden exactamente")
        print("   con los reportados manualmente por Ariadne/Sara.")
    else:
        print("\n⚠️  DIFERENCIAS DETECTADAS:")
        if not eval_match:
            diff_eval = total_eval_calculado - esperado_eval
            signo = "+" if diff_eval > 0 else ""
            print(f"   Evaluadas: {signo}{diff_eval} ({total_eval_calculado:,} vs {esperado_eval:,})")
        if not act_match:
            diff_act = total_act_calculado - esperado_act
            signo = "+" if diff_act > 0 else ""
            print(f"   Activas: {signo}{diff_act} ({total_act_calculado:,} vs {esperado_act:,})")
        print("\n   Nota: Diferencias menores son auditables (revisar pestaña 'Revisión Manual')")
    
    return {
        'mes': mes_nombre,
        'total_cd': total_cd,
        'total_eval': total_eval_calculado,
        'total_act': total_act_calculado,
        'esperado_eval': esperado_eval,
        'esperado_act': esperado_act,
        'match': eval_match and act_match
    }

def main():
    """Demo principal"""
    separador("DEMO EN VIVO — SISTEMA DE FACTURACIÓN AUTOMATIZADA", 80)
    print("\nCliente: Sara/FA (Farmacias)")
    print("Problema: Miles de aplicantes evaluados sin plaza asignada")
    print("Solución: Inferencia automática de plaza desde número de teléfono")
    
    config = Config(str(project_root))
    
    # Procesar julio
    julio_path = project_root / 'data' / 'input' / 'FACTURACIONEX.xlsx'
    if not julio_path.exists():
        print(f"\n❌ Error: No se encontró {julio_path}")
        return
    
    # Procesar julio con totales esperados
    config.set_input_excel(str(julio_path))
    resultado_julio = procesar_mes("JULIO 2024", julio_path, config, esperado_eval=9952, esperado_act=503)
    
    # Procesar agosto
    agosto_path = project_root / 'data' / 'input' / 'FACTURACIONES_2.xlsx'
    if not agosto_path.exists():
        print(f"\n❌ Error: No se encontró {agosto_path}")
        return
    
    # Procesar agosto con totales esperados
    config.set_input_excel(str(agosto_path))
    resultado_agosto = procesar_mes("AGOSTO 2024", agosto_path, config, esperado_eval=10535, esperado_act=559)
    
    # Resumen final
    separador("RESUMEN EJECUTIVO", 80)
    print("\n📊 Procesamiento completado:")
    print(f"   • Julio:  {resultado_julio['total_cd']:>5,} casos resueltos → {resultado_julio['total_eval']:>6,} eval / {resultado_julio['total_act']:>4,} act")
    print(f"   • Agosto: {resultado_agosto['total_cd']:>5,} casos resueltos → {resultado_agosto['total_eval']:>6,} eval / {resultado_agosto['total_act']:>4,} act")
    
    print("\n✅ VENTAJAS DEL SISTEMA:")
    print("   1. Procesa miles de entrevistas en segundos")
    print("   2. Asignación automática de plaza sin intervención manual")
    print("   3. Auditoría completa de casos dudosos para revisión")
    print("   4. Parametrizable: cambio de mes sin modificar código")
    
    separador()
    print("\n🎯 CORRIDO CONTRA 2 MESES DE DATOS REALES SIN MODIFICAR CÓDIGO")
    print("   Pipeline único, catálogos congelados, fuentes dinámicas del backoffice\n")
    separador("", 80)

if __name__ == '__main__':
    main()