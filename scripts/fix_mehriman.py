from sqlalchemy import create_engine, text

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- FIXING USER ID 182 ---")
        
        # 1. Update Username (clean ascii), Role, Shift
        sql = text("""
            UPDATE personel 
            SET kullanici_adi = 'mihrimah.ali', 
                rol = 'Personel', 
                vardiya = 'GÜNDÜZ VARDİYASI' 
            WHERE id = 182
        """)
        conn.execute(sql)
        conn.commit()
        print("✅ User ID 182 updated: mihrimah.ali / Personel / GÜNDÜZ VARDİYASI")
        
        # 2. Verify
        res = conn.execute(text("SELECT * FROM personel WHERE id = 182")).fetchone()
        print(f"New Data: {res.kullanici_adi} | Role: {res.rol} | Shift: {res.vardiya}")

except Exception as e:
    print(f"Error: {e}")
