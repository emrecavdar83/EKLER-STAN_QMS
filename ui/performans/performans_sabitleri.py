# modules/performans/performans_sabitleri.py
# QMS Anayasası: 0 Hardcode Kalkanı

# Polivalans eşikleri (BRC v9 / IFS v8 Uyumlu)
POLIVALANS_ESLIKLERI = {
    1: {"min": 0,  "maks": 45, "kod": 1, "metin": "Tanımlanan Görevi Gerçekleştiremez.", "renk": "#E24B4A"},
    2: {"min": 45, "maks": 60, "kod": 2, "metin": "Tanımlanan görev için eğitim ihtiyacı var.", "renk": "#EF9F27"},
    3: {"min": 60, "maks": 75, "kod": 3, "metin": "Tanımlanan görevi ancak kontrol altında gerçekleştirebilir.", "renk": "#F0D040"},
    4: {"min": 75, "maks": 90, "kod": 4, "metin": "Tanımlanan görevi gerçekleştirebilir.", "renk": "#97C459"},
    5: {"min": 90, "maks": 100, "kod": 5, "metin": "Tanımlanan görevi gerçekleştirebilir. Başka bir personeli eğitebilir.", "renk": "#1D9E75"},
}

AGIRLIKLAR = {
    "mesleki_teknik": 0.70,
    "kurumsal":       0.30,
}

MESLEKI_KRITERLER = [
    "kkd_kullanimi",
    "mesleki_kriter_2",
    "mesleki_kriter_3",
    "mesleki_kriter_4",
    "mesleki_kriter_5",
    "mesleki_kriter_6",
    "mesleki_kriter_7",
    "mesleki_kriter_8",
]

KURUMSAL_KRITERLER = [
    "calisma_saatleri_uyum",
    "ogrenme_kabiliyeti",
    "iletisim_becerisi",
    "problem_cozme",
    "kalite_bilinci",
    "ise_baglilik_aidiyet",
    "ekip_calismasi_uyum",
    "verimli_calisma",
]

KRITER_ETIKETLERI = {
    "kkd_kullanimi":          "KKD Kullanımı",
    "mesleki_kriter_2":       "Hijyen ve Sanitasyon Kuralları",
    "mesleki_kriter_3":       "Makine Kullanım Yetkinliği",
    "mesleki_kriter_4":       "HACCP/Kritik Kontrol Noktaları",
    "mesleki_kriter_5":       "Ürün Bilgisi ve Hassasiyeti",
    "mesleki_kriter_6":       "Kayıt Tutma ve Raporlama",
    "mesleki_kriter_7":       "Çalışma Alanı Düzeni (5S)",
    "mesleki_kriter_8":       "İş Güvenliği (İSG) Uyumu",
    
    "calisma_saatleri_uyum":  "Çalışma Saatlerine Uyum",
    "ogrenme_kabiliyeti":     "Öğrenme Kabiliyeti",
    "iletisim_becerisi":      "İletişim Becerisi",
    "problem_cozme":          "Problem Çözme Yeteneği",
    "kalite_bilinci":         "Kalite Bilinci",
    "ise_baglilik_aidiyet":   "İşe Bağlılık Ve Aidiyet",
    "ekip_calismasi_uyum":    "Ekip Çalışmasına Uygunluk",
    "verimli_calisma":        "Verimli Çalışma ve Tecrübe",
}

DONEM_SECENEKLERI = ["1. DÖNEM", "2. DÖNEM"]
POLIVALANS_RENKLERI = {1: "#E24B4A", 2: "#EF9F27", 3: "#F0D040", 4: "#97C459", 5: "#1D9E75"}

# Rol Tabanlı Erişim (Auth)
IZIN_TABLOSU = {
    "yeni_degerlendirme":   ["Admin", "ÜRETİM MÜDÜRÜ", "BÖLÜM SORUMLUSU", "GIDA MÜHENDİSİ"],
    "rapor_goruntule":      ["Admin", "ÜRETİM MÜDÜRÜ", "BÖLÜM SORUMLUSU", "GIDA MÜHENDİSİ", "KALİTE SORUMLUSU"],
    "denetim_raporu":       ["Admin", "GIDA MÜHENDİSİ", "YÖNETİM"],
    "senkronizasyon":       ["Admin"],
}
