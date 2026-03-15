# EKLERİSTAN A.Ş.
# KALİTE YÖNETİM SİSTEMİ (QMS)
# ÇEKİRDEK ANAYASASI
# VERSİYON 3.0 — NİHAİ SÜRÜM

| Alan | Bilgi |
| :--- | :--- |
| **Versiyon** | 3.0 (Güncellenmiş) |
| **Önceki Versiyon** | 2.0 |
| **Güncelleme Tarihi** | 04.03.2026 |
| **Hazırlayan** | Emre ÇAVDAR — Sistem Admin |
| **Kapsam** | ERP · KPI/GMP · HACCP — Tüm Modüller |
| **Hedef Sertifikalar** | BRC v9 · IFS v8 · FSSC 22000 v6 · ISO 9001 · AIB |
| **Mimari** | Python + Streamlit + SQLite (Lokal) + Supabase PostgreSQL (Üretim) |

---

## ⚠️ V3.0 GÜNCELLEME GEREKÇESİ
Bu güncelleme, v2.0'da tanımlanan 4 kritik güvenlik açığının kapatılmasının ardından sistemin karar güvenliği boyutunu tamamlar.

**Yeni Eklenen Madde:**
**MADDE 10 — 13. Adam Protokolü:** Yapay zekanın, konsensüs oluşmuş kararlarda bile zorunlu karşı senaryo üretmesini anayasal görev olarak tanımlar. Veri senkronizasyonu, mimari değişiklik ve sistem kurulum işlemlerinde devreye girer.

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

### V2.0: Merkezi Cache Yönetimi Zorunluluğu
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

### V2.0: Yetki Cache TTL Kuralı
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

### V2.0: to_sql REPLACE Yasağı
> [!IMPORTANT]
> **KRİTİK KURAL — Veritabanı Yazma Protokolü**
> **YASAK PATTERN:** `df.to_sql('tablo', engine, if_exists='replace', ...)` ← **TAMAMEN YASAK**
> **ZORUNLU PATTERN:** `engine.begin() → UPDATE WHERE id=:id → INSERT (id yoksa)` (UPSERT)

---

## MADDE 7 — Yaşayan Sistem Haritası
Sistemdeki en küçük veri parçasının yolculuğu haritalandırılır. Bu harita güncellenmeden hiçbir modül tamamlanmış sayılmaz.

### V2.0: Harita Güncelleme Zorunluluğu
> [!IMPORTANT]
> **KRİTİK KURAL — ARCHITECTURE.md Güncelleme Protokolü**
> Her refactoring adımı tamamlandığında `ARCHITECTURE.md` MUTLAKA güncellenir.

---

## MADDE 8 — Sistem Başlatma, Arınma ve Evrim Protokolü

### V2.0: Purge Öncelik Listesi
Aşağıdaki pattern'ler tespit edildiğinde ANINDA refactoring önerilir:
- `to_sql(..., if_exists='replace')` → Madde 6 ihlali
- `@st.cache_data(ttl=300)` yetki fonksiyonlarında → Madde 5 ihlali
- `cache.clear()` app.py içinde dağınık → Madde 3 ihlali
- `ARCHITECTURE.md` tarihi 7 günden eski → Madde 7 ihlali
- Fonksiyon > 30 satır → Madde 4 ihlali

---

## MADDE 9 — Yapay Zeka Veri Senkronizasyon Yasağı
Yapay zekanın kendi inisiyatifiyle, sorulmadan veya dolaylı bir yoruma dayanarak lokal veri tabanı ile bulut veri tabanı arasında eşitleme komutu çalıştırması veya script tetiklemesi KESİNLİKLE YASAKTIR.

### Yıkıcı Güç Koruması (Destructive Action Ban)
**Bağlayıcı Kurallar:**
1. AI, açık, net ve doğrudan bir insan talimatı olmadan senkronizasyon araçlarını ASLA çalıştıramaz.
2. AI, bir hatayı çözerken "belki veriler eksiktir, eşitleyeyim" şeklinde mantık yürütemez.
3. İnsan talimatı gelse dahi AI, "Bu işlem operasyonel verileri değiştirecek, onaylıyor musunuz?" diyerek çift onay almak zorundadır.

---

## MADDE 10 — 13. Adam Protokolü

*"Eğer herkes aynı fikirde ise, kimse gerçekten düşünmüyor demektir."*

### Temel İlke
Bir karar sürecinde tüm aktörler (insan + sistem) aynı yönde onay verdiğinde, bu konsensüs güvenin değil, körlüğün işareti olabilir. 13. Adam Protokolü, yapay zekanın bu körlüğü kırmak için zorunlu karşı senaryo üretmesini anayasal bir görev olarak tanımlar.

### Protokolün Devreye Girdiği Durumlar
| Durum | Tetikleyici Koşul |
| :--- | :--- |
| **T1** | Veri Senkronizasyonu: Herhangi bir sync/push/pull kararı öncesi |
| **T2** | Mimari / Kod Değişikliği: Mevcut yapıyı etkileyen her refactoring öncesi |
| **T3** | Kodlama & Sistem Kurulum: Yeni modül, servis veya altyapı kurulumu öncesi |

### AI'ın Zorunlu Karşı Senaryo Yükümlülüğü
Yukarıdaki tetikleyici durumlardan biri oluştuğunda, yapay zeka öneriyi uygulamadan önce aşağıdaki yapıyı zorunlu olarak üretir:

