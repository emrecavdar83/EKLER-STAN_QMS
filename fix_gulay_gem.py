import sqlite3

try:
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    # Find all users with GEM in name
    cursor.execute("SELECT id, ad_soyad, rol, bolum, vardiya, gorev FROM personel WHERE ad_soyad LIKE '%GEM%'")
    rows = cursor.fetchall()
    print("BEFORE:", rows)
    
    # Update Gülay Gem
    cursor.execute("""
        UPDATE personel 
        SET ad_soyad = 'GÜLAY GEM', 
            rol = 'OPERATÖR', 
            bolum = 'KALİTE', 
            vardiya = 'GÜNDÜZ VARDİYASI',
            gorev = 'OPERATÖR'
        WHERE kullanici_adi = 'ggem' OR ad_soyad LIKE '%GEM%'
    """)
    conn.commit()
    
    cursor.execute("SELECT id, ad_soyad, rol, bolum, vardiya, gorev FROM personel WHERE ad_soyad LIKE '%GEM%'")
    print("AFTER:", cursor.fetchall())
except Exception as e:
    print(e)
