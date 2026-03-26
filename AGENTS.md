# EKLERİSTAN A.Ş. — QMS AGENTS.md
**Versiyon:** 3.2 | 2026 Q1  
**Değiştirmeden önce 13. Adam Protokolü uygulanmalıdır (T2 işlemi).**

---

## 1. PROJE KİMLİĞİ

| Alan | Değer |
|---|---|
| Şirket | EKLERİSTAN A.Ş. |
| Proje | EKLERİSTAN QMS |
| Sürüm | v4.1.7 |
| Mimar | Claude.ai (danışman) |
| Uygulayıcı | Antigravity |

---

## 2. STACK

| Katman | Teknoloji |
|---|---|
| Dil | Python 3.12+ |
| UI | Streamlit v1.x |
| ORM | SQLAlchemy 2.0 |
| DB Lokal | SQLite (WAL modu) |
| DB Bulut | Supabase PostgreSQL (public schema) |
| Senkron | Symmetric Twin (lokal ↔ Supabase) |

---

## 3. DOSYA HARİTASI (Bu Anayasa'nın Modülleri)

```
AGENTS.md                          ← Bu dosya (özet + router)
.antigravity/
  rules/
    anayasa.md                     ← Değiştirilemez kurallar
    13-adam.md                     ← 13. Adam Protokolü
    db-rules.md                    ← Veritabanı envanteri
    state-machine.md               ← QDMS durum makinesi
  commands/
    yeni-modul.md                  ← Master prompt şablonu
    13-adam-check.md               ← T1/T2/T3 kontrol komutu
  agents/
    builder.md                     ← S1 Builder tanımı
    auditor.md                     ← S3 Auditor tanımı
    sync-master.md                 ← S5 Sync Master tanımı
```

---

## 4. AJAN ZİNCİRİ (Özet)

```
Builder → Tester → Auditor → Guardian → Sync Master → Protector
  ↑                                         |             |
  └──────── RED ise geri ───────────────┘             └─Hata varsa Deftere yaz
```

### Hukuk Matrisi (Anayasa Sorumlulukları)

| Ajan | Anayasa Maddesi | Görev Tanımı |
|---|---|---|
| **S1 Builder** | Kural 1, 2, 3, 4 | İsimlendirme, Zero Hardcode ve Şirket Adı uyumlu kod yazar. |
| **S2 Tester** | Kural 3, 9 | Fonksiyon boyutu ve Teknik Uyumluluğu (Tech-Ledger) test eder. |
| **S3 Auditor** | **Tüm Kurallar** | Kodun anayasaya %100 uyumunu periyodik olarak denetler. |
| **S4 Guardian** | Kural 2, 5, 6, 8 | 13. Adam Protokolü, Hardcode denetimi ve Tablo koruması yapar. |
| **S5 Sync Master** | Kural 7 | Sadece Dry Run (Kural 7) sonrası senkronizasyon yapar. |
| **S6 Protector** | Kural 9, Madde 18 | Teknik Hata Defteri (Tech-Ledger) ve Görsel Standart koruması sağlar. |

- Max **3 iterasyon** / zincir
- Her adım **Artifact** üretir
- 6. adım (Protector) **Tech-Ledger** dökümünü zorunlu kılar.

---

## 5. MODEL SEÇİM KURALI

| Model | Ajan | Kural |
|---|---|---|
| Gemini Flash | Builder, Tester, Guardian | Hız + quota |
| Claude Sonnet 4.6 | Auditor, Sync Master, Protector | Hata kabul etmez |
| Claude Opus 4.6 | Mimari karar, T2/T3 13. Adam | Günlük max 2-3 sorgu |

---

## 6. STANDART ↔ MODÜL MATRİSİ

| Modül | BRC v9 | IFS v8 | FSSC v6 | ISO 9001 |
|---|---|---|---|---|
| QDMS | 3.7 | 4.2.1 | 2.5.9 | 7.5 |
| HACCP | 2.0 | 2.3.11 | ISO22000/8 | 8.1 |
| Reçete/BOM | 3.4 | 4.1.3 | 2.5.4 | 8.4 |
| Personel | 1.1.2 | 3.3.1 | 2.5.8 | 7.2 |
| DOG | 1.1.2 | 3.2.3 | 2.5.8 | 9.1 |
| MAP/Üretim | 4.6.2 | 4.10 | ISO22000/8 | 8.5 |
| Soğuk Oda | 4.11.1 | 4.9.2 | 2.5.1 | 8.5.1 |
| Düzeltici Faal. | 1.1.12 | 5.1.2 | ISO22000/10 | 10.2 |
| Geri Çağırma | 3.11 | 5.2 | 2.5.17 | 8.7 |

---

## 7. MODÜL DURUMU

| Durum | Modül |
|---|---|
| ✅ CANLI | modules/qdms/, ui/performans/, ui/soguk_oda_ui.py, ui/raporlama_ui.py, logic/auth_logic.py, logic/sync_manager.py |
| ⏳ BEKLEYEN | modules/gunluk_gorev/, modules/dog/ |
| 🔴 KRİTİK EKSİK | modules/recipe_bom/, modules/haccp/, modules/duzeltici/, modules/geri_cagirma/ |

---

*Son güncelleme: 2026 Q1 | Mimar: Claude.ai | Uygulayıcı: Antigravity*  
*Değişiklik için T2 işlemi → 13. Adam Protokolü zorunlu*
