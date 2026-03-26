# EKLERİSTAN A.Ş. — QMS AGENTS.md
# Versiyon: 3.2 | 2026 Q1
# Bu dosya Antigravity ajanlarının Anayasasıdır.
# Değiştirmeden önce 13. Adam Protokolü uygulanmalıdır.

---

## 1. PROJE KİMLİĞİ

```
Şirket   : EKLERİSTAN A.Ş.
Proje    : EKLERİSTAN QMS
Sürüm    : v3.2
Mimar    : Claude.ai (danışman)
Uygulayıcı: Antigravity
```

---

## 2. STACK

```
Dil      : Python 3.12+
UI       : Streamlit v1.x
ORM      : SQLAlchemy 2.0
DB Lokal : SQLite (WAL modu)
DB Bulut : Supabase PostgreSQL (public schema)
Senkron  : Symmetric Twin (lokal ↔ Supabase)
```

---

## 3. DEĞİŞTİRİLEMEZ KURALLAR (ANAYASA)

- Tüm değişken ve fonksiyon adları **Turkish snake_case** olacak
- **Hardcode yasak** — tüm sabitler CONSTANTS.py'den veya ayarlar_moduller tablosundan gelecek
- Her fonksiyon **maksimum 30 satır** olacak
- Şirket adı daima **EKLERİSTAN A.Ş.** — başka isim kullanılmayacak
- **T1 / T2 / T3** işlemlerinden önce 13. Adam Protokolü uygulanacak
- **Guardian red** verdiğinde otomatik devam edilmeyecek — insan onayı zorunlu
- Sync Master **Dry Run** yapmadan gerçek sync yapamaz

---

## 4. 13. ADAM PROTOKOLÜ

```
T1 → Veri sync öncesi
T2 → Kod veya mimari değişikliği
T3 → Yeni modül ekleme

Her T işleminde şu sorular sorulacak:
  1. Veri kaybı riski var mı?
  2. Standart ihlali (BRC/IFS/FSSC/ISO) olur mu?
  3. Geri alma nasıl yapılır?
  4. En kötü senaryo nedir?
  Karar: Devam / Dur / Revize
```

---

## 5. STATE MACHINE (QDMS — DEĞİŞTİRİLEMEZ)

```
taslak → incelemede → aktif → arsiv
```

Bu sıra hiçbir şekilde değiştirilemez.
Builder ajana bu kuralı "değiştirilemez kural" olarak ver.

---

## 6. VERİTABANI ENVANTERİ

### 6.1 Lokal Şema Dosyaları

```
database/schema_qdms.py
  - qdms_gk_kpi       (satır 16)
  - qdms_gk_form      (satır 72)
  - qdms_gk_form_yanit(satır 144)
  - qdms_gk_plan      (satır 183)

database/connection.py
  - sistem_loglari
  - lokasyon_tipleri
  - vardiya_tipleri
  - map_vardiya
```

### 6.2 Supabase Canlı Tablolar (public schema — 60+ tablo)

```
ANA SİSTEM:
  personel              ayarlar_bolumler
  ayarlar_yetkiler      ayarlar_moduller
  sistem_parametreleri

QDMS & KALİTE:
  qdms_belgeler         qdms_talimatlar
  qdms_gk_kpi           qdms_gk_form
  qdms_gk_plan          qdms_revizyon_log
  qdms_yayim            qdms_okuma_onay
  hijyen_kontrol_kayitlari
  gmp_denetim_kayitlari

MAP & ÜRETİM:
  map_bobin_kaydi       map_fire_kaydi
  map_vardiya           map_zaman_cizelgesi
  sicaklik_olcumleri

AKIŞ & FLOW:
  flow_definitions      flow_nodes
  flow_edges

NOT: SOS birimi DB'de ID=18 olarak tanımlıdır.
NOT: qdms_gk_* tabloları lokal + Supabase senkrondur.
```

### 6.3 Protected Tablolar (Sync Master dokunmadan önce onay alır)

```
personel              → 396 kayıt, kritik
ayarlar_yetkiler      → RBAC, güvenlik kritik
sistem_parametreleri  → Grace Period, oturum ayarları
qdms_belgeler         → aktif belgeler
```

---

## 7. MODÜL HARİTASI

