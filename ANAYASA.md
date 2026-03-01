# EKLERİSTAN A.Ş.
# KALİTE YÖNETİM SİSTEMİ (QMS)
# ÇEKİRDEK ANAYASASI
# VERSİYON 2.0  —  NİHAİ SÜRÜM

| Alan | Bilgi |
| :--- | :--- |
| **Versiyon** | 2.0 (Güncellenmiş) |
| **Önceki Versiyon** | 1.0 (İlk Yayın) |
| **Güncelleme Tarihi** | 26.02.2026 |
| **Hazırlayan** | Emre ÇAVDAR — Sistem Admin |
| **Kapsam** | ERP · KPI/GMP · HACCP — Tüm Modüller |
| **Hedef Sertifikalar** | BRC v9 · IFS v8 · FSSC 22000 v6 · ISO 9001 · AIB |
| **Mimari** | Python + Streamlit + SQLite (Lokal) + Supabase PostgreSQL (Üretim) |

---

## ⚠️ V2.0 GÜNCELLEME GEREKÇESİ
Bu güncelleme, refactoring sürecinde tespit edilen 4 kritik güvenlik ve mimari açığı kapatır.

1.  **AÇIK 1 — Madde 5 İhlali:** `kullanici_yetkisi_getir()` cache TTL=300 sn idi. Yetki değişikliği 5 dk boyunca eski yetki ile çalışıyordu. **Yeni kural: TTL ≤ 60 saniye.**
2.  **AÇIK 2 — Madde 6 İhlali:** `to_sql(..., if_exists='replace')` audit log, foreign key ve trigger'ları siliyordu. Bu geçmişe dönük veri manipülasyonuna kapı açıyordu. **Yeni kural: Sadece UPSERT/UPDATE+INSERT pattern. REPLACE yasak.**
3.  **AÇIK 3 — Madde 3 İhlali:** `cached_veri_getir.clear()` çağrıları `app.py` geneline dağılmıştı. Stale data (bayat veri) riski vardı. **Yeni kural: Cache temizleme merkezi cache_manager'dan.**
4.  **AÇIK 4 — Madde 7 İhlali:** `ARCHITECTURE.md` refactoring adımlarında güncellenmiyordu. **Yeni kural: Her adım tamamlandığında harita güncellemesi zorunludur.**

---

## MADDE 1 — Tam Dinamik ve Parametrik Altyapı
### Sıfır Hardcode Prensibi
Sistemin hiçbir kuralı, iş akışı veya tolerans limiti (örn. sıcaklık sınırları, KPI eşikleri, raf ömrü) kodun içine sabitlenemez. Tüm yapı, kullanıcıların arayüz üzerinden dinamik olarak yönetebileceği, değiştirebileceği esneklikte çalışır.

**Zorunlu Uygulama Kuralları:**
- Sıcaklık limitleri, numune sayıları, raf ömrü, KPI eşikleri → Veritabanından okunur
- Departman hiyerarşisi, rol isimleri, yetki seviyeleri → Arayüzden tanımlanır
- Hiçbir modül kendi veritabanı şemasını hard-code içermez
- Yapılandırma değişiklikleri audit log'a düşer (kim/ne zaman/ne değiştirdi)

---

## MADDE 2 — Mutlak Öncelik ve Standartlar Dengeleyicisi
Ticari kaygılar ile teknik gerçekler çeliştiğinde, uluslararası gıda güvenliği standartları (HACCP, BRCGS, IFS) her zaman ağır basar. Halk sağlığı, ürün güvenliği ve mevzuat uyumu esnetilemez.

| Öncelik Sırası | Açıklama |
| :--- | :--- |
| **1. Halk Sağlığı** | İnsan güvenliği — tartışmasız, mutlak öncelik |
| **2. Mevzuat Uyumu** | HACCP, BRCGS v9, IFS v8, FSSC 22000 v6 |
| **3. Ürün Güvenliği** | İzlenebilirlik zinciri, CCP limitleri, allerjen kontrolü |
| **4. Süreç Verimliliği** | Üretim hedefleri, fire oranları, OEE metrikleri |
| **5. Ticari Hedefler** | Maliyet, hız, müşteri tatmini |

