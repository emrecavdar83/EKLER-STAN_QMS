# EKLERİSTAN QMS - TAM SİSTEM ANALİZ RAPORU
**Tarih:** 2026-02-26  
**Durum:** Kapsamlı Analiz Tamamlandı

---

## 1. MODÜL HARİTASI

| Dosya Adı | Fonksiyon / Amaç | Bağımlılıklar |
| :--- | :--- | :--- |
| `app.py` | Merkezi uygulama kontrolü, Navigasyon, Modül yönlendirme | `logic`, `ui`, `constants`, `soguk_oda_utils` |
| `constants.py` | Kurumsal hiyerarşi, Pozisyon seviyeleri, Vardiya tanımları | Bağımsız |
| `logic/settings_logic.py` | Personel, Bölüm, Lokasyon yönetimi için iş mantığı | `app.py` tarafından çağrılır |
| `soguk_oda_utils.py` | SOSTS (Soğuk Oda) backend süreçleri, QR üretim, Planlama | `app.py`, Veritabanı |
| `ui/soguk_oda_ui.py` | SOSTS kullanıcı arayüzü bileşenleri | `app.py`, `soguk_oda_utils` |
| `scripts/sync_manager.py` | Veri senkronizasyonu (DELETE desteği eklendi) | `sqlite`, `postgresql/supabase` |
| `scripts/sync_manager_v3.py` | Otonom çift yönlü (Symmetric Twin) senkronizasyon motoru | `sqlite`, `postgresql/supabase` |
| `sql/` | Veritabanı şeması ve migration betikleri | Supabase / PostgreSQL |

---

## 2. VERİTABANI TABLOLARI VE İLİŞKİLER

### Veri Tanımlama Tabloları:
- **`personel`**: Tüm kullanıcılar ve yetkileri burada tutulur. `id` üzerinden diğer tablolara bağlanır.
- **`ayarlar_bolumler`**: Fabrika hiyerarşisindeki bölümler.
- **`ayarlar_yetkiler`**: RBAC (Rol Bazlı Erişim Kontrolü) matrisini tutar.
- **`lokasyonlar`**: Kat > Bölüm > Hat > Ekipman hiyerarşisi.
- **`ayarlar_urunler`**: Üretilen ürünlerin listesi ve kalite limitleri.

### Operasyonel Kayıt Tabloları:
- **`depo_giris_kayitlari`**: Üretim girişleri.
- **`urun_kpi_kontrol`**: Kalite kontrol formları.
- **`gmp_denetim_kayitlari`**: GMP Denetim formları.
- **`hijyen_kontrol_kayitlari`**: Personel sağlık/hijyen takip.
- **`temizlik_kayitlari`**: Temizlik planı uygulama kayıtları.
- **`soguk_odalar`, `sicaklik_olcumleri`, `olcum_plani`**: SOSTS sisteminin temel verileri.

### Sistem Tabloları:
- **`sync_queue`**: Çevrimdışı veri senkronizasyonu için kullanılan geçici kuyruk.

---

## 3. KULLANICI ROLLERİ VE YETKİLERİ

| Rol | Erişim Seviyesi | Önemli Modüller |
| :--- | :--- | :--- |
| **Admin** | Tam Yetki | Ayarlar, Yetki Yönetimi, Tüm Modüller |
| **Yönetim** | Stratejik Görüntüleme | Kurumsal Raporlama, KPI Analizleri |
| **Kalite Ekibi** | Uzman / Denetçi | GMP Denetimi, Ürün Analizleri, SOSTS |
| **Bölüm Sorumlusu** | Operasyonel Yönetim | Kendi bölümünün Üretim ve Hijyen kayıtları |
| **Personel** | Temel Giriş | Sadece kendisine atanan ve yetki verilen formlar |

---

## 4. EKSİK VEYA YARIM KALAN MODÜLLER

1.  **Senkronizasyon (Phase 3-4):**
    - "Last Write Wins" timestamp mekanizması tam olarak `SyncManagerV3` içine gömülmedi.
    - Event-driven trigger yapısı (Manuel tetikleme yerine otomatik tetikleme) tam entegre edilmeli.
2.  **Hata Yönetimi (Error Handling):**
    - `app.py` içinde birçok blokta `try-except pass` kullanımı mevcut. Bunlar hata loglama sistemine bağlanmalı.
3.  **Performans:**
    - `app.py` 5.000 satırı aşmış durumda. Bu dosyanın bileşenlerinin `ui/` klasörüne taşınması (refactoring) tamamlanmalı.
4.  **Kullanıcı Bildirimleri (Phase 5):**
    - Senkronizasyon hataları veya kritik sıcaklık aşımları için anlık bildirim sistemi henüz pasif.

---

## 5. KRİTİK BAĞIMLILIKLAR VE RİSKLER

- **Supabase Bağımlılığı:** Bulut üzerindeki tüm veriler Supabase (PostgreSQL) üzerinde. Servis kesintisi durumunda lokal SQLite senkronizasyonu kritik önemde.
- **Sync Motoru (SPOF):** `sync_manager.py` projenin en hassas noktasıdır. Burada oluşacak bir mantık hatası veri mükerrerliğine veya kaybına yol açabilir.
- **app.py Monolitik Yapısı:** Tüm UI mantığının tek dosyada olması, geliştirme sırasında beklenmedik yan etkilere yol açabilir.

---

## 6. GENEL SAĞLIK SKORU

| Alan | Puan (1-10) | Notlar |
| :--- | :---: | :--- |
| **Kod Kalitesi** | 6 | `logic` ve `ui` ayrımı iyi başladı ancak `app.py` halen çok büyük. |
| **Güvenlik** | 7 | RBAC yapısı standartlara uygun. Şifreleme güçlendirilebilir. |
| **Performans** | 7 | Caching efektif kullanılıyor. Tablo büyüklüğü arttıkça query optimizasyonu gerekecek. |
| **Test Coverage** | 3 | Birim testler (Unit Tests) ve entegrasyon testleri eksik. |
| **Dokümantasyon**| 4 | Mimari doküman (ARCHITECTURE.md) güncel ancak teknik detay dökümü artırılmalı. |

**Öneri:** Önümüzdeki süreçte `app.py`'ın parçalanmasına ve senkronizasyon motorunun otonom yapısının (Phase 4-5) tamamlanmasına odaklanılmalıdır.
