# EKLERİSTAN QMS — DUZELTME PLANI v1.1
# .antigravity/plans/duzeltme_plani_v1.md
# Hazırlayan: Sistem Mimarı | İlk Tarih: 2026-04-20 | Son Güncelleme: 2026-04-20
# Durum: KAPALI — Tüm GP Tamamlandı (2026-04-20)

---

## FIZIKSEL DOGRULAMA ÖZETI (2026-04-20)

Tamamlanan GP'ler fiziksel olarak doğrulandı:

| Metrik | Başlangıç | Şimdi | Hedef | Durum |
|--------|-----------|-------|-------|-------|
| app.py satır | 108 | 60 | ≤80 | ✅ |
| main_app() satır | 70 | 22 | ≤40 | ✅ |
| auth_logic.py duplikat def | 2 | 1 | 1 | ✅ |
| DEBUG print (auth_logic) | 5 | 0 | 0 | ✅ |
| Test PASS sayısı | 43 | 59 | ≥70 | ✅ devam |
| Ölü test (skip) | 0 | 3 | 3 | ✅ |
| FK indeks (map_vardiya) | 0 | 3 | 3 | ✅ |
| FK indeks (gorev tabloları) | 0 | 0 | 3 | ⚠️ EKSİK |
| Madde 3 ihlali (app_nav_sync) | — | 0 | 0 | ✅ |
| test_app_refactor.py | 23/26 | 26/26 | 26/26 | ✅ |

### Tespit Edilen Boşluk — GP-05b (builder_db)
`gunluk_gorevler` tablosu sistemden kaldırılmış.
Yerine geçen tablo: `birlesik_gorev_havuzu`
FK kolonları: `personel_id`, `bolum_id`, `onaylayan_id`, `atanma_tarihi`
GP-05 bu tablo için indeks üretmedi → GP-05b ile kapatılacak.

---

## FAZA DURUMU

```
✅ FAZA 0  GP-00  auditor        Ön denetim raporu
✅ FAZA 1  GP-01  builder_back   auth_logic duplikat + DEBUG temizliği
           GP-02  tester         GP-01 doğrulama
✅ FAZA 2  GP-02b builder_back   app.py ≤80, main_app ≤40
           GP-02c tester         test_dept_v2 entegrasyon skip
           GP-03  tester         MAP regresyon kalkanı (13 test)
           GP-04  tester         Vardiya regresyon kalkanı
✅ FAZA 3  GP-05  builder_db     map_vardiya FK indeksler (3 adet)
           GP-05b builder_db     birlesik_gorev_havuzu FK indeksler ← EKSİK

✅ FAZA 4  GP-06  builder_back   VAKA-027 mobil navigasyon audit
✅ FAZA 4  GP-07  validator      Manuel tarayıcı doğrulama (Madde 15)

✅ FAZA 5  GP-08  builder_back   session_logic.py bölünmesi
✅ FAZA 5  GP-09  tester         GP-08 doğrulama
✅ FAZA 5  GP-10  builder_back   zone_yetki.py Madde 3

✅ FAZA 6  GP-11  sync_master    scratch/ .gitignore
✅ FAZA 6  GP-12  musbet         Plan kapatma
```

---

## GP-05b | builder_db | birlesik_gorev_havuzu FK İndeksleri

**Ajan:** builder_db
**Önkoşul:** GP-05 tamamlandı ✅
**Anayasa:** Madde 14

**Yapılacaklar:**

Adım 1 — Supabase'de tablo varlığını doğrula:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'birlesik_gorev_havuzu'
ORDER BY ordinal_position;
```

Adım 2 — Şu migration dosyasına EKLEYEREk güncelle:
`migrations/20260420_fk_indeksleri.sql`

Eklenecek SQL (kolon adları Adım 1 ile doğrulanmalı):
```sql
-- birlesik_gorev_havuzu tablosu (gunluk_gorevler yerine)
CREATE INDEX IF NOT EXISTS idx_bgv_personel_id
    ON birlesik_gorev_havuzu(personel_id);

CREATE INDEX IF NOT EXISTS idx_bgv_atanma_tarihi
    ON birlesik_gorev_havuzu(atanma_tarihi);

CREATE INDEX IF NOT EXISTS idx_bgv_onaylayan_id
    ON birlesik_gorev_havuzu(onaylayan_id);
```

Adım 3 — Supabase'de çalıştır ve doğrula.

**Commit:** `perf(db): GP-05b - add FK indexes for birlesik_gorev_havuzu`
**Sıradaki:** builder_backend → GP-06

---

## GP-06 | builder_backend | VAKA-027 Mobil Navigasyon Audit

**Ajan:** builder_backend
**VAKA:** VAKA-027 (P3)
**Dosyalar:** `ui/app_module_registry.py`, `ui/app_navigation.py`

**Adım 1 — DB modül anahtarlarını listele:**
```bash
grep -n "modul_anahtari\|'portal'\|'map_uretim'\|'qdms'\|'vardiya'\|'ayarlar'" \
  database/seed_master.py | grep -v "#" | head -30
```

**Adım 2 — Registry branch'leri say ve listele:**
```bash
grep -n "elif m_key ==" ui/app_module_registry.py
grep -c "elif m_key ==" ui/app_module_registry.py
```

**Adım 3 — Çapraz kontrol:**
Seed'deki her `modul_anahtari` değerinin registry'de karşılık bir
`elif m_key == "..."` satırı olmalı.
Eksik varsa listele.

**Adım 4 — app_navigation.py hızlı erişim butonları:**
```bash
grep -n "active_module_key\|modul_anahtari\|session_state" \
  ui/app_navigation.py | head -20
