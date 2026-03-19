# EKLERİSTAN QMS YAPI RAPORU (REVİZE) — 19.03.2026

Bu rapor, kullanıcı geri bildirimleri doğrultusunda revize edilmiş, sistemin mevcut teknik durumunun kesin ve kanıta dayalı belgesidir.

---

## 1. MİMARİ GENEL BAKIŞ
- **Teknoloji Stack:**
  - **Dil:** Python 3.12+
  - **Arayüz:** Streamlit **v1.54.0** (QMS v3.1.5 Güvenlik Çekirdeği ile optimize edilmiş)
  - **OR/M:** SQLAlchemy 2.0 (engine.begin() atomic pattern)
  - **Veritabanı (Symmetric Twin):** 
    - Lokal: SQLite (`ekleristan_local.db` - WAL modu aktif)
    - Bulut: Supabase PostgreSQL
- **Kod Standartları:** Anayasa v3.x uyarınca 30 satır fonksiyon limiti, UPSERT zorunluluğu.

---

## 2. DOSYA / MODÜL HARİTASI

| Modül Dosyası / Dizini | Sorumluluğu | Durum |
| :--- | :--- | :--- |
| `logic/auth_logic.py` | Merkezi RBAC ve Bcrypt Auto-Migration | ✅ AKTİF |
| `logic/sync_manager.py` | T1 Seviye Senkronizasyon (Lokal <-> Bulut) | ✅ AKTİF |
| `ui/performans/` | Polivalans ve Performans Değerlendirme (5 Dosya) | ✅ AKTİF |
| `modules/qdms/` | Doküman ve Talimat Hayat Döngüsü | ✅ AKTİF |
| `ui/soguk_oda_ui.py` | SOSTS Ölçüm ve QR Entegrasyonu | ✅ AKTİF |
| `ui/raporlama_ui.py` | Kurumsal Raporlama ve Excel İhracatı | ✅ AKTİF |

---

## 3. VERİTABANI ŞEMASI (MEVCUT)

### Kritik Tablolar ve Kolon Güncellemeleri:
- **`personel`**: 
  - `id`, `ad_soyad`, `kullanici_adi`, `sifre`, `rol`
  - **`operasyonel_bolum_id` (Mevcut)**: Matris organizasyon eşleşmesi.
  - **`ikincil_yonetici_id` (Mevcut)**: 327 -> 358 kişi migrasyonu sonrası hiyerarşi.
- **`qdms_*` Serisi (6 Tablo)**: Belgeler, Şablonlar, Revizyon Logları, Yayın, Talimatlar ve Okuma Onayları. (Supabase üzerinde aktif).
- **`performans_degerledirme`**: Polivalans puanları ve sürüm takibi.
- **`ayarlar_bolum_mapping`**: Matris organizasyon eşleşmeleri (Supabase üzerinde aktif).
- **`ayarlar_moduller` & `ayarlar_yetkiler`**: Dinamik RBAC ve Menü yönetimi.

> [!NOTE]
> **Reconcilliation Notu:** `ayarlar_bolum_mapping` tablosu Supabase (Production) tarafında doğrulanmıştır; ancak yerel SQLite (`ekleristan_local.db`) kopyasında bulunmamaktadır. `dijital_donusum_kayitlari` tablosu her iki ortamda da henüz tespit edilememiştir.

---

## 4. QDMS MODÜLÜ (STAGE 7) - AYRINTILI DÖKÜM

Emre Çavdar'ın tanımladığı aşama numaralandırması ve implement edilen dosyalar:

| Aşama | İçerik | Dosyalar | Durum |
| :--- | :--- | :--- | :--- |
| **Stage 7.1-7.2** | Core Logic & Şablon | `belge_kayit.py`, `sablon_motor.py` | ✅ TEST GEÇTİ |
| **Stage 7.3** | PDF Üretimi | `pdf_uretici.py` (ReportLab) | ✅ TEST GEÇTİ |
| **Stage 7.4** | Revizyon & Yayım | `revizyon.py`, `yayim_yonetici.py` | ✅ TEST GEÇTİ |
| **Stage 7.5** | Talimat & Uyumluluk| `talimat_yonetici.py`, `uyumluluk_rapor.py` | ✅ TEST GEÇTİ |

---

## 5. GÜVENLİK & ROL YAPISI (13. ADAM)
- **T1:** Senkronizasyon (SyncManager).
- **T2:** Mimari Değişiklikler (onay mekanizmalı).
- **T3:** Kurulum ve Bootstrap.
- **Personel Girişi:** Bcrypt hash doğrulaması ve güvenli Plaintext fallback süreci.

---

## 6. TEST DURUMU
- **Toplam Test:** `test_qdms_stage7.py` içinde 5 ana süit.
- **Başarı Oranı:** %100 Success.
- **Yüzde:** QDMS modülü için %100 Coverage (Mantıksal).

---
*Rapor Revizyon No: 02 (19.03.2026)*
*Doğrulama: Fiziksel Dosya ve DB Denetimi*
