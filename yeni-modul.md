# /yeni-modul — Master Prompt Şablonu (v2.0)
**Kullanım:** Antigravity Manager'a yapıştır. Sadece `GÖREV` ve `MODÜL SEÇ` alanını doldur.

---

## ADIM 0 — MODÜL SEÇ (Standart maddeler otomatik gelir)

```
Modülünü seç, ilgili satırı kopyala:

gunluk_gorev  → BRC v9 1.1.2 | IFS v8 3.2.3  | FSSC v6 2.5.8  | ISO 9001 7.2
recipe_bom    → BRC v9 3.4   | IFS v8 4.1.3  | FSSC v6 2.5.4  | ISO 9001 8.4
haccp         → BRC v9 2.0   | IFS v8 2.3.11 | FSSC v6 ISO22000/8 | ISO 9001 8.1
duzeltici     → BRC v9 1.1.12| IFS v8 5.1.2  | FSSC v6 ISO22000/10 | ISO 9001 10.2
geri_cagirma  → BRC v9 3.11  | IFS v8 5.2    | FSSC v6 2.5.17 | ISO 9001 8.7
dog           → BRC v9 1.1.2 | IFS v8 3.2.3  | FSSC v6 2.5.8  | ISO 9001 9.1
qdms          → BRC v9 3.7   | IFS v8 4.2.1  | FSSC v6 2.5.9  | ISO 9001 7.5
map_uretim    → BRC v9 4.6.2 | IFS v8 4.10   | FSSC v6 ISO22000/8 | ISO 9001 8.5
soguk_oda     → BRC v9 4.11.1| IFS v8 4.9.2  | FSSC v6 2.5.1  | ISO 9001 8.5.1
```

---

## ŞABLON

```
GÖREV: [MODÜL ADI] modülü geliştir
Şirket: EKLERİSTAN A.Ş. | Proje: EKLERİSTAN QMS v3.2
Standartlar: [ADIM 0'dan seçilen satırı buraya yapıştır]

─────────────────────────────────────────
S1 — BUILDER (Gemini Flash):
─────────────────────────────────────────
modules/[modul_adi]/ altına Python yaz.
• Turkish snake_case zorunlu
• Max 30 satır/fonksiyon
• Hardcode yasak — CONSTANTS.py veya ayarlar_moduller kullan
• State: taslak → incelemede → aktif → arsiv (bu sıra değişmez)
• SQLAlchemy 2.0 ORM | Streamlit v1.x UI

Builder bittikten sonra ZORUNLU kontrol:
  python -m py_compile modules/[modul_adi]/*.py
  python -c "import modules.[modul_adi]"
Her iki komut da hatasız geçmeden S2'ye geçme.

─────────────────────────────────────────
S2 — TESTER (Gemini Flash):
─────────────────────────────────────────
Builder çıktısı için unit test yaz.
• tests/test_[modul_adi].py oluştur
• Her kritik fonksiyon için en az 1 test
• Artifact: hata raporu + geçen/toplam test sayısı
• Builder bitmeden başlama

─────────────────────────────────────────
S4 — GUARDIAN (Gemini Flash):
─────────────────────────────────────────
Zero Hardcode kontrolü yap:
• CONSTANTS.py dışı string/sayı = RED
• Şirket adı "EKLERİSTAN A.Ş." mi kontrol et
• State machine geçişleri kurallara uyuyor mu?
• Fonksiyon 30 satır üstü = RED | İngilizce fn adı = RED
RED → dur, bana getir. Otomatik devam etme. İnsan onayı zorunlu.
ONAY → Aşağıdaki claudes_plan.md adımına geç.

─────────────────────────────────────────
ZİNCİR BİTİŞİ — claudes_plan.md yaz (ZORUNLU):
─────────────────────────────────────────
Dosya: C:\Users\GIDA MÜHENDİSİ\.gemini\antigravity\brain\4a011233-6f51-40d7-bbb8-21b93ec221fd\claudes_plan.md

Şu formatı kullan (olduğu gibi kopyala, sadece [...] doldur):

---
# Claude'un Planı: [GÖREV BAŞLIĞI]

Durum: S4_ONAY
Tarih: [GG.AA.YYYY SS:DD]
Standartlar: [ADIM 0'dan seçilen satır]

## Değiştirilen Dosyalar
- [dosya1.py] — [ne yapıldı]
- [dosya2.py] — [ne yapıldı]

## S4 Guardian Raporu
[RED tespitler varsa listele | Yoksa "Hardcode yok — ONAY"]

## S2 Tester Raporu
[Geçen] / [Toplam] test — [Notlar]

## Yeni Tablolar (S5 için)
[Yeni tablo adları varsa listele | Yoksa "Tablo değişikliği yok"]

## S3 Auditor İçin Denetim Noktaları
[Hangi standart maddesi, hangi fonksiyon — örn: BRC v9 3.7 → belge_kayit()]
---

claudes_plan.md yazdıktan sonra Claude Code'u uyar:
"claudes_plan.md güncellendi — S3+S5 zincirini başlatabilirsin"

─────────────────────────────────────────
GENEL KURALLAR:
─────────────────────────────────────────
• Max 3 iterasyon / zincir
• Her adım Artifact üretir
• 3. iterasyonda çözüm yoksa → dur, rapor et
• Bir sonraki ajan önceki Artifact'i okur
• claudes_plan.md yazılmadan S5 başlayamaz
```

---

## Değişiklik Geçmişi

| Versiyon | Değişiklik | Sebep |
|---|---|---|
| v1.0 | İlk sürüm | — |
| v2.0 | ADIM 0 modül→madde tablosu eklendi | Sertifikasyon riski — [MADDE] boş kalmamalı |
| v2.0 | claudes_plan.md zorunlu hale getirildi | Zincir hafızası + BRC 3.7 denetim kaydı |
| v2.0 | py_compile + import check eklendi | Syntax hatası iterasyon öldürüyor |
