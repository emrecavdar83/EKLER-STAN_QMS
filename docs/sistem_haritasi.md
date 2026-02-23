# 🗺️ EKLERİSTAN QMS - Sistem Mimari Haritası (Madde 7)

**Sürüm:** 1.0 (Anayasal Röntgen Sonrası)
**Son Güncelleme:** 23.02.2026

## 1. Veri Yolculuğu Şablonu
> **Kural:** Kaynağı > İşlem Yolu > Kayıt Noktası > Geri Çağırma

### A. Personel Yönetimi
- **Kaynak:** Kullanıcı Girişi (UI/Personel Kayıt)
- **İşlem Yolu:** `logic/personel_logic.py` (Veya app.py içindeki inline logic)
- **Kayıt Noktası:** `ekleristan_local.db` > `personel` (Tablo)
- **Geri Çağırma:** `SELECT * FROM personel WHERE aktif=1`

### B. Soğuk Oda & Sıcaklık Takibi
- **Kaynak:** Sensör Verisi veya Manuel Giriş (UI/Soğuk Oda)
- **İşlem Yolu:** `soguk_oda_utils.py` > `soguk_oda_schema.py`
- **Kayıt Noktası:** `ekleristan_local.db` > `sicaklik_olcumleri`
- **Geri Çağırma:** `GET_LAST_TEMP(oda_id)` > `soguk_oda_ui.py`

### C. GMP ve Hijyen Denetimleri
- **Kaynak:** Tablet/Mobil Giriş (GMP Formu)
- **İşlem Yolu:** GMP Logic (app.py)
- **Kayıt Noktası:** `gmp_denetim_kayitlari` & `gmp_soru_havuzu`
- **Geri Çağırma:** 📊 KPI Rapor Ekranı

## 2. Aktif Yapı Analizi (Arınma Sonrası)
| Alan | Aktif Tablo/Dosya | Durum |
| :--- | :--- | :--- |
| **Personel** | `personel` | ✅ Temizlendi |
| **Bölümler** | `ayarlar_bolumler` | ✅ Temizlendi |
| **Soğuk Oda** | `soguk_odalar` | ✅ Temizlendi |

---
*Anayasal Purge (Madde 8-B) başarıyla uygulandı. Gereksiz 40+ dosya ve 3 tablo sistemden arındırıldı.*
