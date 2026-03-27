# EKLERİSTAN QMS — Açık Vakalar
# .antigravity/musbet/hafiza/acik_vakalar.md

> Bu dosya musbet ajanı tarafından yönetilir. Manuel düzenleme yapılmaz.
> Her kayıt UPSERT ile güncellenir, silinmez.

---

## 🔴 [VAKA-005] P0: Gemini Pro High/Low API Kota Tükenmesi → Ajan Atama Bozulması

**Tarih:** 2026-03-28
**Durum:** ÇÖZÜLEN VAKA (Mimari Kural Uygulandı)
**Sorumlu Ajanlar:** Tüm pipeline ajanları (özellikle `builder_backend`, `builder_db`)

**Olay Özeti:**
AGENTS.md'de `builder_backend` için Gemini 2.5 Pro High, `builder_db` için Gemini 2.5 Pro Low modeli atanmıştır. Emre Bey'in tespitine göre bu modellerin API kotası dolunca pipeline'daki ajan atama mekanizması sessizce bozulmakta; ajanlar ya hatalı çıktı üretmekte ya da hiç yanıt vermemektedir. Bu durum saatlerce sağlıksız çalışmanın arka planda asıl tetikleyicisi olabilir.

**Çözüm Alternatifleri:**
1. **Fallback Model Tanımı:** AGENTS.md model tablosuna her ajan için bir `fallback` (yedek) model sütunu eklenmelidir. Kota dolduğunda ajan otomatik olarak düşük maliyetli bir modele (örn. Claude Haiku veya Gemini Flash) geçer.
2. **Kota Monitörü (musbet görevi):** Musbet ajanı, uzun pipeline döngülerinde kota limitine yaklaşıldığında uyarı verecek şekilde konfigüre edilmelidir.
3. **Model Dengeleme (Load Balancing):** Kritik ajanlar (builder_backend) için hem Gemini 2.5 Pro hem Claude Sonnet seçenekleri birlikte listelenmeli; biri kotayı bitirince ötekine geçilmelidir.

---

---

## 🔴 [VAKA-001] P0 (MANUEL_RED): Üretim Ortamında Eksik Şema (ProgrammingError)

**Tarih:** 2026-03-27
**Durum:** ÇÖZÜLEN VAKA (Kayıtlı)
**Sorumlu Ajanlar:** `builder_db`, `tester`, `validator`

**Olay Özeti:**
Günlük Görevler modülü geliştirildikten sonra `tester` ve `validator` ajanları başarılı test raporu verdi. Ancak bu testler yalnızca in-memory SQLite üzerinde yapıldı. Üretim ortamına (Streamlit Cloud + Supabase PostgreSQL) çıkıldığında, `birlesik_gorev_havuzu` ve `gunluk_gorev_katalogu` tablolarını oluşturacak migration kodları `database/connection.py` içine hiç eklenmemişti. Sonuç olarak Emre Bey uygulamayı açtığında `sqlalchemy.exc.ProgrammingError` ile sayfa çöktü.

**Çözüm:**
Tablo oluşturma SQL'leri `database/connection.py` → `_create_shadow_tables()` fonksiyonuna eklendi. Tablolar ayrıca script ile doğrudan Supabase'e bastırıldı.

---

## 🔴 [VAKA-004] P0 (KAYSEDİLMEMİŞ): GitHub Push Hatası + Arayüzde Görünmeme (İlk İniş Krizi)

**Tarih:** 2026-03-27 (Akşam saatleri — 1. döngü)
**Durum:** ÇÖZÜLEN VAKA — İLK KAYIT (Daha önce loglanmamıştı)
**Sorumlu Ajanlar:** `builder_frontend`, `sync_master`, `validator`

**Olay Özeti:**
Günlük Görev modülü buluta alındıktan sonra Emre Bey saatlerce modülün arayüzde **hiç gözükmediğini** yaşadı. Birden fazla "hepsini tamamladık" raporu verilmesine karşın doğru ekrana hiç ulaşılamadı. Bu sürece yönelik iki ayrı şube sorunu birleşmiş durumdaydı:

1. **GitHub Push Hatası:** Bazı değişikliklerin commit edilip edilmediği veya doğru branch'e push edildiği doğrulanmamıştı. Streamlit Cloud eski kodu çalıştırıyorken ajanlar yeni kod üzerinden "başarılı" raporu veriyordu.
2. **Arayüzde Görünmeme:** Modülün sidebar'da ve hızlı menüde görünmesi için `ayarlar_moduller` tablosuna uygun bir kayıt ve `ayarlar_yetkiler` tablosuna izin eklemesi gerekmekteydi. Bu adım atlandığı için kullanıcı modüle hiç erişemedi.

