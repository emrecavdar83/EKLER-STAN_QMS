# EKLERİSTAN QMS — AJAN SİSTEMİ RESEPSIYONU
# AGENTS.md | Versiyon: 3.0
# Tüm ajanların giriş noktası. Buradan başla, buraya dön.

---

## 🔴 SIFIRINCI KURAL (Her Ajan İçin Zorunlu)

> Hiçbir ajan, herhangi bir işleme başlamadan önce şu dosyayı okumak **zorundadır:**
> `.antigravity/musbet/hafiza/hafiza_ozeti.md`
>
> Bu dosyayı okumadan kod yazan, migration yazan veya herhangi bir çıktı üreten ajan
> **Anayasa ihlali** gerçekleştirmiş sayılır.

---

## 📋 8'Lİ PIPELINE (Standart İş Akışı)

Bir modül talebi geldiğinde ajanlar **bu sırayla ve yalnızca bu sırayla** çalışır:

```
1. builder_db       → Şema & Migration
        ↓
2. builder_backend  → Business Logic & Servis Katmanı
        ↓
3. builder_frontend → Streamlit UI/UX
        ↓
4. tester           → Birim & Entegrasyon Testleri
        ↓
5. validator        → İnsan Gözü Simülasyonu (Emre Bey)
        ↓
6. guardian         → Risk & Koruma Değerlendirmesi
        ↓
7. auditor          → Anayasa Uyum Denetimi
        ↓
8. sync_master      → Symmetric Twin Senkronizasyonu
```

**musbet** pipeline dışındadır — tüm aşamalarda paralel izler, loglar, uyarır.

---

## ⚙️ MADDE 5 — MODEL ATAMA TABLOSU

| Ajan | Model | Gerekçe |
|------|-------|---------|
| builder_db | Gemini 2.5 Pro Low | Şema üretimi, yapısal düşünme |
| builder_backend | Gemini 2.5 Pro High | Karmaşık logic, SQLAlchemy |
| builder_frontend | Gemini 2.5 Pro Low | UI üretimi, template |
| tester | Gemini Flash | Hız, kural tabanlı test üretimi |
| validator | Claude Sonnet 4.6 | İnsan simülasyonu, nüans |
| guardian | Gemini Flash | Hız, kural tabanlı risk tespiti |
| auditor | Claude Sonnet 4.6 | Derin analiz, standart yorumu |
| sync_master | Claude Sonnet 4.6 | Hafıza, tutarlılık, hata yönetimi |
| musbet | Gemini 2.5 Pro High | Örüntü tespiti, uzun dönem hafıza |

> Mimari kararlar için yedek: **Claude Opus 4.6**

---

## 📁 AJAN DOSYA HARİTASI

```
.antigravity/
├── AGENTS.md                          ← (bu dosya) Router
├── rules/
│   └── anayasa.md                     ← 13 Madde, dokunulmaz
├── commands/
│   └── yeni-modul.md                  ← Master prompt
│
├── builder_db/CLAUDE.md               ← Model: Gemini 2.5 Pro Low
├── builder_backend/CLAUDE.md          ← Model: Gemini 2.5 Pro High
├── builder_frontend/CLAUDE.md         ← Model: Gemini 2.5 Pro Low
├── tester/CLAUDE.md                   ← Model: Gemini Flash
├── validator/CLAUDE.md                ← Model: Claude Sonnet 4.6
├── guardian/CLAUDE.md                 ← Model: Gemini Flash
├── auditor/CLAUDE.md                  ← Model: Claude Sonnet 4.6
├── sync_master/CLAUDE.md              ← Model: Claude Sonnet 4.6
│
└── musbet/                            ← Model: Gemini 2.5 Pro High
    ├── CLAUDE.md
    ├── index.md
    └── hafiza/
        ├── acik_vakalar.md
        ├── cozulmus_vakalar.md
        ├── hafiza_ozeti.md
        └── lessons.md
```

---

## 🚫 DEPRECATED (Kullanım Dışı)

Aşağıdaki dosyalar **silinmiştir**. Referans verilmez:

```
[SİLİNDİ] .antigravity/agents/builder.md
[SİLİNDİ] .antigravity/agents/tester.md
[SİLİNDİ] .antigravity/agents/auditor.md
[SİLİNDİ] .antigravity/agents/guardian.md
[SİLİNDİ] .antigravity/agents/sync-master.md
```

---

## 🔁 DEVRET KURALI

Her ajan işini bitirince:
1. Devir raporu yazar (ne yaptı, ne değişti, risk var mı)
2. Bir sonraki ajanı **ismiyle** çağırır
3. musbet'e bildirim gönderir
4. Kendi işini **sonlandırır** — bir sonraki ajanın işine karışmaz

---

*AGENTS.md | EKLERİSTAN QMS Antigravity Pipeline v3.0*
