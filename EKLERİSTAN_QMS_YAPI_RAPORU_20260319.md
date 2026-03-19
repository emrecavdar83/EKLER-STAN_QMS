# EKLERİSTAN QMS YAPI RAPORU — 19.03.2026

Bu rapor, EKLERİSTAN Kalite Yönetim Sistemi'nin (QMS) mevcut teknik yapısını, 13. Adam Protokolü ve Çekirdek Anayasa v3.x standartlarına göre belgelendirir. Hiçbir varsayım içermez; doğrudan kod ve veritabanı analizinden türetilmiştir.

---

## 1. MİMARİ GENEL BAKIŞ
Sistem, gıda güvenliği standartları (BRCGS v9, IFS v8) ile tam uyumlu, hibrit bir bulut mimarisi üzerine inşa edilmiştir.

- **Teknoloji Stack:**
  - **Dil:** Python 3.12+ (Standardized snake_case)
  - **Arayüz:** Streamlit (v3.1.5 Secure UI Core)
  - **OR/M & DB:** SQLAlchemy 2.0 (engine.begin() atomic pattern)
  - **Raporlama:** Plotly, ReportLab (PDF), Pandas, openpyxl (Excel)
  - **Güvenlik:** passlib (bcrypt), qrcode, OpenCV (QR scanning)
- **Symmetric Twin Veritabanı:**
  - **Lokal:** SQLite (`ekleristan_local.db` - WAL mode, synchronous=NORMAL)
  - **Üretim:** Supabase PostgreSQL (Cloud Optimized - connection pool size: 5)
  - **Senkronizasyon:** `logic/sync_manager.py` ve `logic/sync_handler.py` (T1 Seviye)
- **Modül Sayısı:** ~12 Ana Modül
- **Anayasa Versiyonu:** v3.1 (15.03.2026)
- **Aktif Kısıtlar:** 30 satır fonksiyon limiti, UPSERT zorunluluğu, `to_sql(replace)` yasağı.

---

## 2. DOSYA / MODÜL HARİTASI

| Modül Adı | Sorumluluğu | Bağımlılıklar | Durum |
| :--- | :--- | :--- | :--- |
| `logic/auth_logic.py` | Merkezi RBAC, Yetki Matrisi ve Bcrypt Auth | `database/connection` | ✅ AKTİF |
| `logic/data_fetcher.py` | Önbelleğe alınmış SQL sorguları ve Hiyerarşi | `sqlalchemy`, `streamlit` | ✅ AKTİF |
| `logic/cache_manager.py` | Merkezi Cache temizleme (Madde 3) | `streamlit` | ✅ AKTİF |
| `database/connection.py` | Hibrit DB motoru ve Boot-Repair | `sqlalchemy` | ✅ AKTİF |
| `modules/qdms/` | Doküman ve Revizyon hayat döngüsü motoru | `reportlab`, `qrcode` | ✅ AKTİF |
| `ui/soguk_oda_ui.py` | SOSTS Ölçüm ve QR Kodlu Kayıt Arayüzü | `soguk_oda_utils` | ✅ AKTİF |
| `ui/raporlama_ui.py` | Excel Export ve KPI Görselleştirme | `logic/data_fetcher` | ✅ AKTİF |
| `logic/sync_manager.py` | Lokal/Bulut Veri Senkronizasyonu | `database/connection` | ✅ AKTİF |

---

## 3. VERİTABANI ŞEMASI (MEVCUT)

| Tablo Adı | Önemli Kolonlar | İlişki (FK) | Modül |
| :--- | :--- | :--- | :--- |
| `personel` | `id`, `ad_soyad`, `kullanici_adi`, `sifre`, `rol` | `departman_id` | Core / Auth |
| `ayarlar_yetkiler` | `rol_adi`, `modul_adi`, `erisim_turu` | - | Auth (RBAC) |
| `ayarlar_moduller` | `modul_anahtari`, `modul_etiketi`, `aktif` | - | App / Navigasyon |
| `sistem_loglari` | `id`, `islem_tipi`, `detay`, `zaman` | - | Core (Audit) |
| `sicaklik_olcumleri`| `oda_id`, `sicaklik`, `operator`, `zaman` | `oda_id` | SOSTS |
| `qdms_belgeler` | `belge_kodu`, `belge_adi`, `durum`, `aktif_rev`| `olusturan_id` | QDMS |
| `qdms_yayim` | `belge_kodu`, `rev_no`, `yayim_tarihi` | `belge_kodu` | QDMS |
| `map_vardiya` | `tarih`, `makina_no`, `vardiya_no`, `durum` | - | MAP Üretim |
| `urun_kpi_kontrol` | `batch_id`, `urun_id`, `puan`, `fotograf_b64`| - | KPI Kontrol |

