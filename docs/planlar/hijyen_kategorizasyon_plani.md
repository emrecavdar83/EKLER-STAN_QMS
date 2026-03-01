# Personel Hijyen Modülü Dinamik Kategorizasyon Planı

Kullanıcının "Hijyen modülünde yeterince kategorizasyon olmalı ve bu dinamik hale gelmeli" tespiti üzerine, **Anayasa Madde 1 (Sıfır Hardcode Prensibi)** uyarınca hazırlanmış refactoring (iyileştirme) planıdır. (Sadece plandır, kod yazılmamıştır).

## 1. Mevcut Durum Analizi (Mimari İhlal Tespiti)
Sistem kaynak kodları (`ui/hijyen_ui.py` Satır 51-60 ve 157) taranmıştır. Mevcut yapıda "Uygunsuzluk Sebepleri" ve "Aksiyonlar" kodun içine tamamen gömülü (hardcoded) bir `dictionary` olarak yazılmış durumdadır:
```python
# YASAKLI PATTERN TESPİTİ (ui/hijyen_ui.py)
sebepler = {
    "Sağlık Riski": ["Seçiniz...", "Ateş", "İshal", "Öksürük", "Açık Yara", "Bulaşıcı Şüphe"],
    "Hijyen Uygunsuzluk": ["Seçiniz...", "Kirli Önlük", "Sakal Tıraşı", "Bone/Maske Eksik"]
}
```
Bu durum, yeni bir uyarı/kategori türü (Örn: "Takı takma") gerektiğinde sisteme mühendislik müdahalesi yapılmasını zorunlu kılar ve Anayasa'ya aykırıdır.

## 2. Mimari Çözüm (Veritabanı Katmanı)

Sisteme birbirine bağlı iki yeni konfigürasyon (ayarlar) tablosu eklenecektir. Böylece yönetim paneli üzerinden BRC'nin istediği kırılımlarda istenildiği kadar kategori açılabilir.

**Yeni Tablo 1: `ayarlar_hijyen_kategoriler`**
- `id` (PK)
- `kategori_adi` (Örn: Kişisel Hijyen, Kılık Kıyafet İhlali, Hastalık Durumu, Davranışsal)
- `aktif` (Boolean)

**Yeni Tablo 2: `ayarlar_hijyen_sebepler`**
- `id` (PK)
- `kategori_id` (FK -> ayarlar_hijyen_kategoriler)
- `sebep_adi` (Örn: Ojeli/Uzun Tırnak, Kirli Önlük, Açık Yara)
- `varsayilan_dof` (Örn: "Üretim alanından çıkarıldı", "Tutanak tutuldu") -> Operatörlere kolaylık sağlaması ve standardizasyon için.
- `aktif` (Boolean)

## 3. UI (Arayüz) Revizyonları

1. **Denetim Ekranı (`ui/hijyen_ui.py`):**
   - Kodun içindeki hardcoded sepet tamamen silinecek.
   - Personel denetlenirken "Durum Seçin" açılır listesi veritabanındaki `ayarlar_hijyen_kategoriler` tablosundan dolacak.
   - Seçilen durum kategorisine göre, alt "Neden/Sebep" sekmesi `ayarlar_hijyen_sebepler` tablosundan filtrelenecek.
   - Otomatik olarak "Varsayılan DÖF (Aksiyon)" kutusu önerilerek operatörün işi hızlandırılacak, dilerse üstüne ekleme yapabilecek.

2. **Yönetim Ekranı (`ui/ayarlar/hijyen_ayarlari_ui.py` - YENİ MODÜL):**
   - Sistem Temsilcisinin / Admin'in girdiği (Ürün Ekleme ekranı gibi) yeni bir yönetim ekranı yazılacak.
   - Bu ekrandan BRC denetçisinin beklentisine göre istenildiği kadar kategori ("Dışarıdan Yiyecek Getirme", "Steril Olmayan Eldiven Kullanımı" vs.) eklenebilecektir.

## 4. Uygulama Rotası (Roadmap)
Bu plan onaylandığında şu sıra ile geliştirme yapılacaktır:
1. `sqlite` (lokal) ve `Supabase` (bulut) veritabanlarında `ayarlar_hijyen_*` tabloları SQL ile oluşturulacak.
2. `ui/ayarlar` altına yönetim paneli eklenecek ve `app.py`'ye bağlanacak.
3. Mevcut `hijyen_ui.py` Anayasa'ya uygun ve DB okumalı olarak refactor edilecek.
4. Sync scriptleri (`quick_push_all.py` vb.) yeni tabloları buluta taşıyacak şekilde güncellenecektir.
