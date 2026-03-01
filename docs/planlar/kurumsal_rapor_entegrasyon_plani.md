# Kurumsal A4 Raporlama Standardizasyon Planı

Kullanıcının talebi üzerine, şu anda sadece **KPI (Kalite Analizi)** modülünde uygulanan *kurumsal, logolu, imza alanlı ve A4 yazdırılabilir HTML/PDF formatının*, sistemdeki diğer tüm operasyonel raporlama modüllerine de nasıl entegre edileceğini açıklayan mimari plandır. **Henüz kod yazılmamıştır, onay için sunulmaktadır.**

## 1. Mevcut Durum ve Sorun
Şu anda `ui/raporlama_ui.py` içindeki kurumsal rapor şablonu (HTML, CSS, A4 baskı ayarları, logolar ve imza satırları) sadece `_kpi_html_raporu_olustur` fonksiyonunun içine sıkıştırılmış (hardcoded) durumdadır. Diğer raporlar (Üretim, Hijyen, Temizlik) sadece Streamlit ekranındaki ham tablolar (`st.dataframe`) ve Excel indirme butonundan ibarettir.

## 2. Mimari Çözüm: Şablon Soyutlama (Template Abstraction)

Kurumsal kimliği tüm modüllere yaymak için **Merkezi Rapor Şablonu (Base Report Template)** oluşturulacaktır.

### 2.1. Merkezi Şablon Fonksiyonu
Yeni bir yardımcı fonksiyon olan `olustur_kurumsal_a4_rapor(baslik, alt_baslik, metadatalar, tablo_sutunlari, tablo_satirlari_html)` tasarlanacaktır. 
Bu fonksiyon değişmez HTML/CSS kodlarını içerecek ve modüller sadece kendi satır verilerini bu fonksiyona gönderecektir.

## 3. Modül Bazlı Uyarlama Planı

Hangi modülün Kurumsal A4 Raporuna nasıl yansıtılacağı aşağıda planlanmıştır:

### 🏭 Modül: Üretim ve Verimlilik Raporu
- **Başlık:** GÜNLÜK ÜRETİM VE FİRE BEYAN RAPORU (EKL-URE-001)
- **Satır Verileri:** 
  - Tarih, Saat, Vardiya, Personel.
  - Hedeflenen Ürün, Üretilen Miktar, Fire Miktarı, Lot Numarası.
- **Görsel Durum:** Fire oranı %5'in altındaysa yeşil (ONAY), üstündeyse kırmızı (DİKKAT) arka plan.
- **İmzalar:** Üretim Personeli, Vardiya Amiri, Üretim Müdürü.

### 🧼 Modül: Personel Hijyen Özeti
- **Başlık:** PERSONEL HİJYEN VE SAĞLIK KONTROL RAPORU (EKL-KYS-HIJ-002)
- **Satır Verileri:**
  - Bölüm / Departman.
  - Personel Adı, Vardiya, Saat.
  - Kontrol Durumu (Sorun Yok, Uygunsuzluk, Hastalık, vb.) ve Aksiyon.
- **Görsel Durum:** Uygunsuzluk olan satırlar kırmızı vurgulu.
- **İmzalar:** Kontrolör Personel, Kalite Sorumlusu, İnsan Kaynakları (Opsiyonel).

### 🧹 Modül: Temizlik Takip Raporu
- **Başlık:** ALAN VE EKİPMAN TEMİZLİK DOĞRULAMA RAPORU (EKL-KYS-TEM-003)
- **Satır Verileri:**
  - Odak Bölüm, Temizlenen Alan / Ekipman.
  - Saat, Vardiya, Gerçekleştiren Personel.
  - Kullanılan Kimyasal (varsa) ve Durum Onayı.
- **Görsel Durum:** Onaysız temizlik işlemleri vurgulu gösterilir.
- **İmzalar:** Temizlik Personeli, Vardiya Şefi, Kalite Kontrol Sorumlusu.

## 4. Kullanıcı Arayüzü (UI) Değişiklikleri
Tüm bu modüller için raporlama sekmesinin altına:
1. `st.dataframe` formatında hızlı önizleme.
2. 📥 Excel İndir butonu (Mevcut şekilde devam edecek).
3. 🖨️ **Yazdır / PDF Kaydet** butonunun (Javascript print() fonksiyonu ile) tüm bu raporların altına standart olarak yerleştirilmesi.

---

## Sonraki Adımlar

Bu plan kabul edildiğinde:
1. `raporlama_ui.py` içerisindeki HTML/CSS (Satır 165-237 arası) dışarı çıkarılarak merkezi fonksiyona dönüştürülecektir.
2. Üretim, Hijyen ve Temizlik ekranlarına JavaScript `print()` butonu eklenecektir.
3. Her modül kendi verisini işleyip HTML satır (tr/td) etiketleriyle bu ana fonksiyona besleyecektir.