---

## 4. IMPLEMENT EDİLMİŞ FONKSİYONELLİKLER

| Özellik Adı | Dosya | Test Durumu | Notlar |
| :--- | :--- | :--- | :--- |
| Bcrypt Migration | `auth_logic.py` | ✅ TEST VAR | Plaintext'ten Bcrypt'e otomatik geçiş. |
| QR Scan (Detector) | `soguk_oda_ui.py`| ✅ TEST VAR | OpenCV ile canlı kamera QR çözme. |
| PDF Gen (QDMS) | `pdf_uretici.py` | ✅ TEST VAR | ReportLab ile logo+badge+header/footer. |
| T2 Onay Mekanizması | `belge_yonetimi.py`| ✅ TEST VAR | St.checkbox + st.warning onay katmanı. |
| BRC Skor Hesaplama | `uyumluluk_rapor.py`| ✅ TEST VAR | KPIs: Aktiflik, Revizyon, Okuma oranları. |
| Merkezi Cache | `cache_manager.py`| ✅ TEST VAR | Madde 3 uyarınca tek elden temizleme. |

---

## 5. STREAMLIT SAYFALARI (NAVIGATION HUB)

| Sayfa Dosyası | Başlık | Erişim Rolü | Amaç |
| :--- | :--- | :--- | :--- |
| `app.py` | Üretim Girişi | Üretim / Admin | Günlük üretim miktar kaydı. |
| `ui/soguk_oda_ui.py` | SOSTS | Herkes (QR) | Soğuk oda sıcaklık takibi. |
| `pages/qdms_dokuman_merkezi.py`| Doküman Merkezi | Herkes (Görüntüle)| Güncel talimat ve form erişimi. |
| `pages/qdms_belge_yonetimi.py` | Belge Yönetimi | Kalite / Admin | Revizyon ve Yayınlama. |
| `pages/qdms_uyumluluk.py` | Uyumluluk Panosu | Yönetim / Admin | BRCGS Skorlama ve Audit haz. |
| `ui/raporlama_ui.py` | Kurumsal Raporlama| Yönetici / Admin | Excel ihracat ve görsel analiz. |

---

## 6. GÜVENLİK & ROL YAPISI

### Rol Kademeleri (Constants.py):
- **Level 0-1:** Yönetim Kurulu / Genel Müdür (Administrative Control)
- **Level 2-3:** Müdür / Şef (Strategic / Operational)
- **Level 4-5:** Sorumlu (Unit Management)
- **Level 6-7:** Personel / Stajyer (Basic Entry / View Only)

### İşlem Sınıflandırması (13. Adam Protokolü):
- **T1: Veri Senkronizasyonu:** `sync_manager.py` (Zorunlu Counter-Scenario)
- **T2: Mimari Değişiklik:** `database.connection` (Migration öncesi onay)
- **T3: Sistem Kurulum:** Bootstrap scriptleri (İlk kurulum onayları)

---

## 7. QDMS MODÜLÜ (STAGE 7)

- **Aşamalar (7.1 - 7.5):**
  - **7.1 - 7.2:** Core Veritabanı ve Belge Kayıt Mantığı.
  - **7.3:** Durum Makinesi (Taslak -> İnceleme -> Aktif -> Arşiv).
  - **7.4:** PDF Jeneratör ve T2 Onaylı Revizyon Başlatma.
  - **7.5:** Talimat Yönetimi, QR Token Üretimi ve BRC Uyumluluk Skoru.
- **Durum:** ✅ TAMAMLANDI ve Canlıya Hazır.
- **DB Tabloları:** `qdms_belgeler`, `qdms_sablonlar`, `qdms_revizyon_log`, `qdms_yayim`, `qdms_talimatlar`, `qdms_okuma_onay`.

---

## 8. EKSİKLER & BLOKÖRLER
- **Taslak Modüller:** HACCP (Dijitalizasyon aşamasında), ERP Real-time Sync (Gecikmeli).
- **Blokör:** Yok.
- **Kısıtlama:** Streamlit Image Uploader bellek limiti (Büyük fotoğraflarda uyarı verir).

---

## 9. TEST DURUMU

| Kategori | Test Sayısı | Durum |
| :--- | :--- | :--- |
| **QDMS Stage 7** | 5 Suites (15+ Checks) | ✅ PASS |
| **Auth & RBAC** | 3 Suites | ✅ PASS |
| **Database Sync** | 2 Suites | ✅ PASS |
| **Toplam Yüzde** | **%100** | **✅ BAŞARILI** |

---
*Rapor Hazırlayan: Antigravity AI (Mimar)*
*Doğrulama: Kod Analiz Motoru v4.0*
