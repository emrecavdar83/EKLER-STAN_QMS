# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Çok Ajanlı Sistem

Bu proje **Claude (S3 Auditor / S5 Sync Master)** + **Antigravity (S1 Builder / S2 Tester / S4 Guardian)** iş birliğiyle geliştirilmektedir.

**Koordinasyon dosyası:**
`C:\Users\GIDA MÜHENDİSİ\.gemini\antigravity\brain\4a011233-6f51-40d7-bbb8-21b93ec221fd\claudes_plan.md`

Ajan rolleri ve iş akışı için → [AGENTS.md](AGENTS.md)

### OTOMATİK ZİNCİR KURALI (DEĞİŞTİRİLEMEZ)

Her oturum başında veya kullanıcı yeni bir görev verdiğinde:

1. `claudes_plan.md` dosyasını oku
2. Eğer `Durum: S4_ONAY` satırı varsa → **S3 Auditor** rolünü otomatik üstlen:
   - Değiştirilen dosyaları denetle (BRCGS/IFS/FSSC/ISO maddeleri)
   - Guardian RED tespiti varsa kullanıcıya bildir, devam etme
   - Guardian ONAY ise → **S5 Sync Master** adımına geç
3. S5 Sync Master:
   - `sync_log_preview.txt` üret (Dry Run)
   - Kullanıcıdan "ONAYLA" bekle
   - Onay sonrası SQLite ↔ Supabase sync
   - `claudes_plan.md` durumunu `TAMAMLANDI` olarak güncelle
4. Eğer `Durum: TAMAMLANDI` veya dosya yoksa → normal konuşmaya devam et

**ÖNEMLİ:** Kullanıcı "hepsini çalıştır" veya yeni görev verdiğinde bu zinciri başlat.
Sync için her zaman insan onayı (ONAYLA komutu) zorunludur.

## Project Overview

EKLERİSTAN QMS (v4.0.3) is a Quality Management System for a food production facility, targeting BRCGS v9, IFS v8, FSSC 22000 v6, and ISO 9001 compliance. Built with Python + Streamlit, backed by a dual-database architecture: local SQLite for offline/dev, Supabase PostgreSQL for production.

## Running the Application

```bash
# Activate virtual environment (any of these may exist)
source .venv/Scripts/activate  # Windows Git Bash
.venv\Scripts\activate.bat     # Windows CMD

# Start the app
streamlit run app.py
# App available at http://localhost:8501

# Or use the startup script
./baslat.bat
```

## Running Tests

```bash
python -m pytest tests/ -v

# Individual test suites
python -m pytest tests/test_qdms_stage7.py -v
python -m pytest tests/test_gorev_karti.py -v
python -m pytest tests/test_sosts_bakim.py -v
```

## Verifying a Module Compiles

```bash
python -m py_compile modules/qdms/pdf_uretici.py
```

## Database

Dual-database setup managed in [database/connection.py](database/connection.py):
- **Local:** `ekleristan_local.db` (SQLite, WAL mode) — fallback when no `secrets.toml`
- **Production:** Supabase PostgreSQL via `.streamlit/secrets.toml` → `DB_URL`
- `get_engine()` is a `@st.cache_resource` — single connection pool shared across sessions
- Schema auto-initializes on first `get_engine()` call (creates tables, seeds admin account)
- **Schema changes require a migration script** in `migrations/` or `scripts/` — direct `ALTER TABLE` is forbidden

## Architecture

```
app.py              — Streamlit entry point, session state, auth, routing (monolithic, ~5000+ lines)
constants.py        — Org hierarchy, position levels, shift lists (POSITION_LEVELS, MANAGEMENT_LEVELS)
database/           — SQLAlchemy engine, QDMS schema
logic/              — Business logic (auth, data fetching, cache, sync, zone permissions)
ui/                 — Streamlit UI modules per functional area (qdms, kpi, gmp, uretim, etc.)
modules/qdms/       — QDMS subsystem: document registration, templates, PDF, revisions, job cards
scripts/            — One-off migration and bootstrap scripts
tests/              — pytest test suites
```

Key logic files:
- [logic/auth_logic.py](logic/auth_logic.py) — RBAC, bcrypt authentication, `kullanici_yetkisi_getir_dinamik()`
- [logic/cache_manager.py](logic/cache_manager.py) — **All cache clearing must go through here** (scattered `cached_fn.clear()` calls are forbidden)
- [logic/data_fetcher.py](logic/data_fetcher.py) — Cached data retrieval (TTL-based)
- [logic/zone_yetki.py](logic/zone_yetki.py) — Zone-based permission checks (`zone_girebilir_mi()`, `eylem_yapabilir_mi()`)
- [modules/qdms/pdf_uretici.py](modules/qdms/pdf_uretici.py) — ReportLab server-side PDF generation

## RBAC Levels

| Level | Role |
|-------|------|
| 0 | Yönetim Kurulu (Board) |
| 1 | Genel Müdür (CEO) |
| 2 | Direktörler (Directors) |
| 3 | Müdürler (Managers) |
| 4 | Koordinatör/Şef |
| 5 | Bölüm Sorumlusu |
| 6 | Personel (Staff) |
| 7 | Stajyer/Geçici (Intern) |

## Core Rules (ANAYASA)

These rules are architectural law for this project:

1. **Zero Hardcode** — No business rules (temperature limits, KPI thresholds, tolerances) in code. All config is database-driven.
2. **Turkish snake_case** — Variable and function names use Turkish words in snake_case (e.g., `veri_getir`, `bolum_filtrele`).
3. **Max 30 lines per function.**
4. **Cache TTL ≤ 60 seconds** — Permission caches must expire within 60s.
5. **No ID-based sync** — Cross-database sync uses logical keys (names, codes), never auto-increment IDs.
6. **UPSERT only** — Never use `df.to_sql(if_exists='replace')`. Use proper UPSERT operations.
7. **Maker/Checker** — The user who enters data cannot be the same user who approves it.
8. **13th Adam Protocol** — Before any architectural change or sync operation, generate a mandatory counter-scenario (what could go wrong).
9. **Fail-Safe alerts** — CCP limit breaches trigger automatic alarms without human approval.

## PDF Generation

All PDF output uses ReportLab server-side (no browser `window.print()`). The main PDF module is [modules/qdms/pdf_uretici.py](modules/qdms/pdf_uretici.py).

## Active Development Area

Recent commits are focused on the QDMS (Kalite Doküman Yönetim Sistemi) module, specifically:
- Görev Kartı (Job Card / GK) with BRCGS compliance
- 5-discipline tabbed editor UI
- Hierarchical responsibility-interaction PDF layout
- Content validation per BRCGS standards
