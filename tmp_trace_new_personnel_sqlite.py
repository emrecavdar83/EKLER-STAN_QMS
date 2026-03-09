import sqlite3
import pandas as pd

def check_new_personnel_sqlite():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    
    with open('tmp_trace_personnel_result.txt', 'w', encoding='utf-8') as f:
        f.write("--- Yeni Eklenen Personeller (Ham Sorgu) ---\n")
        try:
            query = """
            SELECT p.id, p.ad_soyad, p.kullanici_adi, d.bolum_adi, p.vardiya, p.durum 
            FROM personel p 
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id 
            WHERE p.ad_soyad IN ('AYŞEGÜL TETİK', 'ZİLAN ÇİFTÇİ', 'ELİF ÇİFTÇİ', 'MUHAMMED İLKER', 'SONYA TETİK')
            """
            
            df = pd.read_sql_query(query, conn)
            f.write("DB Verisi:\n")
            f.write(df.to_string() + "\n")
            
            f.write("\n--- Hijyen Modülü Sorgusu Simülasyonu ---\n")
            query_hijyen = """
            SELECT p.ad_soyad,
                   COALESCE(d.bolum_adi, 'Tanımsız') as bolum,
                   p.vardiya,
                   p.durum
            FROM personel p
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
            WHERE p.ad_soyad IS NOT NULL
            """
            df_hijyen = pd.read_sql_query(query_hijyen, conn)
            
            df_hijyen.columns = ["Ad_Soyad", "Bolum", "Vardiya", "Durum"]
            if not df_hijyen.empty:
                df_hijyen['Durum'] = df_hijyen['Durum'].astype(str).str.strip().str.upper()
                df_hijyen['Vardiya'] = df_hijyen['Vardiya'].astype(str).str.strip()
                df_hijyen['Bolum'] = df_hijyen['Bolum'].astype(str).str.strip()
                
                # AKTIF filtresi
                df_aktif = df_hijyen[df_hijyen['Durum'] == "AKTİF"]
                f.write(f"Toplam Aktif Personel: {len(df_aktif)}\n")
                
                # Yeni personeller listede var mı?
                yeni_isimler = ['AYŞEGÜL TETİK', 'ZİLAN ÇİFTÇİ', 'ELİF ÇİFTÇİ', 'MUHAMMED İLKER', 'SONYA TETİK']
                for isim in yeni_isimler:
                    bulunan = df_aktif[df_aktif['Ad_Soyad'] == isim]
                    if not bulunan.empty:
                        f.write(f"✅ {isim} Hijyen Listesinde ÇIKIYOR. Bölüm: {bulunan['Bolum'].iloc[0]}, Vardiya: {bulunan['Vardiya'].iloc[0]}\n")
                    else:
                        f.write(f"❌ {isim} Hijyen Listesinde ÇIKMIYOR!\n")
                        # Neden çıkmadığını analiz et
                        ham_bulunan = df_hijyen[df_hijyen['Ad_Soyad'] == isim]
                        if ham_bulunan.empty:
                            f.write(f"  -> Sebep: Veritabanında (DB) hiç kaydı yok.\n")
                        else:
                            durum_str = ham_bulunan['Durum'].iloc[0]
                            vardiya_str = ham_bulunan['Vardiya'].iloc[0]
                            f.write(f"  -> DB'de var ama listeye girmiyor. Durum:'{durum_str}', Vardiya:'{vardiya_str}'\n")

        except Exception as e:
            f.write(f"Hata: {e}\n")

if __name__ == "__main__":
    check_new_personnel_sqlite()
