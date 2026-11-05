"""
Módulo de reportes dinámicos - Genera hojas con fórmulas de Excel
que se actualizan automáticamente cuando se edita Data Enriquecida
"""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from typing import List

class DynamicReportGenerator:
    """Genera reportes con fórmulas dinámicas de Excel"""
    
    def __init__(self, excel_path: str):
        """
        Inicializa el generador con la ruta del Excel
        
        Args:
            excel_path: Ruta al archivo Excel con Data Enriquecida
        """
        self.excel_path = excel_path
        self.wb = load_workbook(excel_path)
        
    def add_dynamic_summary_tables(self):
        """
        Agrega hojas con tablas resumen dinámicas que usan fórmulas
        para actualizar automáticamente cuando se edita Data Enriquecida
        """
        # Obtener hoja Data Enriquecida para referencias
        if 'Data Enriquecida' not in self.wb.sheetnames:
            print("⚠ No se encontró hoja 'Data Enriquecida'")
            return
        
        data_sheet = self.wb['Data Enriquecida']
        
        # Encontrar columnas en Data Enriquecida
        header_row = 1
        headers = {}
        for col_idx, cell in enumerate(data_sheet[header_row], 1):
            if cell.value:
                headers[cell.value] = col_idx
        
        # Verificar que existan las columnas necesarias
        required_cols = ['plaza_calculada', 'Estatus', 'Estrellas']
        missing = [c for c in required_cols if c not in headers]
        if missing:
            print(f"⚠ Faltan columnas en Data Enriquecida: {missing}")
            return
        
        # Crear o limpiar hoja de Resumen Dinámico
        sheet_name = 'Resumen Dinámico'
        if sheet_name in self.wb.sheetnames:
            del self.wb[sheet_name]
        
        ws = self.wb.create_sheet(sheet_name)
        
        # Configurar encabezados
        ws['A1'] = 'NOTA: Esta hoja se actualiza automáticamente cuando modificas Data Enriquecida'
        ws['A2'] = 'Plaza'
        ws['B2'] = 'EVALUADO'
        ws['C2'] = 'PARAMETRICO'
        ws['D2'] = 'REVISION ASESOR'
        ws['E2'] = 'Total EVALUADAS'
        ws['F2'] = 'ACTIVAS >35★'
        ws['G2'] = 'ACTIVAS 1-35★'
        ws['H2'] = 'ACTIVAS 0★'
        ws['I2'] = 'Total ACTIVAS'
        
        # Aplicar formato a encabezados
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
            ws[f'{col}1'].font = ws[f'{col}1'].font.copy(bold=True, color='FF0000')
            ws[f'{col}2'].font = ws[f'{col}2'].font.copy(bold=True)
        
        # Obtener plazas únicas de la hoja actual Detalle Facturacion
        if 'Detalle Facturacion' in self.wb.sheetnames:
            detalle_sheet = self.wb['Detalle Facturacion']
            plazas = []
            for row in detalle_sheet.iter_rows(min_row=2, max_col=1, values_only=True):
                if row[0] and row[0] != 'Total general':
                    plazas.append(row[0])
        else:
            print("⚠ No se encontró hoja 'Detalle Facturacion' para obtener plazas")
            return
        
        # Agregar fórmulas para cada plaza
        plaza_col = get_column_letter(headers['plaza_calculada'])
        estatus_col = get_column_letter(headers['Estatus'])
        estrellas_col = get_column_letter(headers['Estrellas'])
        
        row_num = 3
        for plaza in plazas:
            # Escapar comillas en nombre de plaza para la fórmula
            plaza_escaped = plaza.replace('"', '""')
            
            # Plaza
            ws[f'A{row_num}'] = plaza
            
            # EVALUADO
            formula = f'=COUNTIFS(\'Data Enriquecida\'!${plaza_col}:${plaza_col},"{plaza_escaped}",\'Data Enriquecida\'!${estatus_col}:${estatus_col},"EVALUADO")'
            ws[f'B{row_num}'] = formula
            
            # PARAMETRICO
            formula = f'=COUNTIFS(\'Data Enriquecida\'!${plaza_col}:${plaza_col},"{plaza_escaped}",\'Data Enriquecida\'!${estatus_col}:${estatus_col},"PARAMETRICO")'
            ws[f'C{row_num}'] = formula
            
            # REVISION ASESOR
            formula = f'=COUNTIFS(\'Data Enriquecida\'!${plaza_col}:${plaza_col},"{plaza_escaped}",\'Data Enriquecida\'!${estatus_col}:${estatus_col},"REVISION ASESOR")'
            ws[f'D{row_num}'] = formula
            
            # Total EVALUADAS (suma de las 3 anteriores)
            ws[f'E{row_num}'] = f'=B{row_num}+C{row_num}+D{row_num}'
            
            # ACTIVAS >35 estrellas (Alto avance)
            formula = f'=COUNTIFS(\'Data Enriquecida\'!${plaza_col}:${plaza_col},"{plaza_escaped}",\'Data Enriquecida\'!${estatus_col}:${estatus_col},"ACTIVO",\'Data Enriquecida\'!${estrellas_col}:${estrellas_col},">35")'
            ws[f'F{row_num}'] = formula
            
            # ACTIVAS 1-35 estrellas (Medio avance)
            formula = f'=COUNTIFS(\'Data Enriquecida\'!${plaza_col}:${plaza_col},"{plaza_escaped}",\'Data Enriquecida\'!${estatus_col}:${estatus_col},"ACTIVO",\'Data Enriquecida\'!${estrellas_col}:${estrellas_col},">=1",\'Data Enriquecida\'!${estrellas_col}:${estrellas_col},"<=35")'
            ws[f'G{row_num}'] = formula
            
            # ACTIVAS 0 estrellas (Sin avance)
            formula = f'=COUNTIFS(\'Data Enriquecida\'!${plaza_col}:${plaza_col},"{plaza_escaped}",\'Data Enriquecida\'!${estatus_col}:${estatus_col},"ACTIVO",\'Data Enriquecida\'!${estrellas_col}:${estrellas_col},0)'
            ws[f'H{row_num}'] = formula
            
            # Total ACTIVAS (suma de las 3 anteriores)
            ws[f'I{row_num}'] = f'=F{row_num}+G{row_num}+H{row_num}'
            
            row_num += 1
        
        # Agregar fila de totales
        total_row = row_num
        ws[f'A{total_row}'] = 'Total general'
        ws[f'A{total_row}'].font = ws[f'A{total_row}'].font.copy(bold=True)
        
        # Totales con fórmulas SUM
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
            ws[f'{col}{total_row}'] = f'=SUM({col}3:{col}{total_row-1})'
            ws[f'{col}{total_row}'].font = ws[f'{col}{total_row}'].font.copy(bold=True)
        
        # Ajustar anchos de columna
        ws.column_dimensions['A'].width = 40
        for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
            ws.column_dimensions[col].width = 15
        
        print(f"✓ Hoja '{sheet_name}' creada con {len(plazas)} plazas y fórmulas dinámicas")
        
    def save(self):
        """Guarda los cambios en el archivo Excel"""
        self.wb.save(self.excel_path)
        self.wb.close()
        print(f"✓ Archivo guardado: {self.excel_path}")

def add_dynamic_reports_to_excel(excel_path: str):
    """
    Función helper para agregar reportes dinámicos a un Excel existente
    
    Args:
        excel_path: Ruta al archivo Excel
    """
    generator = DynamicReportGenerator(excel_path)
    generator.add_dynamic_summary_tables()
    generator.save()

if __name__ == '__main__':
    # Test
    import sys
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
        add_dynamic_reports_to_excel(excel_path)
    else:
        print("Uso: python dynamic_reports.py <ruta_al_excel>")