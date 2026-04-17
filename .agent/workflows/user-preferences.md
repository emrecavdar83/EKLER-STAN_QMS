# Emre Bey'in çalışma tercihleri, öğrenme yaklaşımı ve EKLERİSTAN QMS ANAYASASI# 📜 KURUMSAL HAFIZA VE ANAYASA (v5.0)

> [!IMPORTANT]
> **TEMEL KURAL:** Yapılan her işlem sonunda mutlaka **Türkçe** geri bildirim verilecek ve tüm planlamalar (implementation plan vb.) **Türkçe** olarak hazırlanacaktır.
> Aşağıdaki maddeler, **.antigravity/rules/anayasa.md** dosyasının "yaşayan" halidir ve her işlemde bağlayıcıdır.

---

## 👨‍🏫 Öğretici Mod (Emre Bey Modu)

Emre Bey bu projeyi öğrenmek istiyor. Yapılan her değişiklikte (Madde 22):

1. **Alternatif Seçenekleri Sun:** En az 2-3 farklı yaklaşım göster, avantaj/dezavantajlarını açıkla (Madde 22 formatı zorunludur).
2. **Risk Analizi Yap:** Değişikliğin mevcut sisteme etkisi, olası yan etkiler, geri dönüş planı.
3. **Açıklayıcı Ol:** Kod ne yapıyor, neden bu şekilde yazıldı, teknik kararların arkasındaki mantık.

---

## 📜 ANAYASA MADDELERİ (30+1 MADDE)

### MADDE 0 — Mutlak Yedekleme ve Güvenli Gönderim Protokolü

> [!IMPORTANT]
> Sisteme dair herhangi bir kod veya veritabanı değişikliği Bulut ortamına (GitHub ve Supabase) gönderilmeden (Push/Merge) önce, Bulutun TAM YEDEĞİ (GitHub Snapshot ve Supabase Data Dump) alınmak zorundadır. Bu kural hiçbir koşulda ihlal edilemez ve atlanamaz. Ajanlar (Yapay Zeka) bu yedeği almadan gönderim yapamazlar. Her ajan, gönderim öncesi "Yedek alındı mı?" sorusunu doğrulamakla YÜKÜMLÜDÜR.

### MADDE 1 — Sıfırıncı Kural (Hafıza ve Doğrusal İlerleme Mecburiyeti)

Hiçbir ajan (Yapay Zeka / Antigravity / Claude), `.antigravity/musbet/hafiza/hafiza_ozeti.md` ve `.antigravity/musbet/hafiza/cozulmus_vakalar.md` dosyalarını okumadan prompt işlemeye, kod yazmaya veya migration üretmeye başlayamaz. Her prompt başlangıcında; geçmiş değişikliklerin zamanı, modülü ve ayrıntıları doğrusal ilerlemeyi anlamak adına okunmak zorundadır. Görev bittiğinde, yapay zeka gerçekleştirdiği tüm iyileştirmeleri tarih, modül ve detay bağımlılıklarıyla birlikte bu dosyalara kaydetmekle YÜKÜMLÜDÜR. Bağlamdan kopuk her eylem anayasa ihlalidir.

### MADDE 2 — Zero Hardcode

Kod içinde sabit değer (string, int, id) kullanımı yasaktır. Tüm değerler `constants.py`, veritabanı veya sistem parametrelerinden gelmelidir.

### MADDE 3 — Max 30 Satır Fonksiyon

Bir fonksiyon veya metod (UI veya Logic fark etmeksizin) 30 satırı geçemez. Geçiyorsa alt parçalara bölünmeli ve sorumluluk devredilmelidir.

### MADDE 4 — UPSERT ve Veri Sağlamlığı

Üretim verisi asla silinmez (`DELETE` yasaktır). Veri her zaman güncellenir (`UPSERT`). Yanlış kayıtlar `durum='PASIF'` olarak işaretlenir.

### MADDE 5 — Korunan Tablolar (Zırhlı Erişim)

`personel`, `ayarlar_yetkiler`, `sistem_parametreleri` ve `qdms_belgeler` tabloları zırhlıdır. Bu tablolara yazma işlemi Guardian onayı olmadan yapılamaz.

### MADDE 6 — 13. Adam Protokolü

Her riskli operasyon öncesi "Bu ters giderse ne olur?" sorusu yazılı cevaplanmalı ve bir karşı senaryo üretilmelidir.

### MADDE 7 — Test-First Geliştirme

Kod yazılmadan önce test senaryosu belirlenir. Testi geçemeyen veya testi olmayan kod "Tamamlandı" kabul edilemez.