---

## MADDE 3 — İzlenebilirlik, Fail-Safe ve Cache Yönetimi
Hammadde girişinden son ürün çıkışına kadar veri zinciri asla koparılamaz. Kritik sapmalar otomatik alarm üretir.

### V2.0 YENİ: Merkezi Cache Yönetimi Zorunluluğu
> [!IMPORTANT]
> **KRİTİK KURAL — Cache Temizleme Protokolü**
> **YASAK:** `cached_veri_getir.clear()` çağrısı `app.py` veya UI modüllerine dağıtılamaz.
> **ZORUNLU:** Tüm cache temizleme işlemleri `logic/cache_manager.py` üzerinden yapılır.

**Fail-Safe Kuralları:**
- CCP limiti aşıldığında sistem otomatik alarm üretir, insan onayı beklenmez
- Soğuk oda ölçümü geciktiğinde dashboard'da kırmızı banner gösterilir
- Kritik KPI RED kararında üretim hattı sorumlusuna anlık bildirim gönderilir

---

## MADDE 4 — Yapay Zeka Kodlama ve Entegrasyon Protokolü
Yeni eklenecek her modül bağımsız çalışacak sadelikte yazılır. Mevcut yapıyı veya veritabanını bozma riski varsa, yapay zeka asla inisiyatif alamaz; tüm riskleri ve değişkenleri bildirerek açık onay almadan kodlama başlatmaz.

**Kodlama Standartları:**
- Fonksiyon başına maksimum 30 satır
- Değişken ve fonksiyon isimleri: Turkish snake_case (örn. `veri_getir`, `bolum_filtrele`)
- Her modül için `python -m py_compile` doğrulaması zorunludur
- Veritabanı şeması değişikliği → migration script zorunlu, doğrudan `ALTER TABLE` yasak

---

## MADDE 5 — Çapraz Denetim ve Granüler Yetkilendirme (RBAC)
ERP, MRP ve QMS süreçleri birbirini sürekli çapraz sorgular. Veriyi giren (Maker) ile onaylayan (Checker) aynı kişi olamaz.

### V2.0 YENİ: Yetki Cache TTL Kuralı
> [!IMPORTANT]
> **KRİTİK KURAL — Yetki Cache Süresi**
> **ESKI (YASAK):** `@st.cache_data(ttl=300)` → 5 dakika eski yetki kalır
> **YENİ (ZORUNLU):** `@st.cache_data(ttl=60)` → Maksimum 60 saniye gecikme
> **Uygulama:** `logic/auth_logic.py` içindeki `kullanici_yetkisi_getir()` fonksiyonu.

**RBAC Seviyeleri:**
- **Seviye 0 — Sistem Admin:** Tüm modüller, şifre/rol yönetimi, DB bakımı
- **Seviye 1 — Yönetim:** Tüm raporlar, onay ekranları, konfigürasyon
- **Seviye 2 — Kalite Sorumlusu:** KPI, GMP, HACCP modülleri
- **Seviye 3 — Vardiya Amiri:** Üretim girişi, hijyen kontrolü, temizlik
- **Seviye 4 — Personel:** Yalnızca kendi bölümünün görev ekranları

---

## MADDE 6 — Etik Mimari ve Veri Bütünlüğü
Sistem, şeffaflığı teşvik eden ve veri manipülasyonunu teknik olarak imkânsız kılan bir denetim/loglama altyapısına sahiptir.

### V2.0 YENİ: to_sql REPLACE Yasağı
> [!IMPORTANT]
> **KRİTİK KURAL — Veritabanı Yazma Protokolü**
> **YASAK PATTERN:** `df.to_sql('tablo', engine, if_exists='replace', ...)` ← **TAMAMEN YASAK**
> **ZORUNLU PATTERN:** `engine.begin() → UPDATE WHERE id=:id → INSERT (id yoksa)` (UPSERT)

