#!/usr/bin/env python3
"""
Script de prueba para los nuevos filtros de centros de costo
"""
import asyncio
import sys
sys.path.append('.')

from app.services.cost_center_service import CostCenterService
from app.schemas.cost_center import CostCenterFilter
from app.database import get_db


async def test_filters():
    """Probar los nuevos filtros de centros de costo"""
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        service = CostCenterService(db)
        
        print("=== Probando filtros de centros de costo ===")
        
        # Test 1: Filtrar por nivel 0 (root)
        print("\n1. Filtro por nivel 0 (centros de costo raíz):")
        filter_level_0 = CostCenterFilter(level=0)
        result = await service.get_cost_centers_list(filter_level_0, skip=0, limit=10)
        print(f"   Encontrados: {result.total} centros de costo de nivel 0")
        for cc in result.cost_centers:
            print(f"   - {cc.code}: {cc.name} (nivel: {cc.level})")
        
        # Test 2: Filtrar por is_active=true y level=1
        print("\n2. Filtro por activos y nivel 1:")
        filter_active_level_1 = CostCenterFilter(is_active=True, level=1)
        result = await service.get_cost_centers_list(filter_active_level_1, skip=0, limit=10)
        print(f"   Encontrados: {result.total} centros de costo activos de nivel 1")
        for cc in result.cost_centers:
            print(f"   - {cc.code}: {cc.name} (nivel: {cc.level}, activo: {cc.is_active})")
        
        # Test 3: Filtrar por has_children=true
        print("\n3. Filtro por centros que tienen hijos:")
        filter_has_children = CostCenterFilter(has_children=True)
        result = await service.get_cost_centers_list(filter_has_children, skip=0, limit=10)
        print(f"   Encontrados: {result.total} centros de costo con hijos")
        for cc in result.cost_centers:
            print(f"   - {cc.code}: {cc.name} (hijos: {cc.children_count})")
        
        # Test 4: Filtrar por is_leaf=true (sin hijos)
        print("\n4. Filtro por centros hoja (sin hijos):")
        filter_leaf = CostCenterFilter(is_leaf=True)
        result = await service.get_cost_centers_list(filter_leaf, skip=0, limit=10)
        print(f"   Encontrados: {result.total} centros de costo hoja")
        for cc in result.cost_centers:
            print(f"   - {cc.code}: {cc.name} (hijos: {cc.children_count})")
        
        # Test 5: Filtrar por is_root=true (sin padre)
        print("\n5. Filtro por centros raíz (sin padre):")
        filter_root = CostCenterFilter(is_root=True)
        result = await service.get_cost_centers_list(filter_root, skip=0, limit=10)
        print(f"   Encontrados: {result.total} centros de costo raíz")
        for cc in result.cost_centers:
            print(f"   - {cc.code}: {cc.name} (padre: {cc.parent_name or 'None'})")
        
        # Test 6: Combinación: activos, nivel 1, con hijos
        print("\n6. Combinación: activos, nivel 1, con hijos:")
        filter_combined = CostCenterFilter(is_active=True, level=1, has_children=True)
        result = await service.get_cost_centers_list(filter_combined, skip=0, limit=10)
        print(f"   Encontrados: {result.total} centros de costo activos, nivel 1, con hijos")
        for cc in result.cost_centers:
            print(f"   - {cc.code}: {cc.name} (nivel: {cc.level}, hijos: {cc.children_count})")
        
        print("\n=== Pruebas completadas ===")


if __name__ == "__main__":
    asyncio.run(test_filters())