### MADDE 8 — Cloud-Primary (Bulut Öncelikli) Mimari

Sistem `Single Source of Truth` olarak Supabase (Postgres) kullanır. Lokal SQLite yedekleme amaçlıdır. Çift yönlü kontrolsüz senkron yasaktır.

### MADDE 9 — KVKK ve Veri Gizliliği

Kişisel veriler (TC No, Telefon, Adres) loglara asla açık metin olarak yazılamaz. Erişim her zaman kısıtlıdır.

### MADDE 10 — Türkçe snake_case ve Kurumsal Dil

Değişkenler, fonksiyonlar ve modüller Türkçe snake_case olmalıdır (Örn: `veri_getir`). Şirket adı her zaman **EKLERİSTAN A.Ş.**'dir.

### MADDE 11 — Manuel Doğrulama ve RED (Validator)

Ajan "Bitti" dese dahi, insan (Emre) veya Validator "Hatalı" derse süreç durur ve P0 (Acil) olarak ilgili ajana iade edilir.

### MADDE 12 — Hata Yönetimi (Fail-Silent / Loud Error)

Kullanıcıya teknik hata (redacted) gösterilen her durum anayasa ihlalidir. Hatalar yakalanmalı, loglanmalı ve çözümle birlikte kaydedilmelidir.

### MADDE 13 — Tek Sorumluluk İlkesi (Role Clarity)

Ajanlar yalnızca kendi rollerini (DB, Backend, Frontend vb.) icra ederler. Rol dışı müdahale Guardian blokajı sebebidir.

### MADDE 14 — Performans ve İndeksleme

Tüm Foreign Key ve sık kullanılan filtre kolonlarına indeks atılması zorunludur. İndekssiz sorgu tasarımı reddedilir.

### MADDE 15 — Bulut Tarayıcı Doğrulama (Browser Test)

Kod buluta yüklendikten sonra tarayıcı üzerinden manuel veya subagent ile tıklanarak doğrulanmadan "Başarılı" sayılamaz.

### MADDE 16 — Mutlak İşlem Yönetimi (Commit/Rollback)

Tüm DB yazma işlemleri `with engine.begin()` veya açık `commit()` ile zırhlanmalıdır. Yarım kalan transaction'lar P0 hatasıdır.

### MADDE 17 — Seed Data ve Seed Scriptleri

Yeni fonksiyonlar için canlı ortam test verisi (Seed Data) scriptleri hazırlanması ve bunların güvenli çalışması zorunludur.

### MADDE 18 — Adım 0: İhtiyaç Analizi ve Kapsam Onayı

İşe başlamadan önce Emre Bey'e 7-15 soru sorulmalı, yanıtlar doğrultusunda plan güncellenmeli ve ONAY alınmalıdır.

### MADDE 19 — UI Kapsülleme (Global st.* Yasağı)

Streamlit fonksiyonları (`st.*`) asla global scope'da (fonksiyon dışında) yazılamaz. `render_*` fonksiyonları içine hapsedilmelidir.

### MADDE 20 — Hiyerarşik Lokasyon Kimliği (XX-YY-ZZ-AA)

Tüm lokasyon ve varlıklar `Kat-Bölüm-Hat-Cihaz` formatında (Örn: 03-01-01-01) benzersiz kodlanmalıdır.

### MADDE 21 — Bart Simpson Döngüsü (Agresif Çevresel Kontrol)

"Ben bunu düzelttim ama neyi bozdum?" sorusu her commit öncesi sorulmalı, yukarı-aşağı kod taraması yapılmalıdır.

### MADDE 22 — Snapshot ve Döküman Bağlam Sadakati

Eğitim verisi yerine projenin yerel snapshot'ları (`.antigravity/context_snapshots/`) teknik otorite kabul edilir.

### MADDE 23 — Hata Senkron Köprüsü ve Kolektif Hafıza

Bulut hataları senkronize edilerek `hata_cozum_gunlugu.md` dosyasına işlenmelidir. Çözümü yazılmayan hata teknik borçtur.

### MADDE 24 — Modül İsimlendirme Standartları

Modüller veritabanındaki `ayarlar_moduller` tablosuna sadık kalarak, hem teknik anahtar hem de etiket (Emoji + İsim) ile tanımlanmalıdır.

### MADDE 25 — Cache Stratejisi ve TTL Yönetimi

Performans için `@st.cache_data` ve `@st.cache_resource` kullanılmalı, veri tazeliği için TTL (Zaman Aşımı) mutlaka belirtilmelidir.

