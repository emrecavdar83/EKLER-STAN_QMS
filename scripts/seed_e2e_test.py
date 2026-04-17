import sqlalchemy
from sqlalchemy import text
import datetime

# Supabase Connection URL
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def seed_test_data():
    engine = sqlalchemy.create_engine(DB_URL)
    today = datetime.date.today().isoformat()
    
    with engine.begin() as conn:
        # 1. Admin ID'sini bul (Genelde 1 ama garantiye alalım)
        admin = conn.execute(text("SELECT id FROM ayarlar_kullanicilar WHERE kullanici_adi = 'Admin'")).fetchone()
        if not admin:
            print("Admin kullanıcısı bulunamadı!")
            return
        admin_id = admin[0]
        
        # 2. Katalogda test görevi var mı?
        katalog_id = 999
        conn.execute(text("""
            INSERT INTO gunluk_gorev_katalogu (id, ad, kategori, aktif_mi)
            VALUES (:id, 'E2E TEST GOREVI (OTONOM)', 'SISTEM', 1)
            ON CONFLICT (id) DO NOTHING
        """), {"id": katalog_id})
        
        # 3. Havuza atama yap (Bugün için)
        conn.execute(text("""
            INSERT INTO birlesik_gorev_havuzu 
            (personel_id, bolum_id, gorev_kaynagi, kaynak_id, atanma_tarihi, hedef_tarih, durum)
            VALUES (:pid, 1, 'KATALOG', :kid, :bugun, :bugun, 'BEKLIYOR')
            ON CONFLICT (personel_id, hedef_tarih, gorev_kaynagi, kaynak_id) 
            DO UPDATE SET durum = 'BEKLIYOR', tamamlanma_tarihi = NULL, sapma_notu = NULL
        """), {"pid": admin_id, "kid": katalog_id, "bugun": today})
        
        print(f"BAŞARILI: Admin ({admin_id}) için {today} tarihli test görevi enjekte edildi.")

if __name__ == "__main__":
    seed_test_data()
