---
description: Emre Bey'in çalışma tercihleri ve öğrenme yaklaşımı
---

# Kullanıcı Tercihleri (Anayasa)

> [!IMPORTANT]
> **TEMEL KURAL (ANAYASA):** Yapılan her işlem sonunda mutlaka **Türkçe** geri bildirim verilecek ve tüm planlamalar (implementation plan vb.) **Türkçe** olarak hazırlanacaktır.

## 👨‍🏫 Öğretici Mod
Emre Bey bu projeyi öğrenmek istiyor. Yapılan her değişiklikte:

1. **Alternatif Seçenekleri Sun:**
   - En az 2-3 farklı yaklaşım göster
   - Her birinin avantaj/dezavantajlarını açıkla

2. **Risk Analizi Yap:**
   - Değişikliğin mevcut sisteme etkisi
   - Olası yan etkiler
   - Geri dönüş planı

3. **Açıklayıcı Ol:**
   - Kod ne yapıyor, neden bu şekilde yazıldı
   - Teknik kararların arkasındaki mantık

## 📋 Örnek Format

### Seçenek A: [İsim]
- **Nasıl çalışır:** ...
- **Avantaj:** ...
- **Dezavantaj:** ...
- **Risk:** Düşük/Orta/Yüksek

### Seçenek B: [İsim]
- **Nasıl çalışır:** ...
- **Avantaj:** ...
- **Dezavantaj:** ...
- **Risk:** Düşük/Orta/Yüksek

### Önerim: [Hangi seçenek ve neden]

---

## 🔧 Proje Bilgileri
- **Proje:** Ekleristan QMS
- **Teknolojiler:** Python, Streamlit, Supabase (PostgreSQL)
- **Kullanıcı:** Emre ÇAVDAR (Gıda Mühendisi)
- **Anayasa:** `.antigravity/rules/anayasa.md` (v4.0) — Her işlem başında okunması zorunludur (Sıfırıncı Kural)

---

## 🤖 AJAN ÇALIŞMA SIRASI (Pipeline)

Bir modül talebi geldiğinde ajanlar **bu sırayla** çalışır. Adım atlanamaz.

```
0. planner          → İhtiyaç Analizi (7-15 Soru) + Emre Onayı
        ↓
1. builder_db       → Şema & Migration (Tablo yapısı)
        ↓
2. builder_backend  → İş Mantığı & Servis (logic/*.py)
        ↓
3. builder_frontend → Streamlit Arayüzü (ui/*.py)
        ↓
4. tester           → Birim & Entegrasyon Testleri
        ↓
5. validator        → Bulut Tarayıcı Testi (Madde 15) — CANLIDA TEST ZORUNLU
        ↓
6. guardian         → Risk & Koruma Değerlendirmesi
        ↓
7. auditor          → Anayasa Uyum Denetimi
        ↓
8. sync_master      → Hafıza & Senkronizasyon Güncellemesi
```

> [!IMPORTANT]
> **Adım 0 ATLANAMAZ.** Emre Bey'in "ONAYLA" veya eşdeğer onayı alınmadan builder_db başlayamaz.
> **Adım 5 EN KRİTİK ADIMDIR.** Test sadece localhost'ta değil, https://ekler-stanqms-hdqwhxqcw3evgpnzgerkec.streamlit.app/ adresinde yapılır.

---

## 🧠 MODEL ATAMA TABLOSU (Hangi Ajan, Hangi AI?)

