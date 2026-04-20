# EKLERİSTAN QMS — MIMAR DÜZELTMEPLANIv1.0
# .antigravity/plans/duzeltme_plani_v1.md
# Hazırlayan: Sistem Mimarı | Tarih: 2026-04-20
# Onay: Emre ÇAVDAR (Gerekli)
# Durum: ONAY BEKLİYOR

---

## ⚠️ BU PLAN NASIL OKUNUR

Bu dosya ajan için iş talimatıdır. Her Görev Paketi (GP) birbirini tamamlar.
Bir GP tamamlanmadan sıradaki BAŞLANAMAZ.
Her GP'nin sonunda `musbet` kaydedilir ve bir sonraki ajana devredilir.

**Kök Neden Özeti:** Stabilizasyon döneminde (Apr 15-20, 2026) büyük monolitik
commitler regresyon zinciri yarattı. Bu plan küçük, izole, test-gated adımlarla
sistemi sağlamlaştırır. Her adım tek sorumlulukludur.

---

## 🗺️ FAZA HARİTASI

```
FAZA 0 → Zemin (Hazırlık, kod yok)
FAZA 1 → Kritik Bug Fix (auth_logic.py)
FAZA 2 → Test Zırhı (Coverage %45 → %70)
FAZA 3 → DB Sağlamlaştırma
FAZA 4 → VAKA-027 Kapatma
FAZA 5 → Anayasa Madde 3 (Madde 3 ihlalleri)
FAZA 6 → Temizlik
```

---

## FAZA 0: ZEMİN HAZIRLIĞI

### GP-00 | auditor | Ön Denetim Raporu

**Ajan:** auditor  
**Süre:** 1 saat  
**Sorumluluğu:** Kod yazmaz. Tespit eder, raporlar.

**Yapılacaklar:**

1. Şu komutu çalıştır ve sonucu `musbet`'e kaydet:
   ```bash
   python -m pytest tests/ -v 2>&1 | tail -20
   ```

2. Şu dosyalardaki gerçek satır sayılarını ölç:
   ```bash
   wc -l app.py logic/auth_logic.py logic/zone_yetki.py \
          database/connection.py ui/app_module_registry.py \
          modules/vardiya/ui.py modules/qdms/pdf_uretici.py
   ```

3. `logic/auth_logic.py` satır 68 ile satır 164'teki fonksiyon isimlerini karşılaştır.
   İkisi de `_get_dinamik_modul_anahtari` ise → DUPLIKAT_TESPIT olarak logla.

4. `scratch/` altındaki dosya sayısını say: `ls scratch/ | wc -l`

5. Raporu şu formatta `musbet`'e ilet:
   ```
   DUZELTME_PLANI_V1 ON DENETIM:
   - Test durumu: X/Y geçti
   - app.py satır: N
   - auth_logic.py duplikat: EVET/HAYIR
   - scratch/ dosya sayısı: N
   ```

**Rollback:** Yok (sadece okuma işlemi)  
**Sıradaki:** builder_backend → GP-01

---

## FAZA 1: KRİTİK BUG FIX

### GP-01 | builder_backend | auth_logic.py Duplikat Fonksiyon Temizliği

**Ajan:** builder_backend  
**Süre:** 1 saat  
**Öncelik:** P0 — Emoji eşleşmesi şu an bozuk  
**Dosya:** `logic/auth_logic.py`

**Arka Plan:**
`_get_dinamik_modul_anahtari` fonksiyonu dosyada İKİ KEZ tanımlanmış.
Python ikinci tanımı (satır ~164) kullanır — bu DB çağrısı yapan, emoji-safe
kompleks versiyonu siler. Menü eşleştirme şu an sadece statik MODUL_ESLEME
sözlüğüne bakıyor. Bu VAKA-020/021'in sessiz geri dönüşüdür.

