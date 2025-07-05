#!/usr/bin/env python3
import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check_tables():
    async with AsyncSessionLocal() as db:
        try:
            # Check if company_settings table exists
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'company_settings'
            """))
            table_exists = result.fetchone()
            print('Table exists:', table_exists is not None)
            
            if table_exists:
                # Check table structure
                result = await db.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'company_settings'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                print('Columns:')
                for col in columns:
                    print(f'  {col[0]}: {col[1]} (nullable: {col[2]})')
                    
                # Try to create a basic company setting record
                print('\nTesting creation of default settings...')
                from app.services.company_settings_service import CompanySettingsService
                service = CompanySettingsService(db)
                
                try:
                    settings = await service.get_or_create_default_settings()
                    print('✅ Default settings created successfully')
                    print(f'Company: {settings.company_name}')
                    print(f'Currency: {settings.currency_code}')
                except Exception as e:
                    print('❌ Error creating default settings:', str(e))
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print('Error:', str(e))
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_tables())
