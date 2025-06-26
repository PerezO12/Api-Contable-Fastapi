"""
Test rápido para el método journals_list corregido
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.services.journal_service import JournalService
from app.schemas.journal import JournalFilter, JournalListItem

async def test():
    async with AsyncSessionLocal() as db:
        service = JournalService(db)
        filters = JournalFilter(type=None, is_active=None, search=None)
        data = await service.get_journals_list(filters, 0, 10)
        print(f'✅ Método get_journals_list funciona. Journals: {len(data)}')
        
        # Probar conversión a JournalListItem
        for item_data in data:
            item = JournalListItem(**item_data)
            print(f'  - {item.name} ({item.code}): {item.total_journal_entries} asientos')

if __name__ == "__main__":
    asyncio.run(test())
