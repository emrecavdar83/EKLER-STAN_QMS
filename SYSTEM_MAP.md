# EKLERİSTAN QMS — SİSTEM HARİTASI
**Versiyon:** v5.9.1 | **Güncelleme:** 2026-04-02 | **Ortam:** Cloud-Primary (Supabase + Streamlit)

---

## 1. GENEL MİMARİ

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KULLANICI TARAYICI                              │
│                    Streamlit Cloud (HTTPS)                              │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────┐
│                          app.py (~430 satır)                            │
│  set_page_config → auth → session_state → zone_gate → modül routing    │
└──────┬──────────────┬───────────────┬─────────────────┬────────────────┘
       │              │               │                 │
  auth_logic     zone_yetki      cache_manager     data_fetcher
  (RBAC+bcrypt)  (zone kapısı)   (TTL≤60s)         (N→1 sorgu)
       │              │               │                 │
┌──────▼──────────────▼───────────────▼─────────────────▼────────────────┐
│                     DATABASE KATMANI                                    │
│   Supabase PostgreSQL (prod)  ←→  SQLite WAL (dev/offline fallback)    │
│   pool_size=5, max_overflow=10, pool_recycle=1800                       │
│   Timezone: Europe/Istanbul                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Uyumluluk Hedefleri
| Standart | Versiyon |
|----------|----------|
| BRCGS    | v9       |
| IFS      | v8       |
| FSSC 22000 | v6    |
| ISO 9001 | 2015     |

---

## 2. YAPAY ZEKA AJAN SİSTEMİ

### 2.1 Ajan Rolleri ve Modeller

| ID | Rol | Model | Sorumluluk |
|----|-----|-------|------------|
| -1 | context_hub | — | Hafıza yükleme, `hafiza_ozeti.md` dağıtımı |
| 0  | planner | Claude Sonnet 4.6 | Görev analizi, `claudes_plan.md` yazma |
| 1  | builder_db | Gemini 2.5 Pro Low | Schema, migration, DB katmanı |
| 2  | builder_backend | Gemini 2.5 Pro High | Business logic, API, auth |
| 3  | builder_frontend | Gemini 2.5 Pro Low | Streamlit UI, bileşenler |
| 4  | tester | Gemini Flash | pytest yazma, test çalıştırma |
| 5  | validator | Claude Sonnet 4.6 | Kod kalite + Anayasa uyum denetimi |
| 6  | guardian | Gemini Flash | Güvenlik taraması, RED/ONAY kararı |
| 7  | auditor (S3) | Claude Sonnet 4.6 | BRCGS/IFS/FSSC/ISO madde denetimi |
| 8  | sync_master (S5) | Claude Sonnet 4.6 | SQLite ↔ Supabase senkronizasyonu |
| 9  | musbet | Gemini 2.5 Pro High | Kolektif hafıza, vaka arşivi |

### 2.2 Koordinasyon Dosyası
```
C:\Users\GIDA MÜHENDİSİ\.gemini\antigravity\brain\
  4a011233-6f51-40d7-bbb8-21b93ec221fd\claudes_plan.md
```

### 2.3 Otomatik Zincir Kuralı
```
Yeni görev
    │
    ▼
claudes_plan.md oku
    │
    ├─ Durum: S4_ONAY ──► S3 Auditor (BRCGS/IFS denetim)
    │                          │
    │                    Guardian RED? ──► Kullanıcıya bildir, DUR
    │                          │ ONAY
    │                          ▼
    │                    S5 Sync Master
    │                          │
    │                    sync_log_preview.txt üret
    │                          │
    │                    "ONAYLA" bekle ◄── İNSAN ONAYI ZORUNLU
    │                          │
    │                    SQLite ↔ Supabase sync
    │                          │
    │                    claudes_plan.md → TAMAMLANDI
    │
    └─ Durum: TAMAMLANDI / dosya yok ──► Normal konuşma
```

### 2.4 Kota Yönetimi (VAKA-005)
- Gemini kotası tükenirse → Fallback model
- Fallback erişilmezse → İşlem **durumlandırılır**, kullanıcıya bildirilir
- Hiçbir ajan `hafiza_ozeti.md` okumadan işe başlayamaz (**Sıfırıncı Kural**)

---

## 3. KULLANICI VE ROL TANIMLARI

### 3.1 RBAC Seviyeleri (Pozisyon Hiyerarşisi)