| Ajan | Birincil Model | Fallback (Kota Dolunca) | Neden? |
|------|---------------|------------------------|--------|
| **planner** | Claude Sonnet 4.6 | Claude Haiku 3.6 | Soru üretimi, kapsam analizi |
| **builder_db** | Gemini 2.5 Pro | Claude Sonnet 4.6 | Şema üretimi, yapısal düşünme |
| **builder_backend** | Gemini 2.5 Pro | Claude Sonnet 4.6 | Karmaşık logic, SQLAlchemy |
| **builder_frontend** | Gemini 2.5 Pro | Claude Sonnet 4.6 | UI üretimi, Streamlit template |
| **tester** | Gemini Flash | Claude Haiku 3.6 | Hız, kural tabanlı test |
| **validator** | Claude Sonnet 4.6 | Claude Haiku 3.6 | İnsan simülasyonu, Bulut Tarayıcı Testi |
| **guardian** | Gemini Flash | Claude Haiku 3.6 | Hız, kural tabanlı risk tespiti |
| **auditor** | Claude Sonnet 4.6 | Claude Haiku 3.6 | Derin analiz, standart yorumu |
| **sync_master** | Claude Sonnet 4.6 | Claude Haiku 3.6 | Hafıza tutarlılığı |
| **musbet** | Gemini 2.5 Pro | Claude Sonnet 4.6 | Örüntü tespiti, uzun dönem hafıza |

> **Kota Kuralı:** Gemini Pro kotası tükenirse Fallback'e geçilir. Fallback da erişilemezse işlem **duraklatılır** — sessiz bozulma KABUL EDİLMEZ. Mimari kararlar için: **Claude Opus 4.6**

---

## 📦 EKLERİSTAN QMS TAM ARAYÜZ HARİTASI (Canlı Audit — 2026-03-28)

> [!IMPORTANT]
> Aşağıdaki tablo canlı ortamda (Streamlit Cloud) yapılan tam tarama sonucudur.
> ❌ = Kritik hata (P0), ⚠️ = Kısmi sorun (P2), ✅ = Sorunsuz

| # | Modül | Dosya | Sekmeler | Durum | Bilinen Hata |
|---|-------|-------|----------|-------|--------------|
| 1 | 🏭 Üretim Girişi | `ui/uretim_ui.py` | *(Tek sayfa)* Form + Günlük İzleme tablosu | ⚠️ | Ürün seed data eksik |
| 2 | 📊 KPI & Kalite Kontrol | `ui/kpi_ui.py` | *(Tek sayfa)* KPI giriş formu | ⚠️ | Ürün seed data eksik |
| 3 | 🛡️ GMP Denetimi | `ui/gmp_ui.py` | *(Tek sayfa)* Bölüm dropdown → Denetim soruları | ✅ | — |
| 4 | 🧼 Personel Hijyen | `ui/hijyen_ui.py` | **Tab1:** ✅ Günlük Denetim \| **Tab2:** ❌ 📊 Dashboard | ❌ | Dashboard: `psycopg2 date()` SQL hatası |
| 5 | 🧹 Temizlik Kontrol | `ui/temizlik_ui.py` | *(Tek sayfa)* 25 görev checklisti | ✅ | — |
| 6 | 📑 Kurumsal Raporlama | `ui/raporlama_ui.py` | *(Tek sayfa)* Tarih + Kategori filtresi → PDF/Excel | ✅ | — |
| 7 | ❄️ Soğuk Oda | `ui/soguk_oda_ui.py` | **Tab1:** 📸 QR Kodu Tara \| **Tab2:** ⌨️ Manuel Dolap Seç | ⚠️ | Alt kısımda Günlük Görevler hatası sızıyor |
| 8 | 🗺️ MAP Üretim | `ui/map_uretim/` | **Tab1:** 🟢 Vardiya \| **Tab2:** 🕹️ Kontrol Merkezi \| **Tab3:** 📊 Rapor | ⚠️ | Sidebar bazen Performans başlığını gösteriyor |
| 9 | 📋 Günlük Görevler | `modules/gunluk_gorev/` | **Tab1:** 📝 Benim Görevlerim \| **Tab2:** 📈 Yönetici Matrisi ✅ \| **Tab3:** ➕ Görev Atama ❌ | ❌ | Tab3: `NameError: 'text' is not defined` (ui.py:84) |
| 10 | 📈 Performans & Polivalans | `ui/performans/` | **Tab1:** ➕ Yeni Değerlendirme \| **Tab2:** 📋 Geçmiş Kayıtlar \| **Tab3:** 📈 Analiz & Matris (pasif) | ✅ | Menüde 2 giriş var, ikisi aynı sayfaya gidiyor |
| 11 | 📄 QDMS | `ui/qdms/` | **Tab1:** 📋 Doküman Merkezi \| **Tab2:** ⚙️ Yönetim \| **Tab3:** 📖 Talimatlar \| **Tab4:** 📊 Uyumluluk | ✅ | En stabil modül |
| 12 | ⚙️ Ayarlar | `ui/ayarlar/` | 14 sekme: Personel, Kullanıcılar, **Ürünler** (boş!), Roller, Yetkiler, Bölümler, Ekipmanlar, Lokasyonlar, KPI Tanımları, GMP Kategorileri, Temizlik Görevleri, Soğuk Oda Dolapları, Sistem Parametreleri, Bakım | ✅ | Ürünler sekmesi boş → Üretim+KPI modülleri uyarı veriyor |
| 13 | 👤 Profilim | `ui/profil_ui.py` | *(Tek sayfa olmalı)* Şifre + Bilgi güncelleme | ❌ | Ağır UI Bleeding: Ayarlar'ın 14 sekmesi sızıyor |

