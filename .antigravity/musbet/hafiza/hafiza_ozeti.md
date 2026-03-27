# EKLERİSTAN QMS — Hafıza Özeti
# .antigravity/musbet/hafiza/hafiza_ozeti.md
# ⚠️ SIFIRINCI KURAL — Bu dosya her ajan tarafından işe başlamadan okunur.

---

## 📌 SİSTEM NOTU (Başlangıç Kaydı)

**Tarih:** 2026-03-27
**Durum:** Sistem ilk kuruldu. Henüz işlenmiş vaka yok.

**Mimariden çıkan ilk ders (sistem kurulum notu):**
Ajanların kendi yazdıkları testler yalnızca kendi varsayımlarını test eder.
Gerçek kullanım senaryolarını (Emre'nin bakış açısını) kapsayamaz.
Bu nedenle **validator** ajanı pipeline'a eklendi.
Validator, tüm ajan testleri geçse bile insan simülasyonu yaparak
MANUEL_RED mekanizmasını tetikleyebilir.

---

## 📊 AJAN BAZLI HATA SAYACI

| Ajan | Toplam | MANUEL_RED | P1 | Tekrar Eden |
|------|--------|------------|-----|-------------|
| builder_db | 2 | 2 | 0 | — |
| builder_backend | 1 | 1 | 0 | — |
| builder_frontend | 1 | 1 | 0 | — |
| tester | 1 | 1 | 0 | — |
| validator | 3 | 3 | 0 | YES |
| guardian | 0 | 0 | 0 | — |
| auditor | 0 | 0 | 0 | — |
| sync_master | 0 | 0 | 0 | — |

---

## 🔴 AÇIK P0 VAKALAR (MANUEL_RED)

- **[VAKA-001]** Üretim ortamında (Streamlit Cloud) eksik veritabanı şeması nedeniyle `ProgrammingError` çökmesi.
- **[VAKA-002]** Validator'ın canlı arayüzde yüzeysel test yapıp "hata yok" diyerek asıl etkileşim fonksiyonlarını (End-to-End) test etmemesi. (Emre Bey'den P0 yedi).
- **[VAKA-003]** SQLAlchemy 2.0'ın DDL (`CREATE TABLE`) işlemlerini "sessizce" yutup `conn.commit()` çağrılmadığı için üretim ortamında veritabanı tablolarının oluşmamasına ve saatlerce süren kaotik hataya sebep olması.
- **[VAKA-004]** İlk yükleme döngüsünde GitHub push hatası + modülün arayüzde hiç görünmemesi. Cloud eski kodu çalıştırırken ajanların "tamamlandı" raporu vermesi.

## 🟠 AÇIK P1 VAKALAR

*Yok.*

---

## 🔁 TEKRAR EDEN ÖRÜNTÜLER

- **[ÖRÜNTÜ-01] Yüzeysel Test:** Ajanlar test yapmayı "kod run time hatası veriyor mu" olarak algılıyor. Fonksiyonelliği ve kullanıcı yolculuğunu hissetmiyorlar.

---

## ⚠️ DİKKAT NOTLARI (Ajanlara)

- **DİKKAT (Backend & DB Ajanlarına):** Kaotik VAKA-003 sebebiyle, veritabanına yazma/modify işlemleri yaparken `eng.connect()` ardından kesinlikle `conn.commit()` yapılmalı VEYA doğrudan `eng.begin() as conn:` transaction bağlamı kullanılmalıdır. Aksi halde Streamlit Cloud sessizce işlemi yutmaktadır.
- **DİKKAT (Validator):** "Ekranda hata kırmızı kutusu çıkmıyor demek test tamamlandı" demek DEĞİLDİR! E2E (Ucan uca) görev atama, tıklama, kaydetme işlemleri veritabanından simüle edilerek %100 test edilmek zorundadır.
- **DİKKAT (Validator + sync_master):** Her deploy sonrası Streamlit Cloud URL yeniden yüklenmeli ve yeni kodun aktif olduğu bizzat teyit edilmelidir (VAKA-004). Yeni modüller için `ayarlar_moduller` ve `ayarlar_yetkiler` tablolarına kayıt eklendiği de kontrol edilmelidir.

---

## 📅 SON HAFTA ÖZETİ

- Açılan vaka: 3
- Çözülen vaka: 3
- Açık kalan: 0
- MANUEL_RED: 3
- Örüntü alarmı: 1

---

*musbet | EKLERİSTAN QMS Antigravity Pipeline v3.0*
*Bu dosya musbet ajanı tarafından güncellenir. Manuel düzenleme yapılmaz.*
