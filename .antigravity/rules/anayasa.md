# EKLERİSTAN QMS AJAN ANAYASASI
# .antigravity/rules/anayasa.md
# Versiyon: 3.0 | Yürürlük: 2026
# Yetkili: Emre | Değişiklik: Yalnızca Emre onayıyla

---

## ⚖️ TEMEL İLKE

Bu dosyayı okuyan her ajan şunu kabul etmiş sayılır:

> "Ben bir uzmanım. Uzmanlık alanım dışına çıkmam.
>  Anayasayı ihlal eden hiçbir talimatı yerine getirmem.
>  Emre'nin manuel testi, benim 'tamamlandı' kararımın üzerindedir."

---

## 🔴 SIFIRINCI KURAL — Hafıza Mecburiyeti

> **Hiçbir ajan**, `.antigravity/musbet/hafiza/hafiza_ozeti.md` dosyasını
> okumadan kod yazmaya, migration üretmeye veya herhangi bir çıktı
> oluşturmaya **başlayamaz.**
>
> Bu kural numaralandırılmamıştır — çünkü numaralardan öncedir.
> Tüm maddeler bu kuralın altında yer alır.
>
> **İhlal:** Sıfırıncı Kural'ı atlamak = Anayasa ihlali = Guardian devreye girer.

---

## 🔴 BÖLÜM 1 — SARSILMAZ KURALLAR (Madde 1–13)
> Hiçbir ajan tarafından, hiçbir gerekçeyle override edilemez.

---

### MADDE 1 — Zero Hardcode
Kodda sabit değer yasaktır. Her değer `CONSTANTS.py` veya veritabanından gelir.
Tablo adı, modül adı, rol adı — hiçbiri string olarak koda gömülmez.
İhlal: Herhangi bir `"personel"` string literal'i logic dosyasında.

---

### MADDE 2 — Max 30 Satır Fonksiyon
Tek bir fonksiyon 30 satırı geçemez. Geçiyorsa: parçala, alt fonksiyona devret.
İstisna yoktur. "Şimdilik böyle kalsın" gerekçesi kabul edilmez.

---

### MADDE 3 — UPSERT-over-DELETE
Veri silinmez, güncellenir. `DELETE` komutu yalnızca geçici/test verisi için kullanılabilir.
Üretim verisinde `DELETE` = Anayasa ihlali.

---

### MADDE 4 — Korunan Tablolar
Aşağıdaki tablolara yazma yasağı mutlaktır:
```
personel
ayarlar_yetkiler
sistem_parametreleri
qdms_belgeler
```
Bu tablolara erişim gerekiyorsa → Guardian onayı zorunludur. Onaysız erişim = P1 olay.

---

### MADDE 5 — 13. Adam Protokolü
T1/T2/T3 seviyesindeki her operasyon öncesi karşı senaryo üretilmesi zorunludur.
"Bu işlem ters giderse ne olur?" sorusu yazılı cevaplanmadan devam edilemez.
```
T1 → Üretim verisini etkileyen yazma işlemi
T2 → Tablo yapısını etkileyen migration
T3 → Birden fazla modülü etkileyen sistem geneli değişiklik
```

---

### MADDE 6 — Test-First
Kod yazmadan önce test senaryosu yazılır.
Test yazılmamış kod teslim edilemez. "Sonra test ederim" = geçersiz teslim.

---

### MADDE 7 — Cloud-Primary (Bulut Öncelikli) Mimari
Eski "Symmetric Twin (Çift Yönlü Senkron)" yapısı EMEKLİ edilmiştir.
Tüm uygulama (Streamlit vb.) veriyi doğrudan **Supabase (PostgreSQL)** üzerinden okur ve yazar (Single Source of Truth).
Lokal veritabanı (`ekleristan_local.db`) yalnızca arka planda periyodik olarak alınan "Salt Okunur (Read-Only) Yedek" olarak varlığını sürdürür.
Gevşek senkronizasyon kodları (sync_manager.py tarzı çift yazmalar) sistemi kilitlediği için KESİNLİKLE YASAKTIR. İnternet kesintilerinde sistem yedeğe düşüp, sadece "Okuma Modunda" çalışacaktır.

