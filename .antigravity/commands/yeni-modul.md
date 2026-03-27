# EKLERİSTAN QMS — YENİ MODÜL MASTER PROMPT
# .antigravity/commands/yeni-modul.md | Versiyon: 3.0
# Kullanım: Antigravity'e "/yeni-modul [modül adı ve açıklaması]" ile tetiklenir.

---

## 🚀 BAŞLATMA TALİMATI

Bir modül talebi aldığında şu adımları **sırasıyla ve eksiksiz** uygula:

---

### ADIM 0 — Hafıza Oku (Tüm Ajanlar İçin Zorunlu)
```
ÖNCE: .antigravity/musbet/hafiza/hafiza_ozeti.md dosyasını oku.
      Bu dosyayı okumadan hiçbir işleme başlama.
      Benzer bir modül daha önce yapıldı mı?
      Tekrar eden hatalar var mı?
      Varsa: ilgili ajanlara bildir, dikkat notunu ekle.
```

---

### ADIM 1 — builder_db'yi Başlat
```
Git: .antigravity/builder_db/CLAUDE.md
Görev: Bu modül için gerekli tablo/şema/migration'ı tasarla ve yaz.
Bitince: Devir raporunu yaz ve ADIM 2'yi çağır.
```

---

### ADIM 2 — builder_backend'i Çağır
```
Git: .antigravity/builder_backend/CLAUDE.md
Ön koşul: builder_db devir raporu mevcut olmalı.
Görev: Business logic ve servis katmanını yaz.
Bitince: Devir raporunu yaz ve ADIM 3'ü çağır.
```

---

### ADIM 3 — builder_frontend'i Çağır
```
Git: .antigravity/builder_frontend/CLAUDE.md
Ön koşul: builder_backend fonksiyon imzaları mevcut olmalı.
Görev: Streamlit UI'ı yaz.
Bitince: Devir raporunu yaz ve ADIM 4'ü çağır.
```

---

### ADIM 4 — tester'ı Çağır
```
Git: .antigravity/tester/CLAUDE.md
Ön koşul: Üç builder çıktısı eksiksiz olmalı.
Görev: Birim ve entegrasyon testlerini yaz ve çalıştır.
Başarısız → ilgili builder'a iade et, ADIM 1/2/3'e dön.
Başarılı → Devir raporunu yaz ve ADIM 5'i çağır.
```

---

### ADIM 5 — validator'ı Çağır
```
Git: .antigravity/validator/CLAUDE.md
Model: Claude Sonnet 4.6
Ön koşul: tester onayı mevcut olmalı.
Görev: Emre Bey gibi düşün, sistemi gerçek kullanım senaryolarıyla test et.

KALDI → musbet'e MANUEL_RED kaydı aç (P0).
         Pipeline DURDU.
         Kök neden hangi ajan? O ajana iade et.
         ADIM 1, 2 veya 3'e dön.

GEÇTİ → Devir raporunu yaz ve ADIM 6'yı çağır.
```

---

### ADIM 6 — guardian'ı Çağır
```
Git: .antigravity/guardian/CLAUDE.md
Model: Gemini Flash
Ön koşul: validator onayı mevcut olmalı.
Görev: Risk değerlendirmesi yap. 13. Adam Protokolü'nü uygula.
       Korunan tablolara erişim var mı? T1/T2/T3 seviyesi nedir?

VETO → Pipeline DURDU. musbet'e P1 kaydı aç.
        İlgili builder'a iade et.

ONAY → Devir raporunu yaz ve ADIM 7'yi çağır.
```

---

### ADIM 7 — auditor'ı Çağır
```
Git: .antigravity/auditor/CLAUDE.md
Model: Claude Sonnet 4.6
Ön koşul: guardian onayı mevcut olmalı.
Görev: Anayasa Madde 1-13 uyumunu denetle.
       BRC v9, IFS v8, ISO 9001 uyumunu kontrol et.

İHLAL → İlgili builder'a iade et. musbet'e denetim bulgusunu logla.
TEMIZ → Devir raporunu yaz ve ADIM 8'i çağır.
```

---

### ADIM 8 — sync_master'ı Çağır
```
Git: .antigravity/sync_master/CLAUDE.md
Model: Claude Sonnet 4.6
Ön koşul: auditor onayı mevcut olmalı.
Görev: Local SQLite ↔ Supabase PostgreSQL senkronizasyonunu yap.
       Symmetric Twin doğrulamasını tamamla.

HATA → Pipeline DURDU. musbet'e P1 kaydı aç. Guardian'a bildir.
TAMAM → Modül canlıya alındı. musbet'e "tamamlandı" logu yaz.
```

---

### ADIM 9 — Kapanış
```
musbet'e son raporu gönder:
  - Modül adı
  - Toplam süre
  - Kaç kez iade yaşandı
  - Hangi ajanlar iade aldı
  - Açık kalan not var mı?

Emre'ye özet sun:
  ✅ [Modül adı] canlıya alındı.
  ℹ️  [N] iade yaşandı, [ajan]'da çözüldü.
```

---

## ⛔ BLOKE KURALLARI

```
- Ön koşul yoksa ajan başlamaz, bekler.
- P0 veya P1 açıkken yeni ADIM başlamaz.
- "Şimdilik geç, sonra düzeltirim" → geçersiz.
- Herhangi bir aşamada şüphe → guardian'a sor.
```

---

*yeni-modul.md | EKLERİSTAN QMS Antigravity Pipeline v3.0*
