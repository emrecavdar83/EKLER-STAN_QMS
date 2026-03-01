# BRC Uyumlu Raporlama ve Otomatik Arşivleme Planı

Bu belge, mevcut HTML rapor taslaklarının **BRCGS v9 Gıda Güvenliği Standardı** gerekliliklerine göre nasıl geliştirileceğini ve sistemin her gece 23:59'da bu raporları nasıl otomatik olarak alıp PDF formatında arşivleyebileceğini planlar. **(Kod yazılmamıştır, sadece planlama yapılmıştır.)**

---

## 1. BRC Uyumlu Rapor İyileştirmeleri

BRC standartları, özellikle izlenebilirlik, düzeltici / önleyici faaliyetler (DÖF) ve doküman kontrolü konusunda son derece katıdır. Raporlarımıza eklenmesi planlanan BRC zorunlu alanları şunlardır:

### 1.1. Tüm Raporlarda Ortak Olması Gerekenler
- **Revizyon Numarası ve Tarihi:** Rapor formunun en son ne zaman güncellendiğine dair (Örn: Rev:02 - 15.01.2026).
- **Sayfa Numaralandırması:** "Sayfa 1 / X" formatında (sayfaların eksik olup olmadığının ispatı için).
- **"Uygunsuzluk Durumunda Yapılacaklar" Uyarı Metni:** Alt bilgi (footer) veya imza alanının üstüne: *"Kritik sapmalarda derhal Kalite Güvence birimine haber veriniz. Ürün karantinaya alınmalıdır."*

### 1.2. Üretim Raporu İyileştirmeleri (Şu Anki Veritabanı İle Mümkün Olan)
### 1.2. Üretim Raporu İyileştirmeleri
- **Lot İzlenebilirliği:** Sadece üretilen ürünün (Çıktı Parti Numarası) `lot_no` sütunu izlenebilirliğin temeli olarak büyük fontlarda gösterilecek.
- **Fire Analizi ve Dinamik Sebep:** Sadece fire oranı değil, yüksek fire durumunda kök nedenin (Örn: Fırın Isı Sapması) seçilebilmesi için önceden hazırlanan dinamik bir "Fire Sebebi" yapısı rapora entegre edilecektir.

### 1.3. Hijyen Raporu İyileştirmeleri (BRC Kapsamı)
- **DÖF (Düzeltici Önleyici Faaliyet) Karşılığı:** Mevcut veritabanındaki **`aksiyon`** sütunu, BRC denetimlerinde doğrudan **DÖF kanıtı** olarak raporun merkezine alınacak. (Örn: "Personel üretim alanından çıkarıldı, oje temizlettirildi").
- **Kök Neden:** Sisteme girilen **`sebep`** sütunu ile uygunsuzluğun nedeni kanıtlanacak.

### 1.4. Temizlik Takip Raporu İyileştirmeleri (BRC Kapsamı)
- **Kullanılan Kimyasalın Dozajı / Konsantrasyonu:** Temizlik işlemi sırasında kullanılan kimyasalın bilgisi ve dozu (örn: "%2'lik Klorlu Köpük" / 50 ppm).
- **Temizlik Öncesi ve Sonrası Doğrulama:** Görsel kontrol onayının yanısıra, cihazla yapılan ölçümlerin **ATP Swab sonucu (RLU)** değerlerini gösteren doğrulama sütunları.

---

## 2. Dinamik Fire Sebepleri İçin Geliştirme Planı

Şu an sistemdeki üretim fireleri sadece miktar ve genel "notlar" olarak alınıyor. İlerleyen süreçte bu durum için şu aksiyon alınacaktır:
- Veritabanına `ayarlar_fire_sebepleri` adında yeni bir tablo eklenecek.
- Yönetim, arayüzden bu sebepleri (Örn: "Düşürme", "Yanma", "Küflenme") dinamik olarak tanımlayabilecek.
- Üretim personeli fire girerken bu listeden seçim yapacak ve bu veri doğrudan rapora "Fire Sebebi" olarak yansıyacak.

---

## 3. Otomatik PDF Arşivleme Planı (23:59 Cron / Cloud Function)

Sistemin her gece kullanıcı müdahalesine gerek kalmadan tüm günün raporlarını PDF yapıp buluta kaydetmesi mümkündür. 

### 2.1. Mimari Altyapı
- **Senaryo:** Uygulama (Streamlit Cloud veya VPS), her gece 23:59'da bir komut dosyası (script) tetikler.
- **Arşivleme Noktası:** Oluşturulan PDF'ler, Supabase Storage'daki güvenli bir `daily_reports_archive` klasörüne (bucket) yüklenir. 

### 2.2. İşlem Adımları
1. **Veri Toplama:** Python script'i (örneğin `auto_reporter.py`) saat 23:59 civarı veritabanına bağlanıp ilgili güne ait Üretim, Hijyen, Temizlik, KPI ve SOSTS (Soğuk Oda) verilerini çeker.
2. **HTML Oluşturma:** Veriler, tasarladığımız kurumsal HTML şablonları kullanılarak RAM üzerinde HTML dosyası haline getirilir.
3. **PDF Dönüştürme:** Python içerisindeki `pdfkit` (veya `weasyprint`) kütüphanesi ile bu HTML dosyaları fiziksel PDF belgelerine dönüştürülür.
4. **Cloud Saklama (Supabase Storage):**
   - Rapor adı formatlanır: `2026-03-01_URETIM_RAPORU.pdf`
   - Supabase Python API kullanılarak `storage.from_('rapor-arsivi').upload(...)` ile buluta yüklenir.
5. **Veritabanı Logu:** Raporların başarıyla oluşturulduğu `otomatik_rapor_loglari` isimli bir tabloya yazılır (Denetimlerde sistemin kendi kendine çalıştığını kanıtlamak için).

### 2.3. Tetikleme Yöntemi (Trigger)
- **Eğer uygulama sadece Streamlit Cloud'daysa:** Streamlit sürekli ayakta kalan bir yapı sunmaz. Bu nedenle Github Actions üzerinden her gün 23:59'da çalışacak bir `Cron Job` oluşturulur. GitHub bu job'ı çalıştırır, job veritabanına bağlanıp raporu üretir ve Supabase'e atar.
- **Eğer Supabase kullanılıyorsa:** Supabase Edge Functions ve `pg_cron` kullanılarak doğrudan veritabanı üzerinden rapor oluşturma tetiklenebilir (ancak PDF çevirimi ağır olduğu için GitHub Actions veya harici bir sunucu daha etkilidir).

---

## Sonraki Adımlar
Bu plan dahilinde şu aşamalar kodlanabilir (Onay verdiğiniz kısımlara göre):
1. **Aşama:** Rapor satırlarına (Üretim, Hijyen, vb.) bahsi geçen BRC DÖF/Karar/Limit gibi alanları ekleyen UI kodlaması.
2. **Aşama:** PDF dönüşümü için `pdfkit` altyapısı kurulumu.
3. **Aşama:** `auto_reporter.py` script'inin yazılması ve Supabase Storage'a atılması.
4. **Aşama:** GitHub Actions yaml dosyasının hazırlanarak gece 23:59 otomasyonunun bağlanması.
