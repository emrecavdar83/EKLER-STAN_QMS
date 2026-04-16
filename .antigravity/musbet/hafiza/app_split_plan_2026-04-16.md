# ✅ Planner Çıktısı — Onaylanmış Scope + Risk Matrisi + Rollback Planı
# app_split_plan_2026-04-16.md | v6.1.9 Grand Unification

---

## 📋 Q9 Analiz Sonucu

```
python (in-tree imports):  0 dosya  → app.py'yi Python modülü olarak import eden YOK
doc/script mentions:       16 dosya → sadece .md dokümantasyonu + shell komutu
```

**Sonuç: Refactor Python bağımlılığı açısından GÜVENLİ.** Yalnızca `streamlit run app.py` komutu korunmalı (değişiklik yok). Dokümantasyon güncellemeleri auditor adımına eklenecek.

---

## 🎯 Onaylanmış Kapsam (12 Soru Cevaplarıyla)

| # | Karar | Etki |
|---|-------|------|
| Q1 | ✅ **4 dosya split** | `logic/app_bootstrap.py`, `logic/app_auth_flow.py`, `ui/app_navigation.py`, `ui/app_module_registry.py` |
| Q2 | ✅ **Monkey patch TAMAMEN KALDIR** — `requirements.txt` sürüm pin | `pandas==2.x`, `sqlalchemy==2.0.x` sabitlenecek. Patch silinir. |
| Q3 | ✅ **Registry pattern** | Dispatcher `dict[slug, ModuleSpec]` ile |
| Q4 | ✅ **Parola doğrulama auth_logic'ten ÇIKAR** → `logic/security/password.py` (YENİ) | `sifre_dogrula`, `sifre_hashle` izole edilir |
| Q5 | ✅ `st.set_page_config` app.py'de **ilk çağrı** (sabit) | Streamlit kısıtı gereği |
| Q6 | ✅ Cookie manager **getter fonksiyon** ile | `from logic.app_bootstrap import get_cookie_manager` |
| Q7 | ✅ Zone gate **dispatcher ile birlikte** | `ui/app_module_registry.py` içinde |
| Q8 | ✅ Admin tools **ayrı dosya** → `logic/app_admin_tools.py` (YENİ — Q8 eklendi) | DB Tanılama + Admin Reset |
| Q9 | ✅ **Python bağımlılığı yok** — güvenli | Yalnızca .md dokümanlar güncellenecek |
| Q10 | ✅ **4 kademeli commit/PR** | Her extraction ayrı + rollback esnek |
| Q11 | ✅ E2E smoke **zorunlu** | Login → 3 modül → Logout + QR bypass |
| Q12 | ✅ Bulut doğrulaması **ADMIN** ile | Tam modül görünürlüğü için |

### 📦 Nihai Dosya Haritası

```
app.py  (513 → ~60 satır)
  ├─ st.set_page_config (Madde 5 gereği ilk)
  ├─ from logic.app_bootstrap import init_app_runtime
  ├─ init_app_runtime() çağrısı (engine, branding, cookie)
  ├─ from logic.app_auth_flow import login_screen, bootstrap_session
  └─ main_app() (~35 satır — sadece yüksek seviye akış)

YENİ DOSYALAR (6 adet):
├─ logic/app_bootstrap.py          [cookie, branding, engine init]
├─ logic/app_auth_flow.py          [login, QR, remember_me, logout]
├─ logic/app_admin_tools.py        [Admin DB tanılama + reset]
├─ logic/security/__init__.py
├─ logic/security/password.py      [sifre_dogrula, sifre_hashle]
├─ ui/app_navigation.py            [header + sidebar + hızlı menü]
└─ ui/app_module_registry.py       [registry + dispatcher + zone_gate]

DEĞİŞECEK DOSYALAR:
├─ app.py                          [minimal entry point]
├─ requirements.txt                [pandas + sqlalchemy pin]
├─ logic/auth_logic.py             [sifre_* fn'leri TAŞINDI — re-export için shim]
└─ tests/test_app_refactor.py      [YENİ: 10+ E2E test]
```

---

## ⚠️ Risk Matrisi

