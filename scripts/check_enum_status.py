import asyncio
import asyncpg

async def check_enums():
    conn = await asyncpg.connect('postgresql://postgres:123456@127.0.0.1:5432/api_contable_dev2')
    try:
        # Check current enum definitions
        result = await conn.fetch("""
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname IN ('accounttype', 'accountcategory')
            ORDER BY t.typname, e.enumsortorder
        """)
        
        current_accounttype = []
        current_accountcategory = []
        
        for row in result:
            if row['typname'] == 'accounttype':
                current_accounttype.append(row['enumlabel'])
            else:
                current_accountcategory.append(row['enumlabel'])
        
        print('Current AccountType enum values:', current_accounttype)
        print('Current AccountCategory enum values:', current_accountcategory)
        
        # Check what values are actually used in the database
        actual_types = await conn.fetch('SELECT DISTINCT account_type FROM accounts ORDER BY account_type')
        actual_categories = await conn.fetch('SELECT DISTINCT category FROM accounts WHERE category IS NOT NULL ORDER BY category')
        
        print('\nActual account_type values in use:', [row['account_type'] for row in actual_types])
        print('Actual category values in use:', [row['category'] for row in actual_categories])
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_enums())
