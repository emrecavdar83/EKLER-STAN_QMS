
# v8.5: Centralized Translation Registry for QMS Reports
# ANAYASA Madde 12: Zero-Hardcode & Localization

TRANSLATION_MAP = {
    # Common Headers
    "id": "ID",
    "tarih": "Tarih",
    "saat": "Saat",
    "kullanici": "Kontrolör",
    "kullanici_id": "Personel ID",
    "personel": "Personel Adı",
    "ad_soyad": "Ad Soyad",
    "durum": "Durum",
    "sebep": "Neden / Detay",
    "aksiyon": "Alınan Aksiyon",
    "bolum": "Bölüm",
    "departman": "Departman",
    "vardiya": "Vardiya",
    
    # MAP Specific
    "urun_adi": "Ürün Adı",
    "miktar": "Miktar",
    "fire_tipi": "Fire Tipi",
    "durus_nedeni": "Duruş Nedeni",
    "sure_dk": "Süre (dk)",
    "bobin_lot": "Bobin Lot No",
    
    # Cold Chain
    "oda_adi": "Oda Adı",
    "sicaklik_degeri": "Sıcaklık (°C)",
    "min_sicaklik": "Min Sınır",
    "max_sicaklik": "Max Sınır",
    "sapma_var_mi": "Sapma Durumu",
    
    # System
    "islem_tipi": "İşlem Türü",
    "detay": "İşlem Detayı",
    "ip_adresi": "IP Adresi",
    "cihaz_bilgisi": "Cihaz / Tarayıcı",
    "zaman": "Kayıt Zamanı"
}

def translate_columns(df):
    """Dataframe sütunlarını Türkçe karşılıklarıyla eşleştirir."""
    if df is None or df.empty:
        return df
    return df.rename(columns={col: TRANSLATION_MAP.get(col.lower(), col.title().replace('_', ' ')) for col in df.columns})

def get_tr_label(key, default=None):
    """Tekil bir anahtarın Türkçe karşılığını döner."""
    return TRANSLATION_MAP.get(str(key).lower(), default or key)
