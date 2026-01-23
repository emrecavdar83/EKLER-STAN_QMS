# ✅ EKLERİSTAN QMS - Test Senaryoları

## İçindekiler

1. [Test Yaklaşımı](#1-test-yaklaşımı)
2. [Test Ortamı Hazırlığı](#2-test-ortamı-hazırlığı)
3. [Giriş/Çıkış Testleri](#3-girişçıkış-testleri)
4. [Üretim Modülü Testleri](#4-üretim-modülü-testleri)
5. [KPI Modülü Testleri](#5-kpi-modülü-testleri)
6. [GMP Denetimi Testleri](#6-gmp-denetimi-testleri)
7. [Personel Hijyen Testleri](#7-personel-hijyen-testleri)
8. [Temizlik Kontrol Testleri](#8-temizlik-kontrol-testleri)
9. [Raporlama Testleri](#9-raporlama-testleri)
10. [RBAC Testleri](#10-rbac-testleri)
11. [Veritabanı Testleri](#11-veritabanı-testleri)
12. [Test Raporu Şablonu](#12-test-raporu-şablonu)

---

## 1. Test Yaklaşımı

### 1.1 Test Türleri

- **Fonksiyonel Testler:** Modül özelliklerinin çalışması
- **Yetki Testleri:** RBAC sisteminin doğruluğu
- **Veri Bütünlüğü:** Veritabanı kayıtlarının tutarlılığı
- **UI/UX Testleri:** Kullanıcı arayüzü ve deneyimi

### 1.2 Test Seviyesi

| Seviye | Açıklama | Kapsam |
|--------|----------|--------|
| **Kritik** | Sistem çalışmaz | Giriş, veritabanı bağlantısı |
| **Yüksek** | Ana özellikler | Üretim kaydı, kalite analizi |
| **Orta** | Yardımcı özellikler | Raporlama, filtreleme |
| **Düşük** | UI iyileştirmeleri | Renk, düzen |

### 1.3 Test Durumu İşaretleme

- ✅ **BAŞARILI:** Test geçti
- ❌ **BAŞARISIZ:** Test başarısız, hata var
- ⚠️ **UYARI:** Çalışıyor ama iyileştirme gerekli
- ⏭️ **ATLANDI:** Test yapılmadı

---

## 2. Test Ortamı Hazırlığı

### 2.1 Ön Koşullar

**Yerel Test:**
- [ ] Python 3.8+ yüklü
- [ ] `pip install -r requirements.txt` çalıştırıldı
- [ ] Graphviz yüklü
- [ ] `ekleristan_local.db` mevcut veya oluşturulabilir

**Cloud Test:**
- [ ] Supabase projesi aktif
- [ ] SQL migration'lar çalıştırıldı
- [ ] Streamlit Cloud'da uygulama deploy edildi
- [ ] Secrets doğru yapılandırıldı

### 2.2 Test Verileri

**Kullanıcılar:**
- Admin (Şifre: 12345)
- Test Kullanıcısı (Rol: Personel)
- Test Kalite Sorumlusu (Rol: Kalite Sorumlusu)

**Ürünler:**
- Çikolatalı Ekler
- Vanilyalı Pataşu
- Kremalı Profiterol

**Departmanlar:**
- Üretim > Pataşu
- Üretim > Ekler
- Kalite > Laboratuvar

---

## 3. Giriş/Çıkış Testleri

### TC-001: Admin Başarılı Giriş

**Öncelik:** Kritik  
**Modül:** Giriş Ekranı

**Ön Koşullar:**
- Uygulama çalışıyor
- Tarayıcı açık

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Uygulamayı aç | Giriş ekranı görünür | [ ] |
| 2 | Kullanıcı: "Admin" seç | Dropdown'da seçili | [ ] |
| 3 | Şifre: "12345" gir | Şifre gizli görünür | [ ] |
| 4 | "Giriş Yap" tıkla | Ana sayfa açılır | [ ] |
| 5 | Sol üstte "👤 Admin" görünür | Kullanıcı adı doğru | [ ] |

**Sonuç:** ___________

---

### TC-002: Hatalı Şifre Kontrolü

**Öncelik:** Yüksek  
**Modül:** Giriş Ekranı

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Kullanıcı: "Admin" seç | Seçili | [ ] |
| 2 | Şifre: "yanlisşifre" gir | Girdi kabul edilir | [ ] |
| 3 | "Giriş Yap" tıkla | Hata mesajı: "❌ Hatalı Şifre!" | [ ] |
| 4 | Giriş ekranında kalınır | Ana sayfaya geçilmez | [ ] |

**Sonuç:** ___________

---

### TC-003: Çıkış Yapma

**Öncelik:** Orta  
**Modül:** Ana Sayfa

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Admin olarak giriş yap | Ana sayfa açılır | [ ] |
| 2 | Sol menüde "Çıkış Yap" tıkla | Giriş ekranına dönülür | [ ] |
| 3 | Tarayıcı geri tuşuna bas | Giriş ekranında kalınır | [ ] |

**Sonuç:** ___________

---

## 4. Üretim Modülü Testleri

### TC-010: Yeni Üretim Kaydı Ekleme

**Öncelik:** Yüksek  
**Modül:** 🏭 Üretim Girişi

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | "🏭 Üretim Girişi" modülünü aç | Form görünür | [ ] |
| 2 | Tarih: Bugün seç | Tarih seçili | [ ] |
| 3 | Vardiya: "GÜNDÜZ VARDİYASI" seç | Seçili | [ ] |
| 4 | Ürün: "Çikolatalı Ekler" seç | Seçili | [ ] |
| 5 | Lot No: "TEST001" gir | Girdi kabul edilir | [ ] |
| 6 | Miktar: 1000 gir | Sayı kabul edilir | [ ] |
| 7 | Fire: 50 gir | Sayı kabul edilir | [ ] |
| 8 | Notlar: "Test kaydı" gir | Metin kabul edilir | [ ] |
| 9 | "💾 Kaydı Onayla" tıkla | Başarı mesajı görünür | [ ] |
| 10 | Sayfa yenilenir | Kayıt listede görünür | [ ] |

**Sonuç:** ___________

---

### TC-011: Lot No Zorunluluk Kontrolü

**Öncelik:** Yüksek  
**Modül:** 🏭 Üretim Girişi

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Form alanlarını doldur | Tamamlandı | [ ] |
| 2 | Lot No alanını BOŞ bırak | Boş | [ ] |
| 3 | "💾 Kaydı Onayla" tıkla | Uyarı: "Lot No Giriniz!" | [ ] |
| 4 | Kayıt eklenmez | Veritabanında yok | [ ] |

**Sonuç:** ___________

---

### TC-012: Üretim Özeti Doğrulama

**Öncelik:** Orta  
**Modül:** 🏭 Üretim Girişi

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | 2 farklı üretim kaydı ekle | Eklendi | [ ] |
| 2 | Tarih filtresinde bugünü seç | Seçili | [ ] |
| 3 | Özet tabloyu kontrol et | 2 satır görünür | [ ] |
| 4 | Toplam Miktar metriğini kontrol et | Doğru toplam | [ ] |
| 5 | Toplam Fire metriğini kontrol et | Doğru toplam | [ ] |
| 6 | Net Üretim = Miktar - Fire | Hesaplama doğru | [ ] |

**Sonuç:** ___________

---

## 5. KPI Modülü Testleri

### TC-020: Ürün Seçimi ve Parametre Yükleme

**Öncelik:** Yüksek  
**Modül:** 🍩 KPI & Kalite Kontrol

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | "🍩 KPI & Kalite Kontrol" aç | Modül açılır | [ ] |
| 2 | Ürün: "Çikolatalı Ekler" seç | Seçili | [ ] |
| 3 | Sistem bilgilerini kontrol et | Raf ömrü, STT, Numune sayısı görünür | [ ] |
| 4 | Parametre alanlarını kontrol et | Brix, pH, Ağırlık vb. görünür | [ ] |

**Sonuç:** ___________

---

### TC-021: Çoklu Numune Girişi

**Öncelik:** Yüksek  
**Modül:** 🍩 KPI & Kalite Kontrol

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Ürün seç (Numune sayısı: 3) | Form açılır | [ ] |
| 2 | Lot No: "TEST002" gir | Kabul edilir | [ ] |
| 3 | STT checkbox işaretle | İşaretli | [ ] |
| 4 | Numune #1 değerlerini gir | Kabul edilir | [ ] |
| 5 | Numune #2 değerlerini gir | Kabul edilir | [ ] |
| 6 | Numune #3 değerlerini gir | Kabul edilir | [ ] |
| 7 | Tat: "Uygun" seç | Seçili | [ ] |
| 8 | Görüntü: "Uygun" seç | Seçili | [ ] |
| 9 | "✅ Analizi Kaydet" tıkla | Başarı mesajı | [ ] |
| 10 | Karar: "ONAY" olmalı | Doğru karar | [ ] |

**Sonuç:** ___________

---

### TC-022: Karar Mantığı (RED)

**Öncelik:** Yüksek  
**Modül:** 🍩 KPI & Kalite Kontrol

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Tüm alanları doldur | Tamamlandı | [ ] |
| 2 | Tat: "Uygun Değil" seç | Seçili | [ ] |
| 3 | Görüntü: "Uygun" seç | Seçili | [ ] |
| 4 | Kaydet | Başarılı | [ ] |
| 5 | Karar: "RED" olmalı | Doğru karar | [ ] |

**Sonuç:** ___________

---

## 6. GMP Denetimi Testleri

### TC-030: Frekans Algoritması Kontrolü

**Öncelik:** Yüksek  
**Modül:** 🛡️ GMP Denetimi

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Modülü aç | Açılır | [ ] |
| 2 | Bugünün frekansını kontrol et | GÜNLÜK her zaman görünür | [ ] |
| 3 | Eğer Pazartesi ise | HAFTALIK de görünür | [ ] |
| 4 | Eğer ayın 1'i ise | AYLIK da görünür | [ ] |

**Sonuç:** ___________

---

### TC-031: Kritik Bulgu Fotoğraf Zorunluluğu

**Öncelik:** Kritik  
**Modül:** 🛡️ GMP Denetimi

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Bölüm seç | Seçili | [ ] |
| 2 | Risk 3 (Kritik) soru bul | Bulundu | [ ] |
| 3 | Durum: "UYGUN DEĞİL" seç | Seçili | [ ] |
| 4 | Fotoğraf yükleme alanı görünür | Görünür | [ ] |
| 5 | Fotoğraf YÜKLEMEDEN kaydet | Hata: "Fotoğraf zorunlu!" | [ ] |
| 6 | Fotoğraf yükle | Yüklendi | [ ] |
| 7 | Açıklama gir | Girildi | [ ] |
| 8 | Kaydet | Başarılı | [ ] |

**Sonuç:** ___________

---

### TC-032: Lokasyon Bazlı Soru Filtreleme

**Öncelik:** Orta  
**Modül:** 🛡️ GMP Denetimi

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Bölüm: "Üretim Alanı" seç | Seçili | [ ] |
| 2 | Soru listesini kontrol et | Sadece Üretim'e ait sorular | [ ] |
| 3 | Bölüm: "Depo" seç | Seçili | [ ] |
| 4 | Soru listesi değişir | Sadece Depo'ya ait sorular | [ ] |

**Sonuç:** ___________

---

## 7. Personel Hijyen Testleri

### TC-040: Vardiya Bazlı Personel Listeleme

**Öncelik:** Yüksek  
**Modül:** 🧼 Personel Hijyen

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Modülü aç | Açılır | [ ] |
| 2 | Vardiya: "GÜNDÜZ VARDİYASI" seç | Seçili | [ ] |
| 3 | Personel listesi görünür | Sadece gündüz vardiyası personeli | [ ] |
| 4 | Bölüm: "Üretim" seç | Seçili | [ ] |
| 5 | Liste daralır | Sadece Üretim personeli | [ ] |

**Sonuç:** ___________

---

### TC-041: Sorunlu Personel Detay Girişi

**Öncelik:** Yüksek  
**Modül:** 🧼 Personel Hijyen

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Bir personel için "Gelmedi" seç | Seçili | [ ] |
| 2 | Detay bölümü açılır | Sebep ve Aksiyon alanları görünür | [ ] |
| 3 | Sebep: "Raporlu" seç | Seçili | [ ] |
| 4 | Aksiyon: "İK Bilgilendirildi" seç | Seçili | [ ] |
| 5 | Kaydet | Başarılı | [ ] |

**Sonuç:** ___________

---

## 8. Temizlik Kontrol Testleri

### TC-050: Saha Uygulama Kaydı

**Öncelik:** Yüksek  
**Modül:** 🧹 Temizlik Kontrol

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | "Saha Uygulama Çizelgesi" tab'ı aç | Açılır | [ ] |
| 2 | Kat: "Zemin Kat" seç | Seçili | [ ] |
| 3 | Temizlik görevleri listelenir | Liste görünür | [ ] |
| 4 | İlk görev: "TAMAMLANDI" seç | Seçili | [ ] |
| 5 | ATP sonucu gir: "120" | Kabul edilir | [ ] |
| 6 | "💾 Kayıtları İşle" tıkla | Başarılı | [ ] |

**Sonuç:** ___________

---

### TC-051: Master Plan Düzenleme

**Öncelik:** Orta  
**Modül:** 🧹 Temizlik Kontrol

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | "Master Plan Düzenleme" tab'ı aç | Açılır | [ ] |
| 2 | Tabloya yeni satır ekle | Eklenir | [ ] |
| 3 | Kat, Bölüm, Ekipman seç | Dropdown'lardan seçilir | [ ] |
| 4 | Kimyasal ve Yöntem seç | Seçilir | [ ] |
| 5 | "💾 Master Planı Güncelle" tıkla | Başarılı | [ ] |

**Sonuç:** ___________

---

## 9. Raporlama Testleri

### TC-060: Hiyerarşik Organizasyon Şeması

**Öncelik:** Yüksek  
**Modül:** 📊 Kurumsal Raporlama

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | "Personel Organizasyon Şeması" seç | Seçili | [ ] |
| 2 | Görünüm: "Hiyerarşik Görünüm" seç | Graphviz şeması görünür | [ ] |
| 3 | Yönetim Kurulu en üstte | Doğru konum | [ ] |
| 4 | Genel Müdür altında | Doğru hiyerarşi | [ ] |
| 5 | Departmanlar doğru sırada | Doğru yapı | [ ] |

**Sonuç:** ___________

---

### TC-061: PDF Çıktısı

**Öncelik:** Orta  
**Modül:** 📊 Kurumsal Raporlama

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Görünüm: "PDF Çıktısı" seç | Yazdırma penceresi açılır | [ ] |
| 2 | Hedef: "PDF olarak kaydet" seç | Seçili | [ ] |
| 3 | Kaydet | PDF indirilir | [ ] |
| 4 | PDF'i aç | A4 yatay, tüm personel görünür | [ ] |

**Sonuç:** ___________

---

### TC-062: Eksik Verili Personel Görünümü

**Öncelik:** Orta  
**Modül:** 📊 Kurumsal Raporlama

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Ayarlar > Personel Listesi aç | Açılır | [ ] |
| 2 | Yeni personel ekle, departman BOŞ bırak | Eklenir | [ ] |
| 3 | Organizasyon Şeması'na dön | Açılır | [ ] |
| 4 | Yeni personel "Tanımsız" altında görünür | Görünür (kaybolmaz) | [ ] |

**Sonuç:** ___________

---

## 10. RBAC Testleri

### TC-070: Admin Tüm Modüllere Erişim

**Öncelik:** Kritik  
**Modül:** Tüm Modüller

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Admin olarak giriş yap | Giriş başarılı | [ ] |
| 2 | Her modülü sırayla aç | Tümü açılır, hata yok | [ ] |
| 3 | Ayarlar modülünü aç | Açılır | [ ] |
| 4 | Yetki Matrisi'ni düzenle | Düzenlenebilir | [ ] |

**Sonuç:** ___________

---

### TC-071: Personel Rol Kısıtlaması

**Öncelik:** Yüksek  
**Modül:** Tüm Modüller

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Personel rolünde kullanıcı oluştur | Oluşturuldu | [ ] |
| 2 | Bu kullanıcı ile giriş yap | Giriş başarılı | [ ] |
| 3 | Ayarlar modülünü açmaya çalış | Hata: "Yetkiniz yok" | [ ] |
| 4 | Üretim modülünü açmaya çalış | Hata: "Yetkiniz yok" | [ ] |

**Sonuç:** ___________

---

### TC-072: Bölüm Sorumlusu Ürün Filtreleme

**Öncelik:** Orta  
**Modül:** 🏭 Üretim Girişi

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Bölüm Sorumlusu (Pataşu) ile giriş yap | Giriş başarılı | [ ] |
| 2 | Üretim Girişi modülünü aç | Açılır | [ ] |
| 3 | Ürün dropdown'ını kontrol et | Sadece Pataşu ürünleri | [ ] |
| 4 | Ekler ürünleri görünmez | Filtrelenmiş | [ ] |

**Sonuç:** ___________

---

## 11. Veritabanı Testleri

### TC-080: Supabase Bağlantı

**Öncelik:** Kritik  
**Modül:** Veritabanı

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Streamlit Cloud'da uygulamayı aç | Açılır | [ ] |
| 2 | Giriş yap | Başarılı | [ ] |
| 3 | Personel listesini görüntüle | Supabase'den veri gelir | [ ] |
| 4 | Yeni kayıt ekle | Supabase'e yazılır | [ ] |
| 5 | Supabase Table Editor'de kontrol et | Kayıt görünür | [ ] |

**Sonuç:** ___________

---

### TC-081: Cache Invalidation

**Öncelik:** Orta  
**Modül:** Veritabanı

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Üretim kaydı ekle | Eklendi | [ ] |
| 2 | Sayfa yenilenmeden liste kontrol et | Yeni kayıt görünür (cache temizlendi) | [ ] |

**Sonuç:** ___________

---

### TC-082: Transaction Bütünlüğü

**Öncelik:** Yüksek  
**Modül:** Veritabanı

**Test Adımları:**

| # | Adım | Beklenen Sonuç | Durum |
|---|------|----------------|-------|
| 1 | Çoklu kayıt işlemi başlat | Başladı | [ ] |
| 2 | Ortada hata oluştur (ağ kes) | Hata oluştu | [ ] |
| 3 | Veritabanını kontrol et | Kısmi kayıt YOK (rollback) | [ ] |

**Sonuç:** ___________

---

## 12. Test Raporu Şablonu

### Test Özeti

**Proje:** EKLERİSTAN QMS  
**Test Tarihi:** ___________  
**Test Eden:** ___________  
**Ortam:** Yerel / Cloud (seçiniz)

### Test Sonuçları

| Kategori | Toplam | Başarılı | Başarısız | Uyarı | Atlanan |
|----------|--------|----------|-----------|-------|---------|
| Giriş/Çıkış | 3 | ___ | ___ | ___ | ___ |
| Üretim | 3 | ___ | ___ | ___ | ___ |
| KPI | 3 | ___ | ___ | ___ | ___ |
| GMP | 3 | ___ | ___ | ___ | ___ |
| Hijyen | 2 | ___ | ___ | ___ | ___ |
| Temizlik | 2 | ___ | ___ | ___ | ___ |
| Raporlama | 3 | ___ | ___ | ___ | ___ |
| RBAC | 3 | ___ | ___ | ___ | ___ |
| Veritabanı | 3 | ___ | ___ | ___ | ___ |
| **TOPLAM** | **25** | ___ | ___ | ___ | ___ |

### Başarı Oranı

**Geçme Kriteri:** %90 (23/25 test başarılı)

**Hesaplama:** (Başarılı / Toplam) × 100 = ___________%

### Kritik Hatalar

| Test ID | Açıklama | Öncelik | Durum |
|---------|----------|---------|-------|
| TC-___ | ___________ | Kritik | Açık |
| TC-___ | ___________ | Yüksek | Açık |

### Öneriler

1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Onay

**Test Lideri:** ___________  
**Tarih:** ___________  
**İmza:** ___________

---

## 📞 Test Desteği

**Hata Bildirimi:**
- GitHub Issues: [github.com/emrecavdar83/EKLER-STAN_QMS/issues](https://github.com/emrecavdar83/EKLER-STAN_QMS/issues)

**Test Soruları:**
- Kalite Sorumlusu veya Sistem Yöneticisi

---

**Son Güncelleme:** 22 Ocak 2026  
**Versiyon:** 1.0
