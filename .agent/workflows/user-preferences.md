---
description: Emre Bey'in çalışma tercihleri ve öğrenme yaklaşımı
---

# Kullanıcı Tercihleri

## 👨‍🏫 Öğretici Mod
Emre Bey bu projeyi öğrenmek istiyor. Yapılan her değişiklikte:

1. **Alternatif Seçenekleri Sun:**
   - En az 2-3 farklı yaklaşım göster
   - Her birinin avantaj/dezavantajlarını açıkla

2. **Risk Analizi Yap:**
   - Değişikliğin mevcut sisteme etkisi
   - Olası yan etkiler
   - Geri dönüş planı

3. **Açıklayıcı Ol:**
   - Kod ne yapıyor, neden bu şekilde yazıldı
   - Teknik kararların arkasındaki mantık

## 📋 Örnek Format

### Seçenek A: [İsim]
- **Nasıl çalışır:** ...
- **Avantaj:** ...
- **Dezavantaj:** ...
- **Risk:** Düşük/Orta/Yüksek

### Seçenek B: [İsim]
- **Nasıl çalışır:** ...
- **Avantaj:** ...
- **Dezavantaj:** ...
- **Risk:** Düşük/Orta/Yüksek

### Önerim: [Hangi seçenek ve neden]

---

## 🔧 Proje Bilgileri
- **Proje:** Ekleristan QMS
- **Teknolojiler:** Python, Streamlit, Supabase (PostgreSQL)
- **Kullanıcı:** Emre ÇAVDAR (Gıda Mühendisi)

---

## ⏰ HATIRLATMA: Lokasyon Revizyon Planı

**Ne zaman:** Lokasyon-Bölüm-Ekipman yapısı tamamlandığında

### Yapılacaklar:
1. **Benzersiz ID Yapısı:**
   ```
   XX-YY-ZZ-AA formatı
   XX = Kat bilgisi (örn: 01, 02, 03)
   YY = Bölüm bilgisi (örn: BOMBA→01, PATASU→02)
   ZZ = Hat bilgisi
   AA = Ekipman bilgisi
   
   Örnek: 03-02-01-05 = Kat3 > Pataşu > Hat1 > Ekipman5
   ```

2. **Tıklanabilir Ağaç Görünümü:**
   - Mevcut lokasyonlar expandable/collapsible olacak
   - Tıklama ile detaylar açılacak

3. **Kullanım Alanları:**
   - **Bakım Prosesi** - Ekipman bakım takibi
   - **QR Kodlu Ekipman Temizlik Kontrolü** - Her ekipmana QR kod, tarama ile temizlik kaydı
   - **İletişim Prosesi** - Konum bazlı bildirimler
   - Tüm modüllerde merkezi referans

### Neden Önemli:
- Benzersiz tanımlama = Raporlamada netlik
- Hiyerarşik kod = Otomatik sıralama ve gruplama
- **QR kod entegrasyonu** = Mobil cihazla hızlı kayıt