### MADDE 26 — Güvenli Tahliye (Logout) Protokolü

Logout işlemi URL parametresi (`?logout=1`) ve session temizliği ile zırhlanmalıdır. Eski cookieler her çıkışta silinmelidir.

### MADDE 27 — Log Formatı ve İzlenebilirlik

Loglar; `Ajan + İşlem Kodu + Timestamp + Detay` formatında olmalıdır. İzlenemeyen hata veya işlem anayasa ihlalidir.

### MADDE 28 — Ajanlar Arası Devir Protokolü

İş bitince devir raporu yazılmalı ve bir sonraki ajan adıyla çağrılmalıdır (Örn: "builder_db -> builder_backend").

### MADDE 29 — PDCA Döngüsü (Planla-Uygula-Kontrol Et-Önlem Al)

Her geliştirme döngüsü bu dörtlüye uymalıdır. Planlanmamış veya kontrol edilmemiş iş reddedilir.

### MADDE 30 — Anayasal Değişmezlik ve Revizyon

Bu anayasa projenin mimari yasasıdır. Değişiklik teklifleri `musbet` üzerinden Emre Bey'e sunulmalı ve ONAY alınmalıdır.

---

## 📜 ANAYASA MADDELERİ (30+1 MADDE)

### MADDE 0 — Mutlak Yedekleme ve Güvenli Gönderim Protokolü

> [!IMPORTANT]
> Sisteme dair herhangi bir kod veya veritabanı değişikliği Bulut ortamına (GitHub ve Supabase) gönderilmeden (Push/Merge) önce, Bulutun TAM YEDEĞİ (GitHub Snapshot ve Supabase Data Dump) alınmak zorundadır. Bu kural hiçbir koşulda ihlal edilemez ve atlanamaz. Ajanlar (Yapay Zeka) bu yedeği almadan gönderim yapamazlar. Her ajan, gönderim öncesi "Yedek alındı mı?" sorusunu doğrulamakla YÜKÜMLÜDÜR.

### MADDE 1 — Sıfırıncı Kural (Hafıza ve Doğrusal İlerleme Mecburiyeti)

Hiçbir ajan (Yapay Zeka / Antigravity / Claude), `.antigravity/musbet/hafiza/hafiza_ozeti.md` ve `.antigravity/musbet/hafiza/cozulmus_vakalar.md` dosyalarını okumadan prompt işlemeye, kod yazmaya veya migration üretmeye başlayamaz. Her prompt başlangıcında; geçmiş değişikliklerin zamanı, modülü ve ayrıntıları doğrusal ilerlemeyi anlamak adına okunmak zorundadır. Görev bittiğinde, yapay zeka gerçekleştirdiği tüm iyileştirmeleri tarih, modül ve detay bağımlılıklarıyla birlikte bu dosyalara kaydetmekle YÜKÜMLÜDÜR. Bağlamdan kopuk her eylem anayasa ihlalidir.

### MADDE 2 — Zero Hardcode

Kod içinde sabit değer (string, int, id) kullanımı yasaktır. Tüm değerler `constants.py`, veritabanı veya sistem parametrelerinden gelmelidir.

### MADDE 3 — Max 30 Satır Fonksiyon

Bir fonksiyon veya metod (UI veya Logic fark etmeksizin) 30 satırı geçemez. Geçiyorsa alt parçalara bölünmeli ve sorumluluk devredilmelidir.

### MADDE 4 — UPSERT ve Veri Sağlamlığı

Üretim verisi asla silinmez (`DELETE` yasaktır). Veri her zaman güncellenir (`UPSERT`). Yanlış kayıtlar `durum='PASIF'` olarak işaretlenir.

### MADDE 5 — Korunan Tablolar (Zırhlı Erişim)

`personel`, `ayarlar_yetkiler`, `sistem_parametreleri` ve `qdms_belgeler` tabloları zırhlıdır. Bu tablolara yazma işlemi Guardian onayı olmadan yapılamaz.

### MADDE 6 — 13. Adam Protokolü

Her riskli operasyon öncesi "Bu ters giderse ne olur?" sorusu yazılı cevaplanmalı ve bir karşı senaryo üretilmelidir.

### MADDE 7 — Test-First Geliştirme

Kod yazılmadan önce test senaryosu belirlenir. Testi geçemeyen veya testi olmayan kod "Tamamlandı" kabul edilemez.

### MADDE 8 — Cloud-Primary (Bulut Öncelikli) Mimari