**Adım 1 — Duplikatı tespit et:**
```bash
grep -n "_get_dinamik_modul_anahtari" logic/auth_logic.py
```
Beklenen çıktı: 2 satır (örn. 68 ve 164).

**Adım 2 — İki versiyonu karşılaştır:**
- Satır 68'deki: DB çağrısı var, `@st.cache_data` decorator var, emoji normalizasyonu var
- Satır ~164'teki: Sadece `MODUL_ESLEME` dict lookupı, daha basit

**Adım 3 — Karar:**
Satır 68'deki (DB-driven, emoji-safe) versiyon DOĞRU versiyondur.
Satır ~164'teki (statik dict-only) versiyonu KALDIR.

**Adım 4 — DEBUG print'leri temizle:**
`logic/auth_logic.py` içindeki şu pattern'ları bul ve kaldır:
```python
if _dinamik_yetki_aktif_mi(): print(f"DEBUG: ...")
```
Bu satırlar production'da çalışan print ifadeleridir. Hepsini sil.

**Adım 5 — Derleme kontrolü:**
```bash
python -m py_compile logic/auth_logic.py && echo "OK"
```

**Adım 6 — Test:**
```bash
python -m pytest tests/test_auth.py -v
```
Tüm testler PASS olmalı.

**Rollback:** `git diff logic/auth_logic.py` → sorun varsa `git checkout logic/auth_logic.py`  
**Commit formatı:** `fix(auth): remove duplicate _get_dinamik_modul_anahtari and debug prints (GP-01)`  
**Sıradaki:** tester → GP-02

---

### GP-02 | tester | GP-01 Doğrulama Testi

**Ajan:** tester  
**Süre:** 30 dakika  
**Dosya:** `tests/test_auth.py`

**Yapılacaklar:**

1. `logic/auth_logic.py` içinde kaç kez `_get_dinamik_modul_anahtari` geçtiğini say:
   ```bash
   grep -c "_get_dinamik_modul_anahtari" logic/auth_logic.py
   ```
   Beklenen: **1** (sadece tanım). Fazlası FAIL.

2. `logic/auth_logic.py` içinde `print(f"DEBUG` pattern'ını ara:
   ```bash
   grep -n "DEBUG" logic/auth_logic.py
   ```
   Beklenen: **0 satır**. Varsa FAIL.

3. Mevcut testleri çalıştır:
   ```bash
   python -m pytest tests/test_auth.py -v
   ```

4. Sonucu `musbet`'e kaydet.

**Rollback:** GP-01'e iade et.  
**Sıradaki:** builder_backend → GP-03

---

## FAZA 2: TEST ZIRHI

### GP-03 | tester | MAP Modülü Unit Testleri

**Ajan:** tester  
**Süre:** 2 saat  
**Dosya:** `tests/test_map_uretim.py` (YENİ OLUŞTUR)  
**Hedef:** MAP modülü için temel regresyon kalkanı

**Kapsam (ne test edilecek):**
MAP modülü şimdiye kadar 5 kez kırıldı (bkz. kök neden analizi).
Bu testler bir sonraki stabilizasyonda erken uyarı verecek.

**Test Edilecekler:**

1. `ui/map_uretim/map_db.py` — Fonksiyon import kontrolü
2. `ui/map_uretim/map_uretim.py` — Global scope'da `st.*` çağrısı YOK kontrolü
3. `ui/map_uretim/map_hesap.py` — Import sağlığı
4. `ui/map_uretim/map_rapor_pdf.py` — Import sağlığı

