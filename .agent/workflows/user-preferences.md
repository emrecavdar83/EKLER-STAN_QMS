---
description: Emre Bey'in çalışma tercihleri ve öğrenme yaklaşımı
---

# Kullanıcı Tercihleri (Anayasa)

> [!IMPORTANT]
> **TEMEL KURAL (ANAYASA):** Yapılan her işlem sonunda mutlaka **Türkçe** geri bildirim verilecek ve tüm planlamalar (implementation plan vb.) **Türkçe** olarak hazırlanacaktır.

## 👨‍🏫 Öğretici Mod
Emre Bey bu projeyi öğrenmek istiyor. Yapılan her değişiklikte:

1. **Alternatif Seçenekleri Sun:** En az 2-3 farklı yaklaşım göster, avantaj/dezavantajlarını açıkla
2. **Risk Analizi Yap:** Değişikliğin mevcut sisteme etkisi, olası yan etkiler, geri dönüş planı
3. **Açıklayıcı Ol:** Kod ne yapıyor, neden bu şekilde yazıldı, teknik kararların arkasındaki mantık

---

## 🔧 Proje Bilgileri
- **Proje:** Ekleristan QMS
- **Teknolojiler:** Python, Streamlit, Supabase (PostgreSQL)
- **Kullanıcı:** Emre ÇAVDAR (Gıda Mühendisi)
- **Anayasa:** `.antigravity/rules/anayasa.md` (v4.0)

---

## 🤖 AJAN ÇALIŞMA SIRASI (Pipeline)

```
0. planner          → İhtiyaç Analizi (7-15 Soru) + Emre Onayı
1. builder_db       → Şema & Migration
2. builder_backend  → İş Mantığı & Servis
3. builder_frontend → Streamlit Arayüzü
4. tester           → Birim & Entegrasyon Testleri
5. validator        → Bulut Tarayıcı Testi (Madde 15) — CANLIDA TEST ZORUNLU
6. guardian         → Risk & Koruma
7. auditor          → Anayasa Uyum Denetimi
8. sync_master      → Hafıza & Senkronizasyon
```

> [!IMPORTANT]
> **Adım 0 ATLANAMAZ.** Emre Bey'in onayı alınmadan builder_db başlayamaz.
> **Adım 5 EN KRİTİK ADIMDIR.** Test mutlaka https://ekler-stanqms-hdqwhxqcw3evgpnzgerkec.streamlit.app/ adresinde yapılır.

---

## 📦 ARAYÜZ HARİTASI (v4.0.3 — Güncel)

> [!NOTE]
> Detaylı veritabanı, fonksiyon ve FK ilişkileri için: `.antigravity/musbet/hafiza/sistem_haritasi.md`
> Çözülmüş hatalar ve ders çıkarılan vakalar için: `.antigravity/musbet/hafiza/hafiza_ozeti.md`

| # | Modül | Sekmeler | Birincil Butonlar | Durum |
|---|-------|----------|-------------------|-------|
| 1 | 🏭 Üretim Girişi | Form + Günlük İzleme | `💾 Üretimi Kaydet` | ✅ |
| 2 | 📊 KPI & Kalite | Dinamik Form | `✅ Analizi Kaydet` | ✅ |
| 3 | 🛡️ GMP Denetimi | Checklist | `✅ Denetimi Tamamla` | ✅ |
| 4 | 🧼 Personel Hijyen | **Tab1:** Denetim \| **Tab2:** Dashboard | `💾 Denetimi Kaydet` | ✅ |
| 5 | 🧹 Temizlik Kontrol | 25 Görev Listesi | `💾 Kayıtları İşle` | ✅ |
| 6 | 📑 Raporlama | Filtre Paneli | `Raporu Oluştur` | ✅ |
| 7 | ❄️ Soğuk Oda | **Tab1:** QR Tara \| **Tab2:** Manuel Seç | `📸 Taramayı Başlat` | ✅ |
| 8 | 🗺️ MAP Üretim | **Tab1:** Vardiya \| **Tab2:** Kontrol Merkezi (Dinamik) \| **Tab3:** Rapor | `🟢 MAKİNEYİ BAŞLAT`, `🔻 Duruşlar`, `🟢 İŞE BAŞLA`, `➕ Üretim Kaydet`, `🔥 Fire`, `🎞️ Bobin` | ✅ |
| 9 | 📋 Günlük Görevler | **Tab1:** Görevlerim \| **Tab2:** Matris \| **Tab3:** Atama | `🚀 GÖREVİ ATA`, `✅ Tamamla` | ✅ |
| 10| 📈 Performans | **Tab1:** Yeni \| **Tab2:** Geçmiş \| **Tab3:** Analiz | `💾 Değerlendirmeyi Kaydet` | ⚠️ |
| 11| 📄 QDMS | **Tab1:** Doküman \| **Tab2:** Yönetim \| **Tab3:** Talimat | `📄 PDF`, `👁️ ÖNİZLE` | ✅ |
| 12| ⚙️ Ayarlar | **14 Sekme** | Tab bazlı yönetim | ✅ |
| 13| 👤 Profilim | Kişisel Bilgiler & Güvenlik | `🚀 Bilgilerimi Güncelle` | ✅ |

> MAP Kontrol Merkezi butonları (🔻 🟢 ➕ 🔥 🎞️) vardiya başladıktan sonra dinamik olarak açılır.

---

## 🗝️ KRİTİK SİSTEM BİLGİLERİ

- **Canlı URL:** https://ekler-stanqms-hdqwhxqcw3evgpnzgerkec.streamlit.app/
- **Veritabanı:** Supabase (PostgreSQL) — Cloud-Primary (Madde 7)
- **Lokal DB:** `ekleristan_local.db` — Sadece Read-Only yedek
- **Test Kullanıcısı:** Admin / 12345

---

## ⏰ PLANLI GELİŞTİRMELER

- **Lokasyon Revizyonu:** `XX-YY-ZZ-AA` formatında benzersiz lokasyon/ekipman hiyerarşisi + QR kod entegrasyonu
- **Performans Modülü:** Analiz sekmesindeki grafik görsellerinin zenginleştirilmesi
- **Vardiya Otomasyonu:** Zaman bazlı otomatik vardiya seçimi