| Risk | Olasılık | Etki | Önlem | Sahip |
|------|:---:|:---:|-------|-------|
| **Monkey patch kaldırma → Pandas SQLAlchemy TypeError** | 🟠 Orta | 🔴 Kritik | Önce `requirements.txt` pin + local test; patch'i SON adımda kaldır | guardian |
| **Circular import** (bootstrap ↔ auth_flow ↔ nav) | 🟠 Orta | 🟠 Orta | TYPE_CHECKING guard; lazy import lambdalar | builder_backend |
| **`st.set_page_config` sıra ihlali** | 🟢 Düşük | 🔴 Kritik | Test: `test_page_config_first()` AST kontrolü | tester |
| **Session state orphaned key** (modül geçişinde) | 🟡 Düşük-Orta | 🟠 Orta | Mevcut `_prev_module_key` temizleme korunur | validator |
| **Parola fn taşınması → auth_logic eski import'lar kırılır** | 🟠 Orta | 🔴 Kritik | `logic/auth_logic.py` re-export shim (backward compat) | builder_backend |
| **Registry entry eksikliği** (14 modülden biri unutulur) | 🟡 Orta | 🔴 Kritik | Test: `test_module_registry_completeness()` DB karşılaştırır | tester |
| **Streamlit Cloud rebuild başarısızlığı** | 🟢 Düşük | 🔴 Kritik | Rollback tag; cloud log izleme | sync_master |
| **Cookie manager singleton çiftlenmesi** | 🟢 Düşük | 🟡 Düşük | Test: `test_cookie_manager_singleton()` | tester |
| **4 PR'ın birbirine bağımlılığı** | 🟠 Orta | 🟡 Düşük | Her commit **kendi başına build'leyebilir** olmalı | validator |
| **Docs drift** (SYSTEM_MAP.md vb.) | 🟡 Orta | 🟢 Düşük | Auditor adımında toplu güncelleme | auditor |
| **Pandas/SQLAlchemy sürüm pin → başka paket çakışması** | 🟡 Orta | 🟠 Orta | `pip check`; lokal venv testi | guardian |

**Genel risk seviyesi:** 🟠 **Orta** (kontrolü yapılabilir)

---

## ⏮️ Rollback Planı

### Ön Koşullar (sync_master'dan ÖNCE)

```bash
# 1. Güvenlik tag'i
git tag v6.1.9-pre-split
git push origin v6.1.9-pre-split

# 2. Requirements.txt için backup
cp requirements.txt requirements.txt.pre-split

# 3. Baseline test snapshot
python -m pytest tests/ > baseline_test_output.txt
```

### 4 Kademeli Commit — Rollback Noktaları

| Commit | Kapsam | Rollback Maliyeti |
|--------|--------|-------------------|
| **C1** — `chore(deps): pin pandas/sqlalchemy versions` | requirements.txt + monkey patch kaldır | `git revert C1` → 1 commit |
| **C2** — `refactor(app): extract bootstrap & auth flow` | logic/app_bootstrap.py + logic/app_auth_flow.py + security/password.py | `git revert C2` → app.py kısmen eski |
| **C3** — `refactor(app): extract navigation + admin tools` | ui/app_navigation.py + logic/app_admin_tools.py | `git revert C3` |
| **C4** — `refactor(app): module dispatcher registry` | ui/app_module_registry.py + app.py <100 satır | `git revert C4` (en riskli) |

### Acil Rollback Prosedürü

```bash
# Sorun Streamlit Cloud'da → hemen geri dön
git revert HEAD  # son commit
git push origin main

# Veya tam rollback (pre-split state) — EMRE BEY ONAYI ŞART
git reset --hard v6.1.9-pre-split
git push origin main --force-with-lease
```

---

## 📊 Başarı Kriterleri

| Kriter | Hedef |
|--------|:-----:|
| `app.py` satır | ≤ 80 |
| `main_app()` satır | ≤ 40 |
| Yeni dosya Max satır | ≤ 200 |
| Max fonksiyon satırı | ≤ 30 (Anayasa) |
| Test coverage (yeni kod) | ≥ 85% |
| E2E smoke pass | 100% |
| pip check | 0 hata |
| Bulut build süresi | ≤ 3 dk |
| Manuel ADMIN E2E | ≤ 5 dk |

---
*Onaylayan: Antigravity | v6.1.9 Integrity Seal | Tarih: 16.04.2026*
