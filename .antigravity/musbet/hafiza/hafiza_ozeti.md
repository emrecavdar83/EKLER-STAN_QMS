# EKLERİSTAN QMS — Hafıza Özeti
# .antigravity/musbet/hafiza/hafiza_ozeti.md
# ⚠️ SIFIRINCI KURAL — Bu dosya her ajan tarafından işe başlamadan okunur.

---

## 📌 SİSTEM DURUMU

**Son Güncelleme:** 2026-03-29
**Versiyon:** v4.0.5
**Mimari:** Cloud-Primary (Supabase/PostgreSQL)
**Sistem Haritası:** `.antigravity/musbet/hafiza/sistem_haritasi.md`

---

## 🗄️ VERİTABANI REFERANS (Hızlı Erişim)

> Detaylı kolon, FK ve modül ilişkileri için: `sistem_haritasi.md` Bölüm 1

### Çekirdek Tablolar (DOKUNULMAZ)
`personel` · `ayarlar_bolumler` · `ayarlar_moduller` · `ayarlar_yetkiler` · `ayarlar_urunler` · `sistem_parametreleri` · `sistem_loglari`

### Operasyonel Tablolar
`depo_giris_kayitlari` · `urun_kpi_kontrol` · `gmp_soru_havuzu` · `hijyen_kontrol_kayitlari` · `ayarlar_temizlik_plani` · `soguk_odalar` · `sicaklik_olcumleri`

### MAP Modülü
`map_vardiya` · `map_zaman_cizelgesi` · `map_fire_kaydi` · `map_bobin_kaydi`

### QDMS Modülü (11 tablo)
`qdms_belgeler` · `qdms_sablonlar` · `qdms_revizyon_log` · `qdms_yayim` · `qdms_talimatlar` · `qdms_okuma_onay` · `qdms_gorev_karti` · `qdms_gk_sorumluluklar` · `qdms_gk_etkilesim` · `qdms_gk_periyodik_gorevler` · `qdms_gk_kpi`

### Günlük Görevler
`gunluk_gorev_katalogu` · `gunluk_periyodik_kurallar` · `birlesik_gorev_havuzu`

### Performans
`performans_degerledirme`

### Flow Engine (HENÜZ AKTİF DEĞİL)
`flow_definitions` · `flow_nodes` · `flow_edges` · `flow_bypass_logs` · `personnel_tasks`

---

## 📊 AJAN BAZLI HATA SAYACI

| Ajan | Toplam | MANUEL_RED | P1 | Tekrar Eden |
|------|--------|------------|-----|-------------|
| builder_db | 2 | 2 | 0 | — |
| builder_backend | 1 | 1 | 0 | — |
| builder_frontend | 1 | 1 | 0 | — |
| tester | 1 | 1 | 0 | — |
| validator | 4 | 4 | 1 | YES |
| guardian | 0 | 0 | 0 | — |
| auditor | 0 | 0 | 0 | — |
| sync_master | 0 | 0 | 0 | — |

---

---

## ✅ ÇÖZÜLMÜŞ VAKALAR (Kronolojik)

