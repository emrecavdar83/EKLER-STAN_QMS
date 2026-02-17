# IMP-005: İşten Ayrılan Personel Yönetimi ve Pasife Alma

## 📋 Özet
Personel yönetim sisteminde işten ayrılan çalışanların kayıtlarının silinmesi yerine "Pasif" statüsüne alınarak arşivlenmesi, sisteme girişlerinin engellenmesi ve raporlamalarda tarihçenin korunması hedeflenmektedir.

## 🔍 Mevcut Durum
- `personel` tablosunda `durum` kolonu mevcut ancak sadece "AKTİF" değeri kullanılıyor.
- Login işleminde aktif/pasif kontrolü henüz net değil.
- İşten çıkış tarihi ve sebebi için veritabanında alan yok.

## 🛠️ Önerilen Çözüm (Seçenek B)

Bu seçenek, sadece statü değiştirmekle kalmaz, kurumsal hafızayı korumak için gerekli ek bilgileri de tutar.

### 1. Veritabanı Güncellemesi
Personel tablosuna şu kolonlar eklenecek:
- `is_cikis_tarihi` (Date): İşten ayrılma tarihi
- `ayrilma_sebebi` (Text): İstifa, Emeklilik, Fesih vb.

### 2. Arayüz (UI) İyileştirmeleri
**Personel Yönetimi Sayfası:**
- Personel listesinde her satıra **"⛔ Pasife Al"** veya **"İşten Çıkar"** butonu/menüsü eklenecek.
- Tıklandığında bir popup açılacak:
  - İşten Çıkış Tarihi (Varsayılan: Bugün)
  - Ayrılma Sebebi (Zorunlu alan)
  - "Onayla" butonu

**Filtreleme:**
- Sayfa açılışında varsayılan olarak sadece **AKTİF** personeller listelenecek.
- "Pasifleri Göster" veya "Tümünü Göster" filtresi eklenecek.

### 3. Güvenlik ve Kısıtlamalar (Logic)
- **Giriş (Login):** Kullanıcı giriş yaparken `durum='AKTİF'` kontrolü eklenecek. Pasif kullanıcılar "Hesabınız pasif durumdadır" uyarısı alacak.
- **Dropdown Listeler:** Formlarda (örn. temizlik yapan personel seçimi) sadece aktif personeller listelenecek.
- **Organizasyon Şeması:** Pasif personeller şemadan otomatik olarak düşecek.

---

## ⚖️ Alternatif Yaklaşım (Seçenek A - Sadece Statü)
Ekstra kolon eklemeden, sadece mevcut `durum` alanını manuel olarak 'PASİF' yapma imkanı tanınır.
- **Avantaj:** Veritabanı değişikliği gerektirmez, hemen uygulanabilir.
- **Dezavantaj:** Ne zaman ve neden ayrıldığı bilgisi kaybolur. Raporlama yapılamaz.

## 📅 Uygulama Planı
1.  `personel` tablosuna yeni kolonların eklenmesi (Script ile).
2.  `app.py` Login fonksiyonuna aktiflik kontrolü eklenmesi.
3.  Personel Tanımlama sayfasındaki formun güncellenmesi.
4.  Diğer modüllerdeki (Dropdown vb.) sorguların `WHERE durum='AKTİF'` olarak güncellenmesi.

## ⚠️ Risk Analizi
- **Veri Tutarlılığı:** Geçmiş kayıtlarda pasif personelin adı geçiyorsa (örn. geçen ayın temizlik raporu) bunlar bozulmamalıdır. (Sistemi bozmaz, sadece yeni kayıtlarda çıkmazlar).
- **Risk Seviyesi:** Düşük

**Karar:** Kurumsal hafıza için **Seçenek B** (Tarih ve Sebep ile Pasife Alma) önerilmektedir.