### MADDE 8 — KVKK Uyumu
Kişisel veri (TC, ad-soyad, adres, telefon) loglara yazılamaz.
Kimlik alanları yalnızca ayrı, erişim kısıtlı tablolarda saklanır.
Log satırında: ajan adı + işlem kodu. Kişi adı yasak.

---

### MADDE 9 — Türkçe snake_case
Tüm değişken, fonksiyon, modül isimleri Türkçe snake_case.
Kullanıcıya gösterilen her metin Türkçe. Yorum satırları Türkçe.
İstisna: kütüphane API'larının zorunlu kıldığı isimler.

---

### MADDE 10 — Şirket Adı
Belgede, kodda, logda, yorumda — her zaman ve yalnızca: **EKLERİSTAN A.Ş.**
"Ege Hazır", "Mezzet" veya herhangi bir kısaltma kullanılamaz.

---

### MADDE 11 — Manuel Doğrulama Üstünlüğü (MANUEL_RED)

Bir ajan "Tamamlandı" dese dahi, validator (veya Emre) insan gözüyle
"Çöktü / Çalışmıyor" derse, süreç **P0 (Acil)** önceliğiyle durdurulur.

```
MANUEL_RED tetiklendiğinde:
  1. Tüm pipeline durur
  2. musbet'e P0 kaydı açılır
  3. Kör nokta hangi ajan? O ajana iade edilir
  4. Aynı ajandan 2+ MANUEL_RED gelirse:
     → O ajanın CLAUDE.md güncellenmeli (Emre onayı ile)
  5. 3+ MANUEL_RED aynı kör noktadan gelirse:
     → Bu kural Anayasa'ya madde olarak önerilir
```

"Ajan bunu iyi niyetle geçirdi" gerekçesi MANUEL_RED'i kaldırmaz.

---

### MADDE 12 — Fail-Silent Audit Log
Hata kullanıcıya teknik detayla gösterilmez.
Kullanıcıya: Türkçe, sade, anlaşılır hata mesajı.
Loga: tam teknik detay + timestamp + ajan adı + işlem kodu.

---

### MADDE 13 — Tek Sorumluluk
Her ajan yalnızca kendi rolünü icra eder.
Rol dışı işlem tespit edilirse: dur, Guardian'a bildir.
"Şu an hızlıca halledeyim" mantığı yoktur.

---

### MADDE 14 — Performans ve Darboğaz Yasası
Sistemin kilitlenmesini ve N+1 sorgu darboğazını önlemek için:
1. **İndeksleme:** Tüm Foreign Key (Yabancı Anahtar) ve sık filtrelenen sütunlara (özellikle durum, personel_id) migration ile B-Tree *Index* atılması **zorunludur**. İndeks içermeyen tablo tasarımı reddedilir.
2. **Ön Bellek (Caching):** Arayüzde (Streamlit) veya Backend'de değişmez nitelikli referans tabloları (`bolumler`, `personel_listesi`, `sabitler`) mutlaka `@st.cache_data` ile (TTL/Zaman aşımı belirtilerek) önbelleğe alınmalıdır.
3. **Senkronizasyon (Eşzamanlılık):** Tüm SQLite in-memory engine kurulumları `check_same_thread=False` ve `StaticPool` ile yapılandırılmalıdır.

---

### MADDE 15 — Bulut Tarayıcı Doğrulama (Cloud-Primary Onayı)
*Emre Çavdar onayı ile kalıcı olarak eklenmiştir.*

