from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("Agregando campos a third_parties...")
    db.execute(text("ALTER TABLE third_parties ADD COLUMN IF NOT EXISTS receivable_account_id UUID"))
    db.execute(text("ALTER TABLE third_parties ADD COLUMN IF NOT EXISTS payable_account_id UUID"))
    db.commit()
    print("✅ Campos agregados exitosamente")
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
