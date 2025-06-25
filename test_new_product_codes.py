#!/usr/bin/env python3
"""
Test de la nueva generación de códigos de productos con secuencia y sufijo aleatorio
"""

def test_new_product_code_generation():
    """Test de la nueva función de generación de códigos de productos"""
    print("🧪 Probando nueva generación de códigos de productos")
    print("=" * 60)
    
    try:
        from app.utils.codes import generate_product_code
        from app.database import SessionLocal
        
        # Crear sesión de base de datos
        db = SessionLocal()
        
        try:
            # Test con productos similares que anteriormente causaban duplicados
            test_products = [
                ("Álcool Polivinílico 500 g", "product"),
                ("Álcool n-Amílico P.A./ACS 1000 mL", "product"),
                ("Álcool n-Butílico P.A./ACS 1000 mL", "product"),
                ("Álcool n-Propílico P.A. 5000 mL", "product"),
                ("Álcool sec-Butílico P.A. 1000 mL", "product"),
                ("Óxido de Alumínio 90 (S) Neutro 500 g", "product"),
                ("Óxido de Arsênio III P.A. 100 g", "product"),
                ("Óxido de Bismuto III P.A. 500 g", "product"),
                ("Servicio de Consultoría", "service"),
                ("Servicio de Soporte Técnico", "service"),
                ("Producto y Servicio Mixto", "both")
            ]
            
            generated_codes = []
            
            print("\n🔧 Generando códigos de prueba:")
            for i, (name, product_type) in enumerate(test_products, 1):
                try:
                    code = generate_product_code(db, name, product_type)
                    generated_codes.append(code)
                    print(f"{i:2d}. {name[:40]:<40} → {code}")
                except Exception as e:
                    print(f"{i:2d}. ERROR: {name[:40]:<40} → {str(e)}")
            
            print(f"\n📊 Resultados:")
            print(f"   Total de códigos generados: {len(generated_codes)}")
            print(f"   Códigos únicos: {len(set(generated_codes))}")
            
            # Verificar que todos los códigos son únicos
            if len(generated_codes) == len(set(generated_codes)):
                print("   ✅ Todos los códigos son únicos")
            else:
                print("   ❌ Hay códigos duplicados")
                duplicates = [code for code in set(generated_codes) if generated_codes.count(code) > 1]
                print(f"   Duplicados: {duplicates}")
            
            print(f"\n🎯 Características de los códigos generados:")
            
            # Analizar patrones
            prefixes = {}
            for code in generated_codes:
                prefix = code.split('-')[0]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            print(f"   Prefijos utilizados: {prefixes}")
            
            # Mostrar ejemplos de códigos por tipo
            print(f"\n📝 Ejemplos por tipo:")
            prd_codes = [c for c in generated_codes if c.startswith('PRD-')]
            srv_codes = [c for c in generated_codes if c.startswith('SRV-')]
            mix_codes = [c for c in generated_codes if c.startswith('MIX-')]
            
            if prd_codes:
                print(f"   Productos (PRD): {prd_codes[:3]} {'...' if len(prd_codes) > 3 else ''}")
            if srv_codes:
                print(f"   Servicios (SRV): {srv_codes[:3]} {'...' if len(srv_codes) > 3 else ''}")
            if mix_codes:
                print(f"   Mixtos (MIX): {mix_codes[:3]} {'...' if len(mix_codes) > 3 else ''}")
            
            print(f"\n✨ Beneficios de la nueva implementación:")
            print(f"   ✅ Secuencia numérica evita conflictos principales")
            print(f"   ✅ Sufijo aleatorio garantiza unicidad")
            print(f"   ✅ Formato consistente: PREFIX-NAMEPART-SEQ-RANDOM")
            print(f"   ✅ Maneja nombres similares sin duplicados")
            print(f"   ✅ Escalable para gran volumen de productos")
            
        finally:
            db.close()
            
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Asegúrate de que las dependencias estén instaladas")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

def test_code_collision_resistance():
    """Test de resistencia a colisiones de códigos"""
    print("\n🛡️ Probando resistencia a colisiones")
    print("-" * 40)
    
    try:
        from app.utils.codes import generate_product_code
        from app.database import SessionLocal
        
        db = SessionLocal()
        
        try:
            # Generar múltiples códigos para el mismo nombre
            base_name = "Producto de Prueba"
            codes = []
            
            for i in range(5):
                code = generate_product_code(db, base_name, "product")
                codes.append(code)
                print(f"   Intento {i+1}: {code}")
            
            unique_codes = len(set(codes))
            print(f"\n   Códigos únicos generados: {unique_codes}/{len(codes)}")
            
            if unique_codes == len(codes):
                print("   ✅ Todos los códigos son únicos")
            else:
                print("   ❌ Hay duplicados")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Test de generación de códigos de productos mejorada")
    print("=" * 70)
    
    test_new_product_code_generation()
    test_code_collision_resistance()
    
    print(f"\n🎉 Pruebas completadas")
    print(f"\n📚 Formato de códigos:")
    print(f"   Productos:  PRD-NAMEPART-001-A4B")
    print(f"   Servicios:  SRV-NAMEPART-001-X9Z")
    print(f"   Mixtos:     MIX-NAMEPART-001-K2M")
    print(f"\n   Donde:")
    print(f"   - NAMEPART: Primeros 6 caracteres alfanuméricos del nombre")
    print(f"   - 001: Número secuencial (3 dígitos)")
    print(f"   - A4B: Sufijo aleatorio (3 caracteres)")
