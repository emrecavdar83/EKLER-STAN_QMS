# EKLERİSTAN QMS — 360° Modül & Arayüz Derin Analiz Rehberi
> **Versiyon:** 6.0 (Kod Taramalı, Tam Kapsam)
> **Son Güncelleme:** 2026-03-29
> **Kapsam:** Tüm UI modülleri, tüm alt sekmeler, tüm butonlar — doğrudan kaynak koddan çekilmiştir.

---

## İÇİNDEKİLER

1. [Sistem Geneli SWOT & Mimari](#1-sistem-geneli-swot--mimari)
2. [Veri Akış Mimarisi](#2-veri-akış-mimarisi)
3. [Kritik İş Kuralları Tablosu](#3-kritik-iş-kuralları-tablosu)
4. [Portal — Merkezi Dashboard](#4-portal--merkezi-dashboard)
5. [QDMS — Kalite Doküman Yönetimi](#5-qdms--kalite-doküman-yönetimi)
6. [MAP Üretim — OEE & Vardiya Kontrol](#6-map-üretim--oee--vardiya-kontrol)
7. [KPI & Kalite Kontrol](#7-kpi--kalite-kontrol)
8. [GMP Denetimi](#8-gmp-denetimi)
9. [Personel Hijyen Kontrol](#9-personel-hijyen-kontrol)
10. [Temizlik Kontrol](#10-temizlik-kontrol)
11. [Soğuk Oda Takip (SOSTS)](#11-soğuk-oda-takip-sosts)
12. [Raporlama Merkezi](#12-raporlama-merkezi)
13. [Performans & Polivalans](#13-performans--polivalans)
14. [Ayarlar & Yönetim Paneli](#14-ayarlar--yönetim-paneli)
15. [Ajan Kullanım Protokolü](#15-ajan-kullanım-protokolü)

---

## 1. SİSTEM GENELİ SWOT & MİMARİ

### Teknik Mimari Direkleri

| Katman | Teknoloji | Dosya | Kural |
| :--- | :--- | :--- | :--- |
| **UI Çerçevesi** | Streamlit (Python) | `app.py` (~5000 satır) | Tüm routing buradan |
| **Veritabanı (Prod)** | Supabase / PostgreSQL | `database/connection.py` | `with eng.begin()` zorunlu |
| **Veritabanı (Dev)** | SQLite WAL mode | `ekleristan_local.db` | `secrets.toml` yoksa otomatik |
| **Önbellek** | `@st.cache_data / @st.cache_resource` | `logic/cache_manager.py` | TTL ≤ 60s (Anayasa Md.13) |
| **RBAC** | Zone bazlı (ops/mgt/sys) | `logic/auth_logic.py` | `kullanici_yetkisi_getir_dinamik()` |
| **PDF Üretimi** | ReportLab (server-side) | `modules/qdms/pdf_uretici.py` | `window.print()` yasak |
| **Canlı Sayaç** | HTML + JS Enjeksiyonu | `ui/map_uretim/map_uretim.py` | `st.components.v1.html()` |
| **Zone Yetki** | `zone_girebilir_mi()` | `logic/zone_yetki.py` | `eylem_yapabilir_mi()` |
| **Veri Yazma** | `db_writer.py` | `logic/db_writer.py` | Merkezi yazma katmanı |

### Genişletilmiş SWOT

| **GÜÇLÜ YÖNLER** | **ZAYIF YÖNLER** |
| :--- | :--- |
| Cloud-Primary: Supabase/PostgreSQL canlı senkronizasyon | Streamlit Rerun Maliyeti: VAKA-008 tipi state çakışmaları (Öneri: `st.fragment`) |
| Katı Anayasa (Madde 1-23): Kod kalitesi garantisi | 8 fonksiyon 30 satır limitini aşıyor (Anayasa Md.12 — `hafiza_ozeti.md`) |
| Zone RBAC: ops/mgt/sys güvenlik katmanı | Test kapsanması %38 — 13/8 modülde test dosyası yok |
| Maker/Checker ilkesi (Anayasa Md.7) | `constants.py` hardcoded pozisyon/vardiya tanımları DB'ye taşınmamış |
| JS Timer Enjeksiyonu: Sayfa yenilemesiz canlı sayaç | Raporlama `window.print()` yerine HTML+CSS yazdırma (tarayıcıya bağımlı) |
| Audit Log: Her kritik işlemde iz kaydı | `get_user_roles()`, `render_sync_button()` emekli fonksiyonlar hâlâ kodda |

| **FIRSATLAR** | **TEHDİTLER** |
| :--- | :--- |
| `st.fragment` ile kısmi render (Streamlit 1.37+) | Flow Engine (5 tablo) hiçbir UI'ye bağlı değil — beklenmedik migration riski |
| IoT sensör API entegrasyonu (SOSTS Manuel → Otomatik) | Migration hatalarının kritik üretim verilerini etkilemesi (VAKA-003 örüntüsü) |
| AI destekli fire ve OEE tahminleme | Emekli kodların yeni geliştirmeleri kirletmesi (Teknik Borç) |

---

## 2. VERİ AKIŞ MİMARİSİ

```
[KULLANICI GİRİŞİ]
       │
       ▼
  ui/*.py  ──(RBAC Kontrolü)──▶  logic/auth_logic.py
       │                              │
       │                    kullanici_yetkisi_var_mi()
       │                    eylem_yapabilir_mi()
       │                              │
       ▼                              ▼
  logic/db_writer.py          logic/zone_yetki.py
  [YAZMA KATMANI]             [ZONE FİLTRESİ]
       │
       │  ⚠️ ZORUNLU: with eng.begin() as conn:
       │  (eng.connect() kullanılırsa sessiz hata — VAKA-003)
       ▼
  database/connection.py
  [SQLAlchemy Engine — @st.cache_resource]
       │
       ├──▶ Supabase/PostgreSQL (prod — secrets.toml varsa)
       └──▶ SQLite WAL (dev — secrets.toml yoksa)
       │
       ▼
  logic/data_fetcher.py
  [OKUMA KATMANI — TTL önbellekli]
       │
       ▼
  logic/cache_manager.py
  [ÖNBELLEK YÖNETİMİ — Tüm clear() buradan]
       │
       ▼
  [ÇIKTI]
       ├──▶ st.dataframe / st.metric  (UI)
       ├──▶ pdf_uretici.py            (ReportLab PDF)
       └──▶ sync_handler.py           (Supabase ↔ SQLite)
```

**Kritik Kural:** Her yeni UI bileşeni bu akışın dışına çıkmamalıdır. `engine.connect()` doğrudan UI'de kullanılmamalı — `data_fetcher.py` veya `db_writer.py` üzerinden geçilmeli.

---

## 3. KRİTİK İŞ KURALLARI TABLOSU

| Anayasa Maddesi | Kural Özeti | Kod Lokasyonu | Güncel Durum |
| :--- | :--- | :--- | :--- |
| **Madde 1** | Sıfır Hardcode | `constants.py` | ⚠️ Pozisyon/vardiya tanımları hardcoded |
| **Madde 3** | Cache Clear → cache_manager | `logic/cache_manager.py` | ✅ Uyumlu |
| **Madde 6** | Audit Log zorunlu | `logic/auth_logic.py:audit_log_kaydet()` | ✅ MAP, QDMS'de aktif |
| **Madde 7** | Maker/Checker | `auth_logic.py` | ✅ QDMS onay akışında aktif |
| **Madde 9** | Fail-Safe CCP Alarmı | `soguk_oda_utils.py` | ✅ SOSTS'ta limit aşımında otomatik |
| **Madde 12** | Max 30 satır/fonksiyon | Tüm codebase | ❌ 8 fonksiyon ihlaliyor |
| **Madde 13** | Cache TTL ≤ 60s | `cache_manager.py` | ✅ Uyumlu |
| **Madde 15** | E2E Test zorunlu | `tests/` | ❌ %38 kapsanma |
| **Madde 19** | Yüksek uyum seviyesi | `ui/qdms_ui.py` | ✅ GK 10 bölüm yapısı |
| **Madde 23** | Bart Simpson (Çift Key) | Tüm `st.form` | ✅ Dinamik key şeması |

---

## 4. PORTAL — Merkezi Dashboard

> **Zone:** `ALL` | **Dosya:** `ui/portal/portal_ui.py` | **Tablo:** `birlesik_gorev_havuzu`, `personel`

### Teknik Mimari

- Sekmesiz tek sayfa yapısı
- Session state'den `available_modules` listesi okunur (`app.py` tarafından doldurulur)
- Kişisel istatistikler için `personel_id` → `birlesik_gorev_havuzu` join sorgusu

### Arayüz Haritası

```
📋 GÜNLÜK ÖZET
  ├── [METRIC] Bekleyen Görev (delta: "-Acil" / "Tamam")
  ├── [METRIC] Tamamlanan Görev
  └── [METRIC] Sistem Durumu ("Aktif / Bulut Senkronize")

🚀 HIZLI ERİŞİM MODÜLLERİ
  └── [KART GRİD — 3 Sütun] Yetkili modüller (HTML card, mavi sol border)
```

### Yetki Matrisi

| Rol | Görüntü |
| :--- | :--- |
| PERSONEL | Kendi görev sayılarını görür |
| YÖNETİCİ | Kendi görev sayılarını görür |
| ADMIN | Kendi görev sayılarını görür (portal istatistikleri kişisel) |

### Analiz

- **Teknik Borç Skoru: 2/5** — Fallback `personel_id = 1` hardcoded satırı var (`portal_ui.py:26`)
- **CSF:** Dashboard yükleme süresi < 2 saniye; modül kartı eksikliğinin %0 olması
- **Dokunulmazlık:** `available_modules` listesi `app.py`'de set edilir — portal_ui.py'de değiştirilmemelidir

---

## 5. QDMS — Kalite Doküman Yönetimi

> **Zone:** `mgt` | **Dosya:** `ui/qdms_ui.py` + `modules/qdms/*`
> **Tablolar:** `qdms_belgeler`, `qdms_revizyon_log`, `qdms_talimatlar`, `qdms_okuma_onay`, `qdms_gorev_karti`, `qdms_gk_sorumluluklar`, `qdms_gk_etkilesim`, `qdms_gk_periyodik_gorevler`, `qdms_gk_kpi`

### Teknik Mimari

- **JSON Schema Engine:** GK editörü pipe-separated text alanlarını parse ederek JSON'a dönüştürür
- **Shadow Tables:** GK verisi `qdms_gorev_karti` ana tablo + 4 alt tablo (sorumluluklar, etkileşimler, periyodik, KPI)
- **QR Kod:** `qrcode` kütüphanesi ile her belge için üretilir
- **ReportLab PDF:** `modules/qdms/pdf_uretici.py` — server-side, tarayıcısız
- **Belge Tipleri:** GK, SO, TL, PR, KYS, FR, PL, GT, LS, KL, YD, SOP (12 tip)

### Ana Sekme Yapısı: 4 Tab

---

#### TAB 1 — 📋 Doküman Merkezi (`qdms_dokuman_merkezi_content`)

```
[FİLTRE SATIRI — 3 Sütun]
  ├── [TEXT INPUT] 🔍 Belge Ara  (key: dm_search)
  ├── [SELECTBOX]  Belge Tipi   (12 seçenek: GK, SO, TL, PR, KYS, FR, PL, LS, KL, GT, YD, SOP)
  └── [SELECTBOX]  Durum        (Tümü / aktif / taslak / incelemede / arsiv)

[BELGE LİSTESİ — Her satır st.container(border=True)]
  Her belge kartı:
  ├── Belge Kodu + Rev No
  ├── Belge Adı + Tip + Alt Kategori
  ├── Durum badge (renk: yeşil=aktif, gri=taslak, turuncu=incelemede, kırmızı=arsiv)
  ├── [BUTTON] 📄 PDF   (key: pdf_{belge_kodu})
  │     └── → Spinner → full_veri çek → pdf_uret() → [DOWNLOAD BUTTON] 📥 İndir
  └── [BUTTON] 👁️ ÖNİZLE (key: pre_{belge_kodu})
        └── → @st.dialog "Belge Önizleme" (width=large)
              GK belgesi için: 4 iç sekme
              ├── 1-3. Profil & Özet (Pozisyon, Departman, Amir, Vekil, Zone, Vardiya, Görev Özeti)
              ├── 4. Sorumluluklar   (5 disiplin: Personel, Operasyon, Gıda Güv., İSG, Çevre)
              ├── 5-7. Yetki & Etkileşim (Finansal yetki TL, İmza, RACI tablosu, Periyodik görevler)
              └── 8-10. Yetkinlik & KPI (Eğitim, Deneyim, Sertifikalar, KPI listesi, Onay notu)
              Diğer belgeler için: amac alanı düz metin
```

---

#### TAB 2 — ⚙️ Yönetim (`qdms_belge_yonetimi_content`)

```
[EXPANDER] ➕ YENİ BELGE OLUŞTUR (varsayılan kapalı)
  └── [FORM] yeni_belge_form
        ├── [SELECTBOX] Belge Tipi (10 seçenek: GK, SO, TL, PR, KYS, FR, PL, LS, KL, SOP)
        ├── [TEXT INPUT] Belge Kodu  (otomatik öneri: belge_kodu_oner())
        ├── [TEXT INPUT] Belge Adı
        ├── [TEXT INPUT] Alt Kategori / Bölüm
        └── [FORM SUBMIT] "Oluştur"  → belge_olustur() → st.rerun()

[DATAFRAME] Mevcut belgeler (kodu, adı, tipi, durumu, rev)

[SELECTBOX] Düzenlenecek Belgeyi Seçin
[BUTTON] 📝 DÜZENLEYİCİYİ AÇ
  └── → @st.dialog "BRC/IFS Görev Kartı & Doküman Editörü" (width=large)
```

**GK Editörü Dialog (8 İç Sekme, tek form: gk_edit_{belge_kodu})**

```
[SEKME 1] 1-2. Profil
  ├── [TEXT INPUT] Pozisyon Adı
  ├── [TEXT INPUT] Departman
  ├── [TEXT INPUT] Bağlı Pozisyon (Amir)
  ├── [TEXT INPUT] Vekâlet Eden
  ├── [TEXT INPUT] Zone / Çalışma Yeri
  └── [TEXT INPUT] Vardiya Türü

[SEKME 2] 3. Özet
  └── [TEXT AREA] Genel Görev Amacı / Özeti

[SEKME 3] 4. Sorumluluklar
  ├── [TEXT AREA] 👥 Personel Sorumlulukları    (her satır = 1 sorumluluk)
  ├── [TEXT AREA] ⚙️ Operasyonel Sorumluluklar
  ├── [TEXT AREA] 🛡️ Gıda Güvenliği Sorumlulukları
  ├── [TEXT AREA] ⚠️ İSG Sorumlulukları
  └── [TEXT AREA] 🌱 Çevre Sorumlulukları

[SEKME 4] 5. Yetkiler
  ├── [TEXT INPUT]  Finansal Yetki (TL)
  ├── [TEXT AREA]   İmza Yetkisi
  └── [TEXT AREA]   Vekâlet Koşulları

[SEKME 5] 6. Etkileşim
  └── [TEXT AREA]   Süreçler Arası Etkileşim
                    Format: Taraf | Konu | Sıklık | RACI

[SEKME 6] 7. Periyodik
  └── [TEXT AREA]   Periyodik Görevler
                    Format: Görev | Periyot | Talimat Kodu | Sertifikasyon

[SEKME 7] 8. Nitelik
  ├── [TEXT INPUT]   Eğitim Gereksinimi
  ├── [NUMBER INPUT] Min. Deneyim (Yıl)
  ├── [TEXT AREA]    Zorunlu Sertifikalar (JSON Liste)
  └── [TEXT AREA]    Tercihli Nitelikler

[SEKME 8] 9. KPI
  └── [TEXT AREA]   Performans Göstergeleri
                    Format: KPI Adı | Birim | Hedef | Periyot | Değerlendirici

[FORM SUBMIT] 💾 GÖREV KARTINI KAYDET VE YAYINLA
  → Parse (5 disiplin + etkileşim + periyodik + KPI)
  → gk_kaydet() → UPSERT → st.rerun()

[DİĞER BELGELER FORMU] doc_edit_{belge_kodu}
  ├── [TEXT INPUT] Belge Adı
  ├── [TEXT AREA]  1. AMAÇ
  ├── [TEXT AREA]  4. UYGULAMA
  └── [FORM SUBMIT] 💾 DÖKÜMANI GÜNCELLE → belge_guncelle()
```

---

#### TAB 3 — 📖 Talimatlar (`qdms_talimat_content`)

```
Alt sekmeler: ["Talimat Oluştur", "Onay Bekleyenler"]

[SUB-TAB 1] Talimat Oluştur
  └── [FORM] talimat_form
        ├── [TEXT INPUT]  Kod (EKL-TL-001)
        ├── [TEXT INPUT]  Adı
        ├── [TEXT AREA]   Adımlar (JSON array)
        └── [FORM SUBMIT] Kaydet → talimat_olustur()

[SUB-TAB 2] Onay Bekleyenler
  └── okunmayan_talimatlar() ile liste (henüz arayüz minimal)
```

---

#### TAB 4 — 📊 Uyumluluk (`qdms_uyumluluk_content`)

```
[METRIC] BRC Uyum Skoru (%)
[PROGRESS BAR] 0-100
  └── uyumluluk_ozeti_getir() → `brc_uyum_skoru`
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Talimat okuma/onaylama (TL tipi belgeler) |
| YÖNETİCİ | Belge oluşturma, revizyon başlatma |
| ADMIN | Arşivleme, şablon düzenleme, belge silme |

### Analiz

- **Teknik Borç Skoru: 2/5** — Belge editörü pipe-parse fragile; JSON editör daha sağlam olur
- **CSF:** Tüm aktif belgelerin rev_no güncel; taslak belge birikmemesi
- **Dokunulmazlık:** `qdms_gk_*` alt tablolarına QDMS dışından UPSERT yapılmamalı

---

## 6. MAP ÜRETİM — OEE & Vardiya Kontrol

> **Zone:** `ALL/ops` | **Dosya:** `ui/map_uretim/map_uretim.py`
> **Tablolar:** `map_vardiya`, `map_zaman_cizelgesi`, `map_fire_kaydi`, `map_bobin_kaydi`

### Teknik Mimari

- **JS Timer Enjeksiyonu:** `_render_live_timer()` → `st.components.v1.html()` — Sayfa yenilemesi olmadan saniye hassasiyetinde sayaç
- **Smart Timer:** `endTime` parametresi ile kapalı vardiyanın saydırmayı durdurması
- **Anti-Çift-Tık Koruması:** `_is_click_safe()` — 0.4 sn debounce
- **Mobil CSS:** Büyük butonlar (75px yüksek), touch-friendly, `@media (max-width: 640px)` responsive

### Makine Listesi

`MAP-01`, `MAP-02`, `MAP-03` — `map_uretim.py:12` (⚠️ Anayasa Md.1 ihlali — DB'ye taşınmalı)

### Ana Sekme Yapısı: 3 Tab

---

#### TAB 1 — Vardiya

```
[DURUM GÖSTERGE — Sidebar/State'den makine seçimi]
  get_aktif_vardiya_live() → Live Check (önbelleksiz)

[AKTİF VARDİYA GÖRÜNÜMÜ — ACIK ise]
  ├── [SUCCESS BANNER] 🟢 Makina | Vardiya No | Başlangıç
  ├── [CAPTION] Operatör + Şef
  ├── [TEXT AREA] Vardiya Notu (key: not_{vardiya_id})
  └── [POPOVER] 🔴 VARDİYASINI KAPAT
        ├── [WARNING] Onay mesajı
        ├── [NUMBER INPUT] Final Üretim Adedi (key: final_{vardiya_id})
        └── [BUTTON] EVET, KAPAT (primary, key: btn_kapat_{vardiya_id})
              → kapat_vardiya() → state temizliği → st.rerun()

[KAPALI VARDİYA GÖRÜNÜMÜ — KAPALI ise]
  └── [INFO] 🏁 Özet bilgi (minimal)

[EXPANDER] ➕ Yeni Makine (Vardiya) Başlat
  └── [FORM] yeni_vardiya_baslatma_formu  (sabit key — time.time() yasak)
        ├── [SELECTBOX]    🏭 Makina Seçin     (sadece boştaki makineler)
        ├── [SELECTBOX]    ⏰ Vardiya No       (1, 2, 3)
        ├── [TEXT INPUT]   👷 Operatör Adı     (disabled — oturum kullanıcısı)
        ├── [TEXT INPUT]   👔 Vardiya Şefi     (opsiyonel)
        ├── [NUMBER INPUT] Besleme Kişi        (0-20)
        ├── [NUMBER INPUT] Kasalama Kişi       (0-20)
        ├── [NUMBER INPUT] 🎯 Hedef Hız pk/dk  (0.1-20.0, step=0.1)
        └── [FORM SUBMIT]  🟢 MAKİNEYİ BAŞLAT (primary)
              → aç_vardiya() → insert_zaman_kaydi("CALISIYOR") → state güncelle → st.rerun()
```

---

#### TAB 2 — Kontrol Merkezi

```
[DURUM BARSI — 3 Sütun]
  ├── [HTML DIV] Makina Durumu (🟢 ÜRETİM / 🔴 DURUŞ / 🏁 TAMAMLANDI)
  ├── [JS TIMER] Durum Süresi (saniye hassasiyetli, canlı)
  └── [JS TIMER] Toplam Vardiya Süresi (saniye hassasiyetli, canlı)

[DIVIDER]

[İKİ KOLON KONTROL PANELİ]

SOL KOLON — ⚡ Duruş Yönetimi:
  CALISIYOR durumunda: 8 duruş nedeni butonu
    ├── [BUTTON] 🔻 ÜST FİLM DEĞİŞİMİ      (key: durus_0)
    ├── [BUTTON] 🔻 ALT FİLM DEĞİŞİMİ      (key: durus_1)
    ├── [BUTTON] 🔻 MOLA / YEMEK            (key: durus_2)
    ├── [BUTTON] 🔻 ARIZA / BAKIM           (key: durus_3)
    ├── [BUTTON] 🔻 SETUP / AYAR            (key: durus_4)
    ├── [BUTTON] 🔻 ÜRETİM BEKLEME          (key: durus_5)
    ├── [BUTTON] 🔻 TEMİZLİK / SANİTASYON   (key: durus_6)
    └── [BUTTON] 🔻 DİĞER                   (key: durus_7)
          → insert_zaman_kaydi("DURUS", neden=ned) → st.rerun()

  DURUS durumunda:
    └── [BUTTON] 🟢 İŞE BAŞLA (primary, key: btn_ise_basla)
          → insert_zaman_kaydi("CALISIYOR") → st.rerun()

SAĞ KOLON — 📦 Üretim & Kayıplar:
  [EXPANDER] ➕ Üretim Ekle (expanded=True)
    ├── [NUMBER INPUT] Eklenen Paket Adedi  (0-10000, step=10)
    ├── [BUTTON] ➕ ÜRETİMİ TOPLA VE KAYDET (primary)
    │     → update_kumulatif_uretim() → st.toast → st.rerun()
    └── [CAPTION] Güncel Toplam

  [POPOVER] 🔥 Fire Ekle
    ├── [NUMBER INPUT] Eklenecek Fire Adedi (1-1000)
    └── 9 fire tipi butonu:
        ├── [BUTTON] ➕ Bobin Başı Fire         (key: fire_in_0)
        ├── [BUTTON] ➕ Bobin Sonu Fire          (key: fire_in_1)
        ├── [BUTTON] ➕ Film Değişimi Fire        (key: fire_in_2)
        ├── [BUTTON] ➕ Sızdırmazlık / Kaçak     (key: fire_in_3)
        ├── [BUTTON] ➕ Yırtık / Delik Film      (key: fire_in_4)
        ├── [BUTTON] ➕ Gaz Hatası               (key: fire_in_5)
        ├── [BUTTON] ➕ Besleme Hatası           (key: fire_in_6)
        ├── [BUTTON] ➕ Operatör Hatası          (key: fire_in_7)
        └── [BUTTON] ➕ Diğer                    (key: fire_in_8)
              → insert_fire() → st.toast → st.rerun()

  [BUTTON] 🎞️ Bobin Değiştir (toggle)
    └── [FORM] bobin_form_konsol (state.map_bobin_form ile toggle)
          ├── [TEXT INPUT]   📦 LOT No
          ├── [SELECTBOX]    🎞️ Film Tipi  (Üst Film / Alt Film)
          ├── [NUMBER INPUT] Yeni Bobin (KG)  (0-100)
          ├── [NUMBER INPUT] Kalan Eskisi (KG) (0-100)
          └── [FORM SUBMIT]  ✅ BOBİNİ KAYDET → insert_bobin()

[ADMIN PANELİ — Yetki gerekli]
  [EXPANDER] ⚠️ Admin Üretim Düzeltme
    ├── [WARNING] Uyarı metni
    ├── [NUMBER INPUT] Yeni Net Toplam Miktar (key: new_total_val)
    ├── [TEXT INPUT]   Düzeltme Nedeni (Zorunlu) (key: adj_reason_net)
    └── [BUTTON] ⚠️ NET TOPLAMI GÜNCELLE VE KAYDET (primary)
          → set_net_uretim() + audit_log_kaydet("MAP_URETIM_DUZELTME_NET")

[EXPANDER] 🕒 Zaman Çizelgesi ve Geçmiş
  ├── [DATAFRAME] Zaman çizelgesi
  ├── [BUTTON] 🗑️ Son Zaman Kaydını Sil → sil_son_zaman_kaydi()
  ├── [DATAFRAME] Son Bobinler (sira_no, degisim_ts, bobin_lot, kullanilan_m)
  └── [DATAFRAME] Son Fireler (fire_tipi, miktar_adet, olusturma_ts)
```

---

#### TAB 3 — 📊 Rapor (Canlı Vardiya Dashboard)

```
[4 KPI KARTI — Üst Satır]
  ├── [METRIC] 📦 Üretim  (gerçekleşen / teorik hedef)
  ├── [METRIC] OEE Kullanılabilirlik (%)
  ├── [METRIC] 🔥 Fire (% / adet)
  └── [METRIC] 🚀 Hız (pk/dk / hedef farkı %)

[4 SÜRE METRİĞİ — Alt Satır]
  ├── [METRIC] ⏱️ Toplam Vardiya (dk)
  ├── [METRIC] 🟢 Toplam Çalışma (dk)
  ├── [METRIC] 🔴 Toplam Duruş (dk)
  └── [METRIC] ☕ Mola (dk)

[2 GRAFİK KOLONU]
  ├── [BAR CHART] ⏱️ Duruş Dağılımı (Neden → Dakika)
  └── [PIE/BAR]   🔥 Fire Dağılımı (Tip → Adet)
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Vardiya başlatma/kapama, duruş/fire/bobin girişi |
| YÖNETİCİ | Tüm sekmeleri görüntüleme, OEE analizi |
| ADMIN | Admin Düzeltme Paneli (audit log ile) |

### Analiz

- **Teknik Borç Skoru: 3/5** — `MAP_MAKINA_LISTESI` hardcoded, mobil çift-tık riski `_is_click_safe()` ile çözülmüş ama 0.4s keyfi değer
- **CSF:** OEE veri bütünlüğü admin düzeltmesi olmadan ≥ %90, vardiya kapanma oranı ≥ %95
- **Dokunulmazlık:** `map_zaman_cizelgesi` tablosuna manual INSERT yapılmamalı — `insert_zaman_kaydi()` zorunlu

---

## 7. KPI & KALİTE KONTROL

> **Zone:** `mgt/ops` | **Dosya:** `ui/kpi_ui.py`
> **Tablolar:** `urun_kpi_kontrol`, `ayarlar_urunler`, `urun_parametreleri`

### Teknik Mimari

- **Dinamik Numune Formu:** `numune_sayisi` DB'den gelir, form alanları runtime üretilir
- **BRC Kanıt Kaydı:** STT fotoğrafı hem diske (`data/uploads/kpi/`) hem Base64 DB'ye kaydedilir (silinmez kanıt)
- **Karar Mantığı:** `tat == "Uygun" AND goruntu == "Uygun"` → `karar = "ONAY"`, aksi → `karar = "RED"`

### Sekme Yapısı: 2 Tab

---

#### TAB 1 — 📏 Yeni Ölçüm Girişi

```
[ÜRÜN SEÇİM SATIRI — 2 Sütun]
  ├── [SELECTBOX]  Ürün Seçin       (bolum_bazli_urun_filtrele() — yetki bazlı)
  ├── [TEXT INPUT] Lot No           (placeholder: Üretim Lot No)
  ├── [SELECTBOX]  Vardiya          (GÜNDÜZ / ARA / GECE — key: kpi_v)

[FORM] kpi_form
  [ÖN KONTROLLER]
    ├── [CHECKBOX]      STT ve Etiket Bilgisi Doğrudur
    └── [FILE UPLOADER] 📸 STT Etiket Fotoğrafı (zorunlu, key: stt_foto_upload)
                        (jpg/png/jpeg)

  [ÖLÇÜM DEĞERLERİ — N Numune, N = DB'den]
    Her numune için (#1, #2, ...):
    └── [NUMBER INPUT] × (parametre sayısı)  (key: n{i}_p{p_idx}, step=0.1)

  [DUYUSAL KONTROL]
    ├── [SELECTBOX] Tat / Koku    (Uygun / Uygun Değil)
    ├── [SELECTBOX] Görüntü / Renk (Uygun / Uygun Değil)
    └── [TEXT AREA] Kalite Notu / Açıklama

  [FORM SUBMIT] ✅ Analizi Kaydet
    → Karar mantığı → Foto kaydet (disk + Base64 DB) → guvenli_kayit_ekle()
    → st.toast → st.rerun()
```

#### TAB 2 — 📊 Ölçüm Geçmişi

```
[INFO] Raporlama modülüne yönlendirme
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Yetki verilirse form doldurma |
| YÖNETİCİ | Ölçüm geçmişi, limit belirleme |
| ADMIN | Ürün parametresi tanımlama |

### Analiz

- **Teknik Borç Skoru: 2/5** — `avg_val1/2/3` legacy uyumluluk için ilk 3 parametreye sabitlenmiş
- **CSF:** Her ölçümde STT fotoğrafı mevcut; RED kararları DÖF akışına bağlanmış
- **Dokunulmazlık:** `urun_kpi_kontrol` tablosunda `foto_b64` sütunu silinmez (BRC kanıt gerekliliği)

---

## 8. GMP DENETİMİ

> **Zone:** `ALL` | **Dosya:** `ui/gmp_ui.py`
> **Tablolar:** `gmp_soru_havuzu`, `gmp_denetim_kayitlari`, `ayarlar_bolumler`

### Teknik Mimari

- **Frekans Motoru:** `_gmp_frekans_hesapla()` — GÜNLÜK her gün, HAFTALIK sadece Pazartesi (weekday=0), AYLIK sadece ayın 1'i
- **13. Adam Koruması:** `st.form` kullanılmaz (dinamik dosya yükleyiciler form içinde çalışmaz — Streamlit kısıtı)
- **Tip Koruması:** `CAST(aktif AS INTEGER) = 1` — SQLite/PostgreSQL boolean uyumsuzluğu önlemi

### Arayüz Haritası (Sekmesiz)

```
[BAŞLIK] 🛡️ GMP DENETİMİ
[CAPTION] Bugünün Frekansı: GÜNLÜK / HAFTALIK / AYLIK

[SELECTBOX] Denetim Yapılan Bölüm (lokasyon_id → bölüm adı)

[SORU LİSTESİ — st.container(border=True) her soru]
  Her soru kartı:
  ├── [MARKDOWN] Soru metni (bold)
  ├── [CAPTION]  Kategori | BRC Ref | Risk Puanı
  └── [RADIO]    Durum: UYGUN / UYGUN DEĞİL (key: gmp_q_{lok_id}_{soru_id})

  UYGUN DEĞİL seçilirse:
    Risk = 3 (Kritik) ise:
      ├── [WARNING] 🚨 KRİTİK BULGU! Fotoğraf zorunludur.
      └── [FILE UPLOADER] ⚠️ Fotoğraf (key: foto_{lok_id}_{soru_id})
    └── [TEXT AREA] Hata Açıklaması / Düzeltici Faaliyet (key: not_{lok_id}_{soru_id})

[BUTTON] ✅ Denetimi Tamamla ve Gönder (use_container_width=True)
  → Kritik soru fotoğraf kontrolü → INSERT INTO gmp_denetim_kayitlari → st.toast → st.rerun()
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Denetim formu doldurma |
| YÖNETİCİ | Denetim geçmişi (Raporlama'dan) |
| ADMIN | Soru havuzu yönetimi (Ayarlar'dan) |

### Analiz

- **Teknik Borç Skoru: 2/5** — `frekans_filtre` f-string SQL injection riski düşük ama parameterize edilmeli
- **CSF:** Kritik (Risk=3) bulgularda fotoğrafsız kayıt %0
- **Dokunulmazlık:** `gmp_soru_havuzu` sadece Ayarlar/GMP Sorular sekmesinden düzenlenmeli

---

## 9. PERSONEL HİJYEN KONTROL

> **Zone:** `ALL` | **Dosya:** `ui/hijyen_ui.py`
> **Tablolar:** `hijyen_kontrol_kayitlari`, `personel`, `ayarlar_bolumler`, `personel_vardiya_programi`

### Teknik Mimari

- **Matris Mimarisi:** `operasyonel_bolum_id` (saha görevi) tabanlı personel yükleme — departman değil saha bazlı
- **Smart State:** Kaydedilmemiş değişiklik varken bölüm/vardiya değiştirilirse uyarı verilir (veri kaybı koruması)
- **Dinamik Kategori:** Seçilen duruma (Gelmedi/Sağlık Riski/Hijyen Uygunsuzluk) göre sebep ve aksiyon listesi değişir

### Sekme Yapısı: Radio (Sekme görünümü)

```
[RADIO] ─── ✅ Günlük Denetim  |  📊 Dashboard ───  (horizontal)
```

---

#### PANEL 1 — ✅ Günlük Denetim

```
[FİLTRE — 2 Sütun]
  ├── [SELECTBOX] Vardiya Seçiniz    (DB'den dinamik — GÜNDÜZ/ARA/GECE)
  └── [SELECTBOX] Bölüm Seçiniz     (operasyonel_bolum_id bazlı)

[DATA EDITOR] Personel Tablosu  (st.data_editor)
  Kolonlar: Personel Adı | Durum (Sorun Yok / Gelmedi / Sağlık Riski / Hijyen Uygunsuzluk)

[SORUNLU PERSONEL DETAY FORMU — 3 Sütunlu grid]
  Her sorunlu personel için (container, border=True):
  ├── [SELECTBOX] Neden?   (duruma göre dinamik liste)
  └── [SELECTBOX] Aksiyon? (duruma göre dinamik liste)

  Gelmedi → Sebep: YİK / Raporlu / Habersiz / Üİzin  | Aksiyon: İK Bilgi / Tutanak / Dahilinde
  Sağlık Riski → Sebep: Ateş / İshal / Öksürük / Yara / Bulaşıcı  | Aksiyon: Md.Bilgi / Eve / Revir / Maskeli
  Hijyen Uyg. → Sebep: Kirli Önlük / Sakal / Bone / Takı  | Aksiyon: Uyarıldı / Giderildi / Eğitim

[BUTTON] 💾 Kaydet  → _hijyen_kaydet() → guvenli_coklu_kayit_ekle() → st.toast → st.rerun()
```

---

#### PANEL 2 — 📊 Dashboard

```
[BAŞLIK] 📊 Hijyen Dashboard | Son 7 Gün

[3 METRIC KARTI]
  ├── [METRIC] 📋 Toplam Denetim
  ├── [METRIC] ⚠️ Uygunsuzluk Bölüm Sayısı (delta: "-N Kritik" / "Temiz")
  └── [METRIC] ✅ Sorunsuz Kayıt

[PIVOT TABLO] Bölüm × Durum (st.dataframe)

[EXPANDER] ⚠️ Son Uygunsuzluk Detayları
  └── [DATAFRAME] Son 20 kayıt (tarih, saat, bölüm, personel, durum, sebep, aksiyon)
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Form doldurma (sadece kendi vardiyası) |
| YÖNETİCİ | Dashboard görüntüleme |
| ADMIN | Tam erişim |

### Analiz

- **Teknik Borç Skoru: 2/5** — Dashboard PostgreSQL'e özgü `INTERVAL '7 days'` — SQLite'ta hata verir
- **CSF:** Her vardiya başında hijyen kaydı tamamlanmış; sağlık riskli personel %0 sahada

---

## 10. TEMİZLİK KONTROL

> **Zone:** `ALL` | **Dosya:** `ui/temizlik_ui.py`
> **Tablolar:** `ayarlar_temizlik_plani`, `lokasyonlar`, `tanim_ekipmanlar`

### Teknik Mimari

- **Master Plan Cache:** `@st.cache_data(ttl=300)` — 5 dakika cache, JOIN'li merkezi sorgu
- **Lokasyon Hiyerarşisi:** Kat → Bölüm → Ekipman (3 seviye)
- **Yetki Kilidi:** `is_controller = kullanici_yetkisi_var_mi("🧹 Temizlik Kontrol", "Düzenle")` — görüntüle/düzenle ayrımı

### Arayüz Haritası

```
[BAŞLIK] 🧹 Temizlik Kontrol

[LOKASYON FİLTRESİ — 4 Sütun]
  ├── [SELECTBOX] 🏢 Kat        (key: t_kat_sel — "Tümü" + dinamik)
  ├── [SELECTBOX] 🏭 Bölüm      (key: t_bol_sel — kata göre dinamik)
  ├── [SELECTBOX] (Hat)         (gelecek)
  └── [SELECTBOX] ⏰ Vardiya    (key: t_shift — GÜNDÜZ/ARA/GECE)

[INFO] Seçilen lokasyon için N görev listelendi.

[SAHA FORMU — Her temizlik görevi]
  Yetki yoksa: [INFO] Salt okunur görünüm

  Yetki varsa her görev için:
  ├── [MARKDOWN]   Yer/Ekipman | Sıklık | Kimyasal | Risk | Metot
  ├── [SELECTBOX]  Durum: Yapıldı / Yapılmadı / Kısmi
  └── (Risk yüksekse) [FILE UPLOADER] Kanıt Fotoğrafı

[BUTTON] ✅ Görevleri Kaydet
  → Doğrulama → INSERT INTO temizlik_kayitlari
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Salt görüntüleme |
| YÖNETİCİ | Form doldurma (Düzenle yetkisi) |
| ADMIN | Plan tanımlama (Ayarlar'dan) |

### Analiz

- **Teknik Borç Skoru: 2/5** — `lokasyonlar` tablosu ile join bağımlılığı; tablo yoksa plan boş gelir
- **CSF:** Günlük görevlerin %100'ü kayıtlı; HAFTALIK/AYLIK görevler zamanında tamamlanmış

---

## 11. SOĞUK ODA TAKİP (SOSTS)

> **Zone:** `ALL` | **Dosya:** `ui/soguk_oda_ui.py`
> **Tablolar:** `soguk_odalar`, `sicaklik_olcumleri`

### Teknik Mimari

- **QR Kod Akışı:** `st.camera_input` → `cv2.QRCodeDetector` → token → oda kimlik doğrulama
- **URL Param Desteği:** `st.query_params.get("scanned_qr")` — dışarıdan QR token beslenebilir
- **Fail-Safe CCP:** Limit aşımında otomatik alarm (Anayasa Madde 9) — human onay beklemez
- **Manuel Yetki:** Sadece ADMIN, SİSTEM ADMİN, KALİTE GÜVENCE MÜDÜRÜ manuel dolap seçebilir

### Arayüz Haritası

```
[BAŞLIK] ❄️ Soğuk Oda Takip Sistemi (SOSTS)

[TOKEN YOK → GİRİŞ EKRANI]

  Yetkili Roller için:
  [RADIO] Giriş Yöntemi: 📸 QR Kodu Tara  |  ⌨️ Manuel Dolap Seç

  Manuel Seç:
    └── [SELECTBOX] Dolap Seçiniz (oda_adi + oda_kodu)
        [BUTTON] ➡️ Seçili Dolaba Git → session_state.scanned_qr_code set → st.rerun()

  QR Tara:
    ├── [BUTTON] 📸 QR Kodu Okut (show_sosts_camera toggle)
    └── (kamera açıkken)
        ├── [BUTTON] ❌ Taramayı İptal Et
        └── [CAMERA INPUT] 📸 QR KODU OKUTMAK İÇİN FOTOĞRAF ÇEKİN
              → cv2.QRCodeDetector → token decode → st.rerun()

[TOKEN VARSA → ÖLÇÜM FORMU]
  ├── Oda bilgisi göster (oda_adi, oda_kodu, sıcaklık limitleri)
  ├── [NUMBER INPUT] Ölçülen Sıcaklık (°C)  (büyük font CSS: 25px)
  ├── [NUMBER INPUT] Nem (%) — opsiyonel
  ├── [TEXT AREA]    Gözlem / Not
  └── [BUTTON] ✅ Ölçümü Kaydet
        → CCP limit kontrolü → Alarm tetikle (Madde 9)
        → kaydet_olcum() → st.rerun()
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Sadece QR okutarak ölçüm girişi |
| YÖNETİCİ | QR ölçüm + geçmiş görüntüleme |
| ADMIN / KALİTE GÜV. MD. | Manuel dolap seçimi + oda tanımlama |

### Analiz

- **Teknik Borç Skoru: 3/5** — Manuel veri girişi (IoT yok); `cv2` bağımlılığı (cloud'da sorun çıkarabilir)
- **CSF:** Her ölçüm periyodunda kayıt tamamlanmış; CCP alarm sıfır gecikmeli tetiklenmiş
- **Dokunulmazlık:** `soguk_odalar.qr_token` alanı değiştirilirse tüm QR etiketleri geçersiz olur — dikkat

---

## 12. RAPORLAMA MERKEZİ

> **Zone:** `mgt` | **Dosya:** `ui/raporlama_ui.py`
> **Tablolar:** Çok kaynaklı (KPI, Hijyen, GMP, SOSTS, MAP, QDMS)

### Teknik Mimari

- **Excel Motoru:** `openpyxl` + `pandas.ExcelWriter` — çift sheet (Kayıtlar + Özet)
- **HTML Rapor Motoru:** `_generate_base_html()` — A4 print-optimized HTML, print CSS `@media print`
- **İsim Standardı:** `RAPOR_ADI_BASTARIH_BITSTARIHI_INDIRMETARIHI.xlsx`
- **Personel Haritası:** `kullanici_adi → "Ad Soyad (Görev) [Saha]"` görünüm formatı

### Arayüz Haritası

```
[BAŞLIK] 📊 Raporlama Merkezi

[SEKME YAPISI — Rapor Kategorileri]

Her rapor sekmesinde:
  ├── [DATE INPUT]    Başlangıç Tarihi
  ├── [DATE INPUT]    Bitiş Tarihi
  ├── (opsiyonel) [MULTISELECT] Bölüm / Ürün / Kullanıcı filtresi
  ├── [BUTTON] 🔍 Raporu Getir
  │     → DB sorgusu → Özet kartlar → Tablo
  ├── [DOWNLOAD BUTTON] 📥 Excel İndir  (key: dl_{RAPOR_ADI}_{time.time()})
  └── [BUTTON] 🖨️ Yazdır / HTML Rapor  (tarayıcı print dialog)
```

**Mevcut Rapor Tipleri (raporlama_ui.py'den tespit edilenler):**
- KPI Kontrol Raporları
- Hijyen Kontrol Kayıtları
- GMP Denetim Sonuçları
- MAP Vardiya & OEE Raporları
- SOSTS Sıcaklık Geçmişi

### Analiz

- **Teknik Borç Skoru: 3/5** — `time.time()` ile dinamik download button key → Anayasa Md.23 riskli (her render yeni widget üretir)
- **CSF:** Excel exportların satır bütünlüğü %100; HTML raporlar A4'te düzgün sayfa kırılımı
- **Dokunulmazlık:** HTML rapor şablonundaki imza alanları manuel değiştirilmemeli — DÖF akışına bağlı

---

## 13. PERFORMANS & POLİVALANS

> **Zone:** `mgt` | **Dosya:** `ui/performans/performans_sayfasi.py` + 5 alt modül
> **Tablo:** `performans_degerledirme`

### Teknik Mimari

- **Modüler Yapı:** 5 dosya (`performans_db`, `performans_form`, `performans_hesap`, `performans_sabitleri`, `performans_sayfasi`)
- **BRC v9 & IFS v8 Uyumu:** Yetkinlik takibi, polivalans düzeyi hesaplama
- **Maker/Checker:** Değerlendiren ≠ değerlendirilen (session_state'den otomatik)

### Sekme Yapısı: 3 Tab

---

#### TAB 1 — ➕ Yeni Değerlendirme

```
[YETKİ KONTROLÜ] Düzenle yetkisi yok ise [WARNING] göster

[ÇALIŞAN BİLGİ FORMU] form.calisan_bilgi_formu(p_df)
  ├── [SELECTBOX]    Çalışan Seçiniz
  ├── [DATE INPUT]   Değerlendirme Tarihi
  └── [SELECTBOX]    Değerlendirme Dönemi

[PUAN GİRİŞ FORMU] form.puan_giris_formu()
  └── (performans_sabitleri'ndeki kategori başlıkları)

[DEĞERLENDIRME ÖZET KARTI] form.degerlendirme_ozet_karti(puanlar)
  └── Ağırlıklı toplam puan + Polivalans düzeyi

[TEXT AREA] 🗒️ Değerlendirme Yorumu & Notlar

[BUTTON] 💾 DEĞERLENDİRMEYİ KAYDET (primary, use_container_width=True)
  → db.degerlendirme_kaydet() → st.success + st.balloons()
```

#### TAB 2 — 📋 Geçmiş Kayıtlar

```
[SORGU FİLTRELERİ — 2 Sütun]
  ├── [SELECTBOX]    Bölüm Filtresi  ("Tümü" + dinamik)
  └── [NUMBER INPUT] Yıl Filtresi    (2020-2100, varsayılan: bu yıl, key: f_yil)

[DATAFRAME] Kayıt listesi
  Kolonlar: tarih, ad soyad, bölüm, ağırlıklı puan, polivalans düzeyi, değerlendiren
```

#### TAB 3 — 📈 Analiz & Matris

```
[INFO] Polivalans Matrisi bir sonraki güncellemede aktif edilecek.
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Görüntüleme yok |
| YÖNETİCİ | Görüntüle + Yeni değerlendirme |
| ADMIN | Tam erişim |

### Analiz

- **Teknik Borç Skoru: 2/5** — Tab 3 henüz boş placeholder
- **CSF:** Yıllık değerlendirme kapsanması %100; polivalans düzeyi tüm personel için hesaplanmış

---

## 14. AYARLAR & YÖNETİM PANELİ

> **Zone:** `sys` | **Dosya:** `ui/ayarlar/ayarlar_orchestrator.py` + 10 alt modül
> **Kapsam:** Tüm sistem konfigürasyonu — 14 sekme

### Sekme Yapısı: 14 Tab

```python
# ayarlar_orchestrator.py:19
tabs = st.tabs([
    "👥 Personel",        # tabs[0]  → render_personel_tab()
    "🔐 Kullanıcılar",    # tabs[1]  → render_kullanici_tab()
    "📦 Ürünler",         # tabs[2]  → render_urun_tab()
    "🎭 Roller",          # tabs[3]  → render_rol_tab()
    "🔑 Yetkiler",        # tabs[4]  → render_yetki_tab()
    "🏭 Bölümler",        # tabs[5]  → render_bolum_tab()
    "📍 Lokasyonlar",     # tabs[6]  → render_lokasyon_tab()
    "🔧 Prosesler",       # tabs[7]  → render_proses_tab()
    "🧹 Temizlik & Tanımlar", # tabs[8] → render_temizlik_tab()
    "🛡️ GMP Sorular",    # tabs[9]  → render_gmp_soru_tab()
    "❄️ Soğuk Oda",       # tabs[10] → render_soguk_oda_ayarlari()
    "🕸️ Akıllı Akış",    # tabs[11] → render_flow_designer()
    "🛡️ Audit Log",      # tabs[12] → render_audit_log_module()
    "🔧 Sistem Bakımı"    # tabs[13] → render_bakim_tab()
])
```

### Tab Detayları

| Tab | İçerik | Kritik Not |
| :--- | :--- | :--- |
| **👥 Personel** | Personel ekle/düzenle/pasif; departman, vardiya, operasyonel bölüm | `personel` çekirdek tablo — DOKUNULMAZ |
| **🔐 Kullanıcılar** | Kullanıcı adı, şifre (bcrypt), rol ataması | Bcrypt hash — düz metin kaydedilmez |
| **📦 Ürünler** | Ürün tanımları, numune sayısı, raf ömrü, parametreler | `ayarlar_urunler` — KPI modülü buraya bağımlı |
| **🎭 Roller** | Rol tanımları (Yönetim Kurulu → Stajyer, 0-7) | `constants.py` RBAC seviyeleri ile senkron olmalı |
| **🔑 Yetkiler** | Modül × İşlem yetki matrisi | `ayarlar_yetkiler` — RBAC motoru buradan beslenir |
| **🏭 Bölümler** | Departman hiyerarşisi | `ayarlar_bolumler` çekirdek tablo |
| **📍 Lokasyonlar** | Fabrika kat/bölüm/hat lokasyonları | Temizlik ve GMP modülleri buraya bağımlı |
| **🔧 Prosesler** | Üretim proses tanımları | `tanim_prosesler` |
| **🧹 Temizlik & Tanımlar** | Temizlik planı, kimyasallar, metodlar | `ayarlar_temizlik_plani` |
| **🛡️ GMP Sorular** | GMP soru havuzu, BRC ref, risk puanı, frekans | `gmp_soru_havuzu` — GMP modülünü besler |
| **❄️ Soğuk Oda** | Oda tanımlama, QR token üretimi, sıcaklık limitleri | QR token değiştirilirse tüm etiketler geçersiz |
| **🕸️ Akıllı Akış** | Flow Designer — `flow_manager.py` | ⚠️ DONMUŞ: 5 tablo var, UI bağlantısı yok |
| **🛡️ Audit Log** | Tüm kritik işlemlerin audit kaydı görüntüleme | `sistem_loglari` — YAZMA YASAK, sadece okuma |
| **🔧 Sistem Bakımı** | Cache temizleme, DB migration durumu, test araçları | `cache_manager.py` üzerinden çalışır |

### ⚠️ Akıllı Akış (Flow Engine) — DONMUŞ MODÜL

```
Durum: ALTYAPI HAZIR, UI BAĞLANTISI YOK
Tablolar: flow_definitions · flow_nodes · flow_edges · flow_bypass_logs · personnel_tasks
Dosya: logic/flow_manager.py, ui/ayarlar/flow_designer_ui.py

KURAL: Hiçbir ajan bu tablolara migration çalıştırmadan yazmamalıdır.
       Aktivasyon kararı Emre onayı gerektirir.
       Builder ajanları bu tablolara dokunmadan önce Guardian onayı almalıdır.
```

### Yetki Matrisi

| Rol | Yetki |
| :--- | :--- |
| PERSONEL | Erişim yok |
| YÖNETİCİ | Audit Log görüntüleme |
| ADMIN | Tüm sekmelere tam erişim |

---

## 15. AJAN KULLANIM PROTOKOLÜ

Her ajan (Planner, Builder, Validator, Guardian) bu dosyayı okuduğunda:

### A. Bağlam Koruma Kuralları

1. **Modül Amacına Sadık Kal:** Her modülün İş Amacı dışına çıkma. KPI modülüne hijyen özelliği ekleme.
2. **Tablo Sadakati:** Modül metadata'sındaki tablolar dışında yeni tablo üretme (gerekirse Guardian onayı al).
3. **Dokunulmazlık Sınırları:** Her modülün "Dokunulmazlık" notuna uy — örn. `map_zaman_cizelgesi`'ne direkt INSERT yasak.

### B. Değişiklik Öncesi Kontrol Listesi

```
□ Hangi tablolar etkileniyor? → hafiza_ozeti.md tablo listesini kontrol et
□ Anayasa Madde 23: Yeni st.form key'i çakışıyor mu? → Context Sweep yap
□ Anayasa Madde 12: Fonksiyon 30 satırı aşıyor mu?
□ Cache: Yeni veri DB'ye yazıldı, cache temizlendi mi? → cache_manager.py
□ Maker/Checker: Veri girişi yapan = onaylayan olabilir mi? (Yasak)
□ Flow Engine: Bu değişiklik flow_* tablolarına dokunuyor mu? → Dur, Guardian sor
```

### C. Hata Önleme Altın Kuralları

- `eng.connect()` değil → `with eng.begin() as conn:` (VAKA-003)
- `df.to_sql(if_exists='replace')` değil → UPSERT (Anayasa Madde 6)
- `st.form()` içinde `st.file_uploader` değil → form dışı kullan (GMP örüntüsü)
- `time.time()` ile dinamik form key değil → sabit semantik key kullan (VAKA-009)

### D. Modül Dokunulmazlık Haritası

| Kritik Bileşen | Dokunulmazlık Nedeni |
| :--- | :--- |
| `personel` tablosu | Tüm RBAC ve yetki sistemi buraya bağlı |
| `ayarlar_yetkiler` tablosu | Tüm `kullanici_yetkisi_var_mi()` sorguları buradan |
| `qdms_gk_*` alt tabloları | QDMS dışından yazılırsa tutarsızlık riski |
| `urun_kpi_kontrol.foto_b64` | BRC silmez kanıt — DROP/NULL yasak |
| `soguk_odalar.qr_token` | Değiştirilirse tüm QR etiketler geçersiz |
| `sistem_loglari` | Audit Log — sadece okuma, yazma yasak |
| `flow_*` tablolar | Donmuş modül — Emre onayı olmadan dokunma |

---

*Son Güncelleme: 2026-03-29*
*Versiyon: 6.0 — Kod Taramalı, Tam Kapsam*
*Bu döküman, `anayasa.md` ve `hafiza_ozeti.md` ile birlikte "Sistemin Ruhu"nu oluşturur.*
*Tüm teknik iddialar doğrudan kaynak koddan (`ui/`, `logic/`, `modules/`) türetilmiştir.*