Sistem `Single Source of Truth` olarak Supabase (Postgres) kullanır. Lokal SQLite yedekleme amaçlıdır. Çift yönlü kontrolsüz senkron yasaktır.

### MADDE 9 — KVKK ve Veri Gizliliği

Kişisel veriler (TC No, Telefon, Adres) loglara asla açık metin olarak yazılamaz. Erişim her zaman kısıtlıdır.

### MADDE 10 — Türkçe snake_case ve Kurumsal Dil

Değişkenler, fonksiyonlar ve modüller Türkçe snake_case olmalıdır (Örn: `veri_getir`). Şirket adı her zaman **EKLERİSTAN A.Ş.**'dir.

### MADDE 11 — Manuel Doğrulama ve RED (Validator)

Ajan "Bitti" dese dahi, insan (Emre) veya Validator "Hatalı" derse süreç durur ve P0 (Acil) olarak ilgili ajana iade edilir.

### MADDE 12 — Hata Yönetimi (Fail-Silent / Loud Error)

Kullanıcıya teknik hata (redacted) gösterilen her durum anayasa ihlalidir. Hatalar yakalanmalı, loglanmalı ve çözümle birlikte kaydedilmelidir.

### MADDE 13 — Tek Sorumluluk İlkesi (Role Clarity)

Ajanlar yalnızca kendi rollerini (DB, Backend, Frontend vb.) icra ederler. Rol dışı müdahale Guardian blokajı sebebidir.

### MADDE 14 — Performans ve İndeksleme

Tüm Foreign Key ve sık kullanılan filtre kolonlarına indeks atılması zorunludur. İndekssiz sorgu tasarımı reddedilir.

### MADDE 15 — Bulut Tarayıcı Doğrulama (Browser Test)

Kod buluta yüklendikten sonra tarayıcı üzerinden manuel veya subagent ile tıklanarak doğrulanmadan "Başarılı" sayılamaz.

### MADDE 16 — Mutlak İşlem Yönetimi (Commit/Rollback)

Tüm DB yazma işlemleri `with engine.begin()` veya açık `commit()` ile zırhlanmalıdır. Yarım kalan transaction'lar P0 hatasıdır.

### MADDE 17 — Seed Data ve Seed Scriptleri

Yeni fonksiyonlar için canlı ortam test verisi (Seed Data) scriptleri hazırlanması ve bunların güvenli çalışması zorunludur.

### MADDE 18 — Adım 0: İhtiyaç Analizi ve Kapsam Onayı

İşe başlamadan önce Emre Bey'e 7-15 soru sorulmalı, yanıtlar doğrultusunda plan güncellenmeli ve ONAY alınmalıdır.

### MADDE 19 — UI Kapsülleme (Global st.* Yasağı)

Streamlit fonksiyonları (`st.*`) asla global scope'da (fonksiyon dışında) yazılamaz. `render_*` fonksiyonları içine hapsedilmelidir.

### MADDE 20 — Hiyerarşik Lokasyon Kimliği (XX-YY-ZZ-AA)

Tüm lokasyon ve varlıklar `Kat-Bölüm-Hat-Cihaz` formatında (Örn: 03-01-01-01) benzersiz kodlanmalıdır.

### MADDE 21 — Bart Simpson Döngüsü (Agresif Çevresel Kontrol)

"Ben bunu düzelttim ama neyi bozdum?" sorusu her commit öncesi sorulmalı, yukarı-aşağı kod taraması yapılmalıdır.

### MADDE 22 — Snapshot ve Döküman Bağlam Sadakati

Eğitim verisi yerine projenin yerel snapshot'ları (`.antigravity/context_snapshots/`) teknik otorite kabul edilir.

### MADDE 23 — Hata Senkron Köprüsü ve Kolektif Hafıza

Bulut hataları senkronize edilerek `hata_cozum_gunlugu.md` dosyasına işlenmelidir. Çözümü yazılmayan hata teknik borçtur.

### MADDE 24 — Modül İsimlendirme Standartları

Modüller veritabanındaki `ayarlar_moduller` tablosuna sadık kalarak, hem teknik anahtar hem de etiket (Emoji + İsim) ile tanımlanmalıdır.

### MADDE 25 — Cache Stratejisi ve TTL Yönetimi

Performans için `@st.cache_data` ve `@st.cache_resource` kullanılmalı, veri tazeliği için TTL (Zaman Aşımı) mutlaka belirtilmelidir.

### MADDE 26 — Güvenli Tahliye (Logout) Protokolü

Logout işlemi URL parametresi (`?logout=1`) ve session temizliği ile zırhlanmalıdır. Eski cookieler her çıkışta silinmelidir.

