# KPI Kalite Kontrol Raporlama Formatı Planı

Bu döküman, mevcut `urun_kpi_kontrol` tablosundaki verilere dayanarak, denetimlerde (ISO, BRC, IFS) sunulabilecek kurumsal, okunaklı ve detaylı bir Kalite Kontrol (KPI) Raporu'nun formatını planlamaktadır. **Bu aşamada sadece planlama yapılmıştır, kod yazılmamıştır.**

## 1. Raporun Amacı ve Hedef Kitlesi
- **Amaç:** Üretilen ürünlerin kalite standartlarına uyumunu izlemek, sapmaları tespit etmek ve gıda güvenliği zincirindeki tüm detayları (lot, STT, sıcaklık ölçümleri, duyusal analiz) tek bir dökümanda şeffaf bir şekilde sunmak.
- **Hedef Kitle:** Kalite Güvence Yönetimi, Dış Denetçiler (BRCGS, IFS), Vardiya Amirleri, Üst Yönetim.

## 2. Rapor Mimarisi ve Sayfa Düzeni (A4 / Web Uyumlu)

Rapor, hem web ortamında (Streamlit) interaktif bir yapıda hem de PDF/HTML formatında yazdırılabilir dikey A4 düzeninde tasarlanacaktır.

### 2.1. Kurumsal Başlık (Header)
- **Sol Üst:** Ekleristan QMS Logosu
- **Orta:** KALİTE KONTROL ve ÜRÜN ANALİZ RAPORU (Doküman No: EKL-KYS-KPI-002)
- **Sağ Üst:** Rapor Oluşturma Tarih/Saati, Raporu Alan Personel

### 2.2. Filtre ve Kapsam Bilgileri
- **Dönem:** [Başlangıç Tarihi] – [Bitiş Tarihi]
- **Ürün:** [Tümü veya Seçilen Ürün]
- **Vardiya / Personel:** [Filtre koşulları]

### 2.3. Üst Düzey Yönetici Özeti (Dashboard Kartları)
Raporun en üstünde hızlı bir durum kontrolü (Health Check):
- **Toplam İncelenen Lot / Numune:** (Sayı)
- **Kalite Onay Oranı:** (Örn: %98.5) 🟢
- **Reddedilen / Uygunsuz Ürün Sayısı:** (Sayı) 🔴
- **Ortalama Ölçüm Sapması:** (Grameraj veya Kalibrasyon farkları)

---

## 3. Detaylı Kayıt Satırları (Veri Formatı)

Her bir kalite kontrol kaydı (`urun_kpi_kontrol` tablosundaki bir satır) dar bir tablo formatında veya "Kart" formatında alt alta listelenecektir.

### 📍 Kart Yapısı / Tablo Sütunları
*Her kayıt bloğunda zorunlu olarak bulunacak alanlar:*

1. **İzlenebilirlik Verileri:** 
   - Tarih, Saat, Vardiya, Personel (Kullanıcı Tarafından).
   - Ürün Adı, Lot Numarası, STT (Son Tüketim Tarihi).
2. **Ölçüm Değerleri (Fiziksel / Kimyasal):**
   - Numune No
   - Ölçüm 1, Ölçüm 2, Ölçüm 3
   - *Planlanan Özellik:* Bu ölçümlerin altına küçük bir satırla "Standart Limitler" (Örn: 50g-55g) ve "Ortalama Değer" hesaplaması eklenecektir.
3. **Duyusal ve Görsel Analiz (Organoleptik):**
   - Tat / Koku Durumu (Uygun / Değil)
   - Renk / Görüntü Durumu (Uygun / Değil)
4. **Nihai Karar ve Açıklama:**
   - **🔴 RED** veya **🟢 ONAY** büyük harf ve ikonlarla.
   - Denetçi / Kalite uzmanı notları (Açık ve okunaklı, text wrap yapılarak).
5. **Görsel Kanıt:**
   - Eğer `fotograf_yolu` veya `fotograf_b64` doluysa, kaydın sağ köşesine iliştirilmiş küçük bir kanıt fotoğrafı (Tıklanınca büyüyecek veya printte net görünecek boyutta).

---

## 4. Alt Bilgi ve Onay Mekanizması (Footer)

Dökümanın en altında, dijital imza yerine geçen loglanmış personel bilgileriyle birlikte matbu imza kutucukları.

- **Fiziksel Denetim Çıktısı İçin Onay Çubuğu:**
   - [ ] Kalite Analisti Adı / İmza
   - [ ] Vardiya Amiri Adı / İmza
   - [ ] Kalite Müdürü Adı / İmza

- **Dipnot:** ISO 9001, BRCGS ve IFS standartları gereği bu raporun sonradan değiştirilemez olduğu (Immutable Audit Log) bilgisi.

---

## 5. Dışa Aktarım (Export) Yetenekleri

- **Dinamil HTML / PDF:** Tarayıcının 'Yazdır' özelliğiyle A4'e tam sığan, renkli ancak print dostu (Color-adjusted) CSS tasarımı.
- **Ham Veri (Excel):** Gelişmiş veri analizi için, resimler hariç tüm metrikleri sütunlara ayrılmış, lot bazlı gruplanmış `xlsx` dökümü.

---

## 6. Sonraki Adımlar (Uygulama - *Beklemede*)

Bu format tarafınızdan **onaylandığında**, `raporlama_ui.py` içerisindeki mevcut `_kpi_html_raporu_olustur` veya yeni bir fonksiyon yazılarak bu veri mimarisi HTML/Streamlit koduna dönüştürülecektir. 

Lütfen planda eklenmesini veya çıkarılmasını istediğiniz bir metrik varsa belirtiniz.
