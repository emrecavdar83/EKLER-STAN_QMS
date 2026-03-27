# EKLERİSTAN QMS — AJAN SİSTEMİ RESEPSIYONU
# AGENTS.md | Versiyon: 4.0
# Tüm ajanların giriş noktası. Buradan başla, buraya dön.

---

## 🔴 SIFIRINCI KURAL (Her Ajan İçin Zorunlu)

> Hiçbir ajan, herhangi bir işleme başlamadan önce şu dosyayı okumak **zorundadır:**
> `.antigravity/musbet/hafiza/hafiza_ozeti.md`
>
> Bu dosyayı okumadan kod yazan, migration yazan veya herhangi bir çıktı üreten ajan
> **Anayasa ihlali** gerçekleştirmiş sayılır.

---

## 📋 9'LU PIPELINE (Standart İş Akışı)

Bir modül talebi geldiğinde ajanlar **bu sırayla ve yalnızca bu sırayla** çalışır:

```
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

**Adım 0 ATLANAMAZ:** Emre Bey'in onayı alınmadan builder_db başlayamaz. Bu Anayasa Madde 18 ihlalidir.
**musbet** pipeline dışındadır — tüm aşamalarda paralel izler, loglar, uyarır.

---

## ⚙️ MADDE 5 — MODEL ATAMA TABLOSU

| Ajan | Ana Model | Fallback (Kota Dolunca) | Gerekçe |
|------|-----------|------------------------|---------|
| **planner** | Claude Sonnet 4.6 | Claude Haiku 3.6 | Sistem haritası, soru üretimi, kapsam analizi |
| builder_db | Gemini 2.5 Pro Low | **Claude Sonnet 4.6** | Şema üretimi, yapısal düşünme |
| builder_backend | Gemini 2.5 Pro High | **Claude Sonnet 4.6** | Karmaşık logic, SQLAlchemy |
| builder_frontend | Gemini 2.5 Pro Low | **Claude Sonnet 4.6** | UI üretimi, template |
| tester | Gemini Flash | Claude Haiku 3.6 | Hız, kural tabanlı test üretimi |
| validator | Claude Sonnet 4.6 | Claude Haiku 3.6 | İnsan simülasyonu, nüans, Bulut Tarayıcı Testi |
| guardian | Gemini Flash | Claude Haiku 3.6 | Hız, kural tabanlı risk tespiti |
| auditor | Claude Sonnet 4.6 | Claude Haiku 3.6 | Derin analiz, standart yorumu |
| sync_master | Claude Sonnet 4.6 | Claude Haiku 3.6 | Hafıza, tutarlılık, hata yönetimi |
| musbet | Gemini 2.5 Pro High | **Claude Sonnet 4.6** | Örüntü tespiti, uzun dönem hafıza |

> ⚠️ **KOTA KURALI (VAKA-005):** Gemini Pro kotası tükenirse ajan Fallback modele geçer.
> Fallback da erişilemezse işlem **duraklatılır** — sessiz bozulma KABUL EDİLMEZ.
> Mimari kararlar için yedek: **Claude Opus 4.6**

---

## 📁 AJAN DOSYA HARİTASI

```
.antigravity/
├── AGENTS.md                          ← (bu dosya) Router
├── rules/
│   └── anayasa.md                     ← 18 Madde, dokunulmaz (Madde 16/17/18 eklendi)
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

*AGENTS.md | EKLERİSTAN QMS Antigravity Pipeline v4.0*
