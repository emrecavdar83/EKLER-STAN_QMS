# EKLERİSTAN QMS - SİSTEM MİMARİ HARİTASI (v3.1)

Bu doküman, Anayasa Madde 7 uyarınca sistemin mevcut yapısını, veri akışını ve modül bağımlılıklarını haritalandırır.

---

## 🏗️ 1. DOSYA YAPISI VE MODÜL HARİTASI

| Katman | Dosya Yolu | Temel Görev | Bağımlılıklar |
| :--- | :--- | :--- | :--- |
| **Giriş** | `app.py` | Ana Streamlit UI & Navigasyon | Logic, Database, UI |
| **Veritabanı** | `database/connection.py` | DB Bağlantı & Bakım (engine, init) | Streamlit Secrets, SQLAlchemy |
| **Veri Çekme** | `logic/data_fetcher.py` | SQL Sarmalayıcıları (run_query, veri_getir) | Database Connection |
| **Veri Yazma** | `logic/db_writer.py` | Güvenli Kayıt Ekleme (Wrapper) | Database Connection, Cache |
| **Mantık** | `logic/settings_logic.py` | Ayarlar modülü iş akışları | Database Connection |
| **Güvenlik** | `logic/auth_logic.py` | Yetkilendirme ve RBAC Mantığı | data_fetcher |
| **Cache Arabirimi**| `logic/cache_manager.py`| Merkezi Cache Temizleme | data_fetcher |
| **Konstantlar** | `constants.py` | Sabit değerler, ikonlar, renkler | - |
| **Senkronizasyon**| `scripts/sync_manager.py`| **Logical Key Sync Protocol (v3.1)** | logic, database |

---

## 🔁 2. REFACTORING DURUMU (AŞAMA 2: Bütünsel Restorasyon)

| Adım | Dosya | Durum | Açıklama |
| :--- | :--- | :--- | :--- |
| **1-12** | *Çeşitli* | ✅ Tamamlandı | Altyapı ve UI Modülerizasyonu. |
| **13.** | `scripts/sync_manager.py` | ✅ Tamamlandı | **ID Translation Katmanı:** Bölüm/Personel ID'leri isim üzerinden tercüme edilir. |
| **14.** | `database/` | ✅ Tamamlandı | **Schema Protection:** `bolum_adi` ve `kullanici_adi` UNIQUE olarak mühürlendi. |
| **15.** | `logic/auth_logic.py` | ✅ Tamamlandı | **Agnostic Comparison:** String normalizasyonu senkronizasyona entegre edildi. |

---

## 🧠 3. CACHE STRATEJİSİ (TTL TABLOSU)

| Fonksiyon | Kaynak | TTL (Saniye) | Gerekçe | Cleared By |
| :--- | :--- | :--- | :--- | :--- |
| `run_query` | `data_fetcher` | 600 | **V3.1 Sunucu Filtreleme Aktif** | - |
| `get_user_roles` | `data_fetcher` | 3600 | Statik Rol Listesi | - |
| `get_department_tree` | `data_fetcher` | 3600 | Hiyerarşik Yapı (Statikleşti) | `cache_manager` |
| `cached_veri_getir` | `data_fetcher` | 60 | Genel Tablo Verileri | `cache_manager` |
| `get_personnel_hierarchy`| `data_fetcher` | 3600 | Performans Odaklı | - |

---

## 🚨 4. TEKNİK KISITLAR VE KURALLAR (V3.1)
- **ID-Based Sync:** KESİNLİKLE YASAK. Tüm senkronizasyon "Logical Keys" (İsim, Kod) üzerinden yapılmalıdır.
- **Unique Constraint:** Kritik tanımlayıcı kolonlar (İsimler, Kullanıcı Adları) DB seviyesinde `UNIQUE` olmalıdır.
- **Normalization:** Veri karşılaştırmaları `auth_logic._normalize_string` üzerinden emoji ve büyük/küçük harf bağımsız yapılmalıdır.
- **to_sql Replacement:** YASAK. Sadece UPSERT kullanılabilir.

---
**Son Güncelleme:** 2026-03-15 18:35 (Istanbul)
**Otorite:** Anayasa v3.1 (EKL-KYS-AUD-001)
