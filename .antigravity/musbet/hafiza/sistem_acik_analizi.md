---
name: sistem_acik_analizi
description: Sistem çapında benzer açıkların detaylı analizi (v7.0.2 sonrası)
type: project
tarih: 2026-04-20
---

# 🔍 SİSTEM ÇAPINDA AÇIK ANALIZI — BENZER SORUNLAR

**Sonuç:** Personel modülünde bulunan senkronizasyon açığı (MADDE 2.1 ve MADDE 31) **9+ modülde benzer şekilde var**.

---

## 📊 AÇIK TESPITI: ÖZET

| # | Modül | Açık Tipi | Durum | Öncelik |
|---|-------|-----------|-------|---------|
| 1 | **PERSONEL** | Field sync + Audit Trail | **ÇÖZÜLDÜ** (v7.0.2) | P0 ✅ |
| 2 | **VARDIYA** | Status change audit yok | AÇIK | P1 |
| 3 | **GÜNLÜK GÖREV** | Assignment audit yok | AÇIK | P1 |
| 4 | **MAP ÜRETİM** | Fire/Bobin history yok | AÇIK | P2 |
| 5 | **QDMS** | Revizyon field-level değil | AÇIK | P2 |
| 6 | **KPI/KALITE** | Data entry audit yok | AÇIK | P2 |
| 7 | **GMP/HİJYEN** | Control audit yok | AÇIK | P2 |
| 8 | **PERFORMANS** | Rating change audit yok | AÇIK | P3 |
| 9 | **SISTEM_LOGLARI** | Generic, field-level değil | AÇIK | P3 |

---

## 1. VARDIYA YÖNETİMİ (Shift Management)

**Dosya:** `modules/vardiya/` (225 satır)

### ❌ AÇIK: Status Değişim Auditi Yok

```
Senaryoyu:
Bölüm Sorumlusu vardiyayı planlar → TASLAK
Müdür Onay Bekliyor'a gönder
Admin tarafından RED edilir
Bölüm Sorumlusu düzeltir → TASLAK

KİM yaptı? NE ZAMAN? 
NEDEN red edildi?
ONCEKİ durum ne idi?
= KAYIT YOK!
```

### ✅ İDEAL HAL:

```sql
CREATE TABLE vardiya_degisim_loglari (
    id SERIAL PRIMARY KEY,
    vardiya_id INTEGER NOT NULL REFERENCES personel_vardiya_programi(id),
    alan_adi VARCHAR(100),           -- 'onay_durumu', 'noten', vb
    eski_deger TEXT,                 -- 'TASLAK'
    yeni_deger TEXT,                 -- 'ONAY_BEKLIYOR'
    degistiren_id INTEGER REFERENCES personel(id),
    degisim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    red_nedeni TEXT                  -- Eğer RED ise
);
```

**Neden?** → Vardiya yönetim akışında (Maker/Checker) kim ve ne zaman onaylama/red yaptı bilinmiyor.

---

## 2. GÜNLÜK GÖREV (Daily Tasks)

**Dosya:** `modules/gunluk_gorev/` (432 satır)

### ❌ AÇIK: Görev Atama Auditi Yok

```
Senaryoyu:
Görev Personel A'ya atanır
Personel B'ye değiştirilir
Tamamlandi_ts'ye yazılır

KİM atadı? NE ZAMAN? NEDEN değiştirildi?
= KAYIT YOK!
```

### ✅ İDEAL HAL:

```sql
CREATE TABLE gunluk_gorev_degisim_loglari (
    id SERIAL PRIMARY KEY,
    gorev_id INTEGER NOT NULL REFERENCES gunluk_gorevler(id),
    alan_adi VARCHAR(100),           -- 'atanan_personel_id', 'tamamlandi_ts'
    eski_deger TEXT,
    yeni_deger TEXT,
    degistiren_id INTEGER REFERENCES personel(id),
    degisim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Neden?** → Görev tasarımı kimin sorumluluğunda olduğu belirsizdir.

---

## 3. MAP ÜRETİM (Production)

**Dosya:** `ui/map_uretim/` (1,396 satır)

### ❌ AÇIK: Fire/Bobin Değişim Tarihi Yok

```
Map başlatıldığında:
- Fire kaydı açılır
- Bobin lot atanır
- Durum 'ACIK'

