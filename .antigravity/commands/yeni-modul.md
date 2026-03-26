# /yeni-modul — Master Prompt Şablonu
**Kullanım:** Antigravity Manager'a yapıştır. `[...]` alanlarını doldur.**

---

## ŞABLON

```
GÖREV: [MODÜL ADI] modülü geliştir
Şirket: EKLERİSTAN A.Ş. | Proje: EKLERİSTAN QMS v3.2
Standartlar: BRC v9 [MADDE], IFS v8 [MADDE], FSSC v6 [MADDE]

---

BUILDER (S1 - Gemini Flash):
modules/[modul_adi]/ altına Python yaz.
- Turkish snake_case zorunlu
- Max 30 satır/fonksiyon
- Hardcode yasak — CONSTANTS.py veya ayarlar_moduller kullan
- State: taslak → incelemede → aktif → arsiv (bu sıra değişmez)
- SQLAlchemy 2.0 ORM kullan
- Streamlit v1.x UI yaz

TESTER (S2 - Gemini Flash):
Builder çıktısı için unit test yaz.
- test_[modul_adi].py dosyası oluştur
- Her kritik fonksiyon için en az 1 test
- Artifact olarak hata raporu sun
- Builder bitmeden başlama

AUDITOR (S3 - Claude Sonnet 4.6):
Standart uyumunu denetle:
- BRC v9 [MADDE] kontrol et
- IFS v8 [MADDE] kontrol et
- FSSC v6 [MADDE] kontrol et
- ISO 9001 [MADDE] kontrol et
KO madde ihlali → kırmızı işaretle, dur, bana getir.

GUARDIAN (S4 - Gemini Flash):
Zero Hardcode kontrolü yap:
- CONSTANTS.py dışı string/sayı ara
- Şirket adı "EKLERİSTAN A.Ş." mi kontrol et
- State machine geçişleri kurallara uyuyor mu?
Bulursan → bana getir, otomatik devam etme. İnsan onayı zorunlu.

SYNK MASTER (S5 - Claude Sonnet 4.6):
Yeni tablolar varsa:
1. sync_log_preview.txt üret
2. Bana göster, onayımı al
3. Onay sonrası SQLite ↔ Supabase sync yap
4. Protected tablolar için ekstra onay al:
   personel, ayarlar_yetkiler, sistem_parametreleri, qdms_belgeler

---

GENEL KURALLAR:
- Max 3 iterasyon / zincir
- Her adım Artifact üretir
- 3. iterasyonda çözüm yoksa → dur, rapor et
- Bir sonraki ajan önceki Artifact'i okur
```

---

## Hazır Kullanım Örnekleri

### modules/gunluk_gorev/ için
```
BRC v9 1.1.2, IFS v8 3.2.3, FSSC v6 2.5.8, ISO 9001 7.2
```

### modules/recipe_bom/ için
```
BRC v9 3.4, IFS v8 4.1.3, FSSC v6 2.5.4, ISO 9001 8.4
```

### modules/haccp/ için
```
BRC v9 2.0, IFS v8 2.3.11, FSSC v6 ISO22000/8, ISO 9001 8.1
```
