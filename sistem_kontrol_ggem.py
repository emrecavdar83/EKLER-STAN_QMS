from database.connection import get_engine
from sqlalchemy import text
import pandas as pd

def check_user_role():
    engine = get_engine()
    with engine.connect() as conn:
        # 1. Personel Bilgisi
        p_sql = text("""
            SELECT p.id, p.ad_soyad, p.rol, p.kullanici_adi, p.durum, b.bolum_adi 
            FROM personel p 
            LEFT JOIN ayarlar_bolumler b ON p.departman_id = b.id 
            WHERE p.ad_soyad LIKE '%GÜLAY GEM%'
        """)
        p_res = conn.execute(p_sql).fetchone()
        
        if not p_res:
            print("GÜLAY GEM isimli kayıt bulunamadı.")
            return

        print(f"--- FİZİKSEL KAYIT ANALİZİ ---")
        print(f"ID: {p_res[0]}")
        print(f"İsim: {p_res[1]}")
        print(f"Sistem Rolü: {p_res[2]}")
        print(f"Kullanıcı Adı: {p_res[3]}")
        print(f"Durum: {p_res[4]}")
        print(f"Departman: {p_res[5]}")
        
        # 2. Yetki Matrisi Kontrolü (Hangi modülleri görebilir?)
        y_sql = text("SELECT modul_adi, erisim_turu FROM ayarlar_yetkiler WHERE rol_adi = :r")
        y_res = conn.execute(y_sql, {"r": p_res[2]}).fetchall()
        
        print(f"\n--- YETKİ MATRİSİ (ERİŞİM) ---")
        if y_res:
            for y in y_res:
                print(f" - {y[0]}: {y[1]}")
        else:
            print("Bu rol için tanımlanmış özel bir yetki matrisi bulunamadı.")

if __name__ == "__main__":
    check_user_role()