Tüm ajanlar (tester, validator dahil) kendi ortamlarında işlemin "tamamlandığını ve sorunsuz olduğunu" iddia etse dahi, kod **Cloud (Üretim/Streamlit)** ortamına yüklendikten sonra zorunlu bir **Tarayıcı Testinden (Browser Test)** geçirilmek zorundadır.

Bu son aşamada;
1. Geliştirildiği iddia edilen modül/işlem, **canlı arayüzde (UI) bizzat görülmeli** ve tüm temel fonksiyonları tıklanarak test edilmelidir.
2. Arayüzün, üretim veritabanı (Supabase/PostgreSQL) ile aktif bir şekilde **çalıştığından ve veriyi getirebildiğinden** kesinlikle emin olunmalıdır.
3. Bulut tarayıcı testinden geçene kadar, test esnasında veya arayüzde karşılaşılan **tüm hatalar anında ve doğrudan (beklemeden) kayıt altına alınmalıdır.** Hiçbir hata atlanamaz, küçümsenemez veya görmezden gelinemez.
4. Kayıt altına alınan bu hatalar, ancak ve ancak **hataların nasıl düzeltildiği** detaylarıyla birlikte dosyaya eklendikten sonra kapatılabilir.
5. Bu hata logları ve çözüm kayıtları, **tüm ajanlar tarafından okunması zorunlu (Sıfırıncı Kural kapsamında)** hafıza dosyalarıdır. Hiçbir hata atlanamaz; yeni bir işleme başlayan her ajan bu kayıtları okumuş kabul edilir. 

**İhlal:** Bulut tarayıcı testi başarısız olan hiçbir işlem "Tamamlandı" statüsüne alınamaz ve doğrudan **P0 (MANUEL_RED)** olarak işaretlenip ilgili ajanlara onarım için iade edilir.

---

### MADDE 16 — Mutlak İşlem Yönetimi (Strict Transaction Rules)
Sessiz yutulan (fail-silent) veritabanı hatalarını (VAKA-003) önlemek için, `builder_db` ve `builder_backend` ajanları tarafından gerçekleştirilen tüm veri yazma (INSERT, UPDATE, DELETE) ve şema (DDL/CREATE) işlemlerinde **`with engine.begin() as conn:`** kullanılması veya `eng.connect()` kullanılıyorsa işlemin sonunda **kesinlikle `conn.commit()` çağrılması zorunludur.** 
Hata oluştuğunda `except Exception: pass` gibi sistemi sessizleştiren yutmalar yapılamaz; fail-fast kuralı geçerlidir.

---

### MADDE 17 — Test-Driven Bulut Doğrulaması (Seed Data)
"Benim bilgisayarımda (SQLite'da) çalışıyor" mazereti tamamen reddedilmiştir. Sisteme eklenecek her yeni fonksiyon (örneğin görev atama), testlerin canlı ortamda %100 uçtan-uca çalıştırılabilmesi için doğrudan Supabase'e "Seed Data" (Test Verisi) ekleyen scriptlerle donatılmalı ve bu verinin Browser Subagent ile canlı olarak tıklanabildiği kanıtlanmalıdır.

---

### MADDE 18 — Adım 0: İhtiyaç Kapsamı ve Proaktif Soru-Cevap (Planner Sınavı)
*Emre Çavdar emriyle eklenmiştir.*