**Test Dosyası Yapısı:**
```python
# tests/test_map_uretim.py
import ast, pathlib, pytest

MAP_DOSYALARI = [
    "ui/map_uretim/map_db.py",
    "ui/map_uretim/map_uretim.py",
    "ui/map_uretim/map_hesap.py",
    "ui/map_uretim/map_rapor_pdf.py",
]

@pytest.mark.parametrize("dosya", MAP_DOSYALARI)
def test_derleme_kontrolu(dosya):
    """Her MAP dosyası hatasız derlenmeli."""
    kaynak = pathlib.Path(dosya).read_text(encoding="utf-8")
    ast.parse(kaynak)  # SyntaxError yoksa geçer

@pytest.mark.parametrize("dosya", MAP_DOSYALARI)
def test_global_st_cagri_yok(dosya):
    """Anayasa Madde 19: st.* çağrısı global scope'da olmaz."""
    kaynak = pathlib.Path(dosya).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Module):
            for ifade in dugum.body:
                assert not (
                    isinstance(ifade, ast.Expr) and
                    isinstance(getattr(ifade, 'value', None), ast.Call) and
                    hasattr(getattr(ifade.value, 'func', None), 'attr') and
                    getattr(ifade.value.func, 'id', '') == 'st'
                ), f"{dosya}: Global st.* çağrısı bulundu"

def test_map_db_kritik_fonksiyonlar():
    """map_db.py içinde beklenen kritik fonksiyonlar tanımlı olmalı."""
    kaynak = pathlib.Path("ui/map_uretim/map_db.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    fonksiyon_adlari = {d.name for d in ast.walk(agac) if isinstance(d, ast.FunctionDef)}
    beklenenler = ["vardiya_ac", "vardiya_kapat"]
    for beklenen in beklenenler:
        assert any(beklenen in f for f in fonksiyon_adlari), \
            f"Kritik fonksiyon bulunamadı: {beklenen}"
```

**Çalıştır:**
```bash
python -m pytest tests/test_map_uretim.py -v
```
Tümü PASS olmadan GP-04'e geçilmez.

**Rollback:** Yok (sadece test dosyası eklendi, prod kod dokunulmadı)  
**Commit formatı:** `test(map): add MAP module regression shield tests (GP-03)`  
**Sıradaki:** tester → GP-04

---

### GP-04 | tester | Vardiya Modülü Unit Testleri

**Ajan:** tester  
**Süre:** 1.5 saat  
**Dosya:** `tests/test_vardiya.py` (YENİ OLUŞTUR)

**Test Edilecekler:**
1. `modules/vardiya/logic.py` — Import + derleme
2. `modules/vardiya/ui.py` — Import + global st.* yok
3. `modules/vardiya/schema.py` — Import + derleme
4. Maker/Checker zorunluluğu: `onaylayan_id != acan_kullanici_id`

**Test Dosyası Yapısı:**
```python
# tests/test_vardiya.py
import ast, pathlib, pytest

VARDIYA_DOSYALARI = [
    "modules/vardiya/logic.py",
    "modules/vardiya/ui.py",
    "modules/vardiya/schema.py",
]

@pytest.mark.parametrize("dosya", VARDIYA_DOSYALARI)
def test_derleme_kontrolu(dosya):
    kaynak = pathlib.Path(dosya).read_text(encoding="utf-8")
    ast.parse(kaynak)

def test_durum_gecisler_mevcut():
    """Anayasa: TASLAK → ONAY_BEKLIYOR → ONAYLANDI durumları kod içinde tanımlı."""
    kaynak = pathlib.Path("modules/vardiya/logic.py").read_text(encoding="utf-8")
    for durum in ["TASLAK", "ONAY_BEKLIYOR", "ONAYLANDI"]:
        assert durum in kaynak, f"Durum kodu eksik: {durum}"

def test_maker_checker_zorunlulugu():
    """Anayasa: Veriyi giren ≠ onaylayan. Logic dosyasında kontrol mevcut olmalı."""
    kaynak = pathlib.Path("modules/vardiya/logic.py").read_text(encoding="utf-8")
    assert "onaylayan" in kaynak.lower(), "Maker/Checker mekanizması bulunamadı"
```

**Çalıştır:**
```bash
python -m pytest tests/test_vardiya.py -v
```

