"""
Test de src/asesor_normalizer.py: validar recorte de estados y alias.
"""
from src.asesor_normalizer import get_asesor_normalizer

def test_normalizer():
    norm = get_asesor_normalizer()
    norm.load()
    
    # Casos conocidos del análisis
    casos = [
        ("ACAPULCO GUERRERO", "ACAPULCO"),
        ("AGUASCALIENTES AGUASCALIENTES", "AGUASCALIENTES"),
        ("MEXICO CENTRO ESTADO DE MEXICO", "MX CENTRO"),
        ("MEXICO NORTE ESTADO DE MEXICO", "MXNTE"),
        ("MEXICO ORIENTE ESTADO DE MEXICO", "MXOTE"),
        ("MEXICO SUR ESTADO DE MEXICO", "MX SUR"),
        ("MONTERREY ORIENTE NUEVO LEON", "MONTERREY ORIENTE"),
        ("PUEBLA PUEBLA", "PUEBLA"),
        ("POZA RICA VERACRUZ", "POZARICA"),
        ("TOLUCA FORANEAS ESTADO DE MEXICO", "TOLUCA FOR"),
        ("TUXTLA FORANEAS CHIAPAS", "TUXTLA FOR"),
        # Overrides especiales
        ("XALAPA XALAPA", "XALAPA"),
        ("PUEBLA FORANEAS PUEBLA FORANEAS", "PUEBLA FOR"),
        ("WIDGET NAUPHILUS", "__SISTEMA__"),
        # Ciudad == estado (no hay sufijo que recortar)
        ("NUEVO LEON NUEVO LEON", "NUEVO LEON"),
        ("TABASCO TABASCO", "TABASCO"),
    ]
    
    print("Validando normalización de asesores:")
    for asesor_raw, esperado in casos:
        resultado = norm.normalize(asesor_raw)
        status = "✓" if resultado == esperado else "✗"
        print(f"  {status} {asesor_raw!r:50} → {resultado!r:20} (esperado: {esperado!r})")
        assert resultado == esperado, f"Falló: {asesor_raw} → {resultado} (esperado {esperado})"
    
    print(f"\n✓ Todos los casos ({len(casos)}) pasaron.")

if __name__ == '__main__':
    test_normalizer()