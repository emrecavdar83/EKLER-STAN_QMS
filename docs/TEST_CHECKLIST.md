# ✅ EKLERİSTAN QMS - Test Checklist

**Proje:** EKLERİSTAN QMS  
**Test Tarihi:** _____ / _____ / _____  
**Test Eden:** _____________________________  
**Ortam:** ☐ Yerel  ☐ Cloud

---

## Test Durumu Göstergeleri

- ✅ **BAŞARILI** - Test geçti
- ❌ **BAŞARISIZ** - Test başarısız, hata var
- ⚠️ **UYARI** - Çalışıyor ama iyileştirme gerekli
- ⏭️ **ATLANDI** - Test yapılmadı

---

## 1. GİRİŞ/ÇIKIŞ TESTLERİ

### TC-001: Admin Başarılı Giriş
**Öncelik:** ⭐⭐⭐ Kritik

- [ ] 1. Uygulamayı aç → Giriş ekranı görünür
- [ ] 2. Kullanıcı: "Admin" seç → Dropdown'da seçili
- [ ] 3. Şifre: "12345" gir → Şifre gizli görünür
- [ ] 4. "Giriş Yap" tıkla → Ana sayfa açılır
- [ ] 5. Sol üstte "👤 Admin" görünür → Kullanıcı adı doğru

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-002: Hatalı Şifre Kontrolü
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Kullanıcı: "Admin" seç → Seçili
- [ ] 2. Şifre: "yanlisşifre" gir → Girdi kabul edilir
- [ ] 3. "Giriş Yap" tıkla → Hata mesajı: "❌ Hatalı Şifre!"
- [ ] 4. Giriş ekranında kalınır → Ana sayfaya geçilmez

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-003: Çıkış Yapma
**Öncelik:** ⭐ Orta

- [ ] 1. Admin olarak giriş yap → Ana sayfa açılır
- [ ] 2. Sol menüde "Çıkış Yap" tıkla → Giriş ekranına dönülür
- [ ] 3. Tarayıcı geri tuşuna bas → Giriş ekranında kalınır

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## 2. ÜRETİM MODÜLÜ TESTLERİ

### TC-010: Yeni Üretim Kaydı Ekleme
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. "🏭 Üretim Girişi" modülünü aç → Form görünür
- [ ] 2. Tarih: Bugün seç → Tarih seçili
- [ ] 3. Vardiya: "GÜNDÜZ VARDİYASI" seç → Seçili
- [ ] 4. Ürün: "Çikolatalı Ekler" seç → Seçili
- [ ] 5. Lot No: "TEST001" gir → Girdi kabul edilir
- [ ] 6. Miktar: 1000 gir → Sayı kabul edilir
- [ ] 7. Fire: 50 gir → Sayı kabul edilir
- [ ] 8. Notlar: "Test kaydı" gir → Metin kabul edilir
- [ ] 9. "💾 Kaydı Onayla" tıkla → Başarı mesajı görünür
- [ ] 10. Sayfa yenilenir → Kayıt listede görünür

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-011: Lot No Zorunluluk Kontrolü
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Form alanlarını doldur → Tamamlandı
- [ ] 2. Lot No alanını BOŞ bırak → Boş
- [ ] 3. "💾 Kaydı Onayla" tıkla → Uyarı: "Lot No Giriniz!"
- [ ] 4. Kayıt eklenmez → Veritabanında yok

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-012: Üretim Özeti Doğrulama
**Öncelik:** ⭐ Orta

- [ ] 1. 2 farklı üretim kaydı ekle → Eklendi
- [ ] 2. Tarih filtresinde bugünü seç → Seçili
- [ ] 3. Özet tabloyu kontrol et → 2 satır görünür
- [ ] 4. Toplam Miktar metriğini kontrol et → Doğru toplam
- [ ] 5. Toplam Fire metriğini kontrol et → Doğru toplam
- [ ] 6. Net Üretim = Miktar - Fire → Hesaplama doğru

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## 3. KPI MODÜLÜ TESTLERİ