Orta yolda:
- Fire değeri değişir
- Bobin değişir
- Durum 'KAPALI' olur

HANGI SAATTE ne değişti?
KİM değiştirdi?
= KAYIT YOK!
```

### ✅ İDEAL HAL:

```sql
CREATE TABLE map_vardiya_degisim_loglari (
    id SERIAL PRIMARY KEY,
    map_vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id),
    alan_adi VARCHAR(100),           -- 'fire_no', 'bobin_lot', 'durum'
    eski_deger TEXT,
    yeni_deger TEXT,
    degistiren_id INTEGER REFERENCES personel(id),
    degisim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Neden?** → Fire ve bobin takibinde veri integriyetesi sağlanamaz.

---

## 4. QDMS (QMS Documents)

**Dosya:** `modules/qdms/` (1,246 satır)

### ⚠️ AÇIK: Revizyon Field-Level Değil

```
qdms_revizyon_log var ✓
Ama sadece belge versiyonu kaydediyor:
- Revizyon No: 1 → 2 → 3
- Tarih: kaydedilir

AMA: Belge içinde HANGİ alanlar değişti?
Nasıl değişti? (sadece başlık mı, tüm bölümler mi?)
= FIELD-LEVEL AUDIT TRAIL YOK!
```

### ✅ İDEAL HAL:

```sql
CREATE TABLE qdms_belge_degisim_detay (
    id SERIAL PRIMARY KEY,
    revizyon_log_id INTEGER REFERENCES qdms_revizyon_log(id),
    alan_adi VARCHAR(100),           -- 'baslik', 'bolum_1', 'amac', vb
    eski_deger TEXT,
    yeni_deger TEXT,
    degistiren_id INTEGER REFERENCES personel(id),
    degisim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Neden?** → Belge revizyonları ne zaman ve nasıl değiştiği bilinmiyor (compliance riski).

---

## 5. KPI & KALITE KONTROL

**Dosya:** `ui/kpi_ui.py` (241 satır)

### ❌ AÇIK: KPI Veri Giriş Auditi Yok

```
KPI veri girişinde:
- Üretim sayısı
- Hata sayısı
- Uygun/Uygun değil

