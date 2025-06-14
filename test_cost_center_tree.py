#!/usr/bin/env python3
"""
Script de prueba para el endpoint de árbol de centros de costo
"""
import asyncio
import sys
sys.path.append('.')

from app.database import AsyncSessionLocal
from app.services.cost_center_service import CostCenterService


async def test_cost_center_tree():
    """Probar el endpoint de árbol de centros de costo"""
    async with AsyncSessionLocal() as db:
        service = CostCenterService(db)
        
        print("=== Probando get_cost_center_tree ===")
        
        # Test 1: Obtener árbol completo (solo activos)
        print("\n1. Árbol completo (solo activos):")
        try:
            tree = await service.get_cost_center_tree(active_only=True)
            print(f"   Encontrados {len(tree)} centros de costo raíz")
            
            def print_tree(nodes, level=0):
                for node in nodes:
                    indent = "  " * level
                    print(f"{indent}- {node.code}: {node.name} (nivel: {node.level}, hijos: {len(node.children)})")
                    if node.children:
                        print_tree(node.children, level + 1)
            
            if tree:
                print_tree(tree)
            else:
                print("   No se encontraron centros de costo")
                
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test 2: Obtener árbol completo (incluyendo inactivos)
        print("\n2. Árbol completo (incluyendo inactivos):")
        try:
            tree_all = await service.get_cost_center_tree(active_only=False)
            print(f"   Encontrados {len(tree_all)} centros de costo raíz (total)")
            
            # Solo mostrar los primeros 3 niveles para no sobrecargar
            def print_limited_tree(nodes, level=0, max_level=2):
                if level > max_level:
                    return
                for node in nodes[:5]:  # Solo los primeros 5 por nivel
                    indent = "  " * level
                    status = "activo" if node.is_active else "inactivo"
                    print(f"{indent}- {node.code}: {node.name} ({status}, nivel: {node.level})")
                    if node.children and level < max_level:
                        print_limited_tree(node.children, level + 1, max_level)
                if len(nodes) > 5:
                    indent = "  " * level
                    print(f"{indent}... y {len(nodes) - 5} más")
            
            if tree_all:
                print_limited_tree(tree_all)
            
        except Exception as e:
            print(f"   ERROR: {e}")
        
        print("\n=== Pruebas completadas ===")


if __name__ == "__main__":
    asyncio.run(test_cost_center_tree())
