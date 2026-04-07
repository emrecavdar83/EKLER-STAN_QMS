from database.connection import get_engine
from sqlalchemy import text

try:
    engine = get_engine()
    with engine.connect() as conn:
        # Check table structure
        res = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'sistem_oturum_izleri'
        """)).fetchall()
        print("Table Structure for sistem_oturum_izleri:")
        for r in res:
            print(f"- {r[0]}: {r[1]}")
        
        # Check if any records exist
        count = conn.execute(text("SELECT COUNT(*) FROM sistem_oturum_izleri")).scalar()
        print(f"Total active sessions: {count}")
except Exception as e:
    print(f"Error checking table: {e}")