### TC-020: Ürün Seçimi ve Parametre Yükleme
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. "🍩 KPI & Kalite Kontrol" aç → Modül açılır
- [ ] 2. Ürün: "Çikolatalı Ekler" seç → Seçili
- [ ] 3. Sistem bilgilerini kontrol et → Raf ömrü, STT, Numune sayısı görünür
- [ ] 4. Parametre alanlarını kontrol et → Brix, pH, Ağırlık vb. görünür

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-021: Çoklu Numune Girişi
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Ürün seç (Numune sayısı: 3) → Form açılır
- [ ] 2. Lot No: "TEST002" gir → Kabul edilir
- [ ] 3. STT checkbox işaretle → İşaretli
- [ ] 4. Numune #1 değerlerini gir → Kabul edilir
- [ ] 5. Numune #2 değerlerini gir → Kabul edilir
- [ ] 6. Numune #3 değerlerini gir → Kabul edilir
- [ ] 7. Tat: "Uygun" seç → Seçili
- [ ] 8. Görüntü: "Uygun" seç → Seçili
- [ ] 9. "✅ Analizi Kaydet" tıkla → Başarı mesajı
- [ ] 10. Karar: "ONAY" olmalı → Doğru karar

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-022: Karar Mantığı (RED)
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Tüm alanları doldur → Tamamlandı
- [ ] 2. Tat: "Uygun Değil" seç → Seçili
- [ ] 3. Görüntü: "Uygun" seç → Seçili
- [ ] 4. Kaydet → Başarılı
- [ ] 5. Karar: "RED" olmalı → Doğru karar

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## 4. GMP DENETİMİ TESTLERİ

### TC-030: Frekans Algoritması Kontrolü
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Modülü aç → Açılır
- [ ] 2. Bugünün frekansını kontrol et → GÜNLÜK her zaman görünür
- [ ] 3. Eğer Pazartesi ise → HAFTALIK de görünür
- [ ] 4. Eğer ayın 1'i ise → AYLIK da görünür

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-031: Kritik Bulgu Fotoğraf Zorunluluğu
**Öncelik:** ⭐⭐⭐ Kritik

- [ ] 1. Bölüm seç → Seçili
- [ ] 2. Risk 3 (Kritik) soru bul → Bulundu
- [ ] 3. Durum: "UYGUN DEĞİL" seç → Seçili
- [ ] 4. Fotoğraf yükleme alanı görünür → Görünür
- [ ] 5. Fotoğraf YÜKLEMEDEN kaydet → Hata: "Fotoğraf zorunlu!"
- [ ] 6. Fotoğraf yükle → Yüklendi
- [ ] 7. Açıklama gir → Girildi
- [ ] 8. Kaydet → Başarılı

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-032: Lokasyon Bazlı Soru Filtreleme
**Öncelik:** ⭐ Orta

- [ ] 1. Bölüm: "Üretim Alanı" seç → Seçili
- [ ] 2. Soru listesini kontrol et → Sadece Üretim'e ait sorular
- [ ] 3. Bölüm: "Depo" seç → Seçili
- [ ] 4. Soru listesi değişir → Sadece Depo'ya ait sorular

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## 5. PERSONEL HİJYEN TESTLERİ

### TC-040: Vardiya Bazlı Personel Listeleme
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Modülü aç → Açılır
- [ ] 2. Vardiya: "GÜNDÜZ VARDİYASI" seç → Seçili
- [ ] 3. Personel listesi görünür → Sadece gündüz vardiyası personeli
- [ ] 4. Bölüm: "Üretim" seç → Seçili
- [ ] 5. Liste daralır → Sadece Üretim personeli

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-041: Sorunlu Personel Detay Girişi
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Bir personel için "Gelmedi" seç → Seçili
- [ ] 2. Detay bölümü açılır → Sebep ve Aksiyon alanları görünür
- [ ] 3. Sebep: "Raporlu" seç → Seçili
- [ ] 4. Aksiyon: "İK Bilgilendirildi" seç → Seçili
- [ ] 5. Kaydet → Başarılı

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## 6. TEMİZLİK KONTROL TESTLERİ

### TC-050: Saha Uygulama Kaydı
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. "Saha Uygulama Çizelgesi" tab'ı aç → Açılır
- [ ] 2. Kat: "Zemin Kat" seç → Seçili
- [ ] 3. Temizlik görevleri listelenir → Liste görünür
- [ ] 4. İlk görev: "TAMAMLANDI" seç → Seçili
- [ ] 5. ATP sonucu gir: "120" → Kabul edilir
- [ ] 6. "💾 Kayıtları İşle" tıkla → Başarılı

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

![alt text](image.png)_________________________________

---

## 7. RAPORLAMA TESTLERİ

### TC-060: Hiyerarşik Organizasyon Şeması
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. "Personel Organizasyon Şeması" seç → Seçili
- [ ] 2. Görünüm: "Hiyerarşik Görünüm" seç → Graphviz şeması görünür
- [ ] 3. Yönetim Kurulu en üstte → Doğru konum
- [ ] 4. Genel Müdür altında → Doğru hiyerarşi
- [ ] 5. Departmanlar doğru sırada → Doğru yapı

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-061: PDF Çıktısı
**Öncelik:** ⭐ Orta