| # | Vaka | Tarih | Kök Neden | Çözüm |
|---|------|-------|-----------|-------|
| 1 | VAKA-001: Eksik şema (ProgrammingError) | 2026-03-27 | DDL'ler connection.py'ye eklenmemişti | `_create_shadow_tables()` güncellendi |
| 2 | VAKA-002: Yüzeysel tarayıcı testi | 2026-03-28 | Validator E2E test yapmadı | Madde 15 kuralı pekiştirildi |
| 3 | VAKA-003: SQLAlchemy sessiz DDL yutması | 2026-03-28 | `conn.commit()` eksikliği | `eng.begin()` zorunlu kılındı |
| 4 | VAKA-004: GitHub Push + arayüzde görünmeme | 2026-03-27 | Cloud eski kodu çalıştırıyordu | Deploy doğrulama kuralı eklendi |
| 5 | VAKA-005: Gemini Pro kota tükenmesi | 2026-03-28 | Fallback model tanımlı değildi | AGENTS.md'ye fallback sütunu eklendi |
| 6 | P0-1: Günlük Görevler NameError | 2026-03-28 | `text` import eksikliği | Import eklendi |
| 7 | P0-2: Hijyen Dashboard SQLite syntax | 2026-03-28 | `date('now')` → `CURRENT_DATE` | PostgreSQL uyumlu sorgu |
| 8 | P0-3: UI Bleeding (modüller arası sızma) | 2026-03-28 | `app.py` dispatcher hatası | Widget key izolasyonu |
| 9 | P0-4: MAP makine başlatma hatası | 2026-03-28 | Eksik tablo şeması (Zaman, Fire, Bobin) | `connection.py` şema onarımı |
| 10| P1: Ürün parametre akışı | 2026-03-28 | `data_fetcher.py` SELECT limiti | `SELECT *` düzeltmesi |
| 11| VAKA-007: MAP Başlatma Görünmeme | 2026-03-29 | Önbellek (Cache) Stale & Sidebar Reset | v4.0.5 Live-Check + State Sync |
| 12| VAKA-006: Hardcoded Kullanıcı Bypass | 2026-03-29 | Statik kullanıcı adı kontrolü | Bypass kodu silindi, DB yetkiye geçildi |
| 13| VAKA-008: Browser Test Loop (Navigasyon) | 2026-03-29 | Sidebar ve Üst Menü Key Conflict | Çift Yönlü Callback Senkronizasyonu |
| 14| VAKA-009: Duplicate Form Key (st.form) | 2026-03-29 | Ajansal Kör Nokta (Spagetti Form) | Anayasa Madde 23 (Bart Simpson) İlanı |

---

## 🔁 TEKRAR EDEN ÖRÜNTÜLER

- **[ÖRÜNTÜ-01] Yüzeysel Test:** Ajanlar hata kutusu çıkmıyor → "çalışıyor" olarak algılıyor. Fonksiyonel E2E test zorunlu.
- **[ÖRÜNTÜ-02] Şema Eksikliği:** Yeni tablo/kolon eklendiğinde `connection.py` migration listesine de eklenmesi unutuluyor.

---

## ⚠️ DİKKAT NOTLARI (Ajanlara)

1. **builder_db & builder_backend:** Veritabanına yazma işlemlerinde `with eng.begin() as conn:` kullanmak ZORUNLUDUR. `eng.connect()` kullanılırsa Streamlit Cloud sessizce işlemi yutar (VAKA-003).
2. **validator:** "Hata kutusu yok" = "çalışıyor" DEĞİLDİR. E2E simülasyon zorunludur (VAKA-002).
3. **Tüm ajanlar:** Her deploy sonrası Cloud URL yeniden yüklenmeli ve yeni kodun aktif olduğu teyit edilmelidir (VAKA-004).
4. **builder_db:** Yeni tablo/kolon eklerken `database/connection.py` → `_get_migration_list()` ve `_create_*_tables()` fonksiyonları da güncellenmelidir (ÖRÜNTÜ-02).
5. **TÜM AJANLAR (KRİTİK):** Koda yeni bir UI bileşeni veya atama eklendiğinde DOSYANIN TAMAMI yukarıdan aşağıya (Context Sweep) taranmalıdır. Mükerrer form/key bırakmak P0 sebebi sayılır. Bu kural **Anayasa Madde 23 (Bart Simpson Döngüsü)** olarak tescillenmiştir (VAKA-009).

---

## 🔍 SİSTEM HARİTASI KRİTİK BULGULARI

> Tam detay: `sistem_haritasi.md`

- ❌ **8 fonksiyon** 30 satır limitini aşıyor (Anayasa Madde 12)
- ❌ **13 modülden 8'inin** test dosyası yok (Test kapsanması: %38)
- ⚠️ **Flow Engine** (5 tablo) hiçbir UI'ye bağlı değil
- ⚠️ **constants.py** hardcoded pozisyon/vardiya tanımları DB'ye taşınmalı
- ❌ `get_user_roles()`, `render_sync_button()` gibi EMEKLİ fonksiyonlar hala kodda

---

## 📅 HAFTALIK İSTATİSTİKLER

- Açılan vaka: 6
- Çözülen vaka: 5
- Açık kalan: 1 (VAKA-006)
- MANUEL_RED: 4
- Örüntü alarmlı: 2

---

*musbet | EKLERİSTAN QMS Antigravity Pipeline v4.0*
*Bu dosya musbet ajanı tarafından güncellenir.*
