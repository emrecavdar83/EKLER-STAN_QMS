# EKLERİSTAN QMS — Hafıza Özeti
# .antigravity/musbet/hafiza/hafiza_ozeti.md
# ⚠️ SIFIRINCI KURAL — Bu dosya her ajan tarafından işe başlamadan okunur.

---

## 📌 SİSTEM DURUMU

**Son Güncelleme:** 2026-04-15
**Versiyon:** v6.0.0 (DATABASE SIMPLIFICATION & MASTER SCHEMA)
**Mimari:** Cloud-Primary (Supabase / Madde 7 Sadakati)
**Mod:** Otonom & Zırhlı (Hardened Mode)
**Sistem Haritası:** `.antigravity/musbet/hafiza/sistem_haritasi.md`

---

## ✅ ÇÖZÜLMÜŞ VAKALAR (Kronolojik)

| # | Vaka | Tarih | Kök Neden | Çözüm |
|---|------|-------|-----------|-------|
| 17 | VAKA-017: Logout Loop Persistence | 2026-03-30 | Cookie vs Session Conflict | URL `?logout=1` Priority Barrier (v5.1.2) |
| 18 | VAKA-018: Navigation AttributeError | 2026-03-30 | Accessing stale state during sync | Try-Except Barrier in `app.py` callbacks |
| 19 | VAKA-019: Elvan Duplicate Record | 2026-03-30 | Corrupted non-ASCII entry (`?`) | Self-healing DELETE in `app.py` unified block |
| 20 | VAKA-020: Operator MAP Perms | 2026-03-30 | Label-Key Mismatch (Label wrote to DB) | Database Normalization (Label -> Slug) |
| 21 | VAKA-021: SQL Join Logic failure | 2026-03-30 | Join on Slug vs Label | `zone_yetki.py` Label-to-Key Bridge (v5.4.0) |
| 22 | VAKA-022: Zone Wipe Bug | 2026-03-30 | SQLite `INSERT OR REPLACE` deletes zones | `ON CONFLICT DO UPDATE` with `CASE` preservation |
| 23 | VAKA-023: Grand Unification Plan | 2026-03-30 | Disconnected Fixes | v5.4.0 Unified Maintenance Block in `app.py` |
| 24 | VAKA-024: Musbet Memory Void | 2026-03-30 | Empty memory files (Constitutional violation) | Memory files populated with v14-v23 history |
| 28 | VAKA-028: Rule Zero Enforcement | 2026-03-30 | Hallucinatory "Done" reports | Physical Integrity Audit Protocol (v5.5.0) |
| 30 | VAKA-030: Persistent Sessions | 2026-03-31 | Manual Login Friction | Cookie-based Auth & Module Memory (v5.8.0) |
| 31 | VAKA-031: KPI BRC Limits | 2026-04-14 | Blind data entry violating BRC | Dynamic Min-Max Spec parsing & Soft-Stop |
| 32 | VAKA-032: MAP UI Stability | 2026-04-14 | `st.popover` state loss | Expander/Toggle replacement for robust sessions |
| 33 | VAKA-033: GMP UI Geri Bildirim Eksikliği | 2026-04-15 | `st.toast` ve `st.rerun` çakışması | Session_state tabanlı Flash Pattern kullanıldı |
| 34 | VAKA-034: Supabase Sadeleştirme | 2026-04-15 | Overloaded Logic & Dead Tables | connection.py refaktör, 6 tablo silindi |
---

## ⚠️ DİKKAT NOTLARI (v5.5.0)

1. **PROMPT_0 PROTOKOLÜ:** Her prompt başında `hafiza_ozeti.md` okunmadan işleme başlanamaz (SIFIRINCI KURAL).
2. **PHYSICAL_CHECK:** "Fixlendi" demeden önce `tmp/` altındaki kilit (lock) dosyalarının varlığı BİZZAT kontrol edilmelidir. 
3. **DİNAMİKLİK:** Modül isimleri koda (hardcode) değil, her zaman veritabanına (`ayarlar_moduller`) sorulmalıdır.

---
*musbet | v5.5.0 Integrity Seal | Tarih: 30.03.2026*