- [ ] 1. Görünüm: "PDF Çıktısı" seç → Yazdırma penceresi açılır
- [ ] 2. Hedef: "PDF olarak kaydet" seç → Seçili
- [ ] 3. Kaydet → PDF indirilir
- [ ] 4. PDF'i aç → A4 yatay, tüm personel görünür

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-062: Eksik Verili Personel Görünümü
**Öncelik:** ⭐ Orta

- [ ] 1. Ayarlar > Personel Listesi aç → Açılır
- [ ] 2. Yeni personel ekle, departman BOŞ bırak → Eklenir
- [ ] 3. Organizasyon Şeması'na dön → Açılır
- [ ] 4. Yeni personel "Tanımsız" altında görünür → Görünür (kaybolmaz)

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## 8. RBAC TESTLERİ

### TC-070: Admin Tüm Modüllere Erişim
**Öncelik:** ⭐⭐⭐ Kritik

- [ ] 1. Admin olarak giriş yap → Giriş başarılı
- [ ] 2. Her modülü sırayla aç → Tümü açılır, hata yok
- [ ] 3. Ayarlar modülünü aç → Açılır
- [ ] 4. Yetki Matrisi'ni düzenle → Düzenlenebilir

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-071: Personel Rol Kısıtlaması
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Personel rolünde kullanıcı oluştur → Oluşturuldu
- [ ] 2. Bu kullanıcı ile giriş yap → Giriş başarılı
- [ ] 3. Ayarlar modülünü açmaya çalış → Hata: "Yetkiniz yok"
- [ ] 4. Üretim modülünü açmaya çalış → Hata: "Yetkiniz yok"

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-072: Bölüm Sorumlusu Ürün Filtreleme
**Öncelik:** ⭐ Orta

- [ ] 1. Bölüm Sorumlusu (Pataşu) ile giriş yap → Giriş başarılı
- [ ] 2. Üretim Girişi modülünü aç → Açılır
- [ ] 3. Ürün dropdown'ını kontrol et → Sadece Pataşu ürünleri
- [ ] 4. Ekler ürünleri görünmez → Filtrelenmiş

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## 9. VERİTABANI TESTLERİ

### TC-080: Supabase Bağlantı
**Öncelik:** ⭐⭐⭐ Kritik

- [ ] 1. Streamlit Cloud'da uygulamayı aç → Açılır
- [ ] 2. Giriş yap → Başarılı
- [ ] 3. Personel listesini görüntüle → Supabase'den veri gelir
- [ ] 4. Yeni kayıt ekle → Supabase'e yazılır
- [ ] 5. Supabase Table Editor'de kontrol et → Kayıt görünür

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-081: Cache Invalidation
**Öncelik:** ⭐ Orta

- [ ] 1. Üretim kaydı ekle → Eklendi
- [ ] 2. Sayfa yenilenmeden liste kontrol et → Yeni kayıt görünür (cache temizlendi)

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

### TC-082: Transaction Bütünlüğü
**Öncelik:** ⭐⭐ Yüksek

- [ ] 1. Çoklu kayıt işlemi başlat → Başladı
- [ ] 2. Ortada hata oluştur (ağ kes) → Hata oluştu
- [ ] 3. Veritabanını kontrol et → Kısmi kayıt YOK (rollback)

**Sonuç:** ☐ ✅ ☐ ❌ ☐ ⚠️ ☐ ⏭️  
**Notlar:** _____________________________________________

---

## TEST ÖZET TABLOSU

| Kategori | Toplam | ✅ Başarılı | ❌ Başarısız | ⚠️ Uyarı | ⏭️ Atlanan |
|----------|--------|-------------|--------------|----------|-----------|
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

---

## BAŞARI ORANI

**Hesaplama:** (Başarılı / Toplam) × 100 = _________%

**Geçme Kriteri:** %90 (23/25 test başarılı)

**Durum:** ☐ GEÇTİ  ☐ KALDI

---

## KRİTİK HATALAR

| Test ID | Açıklama | Öncelik | Durum |
|---------|----------|---------|-------|
| TC-___ | _________________________ | ⭐⭐⭐ | ☐ Açık ☐ Kapalı |
| TC-___ | _________________________ | ⭐⭐⭐ | ☐ Açık ☐ Kapalı |
| TC-___ | _________________________ | ⭐⭐ | ☐ Açık ☐ Kapalı |

---

## ONAY

**Test Lideri:** _____________________________  
**Tarih:** _____ / _____ / _____  
**İmza:** _____________________________

---

**EKLERİSTAN QMS - Test Checklist v1.0**  
**Toplam Test:** 25 | **Sayfa:** 1/1
