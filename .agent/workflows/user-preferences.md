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

## 🔴 SIFIRINCI KURAL — Hafıza Mecburiyeti

> **Hiçbir ajan**, `.antigravity/musbet/hafiza/hafiza_ozeti.md` dosyasını okumadan işlem **başlayamaz.**
> Bu kural numaralandırılmamıştır çünkü her şeyin üzerindedir.

---

## ⚖️ ANAYASA MADDELERİ (1 - 25)

### BÖLÜM 1: SARSILMAZ KURALLAR

- **MADDE 1: Zero Hardcode.** Sabit değer yasaktır. `CONSTANTS.py` veya DB kullanılır.
- **MADDE 2: Max 30 Satır.** Fonksiyonlar 30 satırı geçemez.
- **MADDE 3: UPSERT-over-DELETE.** Veri silinmez, güncellenir.
- **MADDE 4: Korunan Tablolar.** `personel`, `ayarlar_yetkiler`, `sistem_parametreleri`, `qdms_belgeler` tablosuna yazmak için Guardian onayı şarttır.
- **MADDE 5: 13. Adam Protokolü.** T1/T2/T3 işlemleri öncesi: "Ters giderse ne olur?" sorusu yanıtlanmalı.
- **MADDE 6: Test-First.** Önce test senaryosu, sonra kod.
- **MADDE 7: Cloud-Primary.** Tek gerçek veri kaynağı **Supabase**. Lokal DB sadece yedeğe düşerse read-only'dir.
- **MADDE 8: KVKK Uyumu.** Kişisel veri (TC, tel) loglara YAZILAMAZ.
- **MADDE 9: Türkçe snake_case.** Tüm isimlendirme ve yorumlar Türkçe.
- **MADDE 10: Şirket Adı.** Daima: **EKLERİSTAN A.Ş.**
- **MADDE 11: Manuel Red.** Emre Bey "Çalışmıyor" derse, ajan "Tamamlandı" dese bile işlem P0 statüsüyle durur.
- **MADDE 12: Fail-Silent Audit.** Kullanıcıya sade hata, loga tam teknik detay.
- **MADDE 13: Tek Sorumluluk.** Her ajan sadece kendi rolünü yapar.

### BÖLÜM 2: GELİŞMİŞ KURALLAR

- **MADDE 14: Performans.** FK alanlarına indeksleme zorunludur. st.cache_data kullanılmalıdır.
- **MADDE 15: Bulut Tarayıcı Testi.** Canlıda (URL) bizzat tıklanıp görülmeden "Bitti" denilemez.
- **MADDE 16: İşlem Yönetimi.** `with engine.begin()` veya `commit()` kullanımı zorunludur. Sessiz hata yutulamaz.
- **MADDE 17: Seed Data.** Test senaryoları için Supabase'e test verisi ekleyen scriptler hazırlanmalıdır.
- **MADDE 18: Adım 0 (Planner).** İş başı yapmadan önce Emre Bey'e **7 - 15 soru** sorulup onay alınacaktır.
- **MADDE 19: Tam Kapsülleme.** Streamlit (st.*) kodları asla global scope'da olamaz. `render_*` içine hapsedilmelidir.
- **MADDE 20: Lokasyon Kimliği.** Kimlikler daima `XX-YY-ZZ-AA` (Kat-Hat-Cihaz) formatında olmalıdır.
- **MADDE 21: Yüksek Sesli Hata.** Bulutta hata gizlenmez, `traceback.format_exc()` ile loglanır.
- **MADDE 23: Bart Simpson Döngüsü.** "Çalışanı bozmama" yemini. Etraf kontrolü ve çift doğrulama şarttır.
- **MADDE 24: Snapshot Zorunluluğu.** `.antigravity/context_snapshots/` altındaki bağlamlar ajanın teknik otoritesidir.
- **MADDE 25: Hata Senkron Köprüsü.** Bulut hataları Sync Bridge ile lokale çekilir ve `hata_cozum_gunlugu.md`'ye işlenir.

---