| Seviye | Rol | İkon | Renk | Yetki Kapsamı |
|--------|-----|------|------|----------------|
| 0 | Yönetim Kurulu | 🏛️ | `#1A5276` | Tüm modüller, stratejik |
| 1 | Genel Müdür | 👑 | `#2874A6` | Tüm modüller, operasyonel |
| 2 | Direktörler | 📊 | `#3498DB` | Çok departmanlı, stratejik operasyon |
| 3 | Müdürler | 💼 | `#5DADE2` | Departman yönetimi, alt departmanlar |
| 4 | Koordinatör/Şef | 🎯 | `#85C1E9` | Birim yönetimi, takım |
| 5 | Bölüm Sorumlusu | ⭐ | `#A3E4D7` | Takım yönetimi, temel erişim |
| 6 | Personel | 👥 | `#D4E6F1` | Kendi kayıtları, temel erişim |
| 7 | Stajyer/Geçici | 📝 | `#ECF0F1` | Yalnızca görüntüleme |

```python
MANAGEMENT_LEVELS = [0, 1, 2, 3, 4, 5]
STAFF_LEVELS      = [6, 7]
```

### 3.2 Sistem Hesapları

| Kullanıcı Adı | Rol | Amaç |
|---------------|-----|------|
| `Admin` | ADMIN | Sistem yöneticisi, tüm zone'lar açık |
| `Saha_Mobil` | Personel | Mobil terminal girişleri |

### 3.3 Zone-Tabanlı Erişim (3 Katman)

```
Katman 1 — Zone Kapısı (zone_girebilir_mi)
  ops │ mgt │ sys
      │     │
Katman 2 — Modül Görünürlüğü (modul_gorebilir_mi)
  Görüntüle │ Düzenle │ Tam │ Yok
             │
Katman 3 — Eylem Kilidi (eylem_yapabilir_mi)
  Ekle │ Sil │ Onayla │ Yazdır │ ...
```

| Zone | Varsayılan Modül | Kapsam |
|------|-----------------|--------|
| `ops` | uretim_girisi | Üretim, vardiya, MAP, soğuk oda, GMP, hijyen, temizlik, günlük görev |
| `mgt` | kpi_kontrol | QDMS, raporlama, performans |
| `sys` | ayarlar | Admin paneli, yapılandırma |

**ADMIN Bypass:** `user_rol.upper() == 'ADMIN'` → tüm zone + tüm modüller (DB sorgusu yapılmaz)

---

## 4. MODÜL HARİTASI

### 4.1 Modüller — Zone ve Erişim

| Sıra | Anahtar | Etiket | Zone | Zone Kapısı |
|------|---------|--------|------|-------------|
| 0 | `portal` | 🏠 Portal (Ana Sayfa) | — | Yok (herkese açık) |
| 10 | `uretim_girisi` | 🏭 Üretim Girişi | ops | ✅ |
| 20 | `kpi_kontrol` | 🍩 KPI & Kalite Kontrol | ops | ✅ |
| 30 | `gmp_denetimi` | 🛡️ GMP Denetimi | mgt | ✅ |
| 40 | `personel_hijyen` | 🧼 Personel Hijyen | ops | — |
| 50 | `temizlik_kontrol` | 🧹 Temizlik Kontrol | ops | — |
| 60 | `kurumsal_raporlama` | 📊 Kurumsal Raporlama | mgt | ✅ |
| 70 | `soguk_oda` | ❄️ Soğuk Oda Sıcaklıkları | ops | — |
| 80 | `map_uretim` | 📦 MAP Üretim | ops | — |
| 85 | `gunluk_gorevler` | 📋 Günlük Görevler | ops | — |
| 90 | `performans_polivalans` | 📈 Yetkinlik & Performans | mgt | ✅ |
| 95 | `personel_vardiya_yonetimi` | 📅 Vardiya Yönetimi | ops | — |
| 100 | `qdms` | 📁 QDMS | mgt | ✅ |
| 110 | `ayarlar` | ⚙️ Ayarlar | sys | ✅ |
| — | `profilim` | 👤 Profilim | — | — |

### 4.2 Modül → Dosya Eşlemesi

