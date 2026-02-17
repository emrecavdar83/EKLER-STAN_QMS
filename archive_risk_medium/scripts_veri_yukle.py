import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- 1. VERİTABANI BAĞLANTISI ---
DB_URL = 'sqlite:///ekleristan_local.db'
engine = create_engine(DB_URL)
conn = engine.connect()

print("Veritabanına bağlanıldı...")

# --- 2. TABLOLARI OLUŞTUR (Eksik olan Temizlik tabloları dahil) ---
sql_creates = [
    # Personel (Hem giriş yapanlar hem fabrika personeli buraya toplanacak)
    """CREATE TABLE IF NOT EXISTS personel (
        kullanici_adi TEXT, sifre TEXT, rol TEXT, 
        ad_soyad TEXT, bolum TEXT, gorev TEXT, vardiya TEXT, durum TEXT
    )""",
    
    # Ürün Ayarları
    """CREATE TABLE IF NOT EXISTS ayarlar_urunler (
        urun_adi TEXT, raf_omru_gun INTEGER, numune_sayisi INTEGER, 
        olcum1_ad TEXT, olcum1_min REAL, olcum1_max REAL,
        olcum2_ad TEXT, olcum2_min REAL, olcum2_max REAL,
        olcum3_ad TEXT, olcum3_min REAL, olcum3_max REAL,
        uretim_bolumu TEXT, olcum_sikligi_dk INTEGER
    )""",
    
    # Depo / Üretim Girişleri
    """CREATE TABLE IF NOT EXISTS depo_giris_kayitlari (
        tarih TEXT, vardiya TEXT, kullanici TEXT, islem_tipi TEXT, 
        urun TEXT, lot_no TEXT, miktar INTEGER, fire INTEGER, 
        notlar TEXT, zaman_damgasi TEXT
    )""",
    
    # KPI Kontrol
    """CREATE TABLE IF NOT EXISTS urun_kpi_kontrol (
        tarih TEXT, saat TEXT, vardiya TEXT, urun TEXT, lot_no TEXT, 
        stt TEXT, numune_no TEXT, olcum1 REAL, olcum2 REAL, olcum3 REAL, 
        karar TEXT, kullanici TEXT, tat TEXT, goruntu TEXT, notlar TEXT
    )""",
    
    # Hijyen Kontrol
    """CREATE TABLE IF NOT EXISTS hijyen_kontrol_kayitlari (
        tarih TEXT, saat TEXT, kullanici TEXT, vardiya TEXT, bolum TEXT, 
        personel TEXT, durum TEXT, sebep TEXT, aksiyon TEXT, genel_karar TEXT
    )""",

    # --- YENİ EKLENEN TEMİZLİK TABLOLARI ---
    """CREATE TABLE IF NOT EXISTS ayarlar_temizlik_plani (
        kat_bolum TEXT, yer_ekipman TEXT, risk TEXT, siklik TEXT, 
        kimyasal TEXT, uygulama_yontemi TEXT, validasyon TEXT, 
        uygulayici TEXT, kontrol_eden TEXT, kayit_no TEXT
    )""",
    
    """CREATE TABLE IF NOT EXISTS temizlik_kayitlari (
        tarih TEXT, saat TEXT, kullanici TEXT, bolum TEXT, 
        islem TEXT, durum TEXT, dogrulama_tipi TEXT, aciklama TEXT
    )"""
]

for sql in sql_creates:
    conn.execute(text(sql))
print("Tablo yapıları güncellendi.")

