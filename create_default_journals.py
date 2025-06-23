"""
Script para crear diarios por defecto en el sistema
Este script debe ejecutarse después de crear la base de datos inicial
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models.journal import Journal, JournalType
from app.models.user import User


async def create_default_journals():
    """Crea los diarios por defecto del sistema"""
    
    async with AsyncSessionLocal() as db:
        # Verificar si ya existen diarios
        existing_journals = await db.execute(select(Journal))
        if existing_journals.scalars().first():
            print("❌ Ya existen diarios en el sistema. No se crearán diarios por defecto.")
            return

        # Obtener el primer usuario admin para asignar como creador
        admin_user = await db.execute(
            select(User).where(User.is_superuser == True).limit(1)
        )
        admin_user = admin_user.scalar_one_or_none()
        
        if not admin_user:
            print("❌ No se encontró un usuario administrador. Creando diarios sin asignar creador.")
            created_by_id = None
        else:
            created_by_id = admin_user.id
            print(f"✅ Usando usuario administrador: {admin_user.email}")

        # Definir diarios por defecto
        default_journals = [
            {
                "name": "Diario de Ventas",
                "code": "SALE",
                "type": JournalType.SALE,
                "sequence_prefix": "VEN",
                "description": "Diario para registrar todas las facturas de venta y operaciones relacionadas con ingresos por ventas"
            },
            {
                "name": "Diario de Compras",
                "code": "PURCH",
                "type": JournalType.PURCHASE,
                "sequence_prefix": "COM",
                "description": "Diario para registrar todas las facturas de proveedores y gastos operacionales"
            },
            {
                "name": "Diario de Banco Principal",
                "code": "BANK01",
                "type": JournalType.BANK,
                "sequence_prefix": "BNK",
                "description": "Diario para operaciones bancarias, transferencias, pagos y cobros a través de cuentas bancarias"
            },
            {
                "name": "Diario de Efectivo",
                "code": "CASH",
                "type": JournalType.CASH,
                "sequence_prefix": "CAJ",
                "description": "Diario para operaciones en efectivo, pagos menores y gastos de caja chica"
            },
            {
                "name": "Diario General",
                "code": "MISC",
                "type": JournalType.MISCELLANEOUS,
                "sequence_prefix": "GEN",
                "description": "Diario para asientos de ajuste, depreciaciones, provisiones y operaciones contables diversas"
            }
        ]

        # Crear cada diario
        for journal_data in default_journals:
            journal = Journal(
                name=journal_data["name"],
                code=journal_data["code"],
                type=journal_data["type"],
                sequence_prefix=journal_data["sequence_prefix"],
                description=journal_data["description"],
                current_sequence_number=0,
                sequence_padding=4,
                include_year_in_sequence=True,
                reset_sequence_yearly=True,
                requires_validation=False,
                allow_manual_entries=True,
                is_active=True,
                created_by_id=created_by_id,
                last_sequence_reset_year=datetime.now(timezone.utc).year
            )
            
            db.add(journal)
            print(f"✅ Creado diario: {journal_data['name']} ({journal_data['code']})")

        # Guardar cambios
        await db.commit()
        print("🎉 ¡Diarios por defecto creados exitosamente!")


async def list_journals():
    """Lista todos los diarios del sistema"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Journal).order_by(Journal.type, Journal.name)
        )
        journals = result.scalars().all()
        
        if not journals:
            print("❌ No hay diarios en el sistema")
            return
            
        print("\n📊 DIARIOS EN EL SISTEMA:")
        print("=" * 80)
        
        current_type = None
        for journal in journals:
            if current_type != journal.type:
                current_type = journal.type
                print(f"\n📁 {journal.type.value.upper()}:")
                print("-" * 40)
            
            status = "🟢 Activo" if journal.is_active else "🔴 Inactivo"
            print(f"  • {journal.name} ({journal.code})")
            print(f"    Prefijo: {journal.sequence_prefix} | {status}")
            print(f"    Secuencia actual: {journal.current_sequence_number}")
            if journal.description:
                print(f"    Descripción: {journal.description}")
            print()


async def main():
    """Función principal"""
    print("🏗️  INICIALIZADOR DE DIARIOS CONTABLES")
    print("=" * 50)
    
    try:
        # Crear diarios por defecto
        await create_default_journals()
        
        # Listar diarios creados
        await list_journals()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
