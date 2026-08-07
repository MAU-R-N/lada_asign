"""
Test rápido de src/active_plazas.py: verifica carga correcta del JSON.
"""
from src.active_plazas import get_active_plazas_loader

def test_active_plazas():
    loader = get_active_plazas_loader()
    loader.load()
    
    plazas = loader.get_plazas_activas()
    roles = loader.get_all_roles()
    
    print(f"Total roles en JSON: {len(roles)}")
    print(f"Roles ASESOR * con estatus Activo: {len(plazas)}")
    print(f"\nEstatus únicos: {set(v for v in roles.values() if v)}")
    
    # Verificar casos conocidos del análisis
    assert 'ACAPULCO' in plazas, "ACAPULCO debe estar en plazas activas"
    assert 'MX CENTRO' in plazas, "MX CENTRO debe estar en plazas activas"
    assert 'MONTERREY ORIENTE' in plazas, "MONTERREY ORIENTE debe estar en plazas activas"
    assert 'PUEBLA FOR' in plazas, "PUEBLA FOR debe estar en plazas activas"
    assert 'POZARICA' in plazas, "POZARICA debe estar en plazas activas"
    
    # Verificar que roles no-ASESOR no entran
    assert 'CONTACTO DIGITAL' not in plazas, "CONTACTO DIGITAL no debe estar (no tiene prefijo ASESOR)"
    assert 'CLIENTE' not in plazas, "CLIENTE no debe estar"
    
    # Validar método is_plaza_activa
    assert loader.is_plaza_activa('ACAPULCO') == True
    assert loader.is_plaza_activa('PLAZA_INEXISTENTE') == False
    
    print("\n✓ Todas las validaciones pasaron.")
    print(f"\nPrimeras 10 plazas activas (alfabético):")
    for p in sorted(plazas)[:10]:
        print(f"   {p}")

if __name__ == '__main__':
    test_active_plazas()