# --- 3. CSV DOSYALARINI YÜKLEME FONKSİYONU ---
def csv_yukle(dosya_adi, tablo_adi, kolon_haritasi=None):
    tam_yol = dosya_adi  # Dosyalar aynı klasördeyse direkt adını kullanın
    
    # Dosya isminde "Ekleristan_TEST_DATABASE.xlsx - " ön eki varsa onu dikkate al
    # Eğer dosyaların isimlerini kısalttıysan burayı güncelle.
    # Senin yüklediğin dosya isimlerine göre:
    on_ek = "Ekleristan_TEST_DATABASE.xlsx - "
    tam_dosya_adi = f"{on_ek}{dosya_adi}" if not os.path.exists(dosya_adi) else dosya_adi
    
    if os.path.exists(tam_dosya_adi):
        try:
            df = pd.read_csv(tam_dosya_adi)
            
            # Kolon Haritası Varsa Uygula (CSV Başlığı -> SQL Kolonu)
            if kolon_haritasi:
                df = df.rename(columns=kolon_haritasi)
            
            # Sadece veritabanındaki kolonları seç (Hata önlemek için)
            # Burada basitçe append yapıyoruz, kolon isimleri tutmalı.
            df.columns = [c.lower() for c in df.columns] # Hepsini küçük harf yap
            
            # Veritabanına yaz
            df.to_sql(tablo_adi, engine, if_exists='append', index=False)
            print(f"OK: {dosya_adi} -> '{tablo_adi}' tablosuna yuklendi. ({len(df)} kayit)")
        except Exception as e:
            print(f"HATA: {dosya_adi} yuklenirken hata: {e}")
    else:
        print(f"UYARI: Dosya bulunamadi: {tam_dosya_adi}")

# --- 4. YÜKLEME İŞLEMLERİ ---

# 1. Ayarlar: Ürünler
# Mapping: CSV başlıklarını SQL sütunlarına eşliyoruz
mapping_urunler = {
    "Urun_Adi": "urun_adi", "Raf_Omru_Gun": "raf_omru_gun", 
    "Olcum1_Ad": "olcum1_ad", "Olcum1_Min": "olcum1_min", "Olcum1_Max": "olcum1_max",
    "Uretim_Bolumu": "uretim_bolumu", "Numune_Sayisi": "numune_sayisi"
}
csv_yukle("Ayarlar_Urunler.csv", "ayarlar_urunler", mapping_urunler)

# 2. Personel (Giriş Kullanıcıları)
mapping_users = {
    "Kullanici_Adi": "kullanici_adi", "Sifre": "sifre", "Rol": "rol", "Sorumlu_Bolum": "bolum"
}
csv_yukle("Ayarlar_Personel.csv", "personel", mapping_users)

# 3. Personel (Fabrika Çalışanları)
mapping_workers = {
    "Ad_Soyad": "ad_soyad", "Bolum": "bolum", "Vardiya": "vardiya", "Durum": "durum", "Gorev": "gorev"
}
csv_yukle("Ayarlar_Fabrika_Personel.csv", "personel", mapping_workers)

# 4. Depo Giriş Kayıtları
mapping_depo = {
    "Kayit_Yapan": "kullanici", "Islem_Turu": "islem_tipi", "Urun_Adi": "urun", 
    "Parti_Lot_No": "lot_no", "Miktar_Adet": "miktar", "Fire_Adet": "fire", "Kayit_Zamani": "zaman_damgasi"
}
csv_yukle("Depo_Giris_Kayitlari.csv", "depo_giris_kayitlari", mapping_depo)

# 5. KPI Kontrol
mapping_kpi = {
    "Urun_Adi": "urun", "Kayit_Yapan": "kullanici", "Duyusal_Tat": "tat", "Duyusal_Goruntu": "goruntu",
    "Olcum_1": "olcum1", "Olcum_2": "olcum2", "Olcum_3": "olcum3"
}
csv_yukle("Urun_KPI_Kontrol.csv", "urun_kpi_kontrol", mapping_kpi)

# 6. Hijyen Kayıtları
mapping_hijyen = {
    "Denetleyen": "kullanici", "Personel_Adi": "personel", "Genel_Karar": "genel_karar"
}
csv_yukle("Hijyen_Kontrol_Kayitlari.csv", "hijyen_kontrol_kayitlari", mapping_hijyen)