KİM girdti? NE ZAMAN?
NEDEN değişti (eğer düzeltme ise)?
= KAYIT YOK!
```

### ✅ İDEAL HAL:

```sql
CREATE TABLE urun_kpi_degisim_loglari (
    id SERIAL PRIMARY KEY,
    kpi_id INTEGER NOT NULL REFERENCES urun_kpi_kontrol(id),
    alan_adi VARCHAR(100),           -- 'uretim_sayisi', 'hata_sayisi'
    eski_deger TEXT,
    yeni_deger TEXT,
    girisci_id INTEGER REFERENCES personel(id),
    giris_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Neden?** → KPI verilerinin manipülasyonu tespit edilemez.

---

## 6. GMP & HİJYEN KONTROL

**Dosya:** `ui/hijyen_ui.py` (256 satır)

### ❌ AÇIK: Kontrol Sonuç Auditi Yok

```
Hijyen kontrolü yapılır:
- UYGUN / UYGUNSUZ sonuç
- Denetçi atanır
- Foto kaydedilir

Sonra düzeltme yapılır:
- Sonuç değişir
- Periyot değişir

KİM yaptı? NE ZAMAN?
= KAYIT YOK!
```

### ✅ İDEAL HAL:

```sql
CREATE TABLE hijyen_kontrol_degisim_loglari (
    id SERIAL PRIMARY KEY,
    kontrol_id INTEGER NOT NULL REFERENCES hijyen_kontrol(id),
    alan_adi VARCHAR(100),           -- 'sonuc', 'periyot'
    eski_deger TEXT,
    yeni_deger TEXT,
    degistiren_id INTEGER REFERENCES personel(id),
    degisim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Neden?** → FSSC 22000 uyumu için kontrol yapıldığının kanıtı zayıf.

---

## 7. PERFORMANS & POLİVALANS

**Dosya:** `ui/performans/` (282 satır)

### ❌ AÇIK: Rating Değişim Auditi Yok

```
Personel değerlendirilir:
- Başlangıç rating: 3/5
- Müdür revizyonu: 4/5

NEDEN değişti?
YORUM eklenmiş mi?

= RASYONALE KAYITI YOK!
```

### ✅ İDEAL HAL:

```sql
CREATE TABLE performans_degisim_loglari (
    id SERIAL PRIMARY KEY,
    degerlendirme_id INTEGER NOT NULL REFERENCES performans_degerlendirme(id),
    alan_adi VARCHAR(100),           -- 'rating', 'yorum'
    eski_deger TEXT,
    yeni_deger TEXT,
    degistiren_id INTEGER REFERENCES personel(id),
    degisim_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Neden?** → Rating değişimleri arbitrer görünebilir.

---

## 8. SİSTEM LOGLARI (Generic)

**Dosya:** `logic/error_handler.py`, `sistemleri_loglari` tablosu

### ⚠️ AÇIK: Generic Log, Field-Level Değil

```
sistem_loglari tablosu var ✓
Ama sadece:
- islem_tipi: 'PERSONEL_EKLE', 'QDMS_REVIZYON'
- detay: "User 2 added personnel 5" (metin)

AMA: HANGİ alanlar değişti?
NE idi -> NE oldu?

= FIELD-LEVEL CLARITY YOK!
```

### ✅ İDEAL HAL:

Her modüle özgü `*_degisim_loglari` tablosu (tek bir generic log değil).

---

## 📋 ÖZETİ — %100 DINAMIKLIK EKSIKLIKLERI

### Patern:

```
Mevcut: tablo_1 UPDATE → tablo_2'ye field syncing EKSIK
        tablo_1 UPDATE → kim/ne/ne zaman KAYITSIZ
        
İdeal:  tablo_1 UPDATE → tablo_2'ye %100 dinamik sync
        tablo_1 UPDATE → tablo_1_degisim_loglari'ne FULL AUDIT
```

### Etkilenen Alanlar:

1. **Data Integrity** (kim ne değiştirdi?) — 6 modülde eksik
2. **Compliance** (FSSC, KVKK) — 4 modülde eksik
3. **Traceability** (geri izlenebilirlik) — 8 modülde eksik

---

## 🚀 ÇÖZÜM STRATEJİSİ

**Aşama 1 (YAPILDI):**
- ✅ MADDE 2.1 (%100 Dinamiklik) ANAYASA'ya eklendi
- ✅ MADDE 31 (Audit Trail) ANAYASA'ya eklendi
- ✅ personel_degisim_loglari tablosu oluşturuldu
- ✅ dynamic_sync.py yazıldı

**Aşama 2 (YAPILACAK — Önerilen Sıra):**
1. `vardiya_degisim_loglari` (P1) — vardiya onay akışının izlenebilirliği için
2. `gunluk_gorev_degisim_loglari` (P1) — görev atama sorumluluğu için
3. `map_vardiya_degisim_loglari` (P2) — üretim veri bütünlüğü için
4. Diğerleri (P3) — compliance rapor sistemi

---

**Not:** Bu açıklar MADDE 2.1 ve MADDE 31'i ihlal ediyor.
Her modüle audit trail eklemek ≈ 2 hafta (paralel çalışma)
