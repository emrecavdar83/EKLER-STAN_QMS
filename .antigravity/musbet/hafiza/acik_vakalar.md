# 🔴 AÇIK VAKALAR (Audit Takibi)

Bu döküman, mühürlenmeyi bekleyen açık teknik konuları ve riskleri içerir.

## ✅ VAKA-025: Plaintext Şifre Görünürlüğü (ÇÖZÜLDÜ)

- **Risk Seviyesi:** KRİTİK (Güvenlik İhlali)
- **Detay:** `ui/ayarlar/personel_ui.py` içerisindeki `st.data_editor` bileşeni, şifreleri (`sifre`) açık metin (plaintext) olarak gösteriyordu.
- **Çözüm:** SQL seviyesinde veri çekimi kısıtlandı, `st.data_editor` konfigürasyonu zırhlandı.

## ✅ VAKA-026: Toplu Bcrypt Migrasyonu (ÇÖZÜLDÜ)

- **Risk Seviyesi:** YÜKSEK (Güvenlik İhlali)
- **Detay:** Sistem "Lazy Migration" modelinden toplu migrasyona geçirildi.
- **Sonuç:** `scripts/bootstrap_bcrypt.py --uygula` manuel olarak tetiklendi ve başarılı kabul edildi.
- **Durum:** ÇÖZÜLDÜ

## 📍 VAKA-027: Mobil Navigasyon Senkronu

- **Risk Seviyesi:** ORTA (Fonksiyonellik)
- **Detay:** Bazı mobil hızlı erişim butonları (Quick Access), v5.0 öncesi eski modül anahtarlarına referans veriyor olabilir.
- **Beklenen:** Mobil navigasyonun `logic/zone_yetki.py` ile %100 uyumlu hale getirilmesi.

---
**Takipçi:** Antigravity | **Tarih:** 07.04.2026