```
CANLI ✅:
  modules/qdms/              → QDMS Stage 7.1-7.5 (10 dosya)
  ui/performans/             → Polivalans (5 dosya, 17.580 satır)
  ui/soguk_oda_ui.py         → SOSTS
  ui/raporlama_ui.py         → Günlük rapor (1605 satır)
  ui/map_uretim/             → MAP Üretim (5 dosya)
  ui/ayarlar/                → Yönetim arayüzü (11 dosya)
  logic/auth_logic.py        → RBAC v3.2 (489 satır)
  logic/sync_manager.py      → Symmetric Twin (710 satır, 22 tablo)

BEKLEYEN ⏳:
  modules/gunluk_gorev/      → Günlük görev listesi
  modules/dog/               → Davranış Odaklı Gözlem

KRİTİK 🔴:
  modules/recipe_bom/        → Reçete/BOM (HACCP için temel)
  modules/haccp/             → %51 eksik
  modules/duzeltici/         → Yok
  modules/geri_cagirma/      → Yok
```

### Bilinen Teknik Eksikler

```
ui/performans/   → __init__.py eksik (import riski)
app.py satır 154 → boot mesajı tüm kullanıcılara görünüyor (debug kalıntısı)
app.py satır 121 → yorum satırı çift yazılmış
```

---

## 8. 5 AJAN — ROL VE SORUMLULUK

### S1 — BUILDER (Gemini Flash)
```
Görev  : Python/Streamlit kod yazar
Kural  : Turkish snake_case, max 30 satır/fn
Kural  : Hardcode kullanamaz
Kural  : State machine'e uymak zorunda
Dosya  : modules/ veya ui/ altına yazar
```

### S2 — TESTER (Gemini Flash)
```
Görev  : Builder çıktısı için unit test yazar
Kural  : Builder bitmeden başlayamaz
Çıktı  : test_[modul].py + Artifact raporu
```

### S3 — AUDITOR (Claude Sonnet 4.6)
```
Görev  : Standart uyumunu denetler
Referans:
  BRC v9  → Md.1.1.2, 3.7, 4.11.1, 4.6.2, 4.9.1.1
  IFS v8  → Md.1.4, 2.3.11, 3.2.3, 4.1.3, 4.2.1, 4.20
  FSSC v6 → Md.2.5.4, 2.5.8, 2.5.9, 2.5.17
  ISO 9001→ Md.7.5, 8.1, 9.1, 10.2
  AIB     → GMP, Hijyen, IPM
Kural  : KO madde ihlali → kırmızı işaretle, dur
```

### S4 — GUARDIAN (Gemini Flash)
```
Görev  : Zero Hardcode + Anayasa kontrolü
Referans: CONSTANTS.py ve ayarlar_moduller tablosu
Kural  : CONSTANTS.py dışı string/sayı = RED
Kural  : RED → otomatik devam etme → insan onayı
Kural  : Onay sonrası Builder'a geri döner
```

### S5 — SYNC MASTER (Claude Sonnet 4.6)
```
Görev  : SQLite ↔ Supabase senkronizasyonu
Kural  : Dry Run zorunlu → sync_log_preview.txt
Kural  : İnsan onayı olmadan gerçek sync yapamaz
Kural  : Protected tablolara dokunmadan önce ekstra onay
Kural  : Hata → dur, raporla, sync yapma
Sync   : 22 tablo (logic/sync_manager.py → run_full_sync())
```

---

## 9. ZİNCİRLEME GÖREV AKIŞI

```
Builder → Tester → Auditor → Guardian → Sync Master
  ↑                              |
  └──────── RED ise geri ────────┘
                (insan onayı ile)

Kurallar:
  - Bir sonraki ajan önceki Artifact'i okur
  - Maksimum 3 iterasyon / zincir
  - 3. iterasyonda çözüm yoksa → dur, rapor et
  - Her adım Artifact üretir
```

---

## 10. STANDART ↔ MODÜL MATRİSİ

```
Modül            BRC v9    IFS v8    FSSC v6    ISO 9001
────────────────────────────────────────────────────────
QDMS             3.7       4.2.1     2.5.9      7.5
HACCP            2.0       2.3.11    ISO22000/8 8.1
Reçete/BOM       3.4       4.1.3     2.5.4      8.4
Personel         1.1.2     3.3.1     2.5.8      7.2
DOG              1.1.2     3.2.3     2.5.8      9.1
MAP/Üretim       4.6.2     4.10      ISO22000/8 8.5
Soğuk Oda        4.11.1    4.9.2     2.5.1      8.5.1
Düzeltici Faal.  1.1.12    5.1.2     ISO22000/10 10.2
Geri Çağırma     3.11      5.2       2.5.17     8.7
```