```
─────────────────────────────────────────────
⚠️  13. ADAM PROTOKOLÜ — KARŞI SENARYO
─────────────────────────────────────────────
KARAR      : [Yapılmak istenen işlem]
KONSENSÜS  : [Kim/ne onay verdi]

KARŞI SENARYO:
  ╠═ En kötü olası sonuç nedir?
  ╠═ Hangi varsayım yanlışsa bu karar felakete dönüşür?
  ╠═ Geri alınamaz sonuç var mı?
  ╚═ Bu kararı VERMEMEK için en güçlü argüman nedir?

RİSK SEVİYESİ : [ KRİTİK / YÜKSEK / ORTA ]
ÖNERI         : [ DEVAM ET / BEKLE / İPTAL ]
─────────────────────────────────────────────
```

**Bağlayıcı Kurallar**
- AI, karşı senaryo üretmeden hiçbir T1/T2/T3 işlemini başlatamaz.
- Karşı senaryo gerçekçi ve somut olmalıdır — "sorun çıkabilir" gibi muğlak ifadeler geçersizdir.
- AI'ın kendi önerdiği çözüm bile bu protokolden muaf değildir.
- Kullanıcı karşı senaryoyu okuyup açıkça "devam et" demeden işlem başlamaz.
- Karşı senaryo üretimi audit log'a düşer — kim, ne zaman, hangi senaryoyu onayladı.

### Madde 9 ile Birlikte Çalışma
```
Sync / Mimari / Kurulum talebi geldi
              ↓
    Madde 9  →  "İnsan talimatı var mı?"
              ↓ EVET
    Madde 10 →  "13. Adam karşı senaryoyu üret"
              ↓ KULLANICI OKUDU & ONAYLADI
    Madde 9  →  "Çift onay alındı mı?"
              ↓ EVET
          İşlem başlar
```

---

## MADDE 11 — Teknik Dil Birliği (Ubiquitous Language)
QMS V3 geliştirme sürecinde tüm modüller Frontend (Kullanıcı Ekranı), Backend (Veri İşleme) ve Database (Veri Saklama) katmanları olarak adlandırılacaktır. Bu üç katman dışında mimari terim türetilmez; yeni bir mimari kavram için önce Anayasa güncellenir.

---

## MADDE 12 — Veri Güvenliği ve Doğrulama Zorunluluğu
Sisteme girilen her veri, Pydantic modeli aracılığıyla Validation (Doğrulama) testinden geçmeden veritabanına yazılamaz. DB seviyesinde NOT NULL ve CHECK kısıtları zorunludur. Input Validation ve DB Constraint çifte güvencesi projenin güvenlik minimumudur.

---

## MADDE 13 — Sürdürülebilirlik ve Tek Sorumluluk
Her Python fonksiyonu en fazla 30 satır olacak ve yalnızca tek bir iş yapacaktır (Single Responsibility Principle). Fonksiyonun adı, yaptığı işi Türkçe snake_case olarak açıkça ifade etmelidir. Örnek: `musteri_kaydet()`, `lot_olustur()`, `ccp_limiti_kontrol_et()`.

---

## MADDE 14 — Senkronizasyon Bütünlüğü (Symmetric Twin)
SQLite (geliştirme) ve Supabase (üretim) veritabanları her zaman aynı şemayı taşır. Şema değişikliği önce SQLite'a uygulanır, migration scripti yazılır, test geçtikten sonra Supabase'e push edilir. Tek taraflı değişiklik yapılamaz.

---

## MADDE 15 — HACCP Nesneleri Yazılım Objesidir
Her HACCP kavramı (CCP, İzlenebilirlik, Risk Matrisi, CAPA/DÖF) bir veritabanı tablosu ve buna karşılık gelen Python dataclass/Pydantic modeli olarak tanımlanır. HACCP formu doldurmak = DB'ye UPSERT yapmaktır. Kağıt form dijitalleştirilmeden yürürlüğe giremez.

---

## HIZLI BAŞVURU — Yasak ve Zorunlu Pattern'ler

| 🔴 YASAK | ✅ ZORUNLU ALTERNATİF |
| :--- | :--- |
| `to_sql(if_exists='replace')` | `engine.begin() + UPDATE/INSERT (UPSERT)` |
| `@st.cache_data(ttl=300)` — yetki | `@st.cache_data(ttl=60)` — yetki için |
| `cache.clear()` — dağınık | `logic/cache_manager.py` — merkezi |
| Fonksiyon > 30 satır | Küçük, tek sorumluluklu fonksiyonlar (SRP) |
| Hard-coded limit/eşik değerleri | Veritabanından dinamik okuma (Madde 1) |
| AI inisiyatifiyle veri eşitleme | Açık insan talimatı + Madde 9 koruması |
| Karşı senaryosuz T1/T2/T3 işlemi | 13. Adam protokol çıktısı zorunlu |
| HACCP formunun kağıtta kalması | DB tablosu + Backend objesi + Frontend Formu |
| SQLite ve Postgres şema farkı | Symmetric Twin protokolü ve Migration scripti |

---
**EKLERİSTAN A.Ş. — Kalite Yönetim Sistemi**
Versiyon 3.1 — 15.03.2026
Bu belge yaşayan bir dokümandır. Sistem evrimi ile birlikte güncellenir.
