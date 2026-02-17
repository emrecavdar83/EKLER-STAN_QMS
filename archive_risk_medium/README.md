# 🏭 EKLERİSTAN QMS - Kalite Yönetim Sistemi

<div align="center">

![EKLERİSTAN Logo](https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png)

**Gıda Üretim Tesisleri için Kapsamlı Kalite Yönetim Sistemi**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

</div>

---

## 📋 İçindekiler

- [Genel Bakış](#-genel-bakış)
- [Özellikler](#-özellikler)
- [Teknoloji Stack](#-teknoloji-stack)
- [Kurulum](#-kurulum)
- [Hızlı Başlangıç](#-hızlı-başlangıç)
- [Modüller](#-modüller)
- [Dokümantasyon](#-dokümantasyon)
- [Katkıda Bulunma](#-katkıda-bulunma)
- [Lisans](#-lisans)

---

## 🎯 Genel Bakış

**EKLERİSTAN QMS**, gıda üretim tesisleri için özel olarak geliştirilmiş, BRC V9 standartlarına uyumlu, kapsamlı bir Kalite Yönetim Sistemidir. Streamlit tabanlı modern web arayüzü ile kolay kullanım sunar ve Supabase (PostgreSQL) bulut veritabanı ile güvenli veri yönetimi sağlar.

### 🎯 Temel Hedefler

- ✅ **Üretim Takibi**: Lot bazlı üretim kayıtları ve anlık raporlama
- ✅ **Kalite Kontrol**: Dinamik ürün parametreleri ile esnek analiz sistemi
- ✅ **GMP Denetimi**: BRC V9 uyumlu otomatik denetim planlaması
- ✅ **Hijyen Yönetimi**: Personel ve temizlik kontrol sistemleri
- ✅ **Raporlama**: Organizasyon şeması ve detaylı analiz raporları
- ✅ **Yetkilendirme**: Rol bazlı erişim kontrolü (RBAC)

---

## ✨ Özellikler

### 🏭 Üretim Yönetimi
- Lot bazlı üretim kayıt sistemi
- Vardiya takibi ve personel bazlı raporlama
- Gerçek zamanlı üretim özeti ve fire analizi
- Tarih bazlı filtreleme ve Excel export

### 🍩 KPI & Kalite Kontrol
- Ürün bazlı dinamik parametre tanımlama
- Çoklu numune analizi desteği
- Otomatik STT (Son Tüketim Tarihi) hesaplama
- Duyusal kontrol (tat, görüntü) entegrasyonu
- ONAY/RED karar mantığı

### 🛡️ GMP Denetimi
- BRC V9 standartlarına uyumlu soru havuzu
- Akıllı frekans algoritması (Günlük/Haftalık/Aylık)
- Lokasyon bazlı soru filtreleme
- Kritik bulgular için zorunlu fotoğraf ve açıklama
- Risk bazlı puanlama sistemi

### 🧼 Personel Hijyen Kontrolü
- Vardiya ve bölüm bazlı personel takibi
- Akıllı durum tespiti (Gelmedi, Sağlık Riski, Hijyen Uygunsuzluk)
- Dinamik sebep ve aksiyon tanımlama
- Toplu kayıt sistemi

### 🧹 Temizlik & Sanitasyon
- Master temizlik planı yönetimi
- Kat > Bölüm > Hat > Ekipman hiyerarşisi
- Kimyasal envanter yönetimi (MSDS/TDS)
- Validasyon ve verifikasyon takibi
- ATP/Swap test entegrasyonu

### 📊 Kurumsal Raporlama
- Dinamik organizasyon şeması (Graphviz)
- Hiyerarşik departman yapısı (sınırsız derinlik)
- PDF ve Liste formatı çıktılar
- Pozisyon seviyesi bazlı görünüm
- A4 yazdırma optimizasyonu

### ⚙️ Sistem Yönetimi
- Rol bazlı yetkilendirme (RBAC)
- Dinamik departman yönetimi
- Kullanıcı ve yetki matrisi
- Ürün ve parametre tanımları
- Kimyasal envanter yönetimi

---

## 🛠️ Teknoloji Stack

| Kategori | Teknoloji |
|----------|-----------|
| **Frontend** | Streamlit 1.x |
| **Backend** | Python 3.8+ |
| **Veritabanı** | PostgreSQL (Supabase) / SQLite (Yerel) |
| **ORM** | SQLAlchemy |
| **Görselleştirme** | Graphviz, Pandas |
| **PDF Export** | FPDF |
| **Deployment** | Streamlit Cloud |

### Bağımlılıklar

```
streamlit
pandas
sqlalchemy
fpdf
openpyxl
psycopg2-binary
pytz
graphviz
```

---

## 📦 Kurulum

### Ön Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- Git

### Yerel Kurulum

1. **Projeyi Klonlayın**
```bash
git clone https://github.com/emrecavdar83/EKLER-STAN_QMS.git
cd EKLER-STAN_QMS
```

2. **Bağımlılıkları Yükleyin**
```bash
pip install -r requirements.txt
```

3. **Veritabanını Başlatın**
```bash
# SQLite otomatik oluşturulur, manuel kurulum gerekmez
```

4. **Uygulamayı Çalıştırın**
```bash
streamlit run app.py
```

5. **Tarayıcınızda Açın**
```
http://localhost:8501
```

### Cloud Deployment (Supabase + Streamlit Cloud)

1. **Supabase Projesi Oluşturun**
   - [Supabase Dashboard](https://supabase.com/dashboard) → Yeni Proje
   - PostgreSQL bağlantı URL'sini kopyalayın

2. **SQL Migration'ları Çalıştırın**
   - Supabase SQL Editor → `sql/supabase_personel_org_restructure.sql` dosyasını çalıştırın
   - Diğer migration dosyalarını sırayla uygulayın

3. **Streamlit Cloud'a Deploy Edin**
   - [Streamlit Cloud](https://share.streamlit.io/) → New App
   - GitHub repo'nuzu bağlayın
   - Secrets ekleyin:
     ```toml
     [secrets]
     DB_URL = "postgresql://user:pass@host:5432/database"
     ```

4. **Deploy Edin ve Test Edin**

---

## 🚀 Hızlı Başlangıç

### İlk Giriş

1. Uygulamayı başlatın: `streamlit run app.py`
2. Varsayılan kullanıcı ile giriş yapın:
   - **Kullanıcı Adı:** `Admin`
   - **Şifre:** `12345`

### İlk Üretim Kaydı

1. Sol menüden **🏭 Üretim Girişi** seçin
2. Tarih, vardiya ve ürün bilgilerini girin
3. Lot numarası ve miktar bilgilerini ekleyin
4. **💾 Kaydı Onayla** butonuna tıklayın

### Organizasyon Şeması Görüntüleme

1. **📊 Kurumsal Raporlama** → **👥 Personel Organizasyon Şeması**
2. Görünüm formatını seçin (Hiyerarşik / Liste)
3. PDF çıktısı almak için **PDF Çıktısı (Yazdırma)** seçin

---

## 📚 Modüller

### 1. 🏭 Üretim Girişi
Lot bazlı üretim kayıtları, vardiya takibi, üretim özeti raporları.

### 2. 🍩 KPI & Kalite Kontrol
Dinamik ürün parametreleri, çoklu numune analizi, ONAY/RED karar sistemi.

### 3. 🛡️ GMP Denetimi
BRC V9 uyumlu denetim, akıllı frekans algoritması, kritik bulgu yönetimi.

### 4. 🧼 Personel Hijyen
Vardiya bazlı personel kontrolü, durum tespiti, aksiyon takibi.

### 5. 🧹 Temizlik Kontrol
Master plan yönetimi, kimyasal envanter, validasyon/verifikasyon.

### 6. 📊 Kurumsal Raporlama
Organizasyon şeması, hiyerarşik raporlar, PDF export.

### 7. ⚙️ Ayarlar
Kullanıcı yönetimi, RBAC, departman yapısı, sistem konfigürasyonu.

---

## 📖 Dokümantasyon

Detaylı dokümantasyon için `docs/` klasörüne bakın:

- **[Kullanıcı Kılavuzu](docs/KULLANICI_KILAVUZU.md)** - Modül bazlı kullanım rehberi
- **[Teknik Dokümantasyon](docs/TEKNIK_DOKUMANTASYON.md)** - Mimari, veritabanı, API referansı
- **[Test Senaryoları](docs/TEST_SENARYOLARI.md)** - Manuel test checklist'leri
- **[Veritabanı Şeması](docs/VERITABANI_SEMASI.md)** - Tablo yapıları ve ilişkiler

---

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen aşağıdaki adımları izleyin:

1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/YeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik: XYZ'`)
4. Branch'inizi push edin (`git push origin feature/YeniOzellik`)
5. Pull Request oluşturun

### Geliştirme Kuralları

- Türkçe kod yorumları kullanın
- PEP 8 standartlarına uyun
- Her yeni özellik için test senaryosu ekleyin
- Dokümantasyonu güncel tutun

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

---

## 👥 İletişim

**Proje Sahibi:** Emre ÇAVDAR  
**Şirket:** EKLERİSTAN Gıda San. ve Tic. A.Ş.  
**Website:** [www.ekleristan.com](https://www.ekleristan.com)

---

## 🙏 Teşekkürler

- Streamlit ekibine harika framework için
- Supabase ekibine güvenilir veritabanı çözümü için
- Tüm katkıda bulunanlara

---

<div align="center">

**⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!**

Made with ❤️ by EKLERİSTAN Team

</div>