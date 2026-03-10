
import psycopg2

DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def compare_personnel_dept():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("--- PERSONNEL - DEPARTMENT MAPPING AUDIT ---")
        
        # 1. Departman ID'leri ve İsimlerini Çek
        cur.execute("SELECT id, bolum_adi FROM ayarlar_bolumler")
        dept_map = {r[0]: r[1] for r in cur.fetchall()}
        
        # 2. Personel Tablosundaki Tutarsızlıkları Bul (id vs bolum adı uyuşmazlığı)
        cur.execute("""
            SELECT id, ad_soyad, departman_id, bolum, guncelleme_tarihi 
            FROM personel 
            WHERE guncelleme_tarihi::date = CURRENT_DATE
            ORDER BY guncelleme_tarihi DESC
        """)
        rows = cur.fetchall()
        
        print(f"\nBugün güncellenen {len(rows)} kayıt inceleniyor...")
        mismatch_count = 0
        for r in rows:
            pid, ad, d_id, bolum_text, tarih = r
            expected_dept = dept_map.get(d_id, "Bilinmiyor")
            
            # Normalizasyon (boşlukları sil, küçük harf yap)
            clean_expected = str(expected_dept).strip().lower().replace(".. ", "").replace("↳ ", "")
            clean_actual = str(bolum_text).strip().lower().replace(".. ", "").replace("↳ ", "")
            
            if clean_expected != clean_actual and d_id is not None:
                mismatch_count += 1
                print(f"⚠️ UYUMSUZLUK | ID: {pid:3} | Ad: {ad:20} | Tarih: {tarih}")
                print(f"   -> DB ID: {d_id} ({expected_dept}) | Metin: {bolum_text}")

        print(f"\nToplam {mismatch_count} adet uyumsuz kayıt bulundu.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    compare_personnel_dept()
