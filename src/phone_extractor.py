"""
Módulo de extracción de teléfonos - Extrae y normaliza números de la columna Contactos
"""
import re
from typing import Optional

class PhoneExtractor:
    """Extrae y normaliza números de teléfono mexicanos"""
    
    # Patrón para encontrar el bloque después de "Telefono Fijo:"
    PATTERN_TELEFONO_FIJO = re.compile(
        r'Telefono\s+Fijo:\s*([0-9\s\+\-\(\)]+?)(?:\s+Email:|$)',
        re.IGNORECASE
    )
    
    # Patrón para extraer solo dígitos
    PATTERN_DIGITS = re.compile(r'\d')
    
    def extract_phone(self, contactos: str) -> Optional[str]:
        """
        Extrae el número de teléfono del campo Contactos
        
        Args:
            contactos: Texto del campo Contactos
            
        Returns:
            Número normalizado de 10 dígitos o None si no se encuentra
        """
        if not contactos or not isinstance(contactos, str):
            return None
        
        # Estrategia 1: Buscar después de "Telefono Fijo:"
        match = self.PATTERN_TELEFONO_FIJO.search(contactos)
        if match:
            phone_block = match.group(1)
            digits = ''.join(self.PATTERN_DIGITS.findall(phone_block))
            
            # Normalizar: tomar últimos 10 dígitos
            # (esto elimina códigos de país como +52 o 52 o 01)
            if len(digits) >= 10:
                return digits[-10:]
            # Si tiene 9 dígitos, también es válido (lada + número corto)
            elif len(digits) == 9:
                return digits
        
        # Estrategia 2: Fallback - buscar cualquier secuencia de 9+ dígitos
        all_digits = ''.join(self.PATTERN_DIGITS.findall(contactos))
        if len(all_digits) >= 10:
            return all_digits[-10:]
        elif len(all_digits) == 9:
            # Números de 9 dígitos son válidos (ej: 552019446 = lada 55 + 2019446)
            return all_digits
        
        return None
    
    def extract_lada(self, phone: str) -> Optional[str]:
        """
        Extrae la lada del número (primeros 2 o 3 dígitos)
        
        Args:
            phone: Número de 9 o 10 dígitos
            
        Returns:
            Tupla con (lada_2_digitos, lada_3_digitos) para que el matcher pruebe ambas
        """
        if not phone or len(phone) not in [9, 10]:
            return None
        
        # Retornamos las opciones, el matcher probará ambas
        return phone[:2], phone[:3]

if __name__ == '__main__':
    # Test con ejemplos reales
    extractor = PhoneExtractor()
    
    casos_prueba = [
        'CINDY GABRIELA FERNANDEZ Telefono Fijo: 7552403032 Email: fernandezvivianogabriela@gmail.com',
        'ROSARIO RESENDIZ Telefono Fijo: 755 140 07 96 Email: 7555564956rosy@gmail.com',
        'MARIA PETRA VAZQUEZ Telefono Fijo: 33 4792 3046 Email: vazquezmaria179019@gmail.com',
        'AARON HUMBERTO HERNANDEZ Telefono Fijo: 9991501119 Email: aronpinedo@gmail.com',
        'CELINA LUGO Telefono Fijo: 665 799 05 81  Email: celinalugosoto577@gmail.com',
        'MIRIAM FRANCISCO Telefono Fijo: 55 8328 2133  Email: pukamiriam@gmail.com',
        'SIN TELEFONO Email: test@example.com',
        None,
    ]
    
    print("=== TEST PHONE EXTRACTOR ===\n")
    for contacto in casos_prueba:
        phone = extractor.extract_phone(contacto)
        if phone:
            ladas = extractor.extract_lada(phone)
            print(f"✓ {phone} → ladas: {ladas[0]} o {ladas[1]}")
            print(f"  Origen: {contacto[:60]}...")
        else:
            print(f"✗ No extraído")
            print(f"  Origen: {contacto}")
        print()