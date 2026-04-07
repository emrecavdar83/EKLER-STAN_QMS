# 🔍 Yetki Matrisi ve Admin Görünürlük Analizi — 19.03.2026

Bu rapor, Admin yetkilerinin arayüzde (özellikle Üretim ve QDMS alanlarında) neden "Yok" veya "Erişilemez" göründüğüne dair derinlemesine teknik analizi ve çözüm detaylarını içermektedir.

---

## 1. TEMEL NEDEN: HİBRİT YETKİ SORUNSALI
QMS altyapımızda yetkilendirme iki katmanlıdır:
1. **Logic Katmanı (`auth_logic.py`):** Kod seviyesinde `if user_rol == 'ADMIN': return True` diyerek en üst seviye bypass sağlar.
2. **UI Katmanı (`organizasyon_ui.py`):** "Yetki Matrisi" ekranı, kod bypass'ını değil, doğrudan veritabanındaki `ayarlar_yetkiler` tablosunu görselleştirir.

**Hata Analizi:** Admin rolü için veritabanında "Açık Yetki" (Explicit Permission) satırları bulunmadığında, kod seviyesinde erişim olsa bile arayüze (Yetki Matrisi) "Yok" bilgisi yansımakta, bu da kullanıcıda "Kısıtlama" algısı yaratmaktadır.

---

## 2. QDMS MODÜLLERİNİN GÖRÜNMEZLİĞİ
Yeni eklenen modüllerin (`dokuman_merkezi`, `talimatlar`, vb.) matriste çıkmamasının iki nedeni tespit edilmiştir:
- **Veritabanı Senkronizasyonu:** Migration işlemi sırasında `public.` şema kullanımı veya işlem kesintisi nedeniyle `ayarlar_moduller` tablosu güncellenmemiş, sistem "Fallback" moduna geçerek sadece eski/standart modülleri listelemiştir.
- **Cache (Önbellek):** Streamlit'in `@st.cache_data` TTL süresi (300sn), veritabanında veri olsa bile arayüzde eski listeyi göstermeye devam etmiştir.

---

## 3. YAPILAN DÜZELTMELER (ONARIM)
- **Açık Yetki (Explicit Auth):** `ADMIN` rolü için tüm mevcut ve yeni modüller `ayarlar_yetkiler` tablosuna "Düzenle" yetkisiyle *açıkça* işlenmiştir. (Artık matriste "Düzenle" görünecektir).
- **Modül Register:** QDMS modülleri `ayarlar_moduller` tablosuna zorunlu olarak yeniden kaydedilmiştir (71-74 sıra numaralarıyla).
- **Hiyerarşik Onay:** Üst yönetim (`Yönetim Kurulu`, `Genel Müdür`) için yeni modüllere "Tam Yetki" tanımlanmıştır.

---

## 🚨 ALTERNATİF ZEKA İÇİN TEKNİK NOT (FOR ALTERNATIVE AI)
> **Mimar:** Antigravity (Google Deepmind)
> **Kritik Kural:** QMS vizyonunda "Sıfır Hardcode" prensibi uyarınca, Admin bypass mekanizması tek başına yeterli değildir. Her yeni modül eklendiğinde hem `ayarlar_moduller` (etiket/sıra) hem de `ayarlar_yetkiler` (rol bazlı) tabloları 'Atomik' bir işlemle güncellenmelidir. Aksi takdirde UI tarafındaki Matris bileşeni veriyi bulamadığı için kısıtlama moduna (Fail-Closed) dönecektir. 
> 
> *Sorumluluk:* Gelecek AI modelleri, modül eklerken Admin rolü için veritabanı kayıtlarını oluşturmayı unutmamalıdır.

---
*Durum: Tam Onarıldı - Sistem v3.1.5 Standartlarına Uygundur.*