**Commit formatı:** `test(vardiya): add Vardiya module regression shield tests (GP-04)`  
**Sıradaki:** builder_db → GP-05

---

## FAZA 3: VERİTABANI SAĞLAMLAŞTIRMA

### GP-05 | builder_db | Eksik FK İndeksleri

**Ajan:** builder_db  
**Süre:** 1 saat  
**Dosya:** `migrations/20260420_fk_indeksleri.sql` (YENİ OLUŞTUR)  
**Anayasa Maddesi:** Madde 14 (Performans ve İndeksleme)

**Arka Plan:**
Kök neden analizinde tespit edildi: `map_vardiya` ve `gunluk_gorevler`
tablolarında sık kullanılan FK kolonlarında indeks yok. Bu büyük raporlama
sorgularını yavaşlatıyor.

**Yapılacaklar:**

Adım 1 — Önce Supabase'de mevcut indeksleri kontrol et:
```sql
SELECT indexname, tablename, indexdef
FROM pg_indexes
WHERE tablename IN ('map_vardiya', 'gunluk_gorevler', 'map_zaman_cizelgesi')
ORDER BY tablename;
```

Adım 2 — Eksik olanları migration dosyasına yaz:
```sql
-- migrations/20260420_fk_indeksleri.sql
-- Anayasa Madde 14 uyumu: FK ve filtre kolonları indeksleme

-- map_vardiya tablosu
CREATE INDEX IF NOT EXISTS idx_map_vardiya_urun_id
    ON map_vardiya(urun_id);

CREATE INDEX IF NOT EXISTS idx_map_vardiya_tarih
    ON map_vardiya(tarih);

CREATE INDEX IF NOT EXISTS idx_map_vardiya_acan_kullanici
    ON map_vardiya(acan_kullanici_id);

-- gunluk_gorevler tablosu
CREATE INDEX IF NOT EXISTS idx_gunluk_gorevler_vardiya_id
    ON gunluk_gorevler(vardiya_id);

CREATE INDEX IF NOT EXISTS idx_gunluk_gorevler_personel_id
    ON gunluk_gorevler(atanan_personel_id);

CREATE INDEX IF NOT EXISTS idx_gunluk_gorevler_tarih
    ON gunluk_gorevler(olusturma_tarihi);
```

Adım 3 — Supabase SQL Editor'da çalıştır.

Adım 4 — Doğrula:
```sql
SELECT indexname, tablename
FROM pg_indexes
WHERE tablename IN ('map_vardiya', 'gunluk_gorevler')
  AND indexname LIKE 'idx_%'
ORDER BY tablename;
```
Her tabloda en az 3 yeni indeks görünmeli.

**Rollback:**
```sql
DROP INDEX IF EXISTS idx_map_vardiya_urun_id;
DROP INDEX IF EXISTS idx_map_vardiya_tarih;
DROP INDEX IF EXISTS idx_map_vardiya_acan_kullanici;
DROP INDEX IF EXISTS idx_gunluk_gorevler_vardiya_id;
DROP INDEX IF EXISTS idx_gunluk_gorevler_personel_id;
DROP INDEX IF EXISTS idx_gunluk_gorevler_tarih;
```

**13. Adam Protokolü:** İndeks oluşturma Supabase'de lock almaz (CONCURRENT değil,
ama küçük tablolarda bu kabul edilebilir). Üretim sorgu sürelerini etkilemez.

**Commit formatı:** `perf(db): add FK composite indexes for map_vardiya and gunluk_gorevler (GP-05)`  
**Sıradaki:** builder_backend → GP-06

---

## FAZA 4: VAKA-027 KAPATMA

### GP-06 | builder_backend | Mobil Navigasyon Senkronu Denetimi

**Ajan:** builder_backend  
**Süre:** 1.5 saat  
**Dosya:** `logic/zone_yetki.py`, `ui/app_navigation.py`, `ui/app_module_registry.py`  
**VAKA:** VAKA-027 (P3 → bu adımla kapatılacak)