### MADDE 27 — Log Formatı ve İzlenebilirlik

Loglar; `Ajan + İşlem Kodu + Timestamp + Detay` formatında olmalıdır. İzlenemeyen hata veya işlem anayasa ihlalidir.

### MADDE 28 — Ajanlar Arası Devir Protokolü

İş bitince devir raporu yazılmalı ve bir sonraki ajan adıyla çağrılmalıdır (Örn: "builder_db -> builder_backend").

### MADDE 29 — PDCA Döngüsü (Planla-Uygula-Kontrol Et-Önlem Al)

Her geliştirme döngüsü bu dörtlüye uymalıdır. Planlanmamış veya kontrol edilmemiş iş reddedilir.

### MADDE 30 — Anayasal Değişmezlik ve Revizyon

Bu anayasa projenin mimari yasasıdır. Değişiklik teklifleri `musbet` üzerinden Emre Bey'e sunulmalı ve ONAY alınmalıdır.

---

## 🤖 AJAN ÇALIŞMA PLANI (8 Katmanlı Grand Unification)

Bir geliştirme talebi geldiğinde ajanlar şu sırayı takip eder:

0. **planner**          → İhtiyaç Analizi (7-15 Soru) → Kapsam Onayı (Emre)
1. **builder_db**       → Şema Tasarımı & Migration Hazırlığı
2. **builder_backend**  → İş Mantığı (Logic), Servis Katmanı ve DB İşlemleri
3. **builder_frontend** → Streamlit Arayüzü (UI) ve Formlar
4. **tester**           → Birim (Unit) & Entegrasyon Testleri
5. **validator**        → İnsan Gözü Simülasyonu & Bulut Tarayıcı Testi
6. **guardian**         → Risk & Koruma Değerlendirmesi (Veto/Onay)
7. **auditor**          → Anayasa (31 Madde) ve Standartlara Uyum Denetimi
8. **sync_master**      → Sistem Sağlık & Bütünlük Denetimi (Cloud Sync)

---

## 📁 AJAN DOSYA HARİTASI

```text
.antigravity/
├── AGENTS.md                          ← Router
├── rules/
│   └── anayasa.md                     ← 30 Madde (Ana Yasa)
├── commands/
│   └── yeni-modul.md                  ← Master prompt
└── musbet/                            ← Kolektif Hafıza
    └── hafiza/
        ├── hafiza_ozeti.md            ← KRİTİK: Sıfırıncı Kural (Özet)
        ├── cozulmus_vakalar.md        ← GEÇMİŞ: Mühürlenmiş Hatalar
        ├── hata_cozum_gunlugu.md      ← GÜNCEL: Bulut Hata Kayıtları
        └── sistem_haritasi.md         ← GPS: DB, Modül, FK Haritası
```

---

## 📦 SİSTEM HARİTASI (v6.4.0 Pure Cloud)

| # | Modül | URL / Dosya | Durum |
| :--- | :--- | :--- | :--- |
| 1 | 🌍 Canlı URL | <https://ekler-stanqms-hdqwhxqcw3evgpnzgerkec.streamlit.app/> | ✅ |
| 2 | 📊 KPI & Kalite | `modules/kpi/` | ✅ |
| 3 | 🛡️ GMP Denetimi | `modules/gmp/` | ✅ |
| 4 | 🧼 Hijyen | `modules/hijyen/` | ✅ |
| 5 | 🧹 Temizlik | `modules/temizlik/` | ✅ |
| 6 | ❄️ Soğuk Oda | `modules/soguk_oda/` | ✅ |
| 7 | 🗺️ MAP Üretim | `modules/map/` | ✅ |
| 8 | 📋 Günlük Görev | `modules/gorevler/` | ✅ |
| 9 | 📈 Performans | `modules/performans/` | ✅ |
| 10 | 📄 QDMS | `modules/qdms/` | ✅ |
| 11 | ⚙️ Ayarlar | `modules/settings/` | ✅ |

---

## 🗝️ ÖNEMLİ REFERANSLAR

- **VAKA-042:** Admin Yetki Kurtarma & Pure Cloud Geçişi (v6.4.0)
- **VAKA-041:** Grand Unification & app.py Refaktörü (v6.2.0)
- **Konum Yapısı:** Kat > Hat > Cihaz (Örn: 03-01-01-05) (Madde 20)

---

**Onaylanan Madde Sayısı: 31 (30+1)**

*V5.1 | v5.1 GUARDIAN SEAL | 16.04.2026*