```
portal                → ui/portal/portal_ui.py
uretim_girisi         → ui/uretim_ui.py
kpi_kontrol           → ui/kpi_ui.py
gmp_denetimi          → ui/gmp_ui.py
personel_hijyen       → ui/hijyen_ui.py
temizlik_kontrol      → ui/temizlik_ui.py
kurumsal_raporlama    → ui/raporlama_ui.py
soguk_oda             → ui/soguk_oda_ui.py
map_uretim            → ui/map_uretim/map_uretim.py
gunluk_gorevler       → modules/gunluk_gorev/ui.py
performans_polivalans → ui/performans/performans_sayfasi.py
personel_vardiya_yonetimi → modules/vardiya/ui.py
qdms                  → ui/qdms_ui.py
ayarlar               → ui/ayarlar/ayarlar_orchestrator.py
profilim              → ui/profil_ui.py
```

### 4.3 Ayarlar Alt Sekmeleri

| Sekme | Dosya | Zone |
|-------|-------|------|
| Fabrika Ayarları | `ayarlar/fabrika_ui.py` | sys |
| Organizasyon | `ayarlar/organizasyon_ui.py` | sys |
| Personel Yönetimi | `ayarlar/personel_ui.py` | sys |
| Ürün Tanımları | `ayarlar/urun_ui.py` | sys |
| Temizlik/GMP Ayarları | `ayarlar/temizlik_gmp_ui.py` | sys |
| Soğuk Oda Ayarları | `ayarlar/soguk_oda_ayarlari_ui.py` | sys |
| Denetim Günlüğü | `ayarlar/audit_log_ui.py` | sys |
| Sistem Bakımı | `ayarlar/bakim_ui.py` | sys |
| Personel Departman Eşleştirme | `ayarlar/mapping_ui.py` | sys |
| Context Yönetimi | `ayarlar/context_ui.py` | sys |

---

## 5. VERİTABANI TABLOLARI (40 Tablo)

### 5.1 Çekirdek Tablolar (Dokunulmaz)

| Tablo | Açıklama |
|-------|----------|
| `personel` | Tüm kullanıcılar, RBAC, bcrypt şifreler |
| `ayarlar_moduller` | Modül kaydı, zone tanımı, aktif/pasif |
| `ayarlar_yetkiler` | Rol × Modül × Erişim matrisi |
| `ayarlar_bolumler` | Bölüm/departman listesi |
| `ayarlar_urunler` | Ürün tanımları |
| `sistem_parametreleri` | Global yapılandırma değerleri |
| `sistem_loglari` | Tüm işlem audit logu |
| `hata_loglari` | Uygulama hata kayıtları (AI diagnoz ile) |

### 5.2 Operasyonel Tablolar

| Tablo | Modül |
|-------|-------|
| `urun_kpi_kontrol` | KPI |
| `gmp` | GMP Denetimi |
| `hijyen` | Personel Hijyen |
| `temizlik_plani` | Temizlik Kontrol |
| `soguk_odalar`, `sicaklik_olcumleri` | Soğuk Oda |
| `depo_giris` | Üretim Girişi |

### 5.3 MAP Tabloları

| Tablo | İçerik |
|-------|--------|
| `map_vardiya` | Vardiya başlık kaydı |
| `map_zaman_cizelgesi` | Zaman çizelgesi olayları |
| `map_fire_kaydi` | Fire/kayıp kayıtları |
| `map_bobin_kaydi` | Bobin değişim kayıtları |

### 5.4 QDMS Tabloları

| Tablo | İçerik |
|-------|--------|
| `qdms_belgeler` | Doküman kaydı |
| `qdms_sablonlar` | Doküman şablonları |
| `qdms_revizyon_log` | Revizyon geçmişi |
| `qdms_yayim` | Yayın yönetimi |
| `qdms_talimatlar` | Talimatlar |
| `qdms_okuma_onay` | Okuma onay kayıtları |
| `qdms_gorev_karti` | Görev kartları (BRCGS) |
| `qdms_gk_sorumluluklar` | GK sorumluluk matrisi |
| `qdms_gk_etkilesim` | GK etkileşim birimleri |
| `qdms_gk_periyodik_gorevler` | Periyodik görevler |
| `qdms_gk_kpi` | GK KPI tanımları |

### 5.5 Performans Tabloları

| Tablo | İçerik |
|-------|--------|
| `performans_degerledirme` | Yetkinlik değerlendirme |
| `polivalans_matris` | Dönemsel polivalans özeti |

### 5.6 Diğer Tablolar

