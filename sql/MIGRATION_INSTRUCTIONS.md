# 🚀 SUPABASE MIGRATION TALİMATLARI

## ⚠️ ÖNEMLİ - ÖNCE BUNU OKUYUN

Bu migration script **otomatik veri dönüştürme** yapacak. Mevcut `personel` tablosundaki `bolum` string değerlerini `departman_id` foreign key'e dönüştürecek.

**GERİ DÖNÜŞ PLANI:** Eski `bolum` sütunu korunuyor, silinmiyor. Sorun çıkarsa geri dönülebilir.

---

## ADIM 1: Supabase SQL Editor'e Git

1. Tarayıcıda Supabase Dashboard'a git: https://supabase.com/dashboard
2. Projenizi seçin
3. Sol menüden **SQL Editor**'e tıklayın

---

## ADIM 2: Migration Script'i Çalıştır

1. Aşağıdaki dosyayı açın:
   ```
   sql/supabase_personel_org_restructure.sql
   ```

2. **TÜM İÇERİĞİ** kopyalayın (Ctrl+A, Ctrl+C)

3. Supabase SQL Editor'de **"New Query"** butonuna tıklayın

4. Kopyaladığınız SQL kodunu yapıştırın (Ctrl+V)

5. **"Run"** butonuna basın (veya Ctrl+Enter)

---

## ADIM 3: Sonuçları Kontrol Et

Migration başarılı olursa şu mesajları göreceksiniz:

```
NOTICE: BAŞARILI: Tüm personel kayıtları departmanlara eşleştirildi.

sonuc
---------------------------------------------------------
Personel-Organizasyon veri akışı başarıyla yeniden yapılandırıldı!
```

**Eğer uyarı mesajı görürseniz:**
```
NOTICE: UYARI: X adet personel kaydının departmanı eşleştirilemedi.
```

Bu durumda şu sorguyu çalıştırın:
```sql
SELECT id, ad_soyad, bolum 
FROM personel 
WHERE bolum IS NOT NULL 
  AND bolum != '' 
  AND departman_id IS NULL;
```

Eşleşmeyen kayıtları manuel olarak düzeltmeniz gerekebilir.

---

## ADIM 4: Yeni Sütunları Doğrula

Migration tamamlandıktan sonra kontrol edin:

```sql
-- Yeni sütunların eklendiğini doğrula
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'personel' 
  AND column_name IN ('departman_id', 'yonetici_id', 'pozisyon_seviye');
```

Beklenen çıktı:
```
column_name       | data_type
------------------+-----------
departman_id      | integer
yonetici_id       | integer
pozisyon_seviye   | integer
```

---

## ADIM 5: View'ı Doğrula

```sql
-- View'ın oluşturulduğunu doğrula
SELECT * FROM v_organizasyon_semasi LIMIT 5;
```

Eğer veri dönüyorsa başarılı! ✅

---

## ADIM 6: Streamlit Cloud Deploy Bekle

1. GitHub'a push yapıldı, Streamlit Cloud otomatik deploy edecek
2. Deploy tamamlanana kadar bekleyin (genelde 2-3 dakika)
3. Streamlit Cloud Dashboard'dan deploy durumunu kontrol edebilirsiniz

---

## ADIM 7: Production'da Test Et

Deploy tamamlandıktan sonra:

1. **Ayarlar > Kullanıcı Yönetimi** sekmesine git
2. "Yeni Kullanıcı Ekle" formunda yeni alanları gör:
   - 🏭 Departman
   - 👔 Doğrudan Yönetici
   - 📊 Pozisyon Seviyesi
   - 💼 Görev Tanımı

3. **Raporlama > Personel Organizasyon Şeması** sekmesine git
4. Yeni organizasyon şemasını gör (yönetici-çalışan ilişkisi bazlı)

---

## ❌ SORUN ÇIKARSA

### Hata: "relation 'v_organizasyon_semasi' does not exist"

**Çözüm:** Migration script'i tekrar çalıştırın. View oluşturma kısmı başarısız olmuş olabilir.

### Hata: "column 'departman_id' does not exist"

**Çözüm:** Migration script'in tamamını çalıştırdığınızdan emin olun. Sadece bir kısmını çalıştırmış olabilirsiniz.

### Personel departmanları eşleşmedi

**Çözüm:** Manuel düzeltme yapın:

```sql
-- Örnek: "Üretim" departmanına ait personeli güncelle
UPDATE personel 
SET departman_id = (SELECT id FROM ayarlar_bolumler WHERE bolum_adi = 'ÜRETİM' LIMIT 1)
WHERE UPPER(bolum) LIKE '%ÜRETİM%' 
  AND departman_id IS NULL;
```

---

## ✅ BAŞARILI DEPLOYMENT KONTROLÜ

Tüm bunlar çalışıyorsa deployment başarılı:

- ✅ Yeni personel ekleme formu yeni alanları gösteriyor
- ✅ Organizasyon şeması yönetici-çalışan ilişkilerini gösteriyor
- ✅ Departman cluster'ları görünüyor
- ✅ İstatistikler doğru hesaplanıyor

---

## 📞 DESTEK

Sorun çıkarsa:
1. Supabase SQL Editor'deki hata mesajını kaydedin
2. Streamlit Cloud logs'ları kontrol edin
3. Gerekirse geri bildirim verin

**NOT:** Eski `bolum` sütunu korundu, hiçbir veri kaybı yok!