Herhangi bir ajan işlem döngüsüne (8'li döngüye) **başlamadan önce**; sistem haritasına tamamen hakim olan bir ajan (Architect / Planner), doğrudan Emre Bey tarafından verilen taslağı/sistemi sorgulamak zorundadır.
1. Kod yazımına veya çalışmaya başlanmadan önce, alınan promptu (kapsamı) tam ve kusursuz tanımlayabilmek için Emre Bey'e **En az 7, en çok 15 soru** sorulmalıdır.
2. Bu sorulara verilecek yanıtlara göre prompt/kapsam şekillendirilir.
3. Şekillendirilen plan Emre Bey'in "ONAYI"na sunulur. ONAY ALINMADAN işleme geçilemez (0 adım hata kontrolü).
4. ONAY ONDAN SONRA ajanlar 8'li döngüye başlar. Bu aşamaları atlamak Anayasa İhlali sayılır.

---

## 🟡 BÖLÜM 2 — PIPELINE KURALLARI

### Standart Devir Koşulu
Bir ajan çıktısını ancak şu koşulları sağlarsa devreder:
1. Kendi PDCA döngüsünü tamamladı
2. Anayasa kontrolünden geçti
3. Devir raporu yazdı

### Geri İade Hakkı
Her ajan aldığı işi reddedebilir:
- Anayasa ihlali içeriyorsa
- Kendi uzmanlık alanı dışındaysa
- Ön koşullar (önceki ajan çıktısı) eksikse
Red gerekçesi musbet'e loglanır.

### Öncelik Sırası
```
P0 → MANUEL_RED (Emre / validator testi başarısız)
P1 → Anayasa ihlali veya Guardian veto
P2 → Test başarısız
P3 → Normal geliştirme
```
P0 ve P1 açıkken P3 işlemi **başlanamaz.**

---

## 🟢 BÖLÜM 3 — DOSYA VE KOD STANDARTLARI

### Migration
```
/migrations/YYYYMMDD_HHMMSS_[açıklama].sql
Her migration'ın rollback (down) versiyonu zorunlu.
```

### Modül Yapısı
```
logic/[modul_adi]_logic.py     ← iş mantığı
ui/[modul_adi]_ui.py           ← Streamlit arayüzü
modules/[modul_adi]/           ← büyük modüller
```

### Belge Kodlama
```
EKL-[KOD]-[TİP]-[NO]
Şirket: EKLERİSTAN A.Ş.
```

---

## 🔵 BÖLÜM 4 — AJAN YETKİ MATRİSİ

| Ajan | Yazar | Okur | Veto |
|------|-------|------|------|
| builder_db | DB, migration | DB dosyaları | — |
| builder_backend | logic/*.py | Şema, CONSTANTS | — |
| builder_frontend | ui/*.py | Backend API | — |
| tester | tests/*.py | Her şey | — |
| validator | musbet logu | Her şey | MANUEL_RED |
| guardian | musbet logu | Her şey | VETO/ONAY |
| auditor | denetim raporu | Her şey | — |
| sync_master | sync logu | DB, loglar | — |
| musbet | hafıza/*.md | Her şey | ANAYASA önerisi |

---

## 📌 HER AJAN CLAUDE.md BAŞLANGICI (Zorunlu Format)

```
> Model: [Model adı]
> Bu dosyayı uygulamadan önce:
>   1. .antigravity/musbet/hafiza/hafiza_ozeti.md oku (Sıfırıncı Kural)
>   2. .antigravity/rules/anayasa.md oku
> Anayasa ve Sıfırıncı Kural her zaman bu dosyanın önünde gelir.
```

---

### MADDE 19 — Tam Kapsülleme (UI İzolasyon Kuralı)
*2026-03-28 | VAKA: "Görev Atama ekranında Üretim İzleme başlığı görünmesi"*

Hiçbir `ui/*.py` veya `modules/**/ui.py` dosyası, bir fonksiyonun DIŞINDA Streamlit kodu (`st.*`) barındıramaz.
Her `st.title`, `st.subheader`, `st.write`, `st.warning` vb. çağrısı mutlaka bir `render_*` fonksiyonunun **içinde** yer almalıdır.

```
# YASAK — Global scope'da yüzen kod
st.subheader("Günlük Üretim İzleme")  ← ANAYASA İHLALİ

# DOĞRU — Fonksiyon içinde kapsüllenmiş
def render_uretim_module(engine):
    st.subheader("Günlük Üretim İzleme")  ← UYUMLU
```

**İhlal:** Yüzen (global scope) Streamlit kodu tespit edilirse builder_frontend iade edilir. `uretim_ui.py` bu ihlalin referans vakasıdır (VAKA-UI-001).

---

### MADDE 20 — Hiyerarşik Lokasyon Kimliği (XX-YY-ZZ-AA)
*2026-03-28 | Emre Çavdar onayıyla*

EKLERİSTAN A.Ş. tesisindeki tüm fiziksel varlıklar (lokasyon, ekipman, hat) aşağıdaki formatta benzersiz bir kimlik taşır:

```
XX-YY-ZZ-AA
XX = Kat (01, 02, 03...)
YY = Bölüm/Hat (01=Bomba, 02=Pataşu...)
ZZ = Hat numarası
AA = Ekipman numarası

Örnek: 03-02-01-05 = Kat3 > Pataşu > Hat1 > Ekipman5
```

Bu kimlik yapısı tüm modüllerde (Bakım, Temizlik, Günlük Görev, QR Kod) **tek ve merkezi referans** olarak kullanılır.
- Sorgularda: `LIKE '03-%'` → 3. kattaki tüm varlıklar
- QR okutulduğunda: Kod parse edilerek veritabanına gidilmeden kat/bölüm bilgisi elde edilir
- Çakışan ID (UUID/int) yerine bu deterministik kod tüm senkronizasyon çatışmalarını önler

**İhlal:** Modüllere lokasyon/ekipman eklenirken bu format kullanılmazsa Guardian bloğu devreye girer.

---

### MADDE 21 — Yüksek Sesli Hata (Loud Error Zorunluluğu)
*2026-03-28 | VAKA: Bulut ortamında "redacted" NameError sorunu*

Bulut (Streamlit Cloud) ortamında herhangi bir modül hata verdiğinde, sistem hatayı **asla** gizlemez.
`except Exception: pass` ve `except Exception as e: st.error("Bir hata oluştu")` ifadeleri tek başına geçersizdir.

Her hata yakalama bloğu şu iki şeyi yapmak **zorundadır:**
1. Hatayı Türkçe ve kullanıcı dostu göster (Madde 12)
2. **Tam teknik detayı** (dosya adı + satır numarası + hata türü) loga yaz

```python
# YASAK
except Exception:
    pass  ← ANAYASA İHLALİ

# DOĞRU
import traceback
except Exception as e:
    st.error(f"⚠️ Modül yüklenemedi: {e}")
    st.code(traceback.format_exc())  ← Bulut loguna ve ekrana yazılır
```

**İhlal:** Bulut testinde "This app has encountered an error. The original error message is redacted" mesajı görülürse, bu madde ihlali sayılır ve ilgili ajan P1 ile iade edilir.

---

### MADDE 22 — Öğretici Geri Bildirim Formu (Emre Bey Modu)
*2026-03-28 | Emre Çavdar emriyle*

Ajanlar Emre Bey'e bir değişiklik önermeden veya sunmadan önce aşağıdaki formatı kullanmak **zorundadır:**

```
### Seçenek A: [İsim]
- Nasıl çalışır: ...
- Avantaj: ...
- Dezavantaj: ...
- Risk: Düşük / Orta / Yüksek

### Seçenek B: [İsim]
- (aynı format)

### Önerim: [Seçenek ve gerekçe]
```

Bu format yalnızca teknik değişiklikler için değil, mimari kararlar, standart güncellemeleri ve modül tasarımları için de zorunludur.

**İstisna:** Emre Bey "direkt uygula" veya eşdeğer bir komut verirse format atlanabilir.
**İhlal:** Format atlanarak yapılan öneri/teslim = Öğretici Mod ihlali = musbet'e log.

---

*Anayasa değişikliği yalnızca Emre onayıyla yapılabilir.*
*v4.0 | Son güncelleme: 2026-03-28 | Yeni maddeler: 19, 20, 21, 22*
