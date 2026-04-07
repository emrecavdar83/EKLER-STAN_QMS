# EKLERİSTAN QMS — AJAN SİSTEMİ RESEPSIYONU
# AGENTS.md | Versiyon: 5.0 | v5.0 GRAND UNIFICATION

Bu proje **8 Katmanlı Antigravity Pipeline** ile yönetilmektedir. Ajanlar aşağıdaki sırayla ve yalnızca bu sırayla çalışır.

---

## 📋 8'Lİ PIPELINE (Standart İş Akışı)

Bir geliştirme talebi geldiğinde ajanlar şu sırayı takip eder:

0. **planner**          → İhtiyaç Analizi (7-15 Soru) → Kapsam Onayı (Emre)
1. **builder_db**       → Şema Tasarımı & Migration Hazırlığı
2. **builder_backend**  → İş Mantığı (Logic), Servis Katmanı ve DB İşlemleri
3. **builder_frontend** → Streamlit Arayüzü (UI) ve Formlar
4. **tester**           → Birim (Unit) & Entegrasyon Testleri
5. **validator**        → İnsan Gözü Simülasyonu & Bulut Tarayıcı Testi (Madde 15)
6. **guardian**         → Risk & Koruma Değerlendirmesi (Veto/Onay)
7. **auditor**          → Anayasa (30 Madde) ve Standartlara Uyum Denetimi
8. **sync_master**      → Sistem Sağlık & Bütünlük Denetimi (Cloud Sync)

---

## 🛠️ AJAN DOSYA HARİTASI

Tüm ajan konfigürasyonları `.antigravity/` altında düzenlenmiştir:

```
.antigravity/
├── AGENTS.md                          ← Bu dosya (Router)
├── rules/
│   └── anayasa.md                     ← 30 Madde (Ana Yasa)
├── builder_db/CLAUDE.md               ← Model: Gemini 2.5 Pro Low
├── builder_backend/CLAUDE.md          ← Model: Gemini 2.5 Pro High
├── builder_frontend/CLAUDE.md         ← Model: Gemini 2.5 Pro Low
├── tester/CLAUDE.md                   ← Model: Gemini Flash
├── validator/CLAUDE.md                ← Model: Claude Sonnet 4.6
├── guardian/CLAUDE.md                 ← Model: Gemini Flash
├── auditor/CLAUDE.md                  ← Model: Claude Sonnet 4.6
├── sync_master/CLAUDE.md              ← Model: Claude Sonnet 4.6
└── musbet/                            ← Projenin Kolektif Hafızası (Gemini High)
    └── hafiza/
        ├── acik_vakalar.md
        ├── cozulmus_vakalar.md
        ├── hafiza_ozeti.md
        └── sistem_haritasi.md
```

---

## 🚫 DEVR-Ü TESLİM KURALI (Anayasa Madde 28)

Her ajan işini bitirince devir raporunu yazar, bir sonraki ajanı ismiyle çağırır ve kendi işini sonlandırır.

*AGENTS.md | v5.0 Integrity Seal | EKLERİSTAN A.Ş.*
