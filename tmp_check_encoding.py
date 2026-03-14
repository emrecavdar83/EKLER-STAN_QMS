import sqlite3
from sqlalchemy import text
from database.connection import get_engine

try:
    engine = get_engine()
    
    # Check corrupted users
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, ad_soyad, rol, bolum, vardiya FROM personel WHERE ad_soyad LIKE '%GEM%'")).fetchall()
        for r in res:
            print(f"ID: {r[0]} | Ad: {r[1]} | Rol: {r[2]} | Bölüm: {r[3]} | Vardiya: {r[4]}")
            
except Exception as e:
    print(e)
