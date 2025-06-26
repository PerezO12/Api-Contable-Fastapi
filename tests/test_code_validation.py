#!/usr/bin/env python3
"""
Script to test the new code validation
"""
import re

def test_code_validation():
    """Test the new validation pattern"""
    test_codes = [
        'ºTA0035639',  # El código problemático
        'ABC123',      # Código normal
        'TEST-001',    # Con guión
        'PROD_2024',   # Con guión bajo
        'ñABCD',       # Con ñ
        'àbcd',        # Con acentos
        '测试',         # Caracteres chinos
        'ΔΩΨ',         # Caracteres griegos
        'test code',   # Con espacio (debería fallar)
        'test\tcode',  # Con tab (debería fallar)
        'test\ncode',  # Con newline (debería fallar)
    ]
    
    print("Testing new code validation pattern:")
    print("Pattern: r'^[^\\s\\x00-\\x1f\\x7f-\\x9f]+$'")
    print("-" * 50)
    
    for code in test_codes:
        is_valid = bool(re.match(r'^[^\s\x00-\x1f\x7f-\x9f]+$', code.strip()))
        result = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{result:12} | {repr(code)}")

if __name__ == "__main__":
    test_code_validation()
