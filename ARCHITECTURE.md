# EKLERİSTAN QMS - SİSTEM MİMARİ HARİTASI (v2.0)

Bu doküman, Anayasa Madde 7 uyarınca sistemin mevcut yapısını, veri akışını ve modül bağımlılıklarını haritalandırır.

---

## 🏗️ 1. DOSYA YAPISI VE MODÜL HARİTASI

| Katman | Dosya Yolu | Temel Görev | Bağımlılıklar |
| :--- | :--- | :--- | :--- |
| **Giriş** | `app.py` | Ana Streamlit UI & Navigasyon | Logic, Database, UI |
| **Veritabanı** | `database/connection.py` | DB Bağlantı & Bakım (engine, init) | Streamlit Secrets, SQLAlchemy |
| **Veri Çekme** | `logic/data_fetcher.py` | SQL Sarmalayıcıları (run_query, veri_getir) | Database Connection |
| **Veri Yazma** | `logic/db_writer.py` | [YENİ] Güvenli Kayıt Ekleme (Wrapper) | Database Connection, Cache |
| **Mantık** | `logic/settings_logic.py` | Ayarlar modülü iş akışları | Database Connection |
| **Güvenlik** | `logic/auth_logic.py` | Yetkilendirme ve RBAC Mantığı | data_fetcher |
| **Cache Arabirimi**| `logic/cache_manager.py`| Merkezi Cache Temizleme | data_fetcher |
| **Konstantlar** | `constants.py` | Sabit değerler, ikonlar, renkler | - |
| **Senkronizasyon**| `scripts/sync_manager.py`| Symmetric Twin Senkronizasyon | logic, database |

---

## 🔁 2. REFACTORING DURUMU (AŞAMA 1)

| Adım | Dosya | Durum | Açıklama |
| :--- | :--- | :--- | :--- |
| **1.** | `database/connection.py` | ✅ Tamamlandı | Bağlantı ve bakım fonksiyonları ayrıldı. |
| **2.** | `logic/data_fetcher.py` | ✅ Tamamlandı | SQL sorguları ve veri çekme merkezi hale geldi. |
| **3.** | `logic/auth_logic.py` | ✅ Tamamlandı | Yetkilendirme ve login mantığı taşındı. |
| **4.** | `logic/sync_handler.py` | ✅ Tamamlandı | Merkezi senkronizasyon butonu lojiği. |
| **4.5** | `logic/cache_manager.py` | ✅ Tamamlandı | Merkezi cache yönetimi (Madde 3). |
| **5.** | `ui/uretim_ui.py` | ✅ Tamamlandı | Üretim Girişi modülü UI bileşeni. |
| **6.** | `ui/kpi_ui.py` | ✅ Tamamlandı | KPI & Kalite Kontrol modülü UI (Helperlara bölündü). |
| **7.** | `ui/gmp_ui.py` | ✅ Tamamlandı | GMP Denetimi modülü UI (Frekans & Soru yönetimi). |
| **8.** | `ui/hijyen_ui.py` | ✅ Tamamlandı | Personel Hijyen modülü UI (Toplu Kayıt Entegrasyonu). |
| **9.** | `ui/temizlik_ui.py` | ✅ Tamamlandı | Temizlik Kontrol modülü UI (Hiyerarşik & Çift Tablı). |
| **10.** | `ui/raporlama_ui.py` | ✅ Tamamlandı | Kurumsal Raporlama modülü. |
| **11.** | `ui/ayarlar/` | ✅ Tamamlandı | Ayarlar modülü tam modülerizasyon. |
| **12.** | `logic/db_writer.py`| ✅ Tamamlandı | Kayıt fonksiyonlarının app.py'den ayrılması. |

---

## 🧠 3. CACHE STRATEJİSİ (TTL TABLOSU)

| Fonksiyon | Kaynak | TTL (Saniye) | Gerekçe | Cleared By |
| :--- | :--- | :--- | :--- | :--- |
| `run_query` | `data_fetcher` | 1 | Performans/Anlık Veri | - |
| `get_user_roles` | `data_fetcher` | 3600 | Statik Rol Listesi | - |
| `get_department_tree` | `data_fetcher` | 600 | Hiyerarşik Yapı | `cache_manager` |
| `cached_veri_getir` | `data_fetcher` | 60 | Genel Tablo Verileri | `cache_manager` |
| `get_personnel_hierarchy`| `data_fetcher` | 5 | Anlık Şema Güncelliği | - |
| `init_connection` | `connection` | N/A | Resource (Ömür boyu) | - |

---

## 🚨 4. TEKNİK KISITLAR VE KURALLAR (V2.0)
- **to_sql Replacement:** YASAK. Sadece UPSERT kullanılabilir.
- **Hardcode:** YASAK. Tüm sınırlar veritabanından okunur.
- **Cache Clear:** Sadece `logic/cache_manager.py` üzerinden yapılabilir.
- **Fonksiyon Boyu:** Maksimum 30 satır kuralına uyulmalıdır.

---
**Son Güncelleme:** 2026-02-26 18:52 (Istanbul)
**Otorite:** Anayasa v2.0