## 🤖 AJAN ÇALIŞMA PLANI (10'lu Pipeline)

```text
-1. context_hub     → .antigravity/context_snapshots/ ilgili snapshot'ı oku (KRİTİK)
        ↓
 0. planner          → İhtiyaç Analizi (7-15 Soru) → Kapsam Onayı → 0 Adım Hata Kontrolü
        ↓
 1. builder_db       → Şema & Migration
        ↓
 2. builder_backend  → Business Logic & Servis Katmanı
        ↓
 3. builder_frontend → Streamlit UI/UX
        ↓
 4. tester           → Birim & Entegrasyon Testleri + Seed Data Doğrulaması
        ↓
 5. validator        → İnsan Gözü Simülasyonu + Bulut Tarayıcı Testi (Madde 15)
        ↓
 6. guardian         → Risk & Koruma Değerlendirmesi
        ↓
 7. auditor          → Anayasa Uyum Denetimi
        ↓
 8. sync_master      → Symmetric Twin Senkronizasyonu
```

> [!IMPORTANT]
> **Adım 0 ATLANAMAZ.** Emre Bey'in onayı alınmadan builder_db başlayamaz. Bu Anayasa Madde 18 ihlalidir.
> **musbet** pipeline dışındadır — tüm aşamalarda paralel izler, loglar, uyarır.

### ⚙️ MODEL ATAMA TABLOSU

| Ajan | Ana Model | Fallback (Kota Dolunca) | Gerekçe |
| :--- | :--- | :--- | :--- |
| **planner** | Claude Sonnet 3.6 | Claude Haiku 3.6 | Sistem haritası, soru üretimi |
| **builder_db** | Gemini 2.5 Pro Low | Claude Sonnet 3.6 | Şema üretimi, yapısal düşünme |
| **builder_backend** | Gemini 2.5 Pro High | Claude Sonnet 3.6 | Karmaşık logic, SQLAlchemy |
| **builder_frontend** | Gemini 2.5 Pro Low | Claude Sonnet 3.6 | UI üretimi, template |
| **tester** | Gemini Flash | Claude Haiku 3.6 | Hız, kural tabanlı test |
| **validator** | Claude Sonnet 3.6 | Claude Haiku 3.6 | İnsan simülasyonu, Bulut Testi |
| **guardian** | Gemini Flash | Claude Haiku 3.6 | Hız, risk tespiti |
| **auditor** | Claude Sonnet 3.6 | Claude Haiku 3.6 | Derin analiz, uyum yorumu |
| **sync_master** | Claude Sonnet 3.6 | Claude Haiku 3.6 | Hafıza, tutarlılık yönetimi |
| **musbet** | Gemini 2.5 Pro High | Claude Sonnet 3.6 | Örüntü tespiti, uzun hafıza |

> [!WARNING]
> Gemini Pro kotası tükenirse Fallback modele geçilir. Fallback de erişilemezse işlem **duraklatılır.**

---

## 📁 AJAN DOSYA HARİTASI

```text
.antigravity/
├── AGENTS.md                          ← Router
├── rules/
│   └── anayasa.md                     ← 25 Madde
├── commands/
│   └── yeni-modul.md                  ← Master prompt
├── builder_db/CLAUDE.md               ← DB Talimatları
├── builder_backend/CLAUDE.md          ← Backend Talimatları
├── builder_frontend/CLAUDE.md         ← UI/UX Talimatları
└── musbet/                            ← Kolektif Hafıza
    └── hafiza/
        ├── hafiza_ozeti.md            ← KRİTİK: Sıfırıncı Kural
        └── sistem_haritasi.md         ← GPS: DB, Modül, FK Haritası
```

---

## 📦 SİSTEM HARİTASI (v5.0)

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

- **VAKA-003:** Sessiz yutulan DB hatası (Önlem: Madde 16)
- **VAKA-UI-001:** Yüzen st.header hatası (Önlem: Madde 19)
- **Konum Yapısı:** Kat > Hat > Cihaz (Örn: 03-01-01-05) (Madde 20)
