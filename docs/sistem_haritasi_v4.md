# 🗺️ EKLERİSTAN QMS: YAŞAYAN SİSTEM HARİTASI (v4.0)

Bu harita, Anayasa Madde 7 gereği verinin yolculuğunu uçtan uca tanımlar. Harita güncellenmeden hiçbir modül tamamlanmış sayılmaz.

---

## 🏗️ Veri Yolculuğu Şablonu
**Verinin Kaynağı > İşlem Yolu > Kayıt Noktası (Tablo/Hücre) > Geri Çağırma Kodu**

---

## ❄️ 1. SOSTS (Soğuk Oda Takip Sistemi)
- **Kaynak:** Dolap üzerindeki Fiziksel QR Kod + Personel Girişi
- **İşlem Yolu:** `ui/soguk_oda_ui.py` > `soguk_oda_utils.py` (Validation & Logic)
- **Kayıt Noktası:** `ekleristan_local.db` / `sicaklik_olcumleri` & `olcum_plani` (Status Update)
- **Geri Çağırma:** `ui/soguk_oda_ui.py` -> Trend Analizi Sekmesi (`get_trend_data`)

## 👥 2. PERSONEL VE YETKİLENDİRME
- **Kaynak:** Yönetim Paneli / Excel Import
- **İşlem Yolu:** `logic/settings_logic.py` -> `validate_personnel_data`
- **Kayıt Noktası:** `personel` Tablosu
- **Geri Çağırma:** `app.py` -> `kullanici_yetkisi_var_mi` & `init_connection` (RBAC Check)

## 🔄 3. DİJİTAL İKİZ (SENKRONİZASYON)
- **Kaynak:** Lokal SQLite Veritabanı (`ekleristan_local.db`)
- **İşlem Yolu:** `scripts/sync_manager.py` (Upsert logic + Symmetric Mirror)
- **Kayıt Noktası:** Bulut PostgreSQL (Supabase)
- **Geri Çağırma:** Merkezi Yönetim Dashboards / Otonom AI Geliştirme Hafızası

---
*Anayasa Madde 7 Uyumluluk Beyanı: Bu harita, insanın ve yapay zekanın aynı dilde okuyabildiği yaşayan bir dökümandır.*