**Tespit Edilen Kör Nokta:**
Validator ajanının "tamamlandı" demesi için kodun Cloud'da güncel olduğunu bizzat kontrol etmesi gerekirdi. Bu doğrulama adımı, Madde 15'in gerekçelerinden biridir.

**Ders Çıkarılan Kural (Anayasa Madde 15 + Madde 17):**
Her deploy sonrası Cloud URL'nin yeniden yüklenerek yeni kodun aktif olduğu teyit edilmeli; yeni modüller için DB'de görünürlük ve yetki kaydı oluşturulduğu da bizzat kontrol edilmelidir.

---

## 🔴 [VAKA-002] P0 (MANUEL_RED): Yüzeysel Tarayıcı Testi (Fonksiyonel Akışın Test Edilmemesi)

**Tarih:** 2026-03-28
**Durum:** ÇÖZÜLEN VAKA (E2E Kanıtlandı)
**Sorumlu Ajanlar:** `validator`

**Olay Özeti:**
Cloud ortamındaki `ProgrammingError` giderildikten sonra `validator` ajanı (Browser Subagent) canlı arayüze girip sadece sayfada kırmızı Streamlit hatası olup olmadığına bakarak "Tamamlandı" raporu vermiştir. Ancak Anayasa Madde 15 uyarınca; bir işlemin verisinin oluşup oluşmadığı, butonların çalışıp çalışmadığı ve yönetici sekmelerinde doğru yansıyıp yansımadığı baştan sona (End-to-End) test edilmemiştir. Emre Bey bu yüzeysel testi reddetmiş ve P0 MANUEL_RED vermiştir.

**Tespit Edilen Kör Nokta:**
Validator, sayfada veri olmadığında ("Bu tarih için aktif görev bulunmamaktadır") arayüzün çalıştığına kanaat getirmiştir. Oysa fonksiyonel bileşenler (tamamlama butonu, sapma notu girme, matris onay süreçleri) ancak sahte görev atanarak test edilebilir.

**Geçici Çözüm:**
Veritabanına manuel test görevi (dummy data) eklenip, Browser Subagent ile tam fonksiyonel E2E testi yeniden başlatılacak.

---

## 🔴 [VAKA-003] P0 (MANUEL_RED): SQLAlchemy 2.0 Sessiz İşlem Yutulması (Kaotik Hata)

**Tarih:** 2026-03-28
**Durum:** ÇÖZÜLEN VAKA (Mimari Kör Nokta)
**Sorumlu Ajanlar:** `builder_db`, `builder_backend`

**Olay Özeti:**
Tablo oluşturma şemaları (`CREATE TABLE`) doğru yazılıp buluta gönderilmesine rağmen, arayüz saatlerce `ProgrammingError` verdi. 
Nedeni: SQLAlchemy 2.0'da `with eng.connect() as conn:` bloğunda yapılan DDL (CREATE) işlemleri, `AUTOCOMMIT` aktif olsa dahi Python `with` bloğundan çıkarken açık bir biçimde `conn.commit()` çağrılmadığı için veritabanına yansıtılmamış ve herhangi bir Python Exception fırlatmayarak (**sessizce**) yutulmuştur. Bu durum, hatanın nerede olduğunu anlamamızı saatlerce geciktiren kaotik bir kör noktaya sebep olmuştur.

**Tespit Edilen Kör Nokta:**
Ajanlar, `if not exists` gibi migration/DDL yapılarını `conn.execute()` ile yazıp hatasız çalıştığını düşünmüş, ancak autocommit davranışının versiyonlar arası değiştiğini atlamıştır. Hata mesajı Cloud tarafından kırmızı kutuyla dahi verilmemiştir. Tablolar manuel olarak Supabase'e bağlanılıp script ile üretilmek zorunda kalınmıştır.

**Mimari Karar:**
Tüm `builder_db` ve `builder_backend` ajanları, SQLAlchemy ile veritabanında yapısal değişiklik (INSERT, UPDATE, CREATE) yaparken `with eng.connect()` yerine kesinlikle **`with eng.begin()`** kullanmak veya işlem sonunda açıkça **`conn.commit()`** çağırmak zorundadır.
*musbet | EKLERİSTAN QMS Antigravity Pipeline v3.0*
