# 🟢 ÇÖZÜLMÜŞ VAKALAR (v5.0.0 - v5.7.0)

Bu döküman, başarıyla mühürlenen teknik vakaları içerir.

## 📍 VAKA-014: Silme Operasyonu (Symmetric Twin)

- **Sorun:** Veritabanı şişmesi ve gereksiz tablo karmaşası.
- **Çözüm:** "Symmetric Twin" mimarisi ve ilgili tüm tablolar temizlendi, Cloud-Primary yapıya geçildi.

## 📍 VAKA-016: Bcrypt Hash Geçişi

- **Sorun:** Plaintext şifrelerin güvenlik riski oluşturması.
- **Çözüm:** İlk girişte Bcrypt hashleme stratejisi uygulandı, `auth_logic.py` güncellendi.

## 📍 VAKA-019: Elvan Özdemirel Mükerrer Kaydı

- **Sorun:** Veritabanında hatalı ve mükerrer kayıt bulunması.
- **Çözüm:** Self-Healing scripti ile hatalı kayıt silindi, doğru yetki sabitlendi.

## 📍 VAKA-020: Gülay Gem / MAP Yetki Eksikliği

- **Sorun:** OPERATOR rolünün MAP modülünü görememesi.
- **Çözüm:** Zırhlı Normalizasyon ile etiket-anahtar uyuşmazlığı giderildi.

## 📍 VAKA-028: Rule Zero & Cloud Integrity (v5.6.0)

- **Sorun:** Lokal ve Bulut arasındaki otorite karmaşası.
- **Çözüm:** Anayasa Madde 7 uyarınca tüm onarım süreci Bulut Otoritesi'ne (Supabase) devredildi.

## 📍 VAKA-029: Zırhlı Tasfiye & Güvenlik (v5.7.0)

- **Sorun:** Şifrelerin admin panelinde görünmesi ve hantal ölü kodlar (Flow Engine).
- **Çözüm:** Şifre kolonu maskelendi, Flow Engine tasfiye edildi. Tüm dev fonksiyonlar Anayasa Madde 2'ye göre parçalandı.

## 📍 VAKA-031: KPI BRC Limit Entegrasyonu & Soft-Stop (v5.9.0)

- **Tarih:** 14.04.2026 | **Modül:** `kpi_ui.py`, `urun_ui.py`
- **Sorun:** Operatörlerin limit dışı KPI değerlerini körü körüne kaydetmesi (BRC/IFS ihlali).
- **Çözüm:** Spesifikasyon hedefleri min-max olarak dinamik hale getirildi. Form içerisindeki limit ihlalleri otomatik olarak "Deviasyon (RED)" kararı ile etiketlenip "Soft-Stop" kurgusu dahilinde loglanıyor (Kayıt engellenmiyor ama flagleniyor).

## 📍 VAKA-032: MAP Prosesi UI Stability & Kullanıcı Atma (v5.9.0)

- **Tarih:** 14.04.2026 | **Modül:** `map_uretim.py`
- **Sorun:** Tüm map formlarında yer alan `st.popover` nesnelerinin değer girildikçe state'i silip kullanıcıyı menüden atması.
- **Çözüm:** Modüldeki `st.popover` mantığı tamamen kazındı, yerine session_state hapsedilmiş UI elementleri (`st.toggle`, kalıcı `st.expander` ve condition container) yerleştirildi. Böylece çoklu veri girişi olan "Fire Ekle", "Bobin Değiştir" işlemlerinde veya "Vardiya Kapat" işlemlerinde state kaybına kalıcı son verildi.

---
*Mühürleyen: Antigravity | v5.9.0 Security Seal | Tarih: 14.04.2026*
