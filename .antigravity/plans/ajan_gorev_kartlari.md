# AJAN GÖREV KARTLARI — Düzeltme Planı v1.0
# .antigravity/plans/ajan_gorev_kartlari.md
# Bu dosya her ajanın görev başında okuması gereken özet karttır.

---

## 🔴 KURAL: Bu kartı oku → Plan dosyasını aç → Başla

**Plan Dosyası:** `.antigravity/plans/duzeltme_plani_v1.md`
**Başlamadan önce:** `hafiza_ozeti.md` + `cozulmus_vakalar.md` oku (Madde 1)
**Bitince:** `musbet`'e devir bildirimi gönder (GP formatında)

---

## auditor — GP-00 (İLK ADIM)

```
SEN NE YAPACAKSIN?
  Kod yazma. Sadece ölç ve raporla.

KOMUTLAR:
  python -m pytest tests/ -v 2>&1 | tail -20
  wc -l app.py logic/auth_logic.py logic/zone_yetki.py database/connection.py
  grep -n "_get_dinamik_modul_anahtari" logic/auth_logic.py
  ls scratch/ | wc -l

ÇIKTI:
  musbet'e GP-00 raporu gönder.

SONRA:
  builder_backend → GP-01 çağır.
```

---

## builder_backend — GP-01 (KRİTİK BUG)

```
SEN NE YAPACAKSIN?
  logic/auth_logic.py içindeki duplikat fonksiyonu kaldır.
  DEBUG print satırlarını temizle.

DOKUNACAĞIN DOSYA: logic/auth_logic.py (tek dosya)

TEST:
  python -m py_compile logic/auth_logic.py && echo "OK"
  python -m pytest tests/test_auth.py -v

COMMIT:
  fix(auth): remove duplicate _get_dinamik_modul_anahtari and debug prints (GP-01)

SONRA:
  tester → GP-02 çağır.
```

---

## tester — GP-02, GP-03, GP-04

```
GP-02: GP-01 doğrulaması (auth_logic.py)
  - grep -c ile 1 def kaldığını doğrula
  - grep ile DEBUG=0 olduğunu doğrula

GP-03: tests/test_map_uretim.py oluştur (plan dosyasında tam içerik var)
  - MAP modülü derleme + global st.* + kritik fonksiyon testleri
  - python -m pytest tests/test_map_uretim.py -v

GP-04: tests/test_vardiya.py oluştur (plan dosyasında tam içerik var)
  - Vardiya derleme + durum geçişleri + maker/checker testleri

COMMIT:
  test(map): add MAP module regression shield tests (GP-03)
  test(vardiya): add Vardiya module regression shield tests (GP-04)
```

---

## builder_db — GP-05 (VERİTABANI)

```
SEN NE YAPACAKSIN?
  FK indeksleri oluştur: map_vardiya + gunluk_gorevler

ÖNCE:
  Supabase'de pg_indexes sorgusunu çalıştır, mevcut indeksleri gör.

SONRA:
  migrations/20260420_fk_indeksleri.sql dosyasını oluştur.
  Supabase SQL Editor'da çalıştır.
  Doğrula: 6 yeni indeks görünmeli.

13. ADAM PROTOKOLÜ:
  "Bu ters giderse ne olur?"
  → İndeks oluşturma veri kaybı yaratmaz.
  → Rollback: DROP INDEX IF EXISTS (plan dosyasında var)

COMMIT:
  perf(db): add FK composite indexes for map_vardiya and gunluk_gorevler (GP-05)
```

---

## builder_backend — GP-06, GP-08, GP-10

```
GP-06: VAKA-027 — Mobil navigasyon audit (app_module_registry.py)
  - DB modül anahtarları ile registry if/elif branch'lerini eşleştir
  - Eksik branch varsa ekle
  - python -m pytest tests/test_app_refactor.py::TestModuleRegistry -v

GP-08: auth_logic.py → session_logic.py bölünmesi
  - 4 fonksiyon taşı: kalici_oturum_*
  - Re-export import koru (geriye uyumluluk)
  - Tüm testler PASS

GP-10: zone_yetki.py Madde 3 uyumu
  - _modul_yetkileri_getir() 2 helper'a böl
  - Anayasa Madde 3: ≤30 satır/fonksiyon
```

---

## validator — GP-07 (MANUEL DOĞRULAMA)

```
SEN NE YAPACAKSIN?
  Anayasa Madde 15: Tarayıcıda manuel test.

ADIMLAR:
  1. streamlit run app.py
  2. OPS, MGT, SYS rollerinde giriş yap
  3. Her navigasyon butonuna tıkla
  4. "Bilinmeyen modül" hatası: → GP-06'ya iade (P0)
  5. Hata yok: → VAKA-027 KAPALI olarak musbet'e kaydet

SONRA:
  builder_backend → GP-08 çağır.
```

---

## sync_master — GP-11 (TEMİZLİK)

```
SEN NE YAPACAKSIN?
  scratch/ dizinini .gitignore'a al.
  Mevcut tracked dosyaları git takibinden çıkar.

KOMUTLAR:
  # .gitignore'a ekle: scratch/
  git rm -r --cached scratch/
  git status scratch/

COMMIT:
  chore: move scratch/ to .gitignore and untrack debug files (GP-11)
```

---

## musbet — GP-12 (KAPATMA)

```
SEN NE YAPACAKSIN?
  Plan tamamlandığını belgele.
  hafiza_ozeti.md güncelle: v6.9.0 (Duzeltme Plani v1.0 Tamamlandi)
  cozulmus_vakalar.md'ye VAKA-027 kapatma kaydı ekle.
  duzeltme_plani_v1.md içinde her GP → ✅ TAMAMLANDI güncelle.
  lessons.md: yeni ders var mı kontrol et.
```

---

## 📐 BAŞARI TABLOSU (Plan Bitmeden Kapatma Yapma)

| GP | Ajan | Tamamlandı mı? |
|----|------|:--------------:|
| GP-00 | auditor | ⬜ |
| GP-01 | builder_backend | ⬜ |
| GP-02 | tester | ⬜ |
| GP-03 | tester | ⬜ |
| GP-04 | tester | ⬜ |
| GP-05 | builder_db | ⬜ |
| GP-06 | builder_backend | ⬜ |
| GP-07 | validator | ⬜ |
| GP-08 | builder_backend | ⬜ |
| GP-09 | tester | ⬜ |
| GP-10 | builder_backend | ⬜ |
| GP-11 | sync_master | ⬜ |
| GP-12 | musbet | ⬜ |

*Bu tabloyu her GP bitiminde güncelle.*

---
*Sistem Mimarı | 2026-04-20*