---

## 11. MODEL SEÇİM KURALI

```
Gemini Flash  → Builder, Tester, Guardian (hız + quota)
Claude Sonnet → Auditor, Sync Master (hata kabul etmez)
Claude Opus   → Mimari karar, T2/T3 13. Adam (sadece kritik)

NOT: Opus en yüksek quota tüketir. Günlük en fazla
     2-3 Opus sorgusu kullan.
```

---

## 12. MASTER PROMPT ŞABLONU (B-MOD — OTOMATİK ZİNCİR)

### Antigravity'ye yapıştırılacak TEK PROMPT:

```
GÖREV: [buraya görevi yaz]

ZİNCİR: S1 → S2 → S4 → claudes_plan.md'ye yaz → Claude S3+S5 devralır

─────────────────────────────────────────
S1 — BUILDER (Gemini Flash):
─────────────────────────────────────────
• Dosyayı yaz: modules/[modul]/ veya ui/ altına
• Turkish snake_case | Max 30 satır/fn | Hardcode yok
• State machine: taslak → incelemede → aktif → arsiv
• py_compile ile syntax kontrol et

─────────────────────────────────────────
S2 — TESTER (Gemini Flash):
─────────────────────────────────────────
• Builder bitince unit test yaz: tests/test_[modul].py
• Artifact: hata raporu + geçen/kalan test sayısı

─────────────────────────────────────────
S4 — GUARDIAN (Gemini Flash):
─────────────────────────────────────────
• Tüm .py dosyalarını tara: CONSTANTS.py dışı string/sayı = RED
• Fonksiyon 30 satır üstü = RED | İngilizce fn adı = RED
• RED → dur, bana getir. ONAY → bir sonraki adıma geç.

─────────────────────────────────────────
ZİNCİR BİTİŞİ — claudes_plan.md'yi yaz:
─────────────────────────────────────────
Dosya: C:\Users\GIDA MÜHENDİSİ\.gemini\antigravity\brain\4a011233-6f51-40d7-bbb8-21b93ec221fd\claudes_plan.md

Şu formatı kullan (olduğu gibi kopyala, sadece [...] alanlarını doldur):

---
# Claude'un Planı: [GÖREV BAŞLIĞI]

Durum: S4_ONAY
Tarih: [GG.AA.YYYY SS:DD]

## Değiştirilen Dosyalar
- [dosya1.py] — [ne yapıldı]
- [dosya2.py] — [ne yapıldı]

## S4 Guardian Raporu
[RED tespitler varsa listele | Yoksa "Hardcode yok — ONAY"]

## S2 Tester Raporu
[Geçen test sayısı] / [Toplam test] — [Notlar]

## Claude İçin Notlar
[S3 Auditor'un bakması gereken standart maddeleri yaz:
 örn. BRC v9 md.3.7, IFS v8 md.4.2.1 — veya boş bırak]
---

KURAL: Bu dosyayı yazdıktan sonra Claude Code'u uyar:
"claudes_plan.md güncellendi — S3+S5 zincirini başlatabilirsin"
```

### Kullanım Akışı

```
Sen → Antigravity'ye yukarıdaki promptu yapıştır (sadece GÖREV satırını değiştir)
        ↓
    S1 → S2 → S4 otomatik çalışır (Antigravity)
        ↓
    claudes_plan.md'ye "Durum: S4_ONAY" yazar
        ↓
    Claude Code'a gel, "zinciri devral" veya yeni mesaj yaz
        ↓
    Claude otomatik S3 Auditor + S5 Sync Master çalıştırır
        ↓
    claudes_plan.md "Durum: TAMAMLANDI" olur
```

---

## 13. DOSYA KOYMA YERLERİ

```
Bu dosya    → EKLERİSTAN_QMS/AGENTS.md   (proje kökü) ✅
Global      → ~/AGENTS.md                (tüm projeler)
Modül özel  → modules/[modul]/AGENTS.md  (gerekirse)

GEMINI.md   → Eski sürüm, hâlâ okunur
AGENTS.md   → v1.20.3+ geçerli, öncelikli
```

---

_Son güncelleme: 2026 Q1 | Mimar: Claude.ai | Uygulayıcı: Antigravity_
_Değişiklik için T2 işlemi → 13. Adam Protokolü zorunlu_
