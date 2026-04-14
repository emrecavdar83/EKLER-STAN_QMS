# EKLERİSTAN QMS AJAN ANAYASASI

# .antigravity/rules/anayasa.md

# Versiyon: 5.0 | v5.0 GRAND UNIFICATION | Sürüm: 07.04.2026

# Yetkili: Emre | Değişiklik: Yalnızca Emre onayı ile yapılabilir

---

## ⚖️ TEMEL İLKE

Bu dosyayı okuyan her ajan, projenin mimari bütünlüğünü korumayı ve Bart Simpson Döngüsü'nü (çalışanı bozmama) uygulamayı yeminli olarak kabul eder.

---

## 📜 ANAYASA MADDELERİ (30 MADDE)

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

**Onaylanan Madde Sayısı: 30**

*V5.0 | v5.0 GRAND UNIFICATION*
