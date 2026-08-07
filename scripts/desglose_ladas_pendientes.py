"""
Analiza los 48 casos pendientes de ladas conflictivas:
- Cuántos tienen filas_afectadas > 0 en este mes
- Cuántos tienen filas_afectadas == 0
- Genera tabla detallada de los >0 para decisión de Sara
"""
import pandas as pd
from pathlib import Path

def main():
    # Cargar la tabla de conflictos generada previamente
    conflictos_path = Path('data/cache/ladas_conflictivas_propuesta.csv')
    if not conflictos_path.exists():
        print(f"ERROR: {conflictos_path} no existe.")
        print("Ejecuta primero: python3 scripts/generate_tabla_conflictos_ladas.py")
        return
    
    df_conf = pd.read_csv(conflictos_path)
    
    # Filtrar solo los pendientes (sin GT ni PDF aplicable)
    pendientes = df_conf[df_conf['fuente_propuesta'] == 'pendiente_sara'].copy()
    
    print("=" * 100)
    print("DESGLOSE DE 48 CASOS PENDIENTES")
    print("=" * 100)
    print(f"\nTotal pendientes: {len(pendientes)}")
    
    # Clasificar por filas afectadas
    con_filas = pendientes[pendientes['filas_afectadas'] > 0]
    sin_filas = pendientes[pendientes['filas_afectadas'] == 0]
    
    print(f"  - Con filas afectadas > 0: {len(con_filas)}")
    print(f"  - Sin filas (filas_afectadas == 0): {len(sin_filas)}")
    
    # Los de 0 filas no afectan facturación de este mes
    print(f"\n✓ Los {len(sin_filas)} casos con 0 filas NO requieren decisión para este mes")
    print(f"  (no aparecen en los datos, dejar pendientes para futuros meses)")
    
    # Los de >0 filas requieren decisión de Sara
    if len(con_filas) > 0:
        print(f"\n⚠ Los {len(con_filas)} casos con filas > 0 REQUIEREN DECISIÓN:")
        print("\n" + "=" * 100)
        print("TABLA PARA DECISIÓN DE SARA")
        print("=" * 100)
        
        # Cargar data para mostrar plazas activas candidatas por estado
        df_data = pd.read_excel('data/input/FACTURACIONEX.xlsx', sheet_name='data')
        df_ladas_cat = pd.read_excel('data/input/FACTURACIONEX.xlsx', sheet_name='Ladas')
        
        # Plazas activas del mes (columna G del catálogo Ladas)
        plazas_activas = df_ladas_cat['PLAZAS'].dropna().unique()
        print(f"\nPlazas activas disponibles este mes: {len(plazas_activas)}")
        print(f"{sorted(plazas_activas)}\n")
        
        # Para cada lada pendiente con filas>0
        for idx, row in con_filas.iterrows():
            lada = row['lada']
            estados_conflicto = row['estados_conflicto'].split(', ')
            filas = int(row['filas_afectadas'])
            propuesta = row['estado_final']
            
            print(f"\nLADA {lada} ({filas} filas afectadas)")
            print(f"  Estados en conflicto: {', '.join(estados_conflicto)}")
            print(f"  Propuesta automática (primer estado): {propuesta}")
            
            # Buscar plazas activas candidatas para cada estado
            candidatas = {}
            for estado in estados_conflicto:
                # Buscar en catálogo qué plazas activas están asociadas a este estado
                # (asumiendo columna Estado en catálogo Ladas)
                mask_estado = df_ladas_cat['Estado'].str.strip().str.upper() == estado.strip().upper()
                plazas_estado = df_ladas_cat[mask_estado]['PLAZAS'].dropna().unique()
                plazas_estado_activas = [p for p in plazas_estado if p in plazas_activas]
                candidatas[estado] = plazas_estado_activas
            
            print(f"  Plazas activas candidatas por estado:")
            for estado, plazas in candidatas.items():
                if plazas:
                    print(f"    - {estado}: {', '.join(plazas)}")
                else:
                    print(f"    - {estado}: (ninguna plaza activa este mes)")
            
            # Mostrar muestra de filas afectadas
            mask_lada = df_data['LADA'].astype(str) == str(lada)
            muestra = df_data[mask_lada][['Clave', 'Prospecto', 'Contactos', 'ESTADO']].head(3)
            if len(muestra) > 0:
                print(f"  Muestra de filas ({len(muestra)} de {filas}):")
                for _, r in muestra.iterrows():
                    tel = r['Contactos'][:60] if pd.notna(r['Contactos']) else 'N/A'
                    print(f"    - {r['Clave']}: {tel}... → {r['ESTADO']}")
        
        print("\n" + "=" * 100)
        print(f"TOTAL A DECIDIR: {len(con_filas)} ladas")
        print("=" * 100)
        print("\nOpciones para cada lada:")
        print("  1. Usar el primer estado del catálogo (propuesta automática)")
        print("  2. Elegir otro de los estados en conflicto")
        print("  3. Dejar como 'pendiente_sara' y resolver manualmente cada caso")
        
        # Guardar tabla filtrada para revisión
        output_path = Path('data/cache/ladas_pendientes_con_filas.csv')
        con_filas.to_csv(output_path, index=False)
        print(f"\n✓ Tabla guardada en: {output_path}")
    else:
        print("\n✓ NINGUNA lada pendiente tiene filas afectadas en este mes.")
        print("  No se requiere decisión inmediata.")

if __name__ == '__main__':
    main()