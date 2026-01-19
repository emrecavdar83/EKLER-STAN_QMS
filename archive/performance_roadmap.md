# 🚀 Performans Optimizasyon Yol Haritası

Bu belge, Ekleristan QMS uygulamasını hızlandırmak ve daha ölçeklenebilir hale getirmek için belirlenen stratejileri içerir.

## 🛠️ Kısa Vadeli Adımlar (Hızlı Kazanımlar)

### 1. Akıllı Önbellekleme (Caching)
- **Hedef:** Veritabanı yükünü azaltmak.
- **Eylem:** SQL sorgularını `@st.cache_data(ttl=60)` ile sarmalamak. `veri_getir` fonksiyonlarının tamamını bu yapıya geçirmek.
- **Kritik Dosya:** [app.py](file:///c:/Users/GIDA%20M%C3%9CHEND%C4%B0S%C4%B0/OneDrive/Desktop/EKLER%C4%B0STAN_QMS/app.py)

### 2. Veritabanı İndeksleme
- **Hedef:** Sorgu hızını milisaniyelere düşürmek.
- **Eylem:** Sık kullanılan filtreleme sütunlarına (`personel_id`, `tarih`, `bolum_adi`) SQL INDEX eklemek.
- **Kritik Dosya:** `database_indexes.sql` (oluşturulacak veya güncellenecek).

### 3. Streamlit Fragments (@st.fragment)
- **Hedef:** Rerun sürelerini kısaltmak.
- **Eylem:** Sadece veri girişi yapılan formları veya dinamik güncellenen widget'ları `@st.fragment` içine almak. Bu sayede tüm sayfa yerine sadece ilgili bileşen yenilenir.

---

## 🏗️ Orta ve Uzun Vadeli Adımlar (Mimari Gelişim)

### 4. Modüler Mimari (Modülleri Ayırma)
- **Hedef:** Kod okunabilirliğini artırmak ve sadece ihtiyaç duyulan kodun yüklenmesini sağlamak.
- **Eylem:** 1300 satırlık `app.py` içindeki ana fonksiyonları (`main_app` altındaki bölümleri) `src/modules/` dizini altına taşımak.
- **Yapı:**
    - `src/modules/üretim.py`
    - `src/modules/raporlama.py`
    - `src/modules/ayarlar.py`

### 5. Veri Yükleme Optimizasyonu (Fetch Policy)
- **Hedef:** Bellek kullanımını minimize etmek.
- **Eylem:** `SELECT *` kullanımını bırakıp, her ekran için sadece gerekli olan kolonları çekmek (`SELECT isim, tarih ...`).

---

> [!IMPORTANT]
> Bu adımlar uygulamaya geçilirken önce **Caching** ve **İndeksleme** ile başlanması, en hızlı ve görünür performansı sağlayacaktır.
