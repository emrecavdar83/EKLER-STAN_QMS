import pandas as pd
from sqlalchemy import create_engine, text

import os

# --- AYARLAR ---
# Eğer ortam değişkeninde varsa oraya bağlan, yoksa yerel dosyaya.
DB_URL = os.environ.get("DB_URL", 'sqlite:///ekleristan_local.db')
EXCEL_FILE = "Ekleristan_TEST_DATABASE.xlsx"
engine = create_engine(DB_URL)

def kurulum_yap():
    print("Veritabanı kontrol ediliyor (Güvenli Mod)...")
    
    # 1. TABLO KONTROLLERİ VE OLUŞTURMA (SILMEDEN - IF NOT EXISTS)
    with engine.connect() as conn:
        # Personel
        conn.execute(text("""CREATE TABLE IF NOT EXISTS personel (
            ad_soyad TEXT, kullanici_adi TEXT, sifre TEXT, rol TEXT, bolum TEXT,
            gorev TEXT, vardiya TEXT, durum TEXT, ise_giris_tarihi TEXT, sorumlu_bolum TEXT
        )"""))
        
        # Ürün Ayarları
        conn.execute(text("""CREATE TABLE IF NOT EXISTS ayarlar_urunler (
            urun_adi TEXT, raf_omru_gun INTEGER, numune_sayisi INTEGER, gramaj REAL, kod TEXT,
            olcum1_ad TEXT, olcum1_min REAL, olcum1_max REAL,
            olcum2_ad TEXT, olcum2_min REAL, olcum2_max REAL,
            olcum3_ad TEXT, olcum3_min REAL, olcum3_max REAL,
            olcum_sikligi_dk REAL, uretim_bolumu TEXT
        )"""))

        # Temizlik Planı
        conn.execute(text("""CREATE TABLE IF NOT EXISTS ayarlar_temizlik_plani (
            kat_bolum TEXT, yer_ekipman TEXT, risk TEXT, siklik TEXT, kimyasal TEXT,
            uygulama_yontemi TEXT, validasyon TEXT, uygulayici TEXT, kontrol_eden TEXT, kayit_no TEXT,
            validasyon_siklik TEXT, verifikasyon TEXT, verifikasyon_siklik TEXT
        )"""))

        # Kimyasallar
        conn.execute(text("""CREATE TABLE IF NOT EXISTS ayarlar_kimyasallar (
            kimyasal_adi TEXT, tedarikci TEXT, kullanim_alani TEXT, msds_link TEXT, tds_link TEXT, onay_durumu TEXT
        )"""))

        # Ürün Parametreleri (Yeni)
        # HATA DÜZELTME: Postgres 'AUTOINCREMENT' sevmez, 'SERIAL' ister.
        pk_def = "INTEGER PRIMARY KEY AUTOINCREMENT"
        if engine.dialect.name == 'postgresql':
            pk_def = "SERIAL PRIMARY KEY"
            
        conn.execute(text(f"""CREATE TABLE IF NOT EXISTS urun_parametreleri (
            id {pk_def},
            urun_adi TEXT, parametre_adi TEXT, min_deger REAL, max_deger REAL
        )"""))
        
        # Fabrika Tanımları
        conn.execute(text("CREATE TABLE IF NOT EXISTS tanim_bolumler (bolum_adi TEXT)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS tanim_ekipmanlar (ekipman_adi TEXT, bagli_bolum TEXT)"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS tanim_metotlar (metot_adi TEXT, aciklama TEXT)"))
        
        conn.commit()

    # 2. SEED DATE (SADECE TABLOLAR BOŞSA YÜKLE)
    try:
        # Personel Kontrolü
        p_count = pd.read_sql("SELECT count(*) FROM personel", engine).iloc[0,0]
        if p_count == 0:
            print(" -> Personel tablosu boş, Excel'den yükleniyor...")
            try:
                df_p = pd.read_excel(EXCEL_FILE, sheet_name="Ayarlar_Fabrika_Personel")
                df_u = pd.read_excel(EXCEL_FILE, sheet_name="Ayarlar_Personel")
                df_p.columns = [c.lower() for c in df_p.columns]
                df_u.columns = [c.lower() for c in df_u.columns]
                # Birleştir
                df_all = pd.concat([df_p, df_u], axis=0, ignore_index=True)
                df_all.to_sql('personel', engine, if_exists='append', index=False)
                print(f" -- {len(df_all)} Ppersonel eklendi.")
            except Exception as e: print(f" ! Excel Personel Hatası: {e}")
        else:
            print(" -> Personel tablosu dolu, atlanıyor.")

        # Ürün Kontrolü
        u_count = pd.read_sql("SELECT count(*) FROM ayarlar_urunler", engine).iloc[0,0]
        if u_count == 0:
            print(" -> Ürün listesi boş, Excel'den yükleniyor...")
            try:
                df_prod = pd.read_excel(EXCEL_FILE, sheet_name="Ayarlar_Urunler")
                df_prod.columns = [c.lower() for c in df_prod.columns]
                df_prod.to_sql('ayarlar_urunler', engine, if_exists='append', index=False)
            except: pass
        else:
            print(" -> Ürün listesi dolu, atlanıyor.")

        # Temizlik Planı Kontrolü
        t_count = pd.read_sql("SELECT count(*) FROM ayarlar_temizlik_plani", engine).iloc[0,0]
        if t_count == 0:
            print(" -> Temizlik planı boş, yükleniyor...")
            try:
                df_clean = pd.read_excel(EXCEL_FILE, sheet_name="Ayarlar_Temizlik_Plani")
                # Sütun İsimleri (Mapping)
                sutun_haritasi = {
                    'Bölüm': 'kat_bolum', 'Alan/Ekipman': 'yer_ekipman', 'Risk': 'risk', 'Sıklık': 'siklik',
                    'Kimyasal': 'kimyasal', 'Yöntem': 'uygulama_yontemi', 'Validasyon': 'validasyon',
                    'Sorumlu': 'uygulayici', 'Kontrol': 'kontrol_eden', 'Doküman No': 'kayit_no'
                }
                df_clean.rename(columns=sutun_haritasi, inplace=True)
                df_clean.columns = [c.lower().strip().replace(" ", "_").replace("ı","i").replace("ç","c").replace("ş","s").replace("ö","o").replace("ü","u").replace("ğ","g") for c in df_clean.columns]
                
                # Eksik sütunlar
                for col in ["validasyon_siklik", "verifikasyon", "verifikasyon_siklik"]:
                     if col not in df_clean.columns: df_clean[col] = "-"
                
                df_clean.to_sql('ayarlar_temizlik_plani', engine, if_exists='append', index=False)
            except Exception as e: print(f" ! Excel Temizlik Planı Hatası: {e}")
        else:
             print(" -> Temizlik planı dolu, atlanıyor.")

        # Fabrika Tanımları (Varsayılanlar)
        with engine.connect() as conn:
            if conn.execute(text("SELECT count(*) FROM tanim_bolumler")).scalar() == 0:
                conn.execute(text("INSERT INTO tanim_bolumler VALUES ('Üretim'), ('Depo'), ('Paketleme'), ('Ofis')"))
                conn.commit()
            
            if conn.execute(text("SELECT count(*) FROM tanim_metotlar")).scalar() == 0:
                conn.execute(text("INSERT INTO tanim_metotlar VALUES ('Köpüklü Yıkama', '-'), ('Silme', '-'), ('CIP', '-')"))
                conn.commit()

        print("\n" + "="*30)
        print(" SİSTEM GÜVENLİ ŞEKİLDE HAZIR (MEVCUT VERİ KORUNDU)")
        print("="*30)

    except Exception as e:
        print(f"\n❌ Kritik Hata: {e}")

if __name__ == "__main__":
    kurulum_yap()