### 🔴 Açık P0 Hataları (Düzeltilmesi Zorunlu)
1. **Günlük Görevler → Görev Atama:** `NameError: 'text' is not defined` — `ui.py:84`
2. **Personel Hijyen → Dashboard:** `psycopg2 UndefinedFunction: date(unknown,unknown)` — PostgreSQL'de SQLite syntax
3. **Profilim:** Ayarlar modülünün tüm 14 sekmesi sayfaya sızıyor — `app.py` dispatch sorunu

### ⚠️ Açık P2 Sorunları
4. **Üretim + KPI:** `Ayarlar > Ürünler` sekmesine ürün tanımlanmadığı için "Ürün bulunamadı" uyarısı
5. **Sidebar ↔ Hızlı Menü:** Sidebar tıklamaları bazen sayfayı tetiklemiyor

---

## 🗝️ KRİTİK SİSTEM BİLGİLERİ

- **Canlı URL:** https://ekler-stanqms-hdqwhxqcw3evgpnzgerkec.streamlit.app/
- **Veritabanı:** Supabase (PostgreSQL) — Cloud-Primary (Madde 7)
- **Lokal DB:** `ekleristan_local.db` — Sadece Read-Only yedek
- **Lokasyon Standardı:** `XX-YY-ZZ-AA` (Madde 20) — Henüz migrate edilmedi
- **Test Kullanıcısı (Canlı):** Admin / 12345

---

## ⏰ HATIRLATMA: Lokasyon Revizyon Planı

**Ne zaman:** Lokasyon-Bölüm-Ekipman yapısı tamamlandığında

### Yapılacaklar:
1. **Benzersiz ID Yapısı:**
   ```
   XX-YY-ZZ-AA formatı
   XX = Kat bilgisi (örn: 01, 02, 03)
   YY = Bölüm bilgisi (örn: BOMBA→01, PATASU→02)
   ZZ = Hat bilgisi
   AA = Ekipman bilgisi
   
   Örnek: 03-02-01-05 = Kat3 > Pataşu > Hat1 > Ekipman5
   ```

2. **Tıklanabilir Ağaç Görünümü:**
   - Mevcut lokasyonlar expandable/collapsible olacak
   - Tıklama ile detaylar açılacak

3. **Kullanım Alanları:**
   - **Bakım Prosesi** - Ekipman bakım takibi
   - **QR Kodlu Ekipman Temizlik Kontrolü** - Her ekipmana QR kod, tarama ile temizlik kaydı
   - **İletişim Prosesi** - Konum bazlı bildirimler
   - Tüm modüllerde merkezi referans

### Neden Önemli:
- Benzersiz tanımlama = Raporlamada netlik
- Hiyerarşik kod = Otomatik sıralama ve gruplama
- **QR kod entegrasyonu** = Mobil cihazla hızlı kayıt