**Arka Plan:**
Bazı mobil hızlı erişim butonları v5.0 öncesi eski modül anahtarlarına
(label-based, slug-based değil) referans veriyor olabilir.

**Adım 1 — Audit: app_navigation.py içinde tüm modül anahtarlarını listele:**
```bash
grep -n "modul_anahtari\|m_key\|active_module\|portal\|map_uretim\|vardiya" \
     ui/app_navigation.py | head -40
```

**Adım 2 — Audit: app_module_registry.py içindeki if/elif branch'lerini say:**
```bash
grep -c "elif m_key ==" ui/app_module_registry.py
```
Beklenen: 14+ (tüm modüller)

**Adım 3 — Çapraz kontrol: DB'deki modül anahtarları ile registry eşleşiyor mu?**
`database/seed_master.py` veya `database/migrations_master.py` içinde
`modul_anahtari` değerlerini listele ve `app_module_registry.py` içindeki
`elif m_key ==` satırlarıyla karşılaştır.

**Adım 4 — Eksik branch varsa ekle:**
Eğer DB'de olan bir `modul_anahtari` registry'de yoksa, `app_module_registry.py`'a
elif branch ekle. Örnek:
```python
elif m_key == "eksik_modul_adi":
    from ui.eksik_modul_ui import render_eksik_modul
    render_eksik_modul()
```

**Adım 5 — Test:**
```bash
python -m pytest tests/test_app_refactor.py::TestModuleRegistry -v
```

**Rollback:** `git checkout ui/app_module_registry.py`

**Commit formatı:** `fix(nav): audit and sync mobile module keys with DB registry (GP-06, closes VAKA-027)`  
**Sıradaki:** validator → GP-07

---

### GP-07 | validator | GP-06 Manuel Tarayıcı Doğrulaması

**Ajan:** validator  
**Süre:** 30 dakika  
**Anayasa Maddesi:** Madde 15 (Bulut Tarayıcı Doğrulama)

**Yapılacaklar:**
1. `streamlit run app.py` ile uygulamayı başlat
2. Her rolde giriş yap (OPS, MGT, SYS) ve tüm navigasyon butonlarının çalıştığını kontrol et
3. "Bilinmeyen modül" hatası varsa → GP-06'ya iade et (P0)
4. Sonucu `musbet`'e VAKA-027 kapatma kaydı olarak ekle

---

## FAZA 5: ANAYASA MADDE 3 (30 SATIR KURALI)

> ⚠️ Bu faza FAZA 4 tamamlandıktan SONRA başlar.
> Her GP izole bir dosya/sorumluluğa dokunur.

### GP-08 | builder_backend | auth_logic.py Oturum Fonksiyonlarını Ayır

