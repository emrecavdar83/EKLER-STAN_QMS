# 🔴 AÇIK VAKALAR (Audit Takibi)

Bu döküman, mühürlenmeyi bekleyen açık teknik konuları ve riskleri içerir.

### 📍 VAKA-025: Plaintext Şifre Görünürlüğü
- **Risk Seviyesi:** KRİTİK (Güvenlik İhlali)
- **Detay:** `ui/ayarlar/personel_ui.py` içerisindeki `st.data_editor` bileşeni, şifreleri (`sifre`) açık metin (plaintext) olarak göstermektedir.
- **Beklenen:** `column_config` kullanılarak şifre kolonunun maskelenmesi (*******) ve düzenlenememesi.

### 📍 VAKA-026: Toplu Bcrypt Migrasyonu
- **Risk Seviyesi:** YÜKSEK (Güvenlik İhlali)
- **Detay:** Sistem şu an "Lazy Migration" (Giriş yapıldıkça hashleme) modelindedir. Ancak hiç giriş yapmamış personelin şifreleri hâlâ veritabanında plaintext olarak durmaktadır.
- **Beklenen:** Tüm personelin şifrelerini tek seferde Bcrypt ile hash'leyen bir bakım scripti çalıştırılması.

### 📍 VAKA-027: Mobil Navigasyon Senkronu
- **Risk Seviyesi:** ORTA (Fonksiyonellik)
- **Detay:** Bazı mobil hızlı erişim butonları (Quick Access), v5.0 öncesi eski modül anahtarlarına referans veriyor olabilir.
- **Beklenen:** Mobil navigasyonun `logic/zone_yetki.py` ile %100 uyumlu hale getirilmesi.

---
*Takipçi: Antigravity | Tarih: 30.03.2026*