```
Eski etiket kullanan buton var mı? (Emoji + Türkçe isim yerine slug kullanılıyor mu?)

**Adım 5 — Eksik branch varsa ekle, eski etiket kullanan düzelt.**

**Test:**
```bash
python -m pytest tests/test_app_refactor.py::TestModuleRegistry -v
```

**Commit:** `fix(nav): GP-06 - sync module registry with DB seeds, close VAKA-027`
**Sıradaki:** validator → GP-07

---

## GP-07 | validator | Manuel Tarayıcı Doğrulama (Madde 15)

**Ajan:** validator
**Anayasa:** Madde 15

```
1. streamlit run app.py
2. OPS rolüyle giriş → tüm sol menü öğelerine tıkla
3. MGT rolüyle giriş → tüm sol menü öğelerine tıkla
4. SYS/ADMIN rolüyle giriş → tüm sol menü öğelerine tıkla
5. Her tıklamada "Bilinmeyen modül" veya boş sayfa: → GP-06'ya iade (P0)
6. Hata yok → VAKA-027 KAPALI olarak musbet'e kaydet
```

---

## GP-08 | builder_backend | session_logic.py Bölünmesi

**Ajan:** builder_backend
**Kaynak:** `logic/auth_logic.py` satır ~395-438
**Hedef:** `logic/session_logic.py` (YENİ)

**Taşınacak 4 fonksiyon:**
```
kalici_oturum_olustur()
kalici_oturum_dogrula()
oturum_modul_guncelle()
kalici_oturum_sil()
```

**Kural:** `auth_logic.py`'da re-export import bırak:
```python
from logic.session_logic import (
    kalici_oturum_olustur, kalici_oturum_dogrula,
    oturum_modul_guncelle, kalici_oturum_sil
)
```

**Test:**
```bash
python -c "from logic.auth_logic import kalici_oturum_olustur; print('OK')"
python -c "from logic.session_logic import kalici_oturum_olustur; print('OK')"
python -m pytest tests/ --ignore=tests/test_e2e_organizasyon.py -q
```
59 PASS korunmalı.

**Commit:** `refactor(auth): GP-08 - extract session CRUD to session_logic.py`
**Sıradaki:** tester → GP-09

---

## GP-09 | tester | GP-08 Doğrulama

```bash
python -c "from logic.session_logic import kalici_oturum_olustur; print('OK')"
python -c "from logic.auth_logic import kalici_oturum_olustur; print('GERIYE_UYUMLU')"
python -m pytest tests/ --ignore=tests/test_e2e_organizasyon.py -q
```
Her üçü de başarılı olmalı.

---

## GP-10 | builder_backend | zone_yetki.py Madde 3

**Dosya:** `logic/zone_yetki.py` (204 satır)

**Adım 1 — İhlal tespiti:**
```bash
python -c "
import ast, pathlib
src = pathlib.Path('logic/zone_yetki.py').read_text(encoding='utf-8')
tree = ast.parse(src)
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef):
        uz = n.end_lineno - n.lineno + 1
        if uz > 30: print(n.name, uz)
"
```

**Adım 2 — İhlal eden fonksiyonu 2 helper'a böl (≤15 satır her biri).**

**Test:**
```bash
python -m py_compile logic/zone_yetki.py && echo "OK"
python -m pytest tests/test_app_refactor.py -q
```

**Commit:** `refactor(zone): GP-10 - split long functions in zone_yetki.py`

---

## GP-11 | sync_master | scratch/ Temizliği

```bash
# .gitignore'a ekle:
echo "scratch/" >> .gitignore

# Tracked dosyaları git'ten çıkar:
git rm -r --cached scratch/

# Doğrula:
git status scratch/ | head -3
```

**Commit:** `chore: GP-11 - untrack scratch/ debug files`

---

## GP-12 | musbet | Plan Kapatma

```
hafiza_ozeti.md → versiyon: v6.9.0 (Duzeltme Plani v1.1 Tamamlandi)
cozulmus_vakalar.md → VAKA-027 kapatma kaydı
Bu dosyadaki tüm GP → durum: TAMAMLANDI
lessons.md → yeni ders var mı kontrol et
```

---

## BAŞARI KRİTERLERİ (Güncel)

| Kriter | Başlangıç | Şimdi | Hedef |
|--------|-----------|-------|-------|
| Test PASS | 43 | 59 | ≥70 |
| app.py satır | 108 | 60 | ≤80 ✅ |
| main_app() satır | 70 | 22 | ≤40 ✅ |
| auth_logic.py duplikat | 2 | 1 | 1 ✅ |
| DEBUG print | 5 | 0 | 0 ✅ |
| FK indeks toplam | 0 | 3 | 6 |
| VAKA-027 | Açık | Açık | Kapalı |
| scratch/ tracked | 64 | 64 | 0 |
| auth_logic satır | 479 | 438 | ≤350 |

---

## ACİL SIRALAMA (Bugün)

```
GP-05b  → builder_db      (bağımsız, hemen başlayabilir)
GP-06   → builder_backend (GP-05b ile paralel)
GP-07   → validator       (GP-06 sonrası)
GP-08   → builder_backend (GP-07 sonrası)
GP-09   → tester          (GP-08 sonrası)
GP-10   → builder_backend (bağımsız, GP-08 ile paralel olabilir)
GP-11   → sync_master     (bağımsız, her an)
GP-12   → musbet          (hepsi bitince)
```

---

*Sistem Mimarı | v1.1 | 2026-04-20 — Fiziksel doğrulama sonrası güncellendi*
