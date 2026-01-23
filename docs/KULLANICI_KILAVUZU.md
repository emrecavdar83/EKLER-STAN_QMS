# 📖 EKLERİSTAN QMS - Kullanıcı Kılavuzu

## İçindekiler

1. [Giriş](#1-giriş)
2. [Sistem Gereksinimleri](#2-sistem-gereksinimleri)
3. [İlk Giriş ve Kullanıcı Arayüzü](#3-ilk-giriş-ve-kullanıcı-arayüzü)
4. [Üretim Girişi Modülü](#4-üretim-girişi-modülü)
5. [KPI & Kalite Kontrol Modülü](#5-kpi--kalite-kontrol-modülü)
6. [GMP Denetimi Modülü](#6-gmp-denetimi-modülü)
7. [Personel Hijyen Modülü](#7-personel-hijyen-modülü)
8. [Temizlik Kontrol Modülü](#8-temizlik-kontrol-modülü)
9. [Kurumsal Raporlama Modülü](#9-kurumsal-raporlama-modülü)
10. [Ayarlar Modülü (Yönetici)](#10-ayarlar-modülü-yönetici)
11. [Sık Sorulan Sorular](#11-sık-sorulan-sorular)

---

## 1. Giriş

### 1.1 EKLERİSTAN QMS Nedir?

EKLERİSTAN QMS, gıda üretim tesislerinde kalite yönetimi, üretim takibi, hijyen kontrolü ve denetim süreçlerini dijitalleştiren kapsamlı bir web uygulamasıdır. BRC V9 standartlarına uyumlu olarak tasarlanmıştır.

### 1.2 Kimler Kullanabilir?

- **Üretim Personeli:** Üretim kayıtları
- **Kalite Kontrol:** KPI analizleri, GMP denetimleri
- **Vardiya Amirleri:** Personel hijyen, temizlik kontrol
- **Yöneticiler:** Raporlama, organizasyon şeması
- **Sistem Yöneticileri:** Kullanıcı ve yetki yönetimi

---

## 2. Sistem Gereksinimleri

### 2.1 Tarayıcı Gereksinimleri

- **Önerilen:** Google Chrome 90+, Microsoft Edge 90+
- **Desteklenen:** Firefox 88+, Safari 14+
- **Mobil:** iOS Safari, Chrome Mobile

### 2.2 İnternet Bağlantısı

- **Cloud Versiyonu:** Aktif internet bağlantısı gereklidir
- **Yerel Versiyon:** İnternet bağlantısı gerekmez

---

## 3. İlk Giriş ve Kullanıcı Arayüzü

### 3.1 Giriş Ekranı

1. Tarayıcınızda uygulamayı açın
2. Kullanıcı adınızı seçin
3. Şifrenizi girin
4. **Giriş Yap** butonuna tıklayın

**Varsayılan Kullanıcı (İlk Kurulum):**
- Kullanıcı Adı: `Admin`
- Şifre: `12345`

> ⚠️ **Güvenlik Uyarısı:** İlk girişten sonra şifrenizi mutlaka değiştirin!

### 3.2 Ana Arayüz

Giriş yaptıktan sonra karşınıza çıkan ekran:

```
┌─────────────────────────────────────────────────────────┐
│  [Logo]                                                 │
│  👤 Kullanıcı Adı                                       │
│  ─────────────────────                                  │
│  MODÜLLER                                               │
│  ○ 🏭 Üretim Girişi                                     │
│  ○ 🍩 KPI & Kalite Kontrol                              │
│  ○ 🛡️ GMP Denetimi                                      │
│  ○ 🧼 Personel Hijyen                                   │
│  ○ 🧹 Temizlik Kontrol                                  │
│  ○ 📊 Kurumsal Raporlama                                │
│  ○ ⚙️ Ayarlar                                           │
│  ─────────────────────                                  │
│  [Çıkış Yap]                                            │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Üretim Girişi Modülü

### 4.1 Amaç

Günlük üretim verilerinin (lot, miktar, fire) sisteme kaydedilmesi ve raporlanması.

### 4.2 Yeni Üretim Kaydı Ekleme

**Adım 1:** Sol menüden **🏭 Üretim Girişi** seçin

**Adım 2:** Form alanlarını doldurun:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| **Tarih** | Üretim tarihi | 22.01.2026 |
| **Vardiya** | Çalışma vardiyası | GÜNDÜZ VARDİYASI |
| **Ürün** | Üretilen ürün | Çikolatalı Ekler |
| **Lot No** | Üretim lot numarası | 2026012201 |
| **Miktar** | Üretim miktarı (adet/kg) | 5000 |
| **Fire** | Fire miktarı | 50 |
| **Notlar** | Ek açıklamalar | Kalıp değişimi yapıldı |

**Adım 3:** **💾 Kaydı Onayla** butonuna tıklayın

**Adım 4:** Başarı mesajını bekleyin ve kayıt listesinde görüntüleyin

### 4.3 Üretim Özeti Görüntüleme

Sayfa aşağı kaydırıldığında:

- **Tarih Filtresi:** İstediğiniz günü seçin
- **Özet Tablo:** Personel ve ürün bazlı toplam üretim
- **Metrikler:** 
  - 🏭 Toplam Üretim
  - 🔥 Toplam Fire
  - ✅ Net Üretim

### 4.4 Yetki Gereksinimleri

- **Gerekli Yetki:** Düzenle
- **Erişebilen Roller:** Admin, Yönetim, Üretim Sorumlusu

---

## 5. KPI & Kalite Kontrol Modülü

### 5.1 Amaç

Üretilen ürünlerin kalite parametrelerinin (Brix, pH, ağırlık vb.) ölçülmesi ve karar verilmesi.

### 5.2 Kalite Analizi Yapma

**Adım 1:** **🍩 KPI & Kalite Kontrol** modülünü açın

**Adım 2:** Ürün ve Lot Bilgilerini Girin

- **Ürün Seçin:** Dropdown'dan ürünü seçin
- **Lot No:** Üretim lot numarasını girin
- **Vardiya:** Vardiya seçin

**Adım 3:** Sistem Bilgileri

Sistem otomatik olarak gösterir:
- Raf ömrü (gün)
- Son Tüketim Tarihi (STT)
- Numune sayısı

**Adım 4:** Ön Kontroller

☑️ **Üretim Tarihi ve STT Etiket Bilgisi Doğrudur** kutusunu işaretleyin

> ⚠️ Bu kutu işaretlenmeden kayıt yapılamaz!

**Adım 5:** Ölçüm Değerleri

Her numune için parametreleri girin:

```
Numune #1
├─ Brix: 65.2
├─ pH: 4.5
└─ Ağırlık: 45.3

Numune #2
├─ Brix: 65.5
├─ pH: 4.6
└─ Ağırlık: 45.1
```

**Adım 6:** Duyusal Kontrol

- **Tat / Koku:** Uygun / Uygun Değil
- **Görüntü / Renk:** Uygun / Uygun Değil
- **Kalite Notu:** Açıklama girin

**Adım 7:** **✅ Analizi Kaydet** butonuna tıklayın

### 5.3 Karar Mantığı

Sistem otomatik karar verir:

- **ONAY:** Tat ve Görüntü = Uygun
- **RED:** Herhangi biri = Uygun Değil

### 5.4 Yetki Gereksinimleri

- **Gerekli Yetki:** Görüntüle (minimum)
- **Erişebilen Roller:** Admin, Kalite Sorumlusu, Laboratuvar

---

## 6. GMP Denetimi Modülü

### 6.1 Amaç

BRC V9 standartlarına uygun olarak fabrika bölümlerinin hijyen ve GMP denetimlerinin yapılması.

### 6.2 Frekans Algoritması

Sistem otomatik olarak bugünün frekansını belirler:

- **GÜNLÜK:** Her gün
- **HAFTALIK:** Pazartesi günleri
- **AYLIK:** Ayın 1'i

### 6.3 Denetim Yapma

**Adım 1:** **🛡️ GMP Denetimi** modülünü açın

**Adım 2:** Denetim Bölümünü Seçin

Dropdown'dan denetlenecek bölümü seçin:
- Üretim Alanı
- Hammadde Deposu
- Paketleme
- vb.

**Adım 3:** Soruları Cevaplayın

Her soru için:

```
┌─────────────────────────────────────────────────┐
│ Zemin temiz ve kuru mu?                         │
│ 🏷️ Kategori: Hijyen | 📑 BRC: 4.3.1 | ⚡ Risk: 3│
│                                                 │
│ Durum: ○ UYGUN  ○ UYGUN DEĞİL                  │
└─────────────────────────────────────────────────┘
```

**Adım 4:** Uygun Değil İse Detay Girin

Risk seviyesi 3 (Kritik) ise:
- 📷 **Fotoğraf yükleme ZORUNLU**
- 📝 **Hata açıklaması ZORUNLU**

**Adım 5:** **✅ Denetimi Tamamla ve Gönder** butonuna tıklayın

### 6.4 Risk Seviyeleri

| Risk | Anlamı | Zorunlu Alan |
|------|--------|--------------|
| **1** | Düşük | - |
| **2** | Orta | Açıklama |
| **3** | Kritik | Fotoğraf + Açıklama |

### 6.5 Yetki Gereksinimleri

- **Gerekli Yetki:** Görüntüle
- **Erişebilen Roller:** Admin, Kalite, Vardiya Amiri

---

## 7. Personel Hijyen Modülü

### 7.1 Amaç

Vardiya başlangıcında personelin hijyen kontrolünün yapılması ve kayıt altına alınması.

### 7.2 Hijyen Kontrolü Yapma

**Adım 1:** **🧼 Personel Hijyen** modülünü açın

**Adım 2:** Vardiya ve Bölüm Seçin

- **Vardiya:** GÜNDÜZ VARDİYASI / ARA VARDİYA / GECE VARDİYASI
- **Bölüm:** Üretim / Paketleme / Depo vb.

**Adım 3:** Personel Durumlarını İşaretleyin

Tablo üzerinde her personel için durum seçin:

| Personel Adı | Durum |
|--------------|-------|
| Ahmet YILMAZ | Sorun Yok |
| Ayşe DEMİR | Gelmedi |
| Mehmet KAYA | Sağlık Riski |
| Fatma ŞAHİN | Hijyen Uygunsuzluk |

**Adım 4:** Sorunlu Personel İçin Detay Girin

Durum "Sorun Yok" dışında ise:

**Gelmedi:**
- **Neden?** Yıllık İzin / Raporlu / Habersiz Gelmedi
- **Aksiyon?** İK Bilgilendirildi / Tutanak Tutuldu

**Sağlık Riski:**
- **Neden?** Ateş / İshal / Öksürük / Açık Yara
- **Aksiyon?** Eve Gönderildi / Revire Yönlendirildi

**Hijyen Uygunsuzluk:**
- **Neden?** Kirli Önlük / Sakal Tıraşı / Bone Eksik
- **Aksiyon?** Personel Uyarıldı / Uygunsuzluk Giderildi

**Adım 5:** **💾 Denetimi Kaydet** butonuna tıklayın

### 7.3 Yetki Gereksinimleri

- **Gerekli Yetki:** Görüntüle
- **Erişebilen Roller:** Admin, Kalite, Vardiya Amiri

---

## 8. Temizlik Kontrol Modülü

### 8.1 Amaç

Fabrika temizlik planının takibi, kimyasal kullanımı ve verifikasyon kayıtlarının tutulması.

### 8.2 Saha Uygulama Çizelgesi

**Adım 1:** **🧹 Temizlik Kontrol** → **📋 Saha Uygulama Çizelgesi** tab'ını açın

**Adım 2:** Kat/Bölüm ve Vardiya Seçin

- **Kat/Bölüm:** Zemin Kat / 1. Kat / Depo
- **Vardiya:** Vardiya seçin

**Adım 3:** Temizlik Görevlerini İşaretleyin

Her ekipman/alan için:

```
┌──────────────────────────────────────────────┐
│ 📍 Mikser Tankı (Yüksek Risk)                │
│ 🧪 Alkali Deterjan / Günlük                  │
│                                              │
│ Durum: ○ TAMAMLANDI  ○ YAPILMADI            │
│                                              │
│ 🧬 ATP Sonuç/RLU: [150]                     │
└──────────────────────────────────────────────┘
```

**TAMAMLANDI ise:**
- Verifikasyon sonucu girin (ATP/Swap vb.)

**YAPILMADI ise:**
- Neden seçin: Arıza / Malzeme Eksik / Zaman Yetersiz

**Adım 4:** **💾 Tüm Kayıtları Veritabanına İşle** butonuna tıklayın

### 8.3 Master Plan Düzenleme (Yönetici)

**Adım 1:** **⚙️ Master Plan Düzenleme** tab'ını açın

**Adım 2:** Kat Filtresi Kullanın

Yeni kayıt eklerken filtreleme yapın

**Adım 3:** Tabloyu Düzenleyin

Sütunlar:
- 🏢 Kat
- 🏭 Bölüm
- ⚙️ Ekipman
- Kimyasal
- Yöntem
- Uygulayıcı Personel
- Kontrol Eden
- Validasyon Sıklığı
- Verifikasyon Yöntemi
- Risk Seviyesi

**Adım 4:** **💾 Master Planı Güncelle** butonuna tıklayın

### 8.4 Yetki Gereksinimleri

- **Saha Uygulama:** Görüntüle (Kayıt: Admin, Kalite, Vardiya Amiri)
- **Master Plan:** Düzenle (Sadece Admin, Kalite Sorumlusu)

---

## 9. Kurumsal Raporlama Modülü

### 9.1 Personel Organizasyon Şeması

**Adım 1:** **📊 Kurumsal Raporlama** → **👥 Personel Organizasyon Şeması** seçin

**Adım 2:** Görünüm Formatı Seçin

- **Hiyerarşik Görünüm:** Graphviz ile görsel şema
- **Liste Formatı:** Basit hiyerarşik liste
- **PDF Çıktısı:** A4 yazdırma formatı

**Adım 3:** Organizasyon Yapısı

```
🏛️ Yönetim Kurulu
└─ 👑 Genel Müdür
   ├─ 📊 Üretim Müdürü
   │  ├─ 💼 Üretim Şefi
   │  │  └─ 👥 Üretim Personeli
   │  └─ 💼 Paketleme Şefi
   │     └─ 👥 Paketleme Personeli
   └─ 📊 Kalite Müdürü
      └─ 💼 Kalite Sorumlusu
         └─ 👥 Laboratuvar Teknisyeni
```

**Adım 4:** PDF İndirme

PDF formatında indirmek için:
1. **PDF Çıktısı (Yazdırma)** seçin
2. Tarayıcınızın yazdırma penceresinde **PDF olarak kaydet** seçin
3. Dosyayı kaydedin

### 9.2 Diğer Raporlar

- **🏭 Üretim ve Verimlilik:** Tarih aralığı bazlı üretim analizi
- **🍩 Kalite (KPI) Analizi:** ONAY/RED oranları, trend analizi
- **🧼 Personel Hijyen Özeti:** Vardiya bazlı hijyen istatistikleri
- **🧹 Temizlik Takip Raporu:** Tamamlanma oranları

### 9.3 Yetki Gereksinimleri

- **Gerekli Yetki:** Görüntüle
- **Erişebilen Roller:** Tüm kullanıcılar (kendi bölümleri)

---

## 10. Ayarlar Modülü (Yönetici)

### 10.1 Kullanıcı Yönetimi

**Yeni Kullanıcı Ekleme:**

1. **Personel Listesi** tab'ını açın
2. Tabloya yeni satır ekleyin
3. Bilgileri doldurun:
   - Ad Soyad
   - Kullanıcı Adı
   - Şifre
   - Rol
   - Bölüm
   - Vardiya
   - Durum (AKTİF/PASİF)
4. **💾 Kaydet** butonuna tıklayın

**Kullanıcı Düzenleme:**

1. Tabloda ilgili satırı bulun
2. Değişiklik yapın
3. **💾 Kaydet** butonuna tıklayın

### 10.2 Rol Yönetimi

**Yeni Rol Ekleme:**

1. **🎭 Rol Yönetimi** tab'ını açın
2. **➕ Yeni Rol Ekle** bölümünü genişletin
3. Rol adı ve açıklama girin
4. **Rolü Ekle** butonuna tıklayın

**Mevcut Roller:**
- Admin
- Yönetim
- Kalite Sorumlusu
- Vardiya Amiri
- Bölüm Sorumlusu
- Personel

### 10.3 Yetki Matrisi

**Rol Yetkilerini Düzenleme:**

1. **🔑 Yetki Matrisi** tab'ını açın
2. Rol seçin
3. Her modül için yetki seviyesi belirleyin:
   - **Yok:** Erişim yok
   - **Görüntüle:** Sadece görüntüleme
   - **Düzenle:** Tam erişim
4. **💾 Yetkilerini Kaydet** butonuna tıklayın

### 10.4 Departman Yönetimi

**Yeni Departman Ekleme:**

1. **🏭 Departman Yönetimi** tab'ını açın
2. **➕ Yeni Departman Ekle** bölümünü genişletin
3. Bilgileri girin:
   - Departman Adı
   - Bağlı Olduğu Ana Departman (opsiyonel)
   - Sıra No
   - Açıklama
4. **Departmanı Ekle** butonuna tıklayın

**Hiyerarşik Yapı Örneği:**

```
🏢 ÜRETİM
  └─ 👥 PATAŞU
  └─ 👥 EKLER
  └─ 👥 PAKETLEME

🏢 KALİTE
  └─ 👥 LABORATUVAR
  └─ 👥 NUMUNE ALMA
```

### 10.5 Yetki Gereksinimleri

- **Gerekli Yetki:** Düzenle
- **Erişebilen Roller:** Sadece Admin

---

## 11. Sık Sorulan Sorular

### 11.1 Genel Sorular

**S: Şifremi unuttum, ne yapmalıyım?**  
C: Sistem yöneticinize başvurun. Admin kullanıcısı Ayarlar > Personel Listesi'nden şifrenizi sıfırlayabilir.

**S: Modüle erişemiyorum, "Yetkiniz yok" hatası alıyorum?**  
C: Rolünüzün o modüle erişim yetkisi yok. Sistem yöneticinizden yetki talep edin.

**S: Kaydettiğim veri görünmüyor?**  
C: Sayfayı yenileyin (F5). Hala görünmüyorsa sistem yöneticinize bildirin.

### 11.2 Üretim Modülü

**S: Lot numarası zorunlu mu?**  
C: Evet, lot numarası olmadan kayıt yapılamaz.

**S: Geçmiş tarihli kayıt girebilir miyim?**  
C: Evet, tarih alanından istediğiniz tarihi seçebilirsiniz.

### 11.3 KPI Modülü

**S: Numune sayısı nasıl belirleniyor?**  
C: Ürün tanımlarında belirtilen numune sayısı otomatik gelir. Değiştirmek için Ayarlar > Ürün Tanımları'ndan düzenleyin.

**S: STT tarihi yanlış hesaplanıyor?**  
C: Ürün tanımlarındaki raf ömrü (gün) değerini kontrol edin.

### 11.4 GMP Denetimi

**S: Bugün hangi soruları cevaplamalıyım?**  
C: Sistem bugünün frekansına göre (Günlük/Haftalık/Aylık) otomatik soruları getirir.

**S: Kritik soruda fotoğraf yükleyemiyorum?**  
C: Fotoğraf formatı JPG, PNG veya JPEG olmalıdır. Dosya boyutu 5MB'dan küçük olmalıdır.

### 11.5 Temizlik Modülü

**S: Master planda değişiklik yapamıyorum?**  
C: Master plan düzenleme yetkisi sadece Admin ve Kalite Sorumlusu rollerinde vardır.

**S: ATP sonucu nereye girilir?**  
C: Saha Uygulama Çizelgesi'nde, durum "TAMAMLANDI" seçildiğinde verifikasyon alanı açılır.

### 11.6 Organizasyon Şeması

**S: PDF çıktısı alırken sayfa boş geliyor?**  
C: Tarayıcınızın pop-up engelleyicisini kapatın. Chrome kullanıyorsanız yazdırma penceresinde "Hedef" olarak "PDF olarak kaydet" seçin.

**S: Bazı personeller şemada görünmüyor?**  
C: Personelin departman ve pozisyon seviyesi bilgileri eksik olabilir. Ayarlar > Personel Listesi'nden kontrol edin.

---

## 📞 Destek

Sorunlarınız için:

- **Teknik Destek:** IT departmanınıza başvurun
- **Kullanım Soruları:** Kalite Sorumlusu veya Sistem Yöneticisi
- **Özellik Talepleri:** Yönetim ekibinize bildirin

---

**Son Güncelleme:** 22 Ocak 2026  
**Versiyon:** 1.0
