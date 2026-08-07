"""
Módulo de matching de LADA - Cruza ladas contra el catálogo y obtiene el estado
"""
import pandas as pd
from typing import Optional, Tuple

class LadaMatcher:
    """Matcher de ladas contra catálogo para obtener estado"""

    def __init__(self, df_ladas: pd.DataFrame = None, catalogo_overrides_path: str = None):
        """
        Inicializa el matcher con el catálogo completo del Excel y los overrides limpios.

        El catálogo base (pestaña Ladas del Excel, ~4477 filas) contiene todas las ladas.
        El CSV de overrides (catálogo limpio) resuelve las ladas conflictivas con una
        decisión documentada (GT Ariadne, IFT, frecuencia real, etc.). Los overrides
        tienen prioridad sobre el catálogo base.

        Args:
            df_ladas: DataFrame del catálogo base (Excel, ~4477 filas).
                      Si None, se carga desde el Excel de entrada.
            catalogo_overrides_path: Ruta al CSV de overrides (catálogo limpio).
                                     Si None, usa config/catalogo_ladas_limpio.csv
        """
        from pathlib import Path

        # 1. Cargar catálogo BASE desde el Excel (todas las ladas, 2 y 3 dígitos)
        if df_ladas is None:
            excel_path = Path(__file__).parent.parent / 'data' / 'input' / 'FACTURACIONEX.xlsx'
            df_ladas = pd.read_excel(excel_path, sheet_name='Ladas')

        # Catálogo base: lada → lista de estados (múltiples filas por lada)
        self.lada_to_estados_base = {}
        for _, row in df_ladas.iterrows():
            lada = str(row['LADA']).strip() if pd.notna(row['LADA']) else None
            estado = str(row['Estado']).strip() if pd.notna(row['Estado']) else None

            if lada and estado:
                self.lada_to_estados_base.setdefault(lada, []).append(estado)

        # 2. Cargar OVERRIDES del catálogo limpio (ladas conflictivas resueltas)
        if catalogo_overrides_path is None:
            catalogo_overrides_path = Path(__file__).parent.parent / 'config' / 'catalogo_ladas_limpio.csv'

        df_overrides = None
        if Path(catalogo_overrides_path).exists():
            df_overrides = pd.read_csv(catalogo_overrides_path)

        # 3. Diccionario final: lada → (estado, fuente)
        self.lada_to_estado = {}
        self.lada_to_fuente = {}

        # Prioridad 1: overrides resueltos (decisiones documentadas)
        overrides_aplicados = 0
        if df_overrides is not None:
            for _, row in df_overrides.iterrows():
                lada = str(int(row['lada'])).strip()
                estado = str(row['estado']).strip()
                fuente = str(row['fuente']).strip()
                self.lada_to_estado[lada] = estado
                self.lada_to_fuente[lada] = fuente
                overrides_aplicados += 1

        # Prioridad 2: resto del catálogo base sin conflicto (primer estado)
        base_sin_conflicto = 0
        for lada, estados in self.lada_to_estados_base.items():
            if lada not in self.lada_to_estado:
                self.lada_to_estado[lada] = estados[0]
                self.lada_to_fuente[lada] = 'catalogo_base'
                base_sin_conflicto += 1

        print(f"✓ LadaMatcher inicializado con {len(self.lada_to_estado)} ladas")
        print(f"  - Catálogo base (sin conflicto): {base_sin_conflicto}")
        print(f"  - Overrides aplicados (conflictivas): {overrides_aplicados}")

        # Reporte de fuentes
        fuentes = {}
        for f in self.lada_to_fuente.values():
            fuentes[f] = fuentes.get(f, 0) + 1
        print(f"  Distribución fuentes: {dict(sorted(fuentes.items(), key=lambda x: -x[1]))}")

    def match_lada(self, lada_2: str, lada_3: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Intenta matchear la lada contra el catálogo.

        Args:
            lada_2: Lada de 2 dígitos
            lada_3: Lada de 3 dígitos

        Returns:
            (lada_matched, estado) o (None, None) si no hay match
        """
        # Probar primero lada de 2 dígitos
        if lada_2 in self.lada_to_estado:
            return lada_2, self.lada_to_estado[lada_2]

        # Si no, probar lada de 3 dígitos
        if lada_3 in self.lada_to_estado:
            return lada_3, self.lada_to_estado[lada_3]

        # No hay match
        return None, None

    def get_estado(self, lada: str) -> Optional[str]:
        """Obtiene el estado de una lada específica"""
        return self.lada_to_estado.get(lada)


if __name__ == '__main__':
    # Test con datos reales
    from config import Config
    from excel_loader import ExcelLoader
    from phone_extractor import PhoneExtractor

    config = Config('..')
    loader = ExcelLoader(config.input_excel_path)
    df_data, df_ladas, plazas = loader.load_all()

    matcher = LadaMatcher(df_ladas)  # Catálogo base + overrides
    extractor = PhoneExtractor()

    # Probar con filas de CONTACTO DIGITAL
    cd_rows = df_data[df_data['Asesor'] == 'CONTACTO DIGITAL '].head(10)

    print("\n=== TEST LADA MATCHER ===\n")
    coincidencias = 0
    for idx, row in cd_rows.iterrows():
        phone = extractor.extract_phone(row['Contactos'])
        if phone:
            lada_2, lada_3 = extractor.extract_lada(phone)
            lada_matched, estado = matcher.match_lada(lada_2, lada_3)

            # Comparar con LADA precalculada
            lada_precalc = str(row['LADA']).strip() if pd.notna(row['LADA']) else None
            estado_precalc = str(row['ESTADO']).strip() if pd.notna(row['ESTADO']) else None

            match_lada = (lada_matched == lada_precalc)
            match_estado = (estado == estado_precalc)

            if match_lada:
                coincidencias += 1

            status = "✓" if (match_lada and match_estado) else "✗"
            print(f"{status} Tel: {phone} → Lada: {lada_matched} Estado: {estado}")
            print(f"   Esperado: Lada: {lada_precalc} Estado: {estado_precalc}")
            print()

    print(f"Coincidencias lada: {coincidencias}/{len(cd_rows)}")