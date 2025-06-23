"""
Script para debuggear el problema con la consulta de journals
"""
import asyncio
import sys
import os
from datetime import datetime
from pydantic import ValidationError

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.services.journal_service import JournalService
from app.schemas.journal import JournalFilter, JournalListItem
from app.utils.pagination import create_paged_response


async def debug_journals():
    """Debuggear el problema con los journals"""
    print("🔍 Iniciando debug de journals...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Crear servicio
            journal_service = JournalService(db)
            
            # Crear filtros como en la API
            filters = JournalFilter(
                type=None,
                is_active=None,
                search=None
            )
            
            print("📊 Ejecutando consulta de journals...")
            
            # Obtener journals
            journals = await journal_service.get_journals(
                filters=filters,
                skip=0,
                limit=50,
                order_by="name",
                order_dir="asc"
            )
            
            print(f"✅ Consulta exitosa. Se encontraron {len(journals)} journals")
            
            # Intentar contar
            total = await journal_service.count_journals(filters)
            print(f"📈 Total de journals: {total}")
            
            # Verificar cada journal individualmente
            print("\n🔍 Verificando cada journal:")
            for i, journal in enumerate(journals):
                try:
                    print(f"  {i+1}. Journal ID: {journal.id}")
                    print(f"     Nombre: {journal.name}")
                    print(f"     Código: {journal.code}")
                    print(f"     Tipo: {journal.type}")
                    print(f"     Activo: {journal.is_active}")
                    print(f"     Creado: {journal.created_at}")
                    
                    # Verificar que tenga el atributo total_journal_entries
                    if hasattr(journal, 'journal_entries'):
                        total_entries = len(journal.journal_entries)
                        print(f"     Total asientos: {total_entries}")
                    else:
                        print(f"     ⚠️  No tiene relación journal_entries cargada")
                    
                    # Intentar crear JournalListItem manualmente
                    try:
                        list_item_data = {
                            'id': journal.id,
                            'name': journal.name,
                            'code': journal.code,
                            'type': journal.type,
                            'sequence_prefix': journal.sequence_prefix,
                            'is_active': journal.is_active,
                            'current_sequence_number': journal.current_sequence_number,
                            'total_journal_entries': len(journal.journal_entries) if hasattr(journal, 'journal_entries') else 0,
                            'created_at': journal.created_at
                        }
                        
                        list_item = JournalListItem(**list_item_data)
                        print(f"     ✅ JournalListItem creado exitosamente")
                        
                    except ValidationError as ve:
                        print(f"     ❌ Error validando JournalListItem: {ve}")
                        print(f"        Datos: {list_item_data}")
                    except Exception as e:
                        print(f"     ❌ Error creando JournalListItem: {e}")
                        
                except Exception as e:
                    print(f"     ❌ Error procesando journal {i+1}: {e}")
                
                print()
            
            # Intentar crear la respuesta paginada
            print("🔄 Intentando crear respuesta paginada...")
            try:
                # Convertir a lista de JournalListItem manualmente
                journal_list_items = []
                for journal in journals:
                    try:
                        list_item_data = {
                            'id': journal.id,
                            'name': journal.name,
                            'code': journal.code,
                            'type': journal.type,
                            'sequence_prefix': journal.sequence_prefix,
                            'is_active': journal.is_active,
                            'current_sequence_number': journal.current_sequence_number,
                            'total_journal_entries': len(journal.journal_entries) if hasattr(journal, 'journal_entries') else 0,
                            'created_at': journal.created_at
                        }
                        
                        list_item = JournalListItem(**list_item_data)
                        journal_list_items.append(list_item)
                        
                    except Exception as e:
                        print(f"❌ Error convirtiendo journal {journal.id}: {e}")
                
                print(f"📝 Convertidos {len(journal_list_items)} journals a JournalListItem")
                
                # Crear respuesta paginada
                response = create_paged_response(
                    items=journal_list_items,
                    total=total,
                    skip=0,
                    limit=50
                )
                
                print("✅ Respuesta paginada creada exitosamente")
                print(f"   Items: {len(response.items)}")
                print(f"   Total: {response.total}")
                
            except Exception as e:
                print(f"❌ Error creando respuesta paginada: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            print(f"❌ Error en consulta principal: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_journals())