# 7. Temizlik Planı (Akıllı Yükleme)
def temizlik_plani_yukle():
    tablo_adi = "ayarlar_temizlik_plani"
    excel_dosya = "Ekleristan_TEST_DATABASE.xlsx"
    
    if os.path.exists(excel_dosya):
        try:
            # Excel'den oku
            df = pd.read_excel(excel_dosya, sheet_name="Ayarlar_Temizlik_Plani")
            
            # Kolon Isimlerini Normallestir (kucuk harf, bosluksuz)
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Akilli Mapping
            yeni_kolonlar = {}
            for col in df.columns:
                c_str = str(col).lower()
                if any(x in c_str for x in ['kat', 'bölüm', 'bolum', 'department']):
                    yeni_kolonlar[col] = 'kat_bolum'
                elif any(x in c_str for x in ['alan', 'ekipman', 'item']):
                    yeni_kolonlar[col] = 'yer_ekipman'
                elif 'risk' in c_str:
                    yeni_kolonlar[col] = 'risk'
                elif any(x in c_str for x in ['siklik', 'sıklık', 'frequency']):
                    yeni_kolonlar[col] = 'siklik'
                elif any(x in c_str for x in ['kimyasal', 'chemical', 'konsantrasyon']):
                    yeni_kolonlar[col] = 'kimyasal'
                elif any(x in c_str for x in ['yöntem', 'yontem', 'method']):
                    yeni_kolonlar[col] = 'uygulama_yontemi'
                elif any(x in c_str for x in ['validasyon', 'verification', 'doğrulama', 'dogrulama']):
                    yeni_kolonlar[col] = 'validasyon'
                elif any(x in c_str for x in ['uygulayıcı', 'uygulayici', 'sorumlu']):
                    yeni_kolonlar[col] = 'uygulayici'
                elif any(x in c_str for x in ['kontrol', 'denetleyen']):
                    yeni_kolonlar[col] = 'kontrol_eden'
                elif any(x in c_str for x in ['kayıt', 'kayit', 'no']):
                    yeni_kolonlar[col] = 'kayit_no'
            
            df = df.rename(columns=yeni_kolonlar)
            
            # Eksik sütunları varsayılan değerlerle doldur
            beklenen_sutunlar = [
                'kat_bolum', 'yer_ekipman', 'risk', 'siklik', 'kimyasal',
                'uygulama_yontemi', 'validasyon', 'uygulayici', 'kontrol_eden', 'kayit_no'
            ]
            
            for col in beklenen_sutunlar:
                if col not in df.columns:
                    if col == 'risk': df[col] = 'Belirtilmemiş'
                    else: df[col] = '-' # Diğerleri için tire koy

            # Sadece gerekli sütunları ve doğru sırada al
            df_final = df[beklenen_sutunlar]
            
            # Veritabanını sıfırdan oluştur
            df_final.to_sql(tablo_adi, engine, if_exists='replace', index=False)
            print(f"OK: '{tablo_adi}' tablosuna YENİ ŞEMA ile yüklendi. ({len(df_final)} kayıt)")
            print(f"    -> Yüklenen Sütunlar: {df_final.columns.tolist()}")
            
        except Exception as e:
             print(f"HATA: {excel_dosya} yuklenirken hata: {e}")
    else:
        print(f"UYARI: {excel_dosya} bulunamadi, atlaniyor.")

temizlik_plani_yukle()

# 8. Temizlik Kayıtları (Yeni)
mapping_temizlik_log = {
    "Islem": "islem", "Dogrulama_Tipi": "dogrulama_tipi"
}
csv_yukle("Temizlik_Kayitlari.csv", "temizlik_kayitlari", mapping_temizlik_log)

print("\nTum islemler tamamlandi! app.py dosyasini calistirabilirsiniz.")