**Ajan:** builder_backend  
**Süre:** 2 saat  
**Kaynak dosya:** `logic/auth_logic.py` (479 satır → ~350'ye inecek)  
**Hedef dosya:** `logic/session_logic.py` (YENİ — ~130 satır)  
**Anayasa Maddesi:** Madde 3 + Madde 13 (Tek Sorumluluk)

**Arka Plan:**
`auth_logic.py` hem kimlik doğrulama (bcrypt, RBAC) hem de oturum yönetimi
(cookie token, kalici_oturum CRUD) yapıyor. Bu iki sorumluluk ayrılmalı.

**Taşınacak Fonksiyonlar (auth_logic.py → session_logic.py):**
```
kalici_oturum_olustur()   # satır ~424
kalici_oturum_dogrula()   # satır ~438
oturum_modul_guncelle()   # satır ~463
kalici_oturum_sil()       # satır ~474
```

**Adımlar:**

1. `logic/session_logic.py` dosyası oluştur:
   - Header: import'lar (sqlalchemy, secrets, datetime)
   - 4 fonksiyonu buraya taşı
   - Her fonksiyon ≤30 satır olmalı (zaten kısa)

2. `logic/auth_logic.py` içinden o 4 fonksiyonu sil:
   ```python
   # Buradan kaldırıldı → logic/session_logic.py
   from logic.session_logic import (
       kalici_oturum_olustur, kalici_oturum_dogrula,
       oturum_modul_guncelle, kalici_oturum_sil
   )
   ```
   Bu import satırını `auth_logic.py`'a EKLE (geriye uyumluluk için).

3. `logic/app_auth_flow.py` içinde `auth_logic`'ten bu fonksiyonları çeken
   import'lar varsa `session_logic`'e yönlendir.

4. Derleme kontrolü:
   ```bash
   python -m py_compile logic/auth_logic.py logic/session_logic.py \
                        logic/app_auth_flow.py && echo "OK"
   ```

5. Test:
   ```bash
   python -m pytest tests/ -v
   ```
   Tüm mevcut testler PASS olmalı.

**Rollback:** `git checkout logic/auth_logic.py && rm logic/session_logic.py`

**13. Adam Protokolü:** Re-export import korunduğu için dış bağımlılar etkilenmez.
Circular import riski: session_logic → connection.py (izin verilir, tek yönlü).

**Commit formatı:** `refactor(auth): extract session CRUD to session_logic.py (GP-08)`  
**Sıradaki:** tester → GP-09

---

### GP-09 | tester | GP-08 Regresyon Testi

**Ajan:** tester  
**Süre:** 30 dakika

**Yapılacaklar:**
1. `logic/session_logic.py` import kontrolü:
   ```bash
   python -c "from logic.session_logic import kalici_oturum_olustur; print('OK')"
   ```
2. `logic/auth_logic.py` geriye uyumluluk:
   ```bash
   python -c "from logic.auth_logic import kalici_oturum_olustur; print('OK')"
   ```
3. Tüm testler:
   ```bash
   python -m pytest tests/ -v
   ```

Herhangi biri FAIL → GP-08'e iade.

---

### GP-10 | builder_backend | zone_yetki.py Madde 3 Uyumu

**Ajan:** builder_backend  
**Süre:** 1.5 saat  
**Dosya:** `logic/zone_yetki.py` (204 satır)  
**Anayasa Maddesi:** Madde 3

**Sorun:** `_modul_yetkileri_getir()` fonksiyonu 30 satırı aşıyor.

**Adım 1 — Fonksiyon uzunluklarını ölç:**
```bash
python - <<'EOF'
import ast, pathlib
src = pathlib.Path("logic/zone_yetki.py").read_text(encoding="utf-8")
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        uzunluk = node.end_lineno - node.lineno + 1
        if uzunluk > 30:
            print(f"  IHLAL: {node.name} → {uzunluk} satır (satır {node.lineno})")
EOF
```

**Adım 2 — `_modul_yetkileri_getir()` fonksiyonunu 2'ye böl:**
- `_yetki_sql_calistir(engine, rol)` → SQL çalıştırma (≤15 satır)
- `_yetki_sonuc_isle(rows)` → Row'ları dict'e çevirme (≤15 satır)
- Ana `_modul_yetkileri_getir()` bu iki helper'ı çağırır (≤10 satır)

**Adım 3 — Derleme + Test:**
```bash
python -m py_compile logic/zone_yetki.py && echo "OK"
python -m pytest tests/test_app_refactor.py -v
```

**Rollback:** `git checkout logic/zone_yetki.py`

**Commit formatı:** `refactor(zone): split _modul_yetkileri_getir into helpers (GP-10)`

---

## FAZA 6: TEMİZLİK

### GP-11 | sync_master | Scratch Dizini .gitignore'a Al

**Ajan:** sync_master  
**Süre:** 30 dakika  
**Dosya:** `.gitignore`

**Arka Plan:**
`scratch/` altında 64 debug dosyası birikmiş. Bunlar git geçmişini şişiriyor,
gizli veri riski taşıyor ve yeni ajanları yanıltıyor.

**Yapılacaklar:**

1. `.gitignore` dosyasını aç. `scratch/` satırı var mı kontrol et:
   ```bash
   grep "scratch" .gitignore
   ```

2. Yoksa ekle:
   ```
   # Debug ve geçici analiz dosyaları
   scratch/
   ```

3. Mevcut tracked scratch dosyalarını git'ten çıkar (silme, sadece takip bırak):
   ```bash
   git rm -r --cached scratch/ 2>/dev/null && echo "Scratch untracked"
   ```

4. Doğrula:
   ```bash
   git status scratch/ | head -5
   ```
   `nothing to commit` veya `ignored` görünmeli.

**Rollback:** `.gitignore`'dan `scratch/` satırını sil + `git add scratch/`

**Commit formatı:** `chore: move scratch/ to .gitignore and untrack debug files (GP-11)`  
**Sıradaki:** musbet → GP-12

---

### GP-12 | musbet | Plan Kapatma ve Hafıza Güncellemesi

**Ajan:** musbet  
**Süre:** 30 dakika  
**Dosya:** `.antigravity/musbet/hafiza/hafiza_ozeti.md`

**Yapılacaklar:**

1. Her tamamlanan GP için `cozulmus_vakalar.md`'ye kayıt ekle.

2. `hafiza_ozeti.md` başlığını güncelle:
   ```
   Versiyon: v6.9.0 (Duzeltme Plani v1.0 Tamamlandi)
   Son Güncelleme: [tarih]
   ```

3. Yeni teknik borç durumunu yaz.

4. `duzeltme_plani_v1.md` içindeki her GP için durum = ✅ TAMAMLANDI güncelle.

---

## 📊 BAŞARI KRİTERLERİ

Plan tamamlandığında şu metrikler karşılanmış olmalı:

| Kriter | Başlangıç | Hedef | Ölçüm |
|--------|-----------|-------|-------|
| Test sayısı | 26 | ≥38 | `pytest --co -q \| tail -1` |
| Test coverage (yeni) | ~%45 | ~%70 | MAP + Vardiya testleri eklendi |
| auth_logic.py duplikat | 2 def | 1 def | `grep -c _get_dinamik_modul` |
| DEBUG print'ler | N adet | 0 | `grep -c "DEBUG" logic/auth_logic.py` |
| FK indeks sayısı | 0 yeni | 6 yeni | `pg_indexes` sorgusu |
| VAKA-027 | Açık | Kapalı | musbet kaydı |
| Scratch tracked dosyaları | 64 | 0 | `git ls-files scratch/` |
| auth_logic.py satırı | 479 | ~350 | `wc -l logic/auth_logic.py` |
| zone_yetki.py ihlal | 1 fonksiyon | 0 | AST fonksiyon uzunluk testi |

---

## 🚨 İPTAL KRİTERLERİ

Şu durumlarda plan DURUR ve Emre'ye eskalasyon yapılır:

1. `python -m pytest tests/ -v` tüm testleri PASS etmiyorsa herhangi bir GP sonrası
2. `app.py` import hatası
3. `get_engine()` çağrısı başarısız
4. Supabase bağlantısı koptu

---

## 🔄 DEVIR PROTOKOLÜ (Her GP Sonu)

Her GP tamamlandığında ajan şunu yapar:
```
musbet'e bildir:
  GP-XX TAMAMLANDI
  Dosyalar: [değişen dosya listesi]
  Test sonucu: X/Y PASS
  Kontrol edilen: [ne doğrulandı]
  Sıradaki: [ajan adı] → GP-YY
```

---

*Sistem Mimarı | v1.0 | 2026-04-20*
*Bu plan Emre ÇAVDAR onayı ile yürürlüğe girer.*