| Tablo | İçerik |
|-------|--------|
| `gunluk_gorev_katalogu` | Görev şablonları |
| `gunluk_periyodik_kurallar` | Tekrarlayan görev kuralları |
| `birlesik_gorev_havuzu` | Birleşik görev havuzu |
| `personel_vardiya_programi` | Haftalık vardiya planı |
| `qms_departmanlar` | QMS hiyerarşik departman yapısı |
| `qms_departman_turleri` | Departman türleri |
| `personel_transfer_log` | Personel transfer geçmişi |
| `personel_performans_skorlari` | Performans skor özeti |
| `kalici_oturumlar` | "Beni Hatırla" token kayıtları |

### 5.7 Ölü Tablolar (Flow Engine — Kullanılmıyor)
`flow_definitions`, `flow_nodes`, `flow_edges`, `flow_bypass_logs`, `personnel_tasks`

---

## 6. VERİ AKIŞI

```
Kullanıcı Girişi
      │
      ▼
  Cookie Kontrolü (extra_streamlit_components)
      │
      ├─ Token var → kalici_oturum_dogrula() → session_state yükle
      └─ Yok → Login formu → sifre_dogrula() → bcrypt + plaintext fallback
                                    │
                              yetki_haritasi_yukle()
                              (ayarlar_yetkiler JOIN ayarlar_moduller)
                                    │
                              session_state['yetki_haritasi']
                                    │
                    ┌───────────────▼───────────────────────┐
                    │          Sidebar Render                │
                    │  modul_gorebilir_mi() → menü listesi  │
                    └───────────────┬───────────────────────┘
                                    │ m_key seçimi
                              zone_gate(z) kontrolü
                                    │
                              Modül Fonksiyonu çağrısı
                                    │
                    ┌───────────────▼───────────────────────┐
                    │         Logic Katmanı                 │
                    │  data_fetcher (TTL cache)             │
                    │  db_writer (UPSERT)                   │
                    │  cache_manager (clear)                │
                    └───────────────┬───────────────────────┘
                                    │
                    ┌───────────────▼───────────────────────┐
                    │      Supabase / SQLite                │
                    │  audit_log_kaydet() her işlemde       │
                    └───────────────────────────────────────┘
```

---

## 7. ANAYASA (9 Temel Kural)

| # | Kural | Detay |
|---|-------|-------|
| 1 | **Zero Hardcode** | Sıcaklık limitleri, KPI eşikleri, toleranslar DB'de |
| 2 | **Turkish snake_case** | `veri_getir`, `bolum_filtrele` |
| 3 | **Max 30 satır/fonksiyon** | Her fonksiyon ≤30 satır |
| 4 | **Cache TTL ≤ 60s** | Yetki önbellekleri 60 saniyede sona erer |
| 5 | **ID-based sync yasak** | Çapraz-DB sync'te isimler/kodlar kullanılır |
| 6 | **UPSERT only** | `df.to_sql(replace)` yasak |
| 7 | **Maker/Checker** | Veri giren = onaylayan olamaz |
| 8 | **13th Adam Protokolü** | Mimari değişiklik öncesi karşı senaryo zorunlu |
| 9 | **Fail-Safe alarmlar** | CCP limit aşımları insan onayı beklemeden tetiklenir |

---

## 8. GÜVENLİK MİMARİSİ

