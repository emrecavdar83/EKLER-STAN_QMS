# ANAYASA — Değiştirilemez Kurallar
**EKLERİSTAN QMS v3.2 | Madde 1-16 (Çekirdek) + Madde 17 (Ajan)**

---

## MADDE 1-16 (Özet)
*(Tam metin: c:\Projeler\S_program\EKLERİSTAN_QMS\ANAYASA.md üzerinden taşındı)*
- Zero Hardcode (Madde 1)
- BRC v9/IFS v8 Uyumu (Madde 2)
- Merkezi Cache (Madde 3)
- 30 Satır Kuralı & Naming (Madde 4, 13)
- 13. Adam Protokolü (Madde 10)
- Symmetric Twin (Madde 14)
- Atomik Bootstrap (Madde 16)

---

## MADDE 17 — Teknik Uyumluluk (v4.1.4)
Her `git push` öncesinde **S6-Protector** tarafından `tech-ledger.md` denetimi yapılır. 
Hata kayıt defterindeki ("TRC", "IND", "PKG", "PTH", "DRI", "REG", "VER") kriterlerine uymayan hiçbir kod canlıya çıkamaz.

---

## MADDE 18 — Döküman Yönetimi ve Görsel Standartlar
Sistemden üretilen tüm PDF, Rapor ve Çıktılar aşağıdaki "Onaylı Sayfa Yapısı"na (v4.1.7) uymak zorundadır:

### 18.1 Üst Bilgi (Header) Yapısı
- **Logo (NW):** Sol üst köşede, mm bazlı sabit koordinatta (`height - 25mm`).
- **Orta Alan:** 
  - Üst: Kalın (Bold) Belge Adı.
  - Alt: Belge Kodu | İlk Yayın Tarihi.
- **Sağ Alan:**
  - Üst: Rev No (örn. 01).
  - Alt: Rev Tarihi (GG.AA.YYYY).
- **Ayırıcı (Separator):** Dark Navy Blue (#0d1f3c) yatay çizgi (0.5pt).

### 18.2 Alt Bilgi (Footer) Yapısı
- **Sol:** "DAHİLİ KULLANIM" ibaresi (7pt).
- **Orta:** "EKLERİSTAN QMS vX.X.X" (Dinamik sürüm bilgisi).
- **Sağ:** BASKI TARİHİ: GG.AA.YYYY SS:DD | SAYFA: X / Y.

### 18.3 Yazı Karakteri ve Stil
- **Font:** Kurumsal Vera/Helvetica ailesi (Türkçe karakter desteği zorunlu).
- **Renk Paleti:** Başlıklar ve Çizgiler için Kurumsal Lacivert (#0d1f3c).

---

## MADDE 19 — Görev Kartı (GK) Standart Mimarisi
Tüm Pozisyon/Görev Tanımları (GK dökümanları) istisnasız aşağıdaki 10 bölümden oluşur:

1. **BELGE KİMLİĞİ:** Kod, Revizyon, Tarih, Durum.
2. **POZİSYON PROFİLİ:** Ünvan, Departman, Üst amir, Vekil, Çalışma yeri, Vardiya.
3. **GÖREV ÖZETİ:** Pozisyonun organizasyondaki ana amacı.
4. **SORUMLULUK ALANLARI (5 Disiplin):** Personel, Operasyon, Gıda Güv/Kalite, İSG, Çevre.
5. **YETKİ SINIRLARI:** DÖF, Raporlama, Üretim Durdurma, Acil Durum, Finans yetkileri.
6. **SÜREÇLER ARASI ETKİLEŞİM (RACI):** Departman bazlı R/A/C/I matrisi.
7. **PERİYODİK GÖREV LİSTESİ:** Sürekli ve dönemsel görevler + Standart referansı.
8. **NİTELİK & YETKİNLİK:** Eğitim, teknik beceri, kişisel özellikler, tecrübe.
9. **PERFORMANS GÖSTERGELERİ (KPI):** KPI Adı, Hedef/Formül.
10. **ONAY & İMZA:** Hazırlayan, Kontrol Eden, Onaylayan imza bölümleri.

**Yasak:** Bu 10 bölümlü yapıdan herhangi birinin silinmesi veya birleştirilmesi "Mimari Sapma" (DRI-001) sayılır ve Auditor tarafından yasaklanır.

---

*Bu kuralları ihlal eden her çıktı → Auditor veya Guardian tarafından durdurulur.*