---

## MADDE 7 — Yaşayan Sistem Haritası
Sistemdeki en küçük veri parçasının yolculuğu haritalandırılır. Bu harita güncellenmeden hiçbir modül tamamlanmış sayılmaz.

### V2.0 YENİ: Harita Güncelleme Zorunluluğu
> [!IMPORTANT]
> **KRİTİK KURAL — ARCHITECTURE.md Güncelleme Protokolü**
> Her refactoring adımı tamamlandığında `ARCHITECTURE.md` MUTLAKA güncellenir.

---

## MADDE 8 — Sistem Başlatma, Arınma ve Evrim Protokolü

### V2.0 YENİ — Purge Öncelik Listesi
Aşağıdaki pattern'ler tespit edildiğinde ANINDA refactoring önerilir:
- `to_sql(..., if_exists='replace')` → Madde 6 ihlali
- `@st.cache_data(ttl=300)` yetki fonksiyonlarında → Madde 5 ihlali
- `cache.clear()` app.py içinde dağınık → Madde 3 ihlali
- `ARCHITECTURE.md` tarihi 7 günden eski → Madde 7 ihlali
- Fonksiyon > 30 satır → Madde 4 ihlali

---

## MADDE 9 — Yapay Zeka Veri Senkronizasyon Yasağı
Yapay zekanın (AI) **kendi inisiyatifiyle, sorulmadan veya dolaylı bir yoruma dayanarak** lokal veri tabanı ile bulut (cloud) veri tabanı arasında eşitleme (senkronizasyon, push, pull) komutu çalıştırması veya script tetiklemesi **KESİNLİKLE YASAKTIR.**

### Yıkıcı Güç Koruması (Destructive Action Ban)
Veri eşitleme işlemleri, özellikle operasyonel tablolarda (KPI, üretim, sıcaklık vb.) geri dönüşü olmayan veri kayıplarına yol açabilecek kadar yüksek risk taşır.

**Bağlayıcı Kurallar:**
1. AI, "verileri eşitle", "sync yap", "cloud'a gönder" gibi **açık, net ve doğrudan bir insan talimatı olmadan** senkronizasyon araçlarını (örn. `quick_push_all.py`, `sync_manager.py`) ASLA çalıştıramaz.
2. AI, bir hatayı çözerken "belki veriler eksiktir, eşitleyeyim" şeklinde mantık yürütemez.
3. İnsan talimatı gelse dahi AI, "Bu işlem operasyonel verileri değiştirecek, onaylıyor musunuz?" diyerek çift onay almak zorundadır.

---

## HIZLI BAŞVURU — Yasak ve Zorunlu Pattern'ler

| 🔴 YASAK | ✅ ZORUNLU ALTERNATIF |
| :--- | :--- |
| `to_sql(if_exists='replace')` | `engine.begin() + UPDATE/INSERT (UPSERT)` |
| `@st.cache_data(ttl=300)` — yetki | `@st.cache_data(ttl=60)` — yetki için |
| `cache.clear()` — dağınık | `logic/cache_manager.py` — merkezi |
| `ARCHITECTURE.md` güncellenmeden kapat | Her adımda harita güncellemesi zorunlu |
| Fonksiyon > 30 satır | Küçük, tek sorumluluklu fonksiyonlar |
| Hard-coded limit/eşik değerleri | Veritabanından dinamik okuma |
| Geçmişe dönük kayıt değişikliği | Teknoloji olarak imkânsız — immutable log |
| AI inisiyatifiyle veri eşitleme (Sync) | Açık insan talimatı + Operasyonel koruma (Madde 9) |

---
**EKLERİSTAN A.Ş. — Kalite Yönetim Sistemi**
Bu belge yaşayan bir dokümandır. Sistem evrimi ile birlikte güncellenir.