### 8.1 Kimlik Doğrulama
- **Birincil:** bcrypt (`$2b$` formatı, 64-byte slice)
- **Fallback:** Plaintext (Grace period: 2026-06-15'e kadar — VAKA-026)
- **Lazy Migration:** İlk başarılı girişte plain → bcrypt otomatik güncellenir

### 8.2 Oturum Yönetimi
- **Cookie:** `extra_streamlit_components.CookieManager` ("Beni Hatırla")
- **Token:** `kalici_oturumlar` tablosu, 7 günlük geçerlilik
- **Session State:** `user`, `user_rol`, `user_id`, `yetki_haritasi`

### 8.3 Hata Kayıt Sistemi
```
Hata oluşur
    │
    ▼
logic/error_handler.py
    ├─ logs/error_blackbox.log (append, 1000 satır rotasyon)
    ├─ hata_loglari tablosu (Supabase)
    └─ AI Diagnosis (12 pattern)
           ├─ SQLite locked
           ├─ Timeout/connection
           ├─ StaleDataError
           ├─ KeyError, IndexError
           ├─ AttributeError/NoneType
           ├─ bcrypt errors
           └─ ...

Bulut Sync:
    logic/hata_sync.py → logs/hata_loglari/YYYY-MM-DD_hata.jsonl
    scripts/hata_sync_daemon.py (arka planda, 5 dakika interval)
```

---

## 9. AÇIK VAKALAR VE TEKNİK BORÇ

### 9.1 Açık Güvenlik Vakaları

| ID | Öncelik | Konu | Konum |
|----|---------|------|-------|
| VAKA-025 | 🔴 KRİTİK | Plaintext şifre görünürlüğü (st.data_editor) | `ui/ayarlar/personel_ui.py` |
| VAKA-026 | 🟠 YÜKSEK | Lazy bcrypt tamamlanmamış (hiç giriş yapmayan personel) | `logic/auth_logic.py` |
| VAKA-027 | 🟡 ORTA | Mobil navigasyon eski anahtar uyumsuzluğu | `app.py` sidebar |

### 9.2 Teknik Borç

| Alan | Sorun | Öneri |
|------|-------|-------|
| Flow Engine | 5 tablo ölü kod | Silinmeli |
| constants.py | Pozisyon/vardiya hardcoded | DB'ye taşınmalı |
| Test kapsamı | ~%38 (8/13 modülde test yok) | Test eklenecek modüller: MAP, performans, vardiya, raporlama |
| 30 satır limiti | 8 fonksiyon aşıyor | Refactor |
| `mapping_ui.py` | dept_options çift DB çağrısı | Tek seferlik çekmeye refactor |

---

## 10. ÖNEMLİ DOSYA DİZİNİ

```
app.py                          — Streamlit giriş noktası
constants.py                    — Org hiyerarşi, pozisyon seviyeleri
AGENTS.md                       — Ajan rolleri ve iş akışı
CLAUDE.md                       — Proje rehberi ve Anayasa

database/
  connection.py                 — Engine, schema init, bootstrap
  schema_qdms.py               — QDMS tablo tanımları

logic/
  auth_logic.py                — Kimlik doğrulama, RBAC, audit log
  zone_yetki.py                — 3 katmanlı zone erişim sistemi
  cache_manager.py             — Merkezi cache temizleme
  data_fetcher.py              — TTL cache'li veri çekme
  error_handler.py             — Hata kayıt + AI diagnoz
  hata_sync.py                 — Supabase → yerel JSONL sync
  settings_logic.py            — Ayarlar iş mantığı
  context_manager.py           — Context yönetimi

ui/
  [modül]_ui.py                — Her modülün UI katmanı
  ayarlar/
    ayarlar_orchestrator.py    — Ayarlar ana yönlendirici
    audit_log_ui.py            — Denetim günlüğü + bulut analiz
    bakim_ui.py                — Modül erişim tarayıcı dahil
    mapping_ui.py              — Personel departman eşleştirme
    personel_ui.py             — ⚠️ VAKA-025 (şifre görünürlüğü)

modules/
  qdms/
    pdf_uretici.py             — ReportLab sunucu PDF üretimi
    gorev_karti.py             — BRCGS Görev Kartı
  gunluk_gorev/ui.py          — Günlük görev modülü
  vardiya/ui.py                — Vardiya yönetimi

scripts/
  hata_sync_daemon.py          — Arka plan hata sync (--interval 300s)
  bootstrap_local.py           — Yerel SQLite başlatma

logs/
  error_blackbox.log           — Yerel hata logu (append, 1000 satır)
  hata_loglari/                — YYYY-MM-DD_hata.jsonl dosyaları

.antigravity/musbet/hafiza/
  hafiza_ozeti.md              — Kolektif hafıza özeti (OKUNMADAN BAŞLAMA)
  acik_vakalar.md              — Açık vakalar
  cozulmus_vakalar.md          — Çözülen vakalar
  lessons.md                   — Öğrenilen dersler
  sistem_haritasi.md           — Sistem haritası (detaylı)
```

---

## 11. KARŞILAŞTIRMALI ÇEVRE TABLOSU

| Özellik | Geliştirme (SQLite) | Üretim (Supabase) |
|---------|---------------------|-------------------|
| Bağlantı | Yerel dosya | PostgreSQL TCP |
| Pool | Yok | size=5, overflow=10 |
| WAL | Evet | — |
| secrets.toml | Yok (fallback) | `DB_URL` gerekli |
| Timezone | Sistem | Europe/Istanbul |
| AUTOCOMMIT | Hayır | Schema init için Evet |

---

*Bu dosya `logic/`, `database/`, `ui/`, `modules/`, `AGENTS.md`, `CLAUDE.md` ve `.antigravity/musbet/hafiza/` analizi sonucu otomatik üretilmiştir.*
*Güncelleme: `2026-04-02` — EKLERİSTAN QMS Stabilizasyon Sprint*
