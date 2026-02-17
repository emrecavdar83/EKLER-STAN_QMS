from sqlalchemy import create_engine, text

def robust_fix():
    print("--- FIXING ACCOUNTS (LOCAL) ---")
    try:
        engine = create_engine('sqlite:///ekleristan_local.db')
        with engine.connect() as conn:
            # 1. Delete existing targeting specific user names
            print("Deleting old records for 'Admin' and 'emre.cavdar'...")
            conn.execute(text("DELETE FROM personel WHERE kullanici_adi IN ('Admin', 'emre.cavdar')"))
            
            # 2. Re-create Admin
            print("Creating 'Admin'...")
            conn.execute(text("""
                INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'Admin', 'AKTİF', 0)
            """))
            
            # 3. Re-create Emre (Preserving other details if possible? No, fresh start is safer for login)
            # User ID 2 is preferred for Emre if possible, but auto-increment might give new ID.
            # Let's try to force ID if needed, or just let it be.
            # We'll just insert him.
            print("Creating 'emre.cavdar'...")
            conn.execute(text("""
                INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, durum, gorev, pozisyon_seviye)
                VALUES ('EMRE ÇAVDAR', 'emre.cavdar', 'Ekler2024!', 'Admin', 'AKTİF', 'GENEL MÜDÜR', 1)
            """))
            
            conn.commit()
            print("✅ Accounts fixed locally.")
            
    except Exception as e:
        print(f"Local Fix Error: {e}")

if __name__ == "__main__":
    robust_fix()
