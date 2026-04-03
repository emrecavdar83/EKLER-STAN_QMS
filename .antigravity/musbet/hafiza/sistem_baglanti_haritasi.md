# EKLERİSTAN QMS — Tam Bağlantı, Fonksiyon ve Veritabanı Haritası
> **Versiyon:** 1.0 | **Tarih:** 2026-03-29
> **Kapsam:** Her dosya, her fonksiyon, her tablo, her bağımlılık — kaynak koddan birebir

---

## İÇİNDEKİLER

1. [Sistem Genel Mimarisi](#1-sistem-genel-mimarisi)
2. [Dosya Bağımlılık Ağı](#2-dosya-bağımlılık-ağı)
3. [Veritabanı Bağlantı Katmanı](#3-veritabanı-bağlantı-katmanı)
4. [Tüm Tablolar ve İlişkiler](#4-tüm-tablolar-ve-ilişkiler)
5. [Logic Katmanı — Tüm Fonksiyonlar](#5-logic-katmanı--tüm-fonksiyonlar)
6. [Giriş ve Oturum Akışı](#6-giriş-ve-oturum-akışı)
7. [Yetki Sistemi Nasıl Çalışır](#7-yetki-sistemi-nasıl-çalışır)
8. [Önbellek Sistemi](#8-önbellek-sistemi)
9. [Veri Yazma Akışı](#9-veri-yazma-akışı)
10. [Migration Sistemi](#10-migration-sistemi)
11. [Modül — Tablo Bağımlılık Matrisi](#11-modül--tablo-bağımlılık-matrisi)

---

## 1. SİSTEM GENEL MİMARİSİ

```
KULLANICI TARAYICISI
        │
        ▼
    app.py  ── Tek giriş noktası (~430 satır)
        │       Routing, Login, Session, Sidebar
        │
        ├── logic/auth_logic.py       ← Kimlik doğrulama + RBAC
        ├── logic/zone_yetki.py       ← Zone kapısı (RAM tabanlı)
        ├── logic/data_fetcher.py     ← Önbellekli okuma
        ├── logic/db_writer.py        ← Güvenli yazma
        ├── logic/cache_manager.py    ← Merkezi cache yönetimi
        ├── logic/alerts_logic.py     ← SOSTS gecikme uyarıları
        ├── logic/sync_handler.py     ← Emekli (Cloud-Primary sonrası)
        │
        ├── database/connection.py    ← Engine fabrikası (@cache_resource)
        ├── database/schema_qdms.py   ← QDMS tablo tanımları
        │
        ├── constants.py              ← Pozisyon seviyeleri, vardiya listesi
        │
        ├── ui/ ──────────────────── Modül UI dosyaları
        │    ├── portal/portal_ui.py
        │    ├── qdms_ui.py
        │    ├── map_uretim/map_uretim.py
        │    ├── kpi_ui.py
        │    ├── gmp_ui.py
        │    ├── hijyen_ui.py
        │    ├── temizlik_ui.py
        │    ├── soguk_oda_ui.py
        │    ├── raporlama_ui.py
        │    ├── uretim_ui.py
        │    ├── profil_ui.py
        │    ├── performans/performans_sayfasi.py
        │    └── ayarlar/ayarlar_orchestrator.py (14 alt sekme)
        │
        └── modules/qdms/ ─────────── QDMS alt modülleri
             ├── belge_kayit.py
             ├── revizyon.py
             ├── pdf_uretici.py
             ├── gk_logic.py
             ├── sablon_motor.py
             ├── talimat_yonetici.py
             └── uyumluluk_rapor.py
```

---

## 2. DOSYA BAĞIMLILIK AĞI

### Kim Kimi Çağırıyor?

| Çağıran Dosya | Çağrılan Dosya | Çağrılan Fonksiyon | Neden |
| :--- | :--- | :--- | :--- |
| `app.py` | `database/connection.py` | `get_engine()` | Motor nesnesi |
| `app.py` | `logic/auth_logic.py` | `sistem_modullerini_getir()`, `kullanici_yetkisi_var_mi()`, `sifre_dogrula()`, `audit_log_kaydet()` | Giriş + RBAC |
| `app.py` | `logic/zone_yetki.py` | `yetki_haritasi_yukle()`, `zone_girebilir_mi()`, `modul_gorebilir_mi()`, `eylem_yapabilir_mi()`, `varsayilan_modul_getir()` | Zone routing |
| `app.py` | `logic/data_fetcher.py` | `run_query()`, `get_user_roles()`, `veri_getir()`, `get_personnel_hierarchy()` | Veri okuma |
| `app.py` | `logic/cache_manager.py` | `clear_all_cache()`, `clear_personnel_cache()` | Cache yönetimi |
| `app.py` | `constants.py` | `POSITION_LEVELS`, `MANAGEMENT_LEVELS`, `get_position_name()`, `VARDIYA_LISTESI` | Pozisyon bilgileri |
| `logic/auth_logic.py` | `database/connection.py` | `get_engine()` | DB bağlantısı |
| `logic/data_fetcher.py` | `database/connection.py` | `get_engine()` | DB bağlantısı |
| `logic/db_writer.py` | `database/connection.py` | `get_engine()` | DB bağlantısı |
| `logic/db_writer.py` | `logic/cache_manager.py` | `clear_personnel_cache()` | Yazma sonrası cache temizle |
| `logic/zone_yetki.py` | *(sadece sqlalchemy)* | — | Bağımsız, DB'ye doğrudan bağlanır |
| `logic/cache_manager.py` | `logic/data_fetcher.py` | `cached_veri_getir.clear()`, `get_personnel_hierarchy.clear()`, `run_query.clear()` | Cache temizleme |
| `logic/cache_manager.py` | `logic/zone_yetki.py` | `_YETKI_CACHE.clear()` | Zone cache temizle |
| `logic/alerts_logic.py` | `soguk_oda_utils` | `get_overdue_summary()` | SOSTS gecikme kontrolü |
| `database/connection.py` | `database/schema_qdms.py` | `init_qdms_tables()` | QDMS şema başlatma |
| `database/connection.py` | `soguk_oda_utils` | `init_sosts_tables()` | SOSTS şema başlatma |
| `ui/qdms_ui.py` | `modules/qdms/belge_kayit.py` | `belge_olustur()`, `belge_listele()`, `belge_getir()`, `belge_guncelle()`, `belge_kodu_oner()` | Belge CRUD |
| `ui/qdms_ui.py` | `modules/qdms/pdf_uretici.py` | `pdf_uret()` | PDF üretimi |
| `ui/qdms_ui.py` | `modules/qdms/gk_logic.py` | `gk_getir()`, `gk_kaydet()` | GK CRUD |
| `ui/qdms_ui.py` | `modules/qdms/talimat_yonetici.py` | `talimat_olustur()`, `talimat_getir_by_kod()`, `okunmayan_talimatlar()`, `okuma_onay_kaydet()` | Talimat yönetimi |
| `ui/qdms_ui.py` | `modules/qdms/uyumluluk_rapor.py` | `uyumluluk_ozeti_getir()` | BRC uyum skoru |
| `ui/map_uretim/map_uretim.py` | `ui/map_uretim/map_db.py` | Tüm DB işlemleri | MAP veritabanı |
| `ui/map_uretim/map_uretim.py` | `ui/map_uretim/map_hesap.py` | `hesapla_sure_ozeti()`, `hesapla_uretim()`, `hesapla_durus_ozeti()` | OEE hesapları |
| `ui/raporlama_ui.py` | `soguk_oda_utils` | `get_matrix_data()`, `get_trend_data()` | SOSTS rapor verileri |

---

## 3. VERİTABANI BAĞLANTI KATMANI

### `database/connection.py` — `get_engine()`

Bu fonksiyon sistemin **kalp atışıdır**. Tüm DB bağlantıları buradan geçer.

```
get_engine() çağrıldığında ne olur?
─────────────────────────────────
1. @st.cache_resource nedeniyle SADECE 1 KEZ çalışır (sunucu yeniden başlayana kadar)

2. Bağlantı türü belirlenir:
   ├── secrets.toml'da DB_URL var → Supabase/PostgreSQL
   │     pool_size=5, max_overflow=10, pool_pre_ping=True
   │     pool_recycle=1800 (30 dk)
   │     SET TIMEZONE='Europe/Istanbul' event listener
   └── secrets.toml yok → SQLite (ekleristan_local.db)
         PRAGMA journal_mode=WAL
         PRAGMA synchronous=NORMAL

3. Bakım işlemleri (AUTOCOMMIT modunda):
   ├── _ensure_schema_sync_with_conn()  → Migration listesi çalıştır
   ├── _ensure_critical_data_with_conn() → Shadow tablolar + MAP tabloları oluştur
   ├── _ensure_admin_account_with_conn() → Admin + Saha_Mobil hesabı garantile
   ├── init_qdms_tables()               → 11 QDMS tablosu
   └── init_sosts_tables()              → SOSTS tabloları

4. Engine nesnesi döner (tüm sisteme paylaşılır)
```

### Bağlantı Kuralı (VAKA-003'ten Öğrenildi)

```
YANLIŞ → engine.connect()         # Sessiz hata yutabilir
DOĞRU  → with engine.begin() as conn:  # Atomik, commit garantili
```

---

## 4. TÜM TABLOLAR VE İLİŞKİLER

### 4.1 ÇEKİRDEK TABLOLAR (DOKUNULMAZ)

#### `personel` — Tüm sistemin merkezi

| Kolon | Tip | Açıklama |
| :--- | :--- | :--- |
| id | PK | Otomatik artan |
| ad_soyad | TEXT | Tam isim |
| kullanici_adi | TEXT UNIQUE | Giriş için |
| sifre | TEXT | bcrypt hash (plain-text geçiş süreci 2026-06-15'te biter) |
| rol | TEXT | ADMIN / Müdür / Personel... |
| durum | TEXT | AKTİF / PASİF |
| departman_id | FK → ayarlar_bolumler.id | Departman bağlantısı |
| operasyonel_bolum_id | FK → ayarlar_bolumler.id | Saha görevi (Hijyen matrisinde kullanılır) |
| pozisyon_seviye | INTEGER | 0=YK, 1=GM, ..., 7=Stajyer |
| yonetici_id | FK → personel.id | Kendi tablosuna self-reference |
| ikincil_yonetici_id | FK → personel.id | Saha sorumlusu |
| guncelleme_tarihi | TIMESTAMP | Migration v3.5 ile eklendi |

**Kimler bağlı:** `ayarlar_yetkiler`, `qdms_belgeler`, `qdms_revizyon_log`, `qdms_yayim`, `qdms_okuma_onay`, `qdms_gorev_karti`, `hijyen_kontrol_kayitlari`, `performans_degerledirme`, `personel_vardiya_programi`, `sistem_oturum_izleri`

#### `ayarlar_bolumler` — Organizasyon ağacı

| Kolon | Tip | Açıklama |
| :--- | :--- | :--- |
| id | PK | — |
| bolum_adi | TEXT | Bölüm/departman adı |
| ana_departman_id | FK → ayarlar_bolumler.id | Self-reference (hiyerarşi) |
| tur | TEXT | ops / mgt / sys / NULL |
| sira_no | INTEGER | Gösterim sırası |
| aktif | INTEGER | 1=aktif |

**Kimler bağlı:** `personel`, `gmp_soru_havuzu`, `gmp_denetim_kayitlari`, `hijyen_kontrol_kayitlari`, `ayarlar_temizlik_plani`

#### `ayarlar_moduller` — Modül kayıt defteri

| Kolon | Tip | Açıklama |
| :--- | :--- | :--- |
| id | PK | — |
| modul_anahtari | TEXT UNIQUE | `kpi_kontrol`, `map_uretim` ... |
| modul_etiketi | TEXT | `🍩 KPI & Kalite Kontrol` |
| sira_no | INTEGER | Menü sırası |
| aktif | INTEGER | 1=menüde görünür |
| zone | TEXT | ops / mgt / sys |

**Bootstrap:** `get_engine()` içinde 12 modül otomatik UPSERT edilir.

#### `ayarlar_yetkiler` — RBAC matrisi

| Kolon | Tip | Açıklama |
| :--- | :--- | :--- |
| id | PK | — |
| rol_adi | TEXT | `ADMIN`, `Müdür`... |
| modul_adi | TEXT | FK mantıksal → `ayarlar_moduller.modul_anahtari` |
| erisim_turu | TEXT | `Görüntüle` / `Düzenle` / `Yok` |
| sadece_kendi_bolumu | INTEGER | 1=bölüm filtreli erişim |
| eylem_yetkileri | JSON | `{"ekle": true, "sil": false}` |
| zone_erisim | TEXT | ops / mgt / sys |

**Çekilen:** `kullanici_yetkisi_var_mi()` ve `yetki_haritasi_yukle()` her ikisi de buradan okur.

#### `sistem_parametreleri`

| Kolon | Tip | Açıklama |
| :--- | :--- | :--- |
| param_adi | TEXT | `plaintext_fallback_aktif`, `fallback_bitis_tarihi` |
| param_degeri | TEXT | Değer |

**Kullanım:** `_plaintext_fallback_izni_var_mi()` — plain-text şifre geçiş sürecini kontrol eder.

#### `sistem_loglari` — Audit trail

| Kolon | Tip | Açıklama |
| :--- | :--- | :--- |
| id | PK | — |
| islem_tipi | TEXT | `GIRIS_BASARISIZ`, `MAP_URETIM_DUZELTME_NET`, `ERISIM_REDDEDILDI`... |
| detay | TEXT | `[kullanici_adi] açıklama` |
| zaman | TIMESTAMP | Otomatik |

**KURAL:** Sadece `audit_log_kaydet()` fonksiyonu yazar. UI'den doğrudan yazma yasak.

---

### 4.2 OPERASYONELTableName TABLOLAR

#### `urun_kpi_kontrol`

| Kolon | Açıklama |
| :--- | :--- |
| tarih, saat, vardiya | Zaman bilgisi |
| urun, lot_no, stt | Ürün ve lot |
| numune_no | Numune sayısı |
| olcum1/2/3 | İlk 3 parametre ortalaması (legacy) |
| karar | `ONAY` / `RED` |
| kullanici | Kaydeden |
| tat, goruntu | Duyusal kontrol |
| fotograf_yolu | Disk yolu |
| fotograf_b64 | Base64 kanıt (BRC — SİLİNEMEZ) |

**Migration:** `fotograf_b64` sonradan `ALTER TABLE` ile eklendi.

#### `gmp_soru_havuzu`

| Kolon | Açıklama |
| :--- | :--- |
| soru_metni | Denetim sorusu |
| kategori | Genel / Hijyen... |
| brc_ref | BRC madde numarası |
| risk_puani | 1/2/3 (3=Kritik) |
| frekans | GÜNLÜK / HAFTALIK / AYLIK |
| lokasyon_ids | Virgüllü ID listesi |
| aktif | 1/0 |

**Kullanım:** `_gmp_soru_getir()` frekans ve lokasyon filtresiyle çeker.

#### `gmp_denetim_kayitlari`

| Kolon | Açıklama |
| :--- | :--- |
| tarih, saat, kullanici | Kim, ne zaman |
| lokasyon_id | FK → ayarlar_bolumler.id |
| soru_id | FK → gmp_soru_havuzu.id |
| durum | `UYGUN` / `UYGUN DEĞİL` |
| fotograf_yolu | Kritik bulgular için |
| notlar | Düzeltici faaliyet |
| brc_ref, risk_puani | Snapshot (değişirse kayıt korunur) |

#### `hijyen_kontrol_kayitlari`

| Kolon | Açıklama |
| :--- | :--- |
| tarih, saat, kullanici | Denetçi bilgisi |
| vardiya | GÜNDÜZ / ARA / GECE |
| bolum | Bölüm adı (text snapshot) |
| personel | Personel adı (text snapshot) |
| durum | Sorun Yok / Gelmedi / Sağlık Riski / Hijyen Uygunsuzluk |
| sebep | Seçilen sebep |
| aksiyon | Alınan aksiyon |

#### `soguk_odalar`

| Kolon | Açıklama |
| :--- | :--- |
| oda_adi, oda_kodu | Kimlik |
| qr_token | QR etiket bağlantısı (değişirse tüm etiketler geçersiz!) |
| min_sicaklik, max_sicaklik | CCP limitleri |
| olcum_periyodu_dk | Ölçüm sıklığı (dakika) |
| aktif | 1/0 |

#### `sicaklik_olcumleri`

| Kolon | Açıklama |
| :--- | :--- |
| oda_id | FK → soguk_odalar.id |
| sicaklik_c | Ölçülen değer |
| planlanan_zaman | Migration ile eklendi |
| qr_ile_girildi | 1=QR, 0=Manuel |
| kullanici | Giren kişi |
| notlar | Gözlem |

---

### 4.3 MAP (Üretim) TABLOLARI

Tüm MAP tabloları `database/connection.py:_create_map_performance_tables()` içinde oluşturulur.

#### `map_vardiya` — Ana kayıt

| Kolon | Açıklama |
| :--- | :--- |
| tarih | YYYY-MM-DD |
| makina_no | MAP-01 / MAP-02 / MAP-03 |
| vardiya_no | 1 / 2 / 3 |
| baslangic_saati | HH:MM |
| bitis_saati | HH:MM (kapanınca dolar) |
| operator_adi | Sistem giren kullanıcı (disabled input) |
| vardiya_sefi | Opsiyonel |
| besleme_kisi, kasalama_kisi | Personel sayısı |
| hedef_hiz_paket_dk | Hedef hız pk/dk |
| gerceklesen_uretim | Kümülatif toplam |
| acan_kullanici_id, kapatan_kullanici_id | Hesap verebilirlik |
| durum | `ACIK` / `KAPALI` |
| notlar | Vardiya notu |

#### `map_zaman_cizelgesi` — Saniye hassasiyetli duruş kaydı

| Kolon | Açıklama |
| :--- | :--- |
| vardiya_id | FK → map_vardiya.id |
| sira_no | Olay sırası |
| baslangic_ts | ISO timestamp |
| bitis_ts | Dolarsa sure_dk hesaplanır |
| durum | `CALISIYOR` / `DURUS` |
| neden | Duruş nedeni |

**KURAL:** Bu tabloya sadece `map_db.insert_zaman_kaydi()` yazar, direkt SQL yasak.

#### `map_fire_kaydi`

| Kolon | Açıklama |
| :--- | :--- |
| vardiya_id | FK → map_vardiya.id |
| fire_tipi | 9 tip (Bobin Başı, Film Değişimi...) |
| miktar_adet | Adet |
| olusturma_ts | Otomatik |

#### `map_bobin_kaydi`

| Kolon | Açıklama |
| :--- | :--- |
| vardiya_id | FK → map_vardiya.id |
| sira_no | Değişim sırası |
| bobin_lot | Lot no |
| film_tipi | Üst Film / Alt Film |
| baslangic_kg, bitis_kg | Kg değerleri |
| kullanilan_kg | Hesaplanan |

---

### 4.4 QDMS TABLOLARI (11 Tablo — `database/schema_qdms.py`)

```
qdms_belgeler (Ana tablo)
    │
    ├── qdms_sablonlar          (Belge şablon konfigürasyonu)
    ├── qdms_revizyon_log       (Revizyon geçmişi — degistiren_id → personel.id)
    ├── qdms_yayim              (Yayım kaydı — yayimlayan_id → personel.id)
    ├── qdms_talimatlar         (SOP/Talimat adımları — adimlar_json)
    ├── qdms_okuma_onay         (Kim okudu — personel_id → personel.id)
    └── qdms_gorev_karti        (GK Ana tablo — belge_kodu ile bağlı)
            │
            ├── qdms_gk_sorumluluklar    (5 disiplin: personel/operasyon/gida_guvenligi/isg/cevre)
            ├── qdms_gk_etkilesim        (RACI matrisi)
            ├── qdms_gk_periyodik_gorevler (Periyodik görevler)
            └── qdms_gk_kpi             (KPI listesi)
```

#### `qdms_belgeler` — Tüm belgelerin kaydı

| Kolon | Açıklama |
| :--- | :--- |
| belge_kodu | UNIQUE (EKL-GK-001) |
| belge_tipi | GK / SO / TL / PR / KYS / FR / PL / LS / KL / YD / SOP |
| alt_kategori | Bölüm / kategori |
| aktif_rev | Aktif revizyon no |
| durum | taslak / incelemede / aktif / arsiv |
| olusturan_id | FK → personel.id |
| amac, kapsam, tanimlar, dokumanlar, icerik | v3.5 Migration ile eklendi |

#### `qdms_gk_sorumluluklar`

| Kolon | Açıklama |
| :--- | :--- |
| belge_kodu | FK → qdms_belgeler.belge_kodu |
| disiplin_tipi | personel / operasyon / gida_guvenligi / isg / cevre |
| sira_no | Gösterim sırası |
| sorumluluk | Sorumluluk metni |
| etkilesim_birimleri | RACI bağlantılı birimler |

---

### 4.5 DİĞER TABLOLAR

| Tablo | Açıklama | Oluşturan |
| :--- | :--- | :--- |
| `ayarlar_urunler` | Ürün tanımları (numune_sayisi, raf_omru_gun...) | Ayarlar/Ürünler |
| `urun_parametreleri` | Dinamik ölçüm parametreleri | Ayarlar/Ürünler |
| `depo_giris_kayitlari` | Hammadde giriş kayıtları | Üretim Girişi |
| `ayarlar_temizlik_plani` | Temizlik master planı | Ayarlar |
| `lokasyonlar` | Kat/Bölüm/Hat hiyerarşisi | Ayarlar |
| `tanim_ekipmanlar` | Ekipman tanımları | Ayarlar |
| `gunluk_gorev_katalogu` | Görev şablonları | Ayarlar |
| `gunluk_periyodik_kurallar` | Tekrarlayan görev kuralları | Ayarlar |
| `birlesik_gorev_havuzu` | Aktif görevler (portal + günlük görevler) | Logic |
| `performans_degerledirme` | Personel değerlendirme kayıtları | Performans |
| `personel_vardiya_programi` | Vardiya ve izin programı | Ayarlar |
| `sistem_oturum_izleri` | Remember Me token'ları (7 günlük) | auth_logic |
| `lokasyon_tipleri` | Shadow tablo | connection.py |
| `vardiya_tipleri` | Shadow tablo | connection.py |
| `sistem_loglari` | Audit trail (SADECE OKUMA) | connection.py |
| `flow_definitions` | Akıllı Akış — DONMUŞ | schema |
| `flow_nodes` | Akıllı Akış — DONMUŞ | schema |
| `flow_edges` | Akıllı Akış — DONMUŞ | schema |
| `flow_bypass_logs` | Akıllı Akış — DONMUŞ | schema |
| `personnel_tasks` | Akıllı Akış — DONMUŞ | schema |

---

## 5. LOGIC KATMANI — TÜM FONKSİYONLAR

### `logic/auth_logic.py`

| Fonksiyon | Ne Yapar | DB Bağlantısı | Cache |
| :--- | :--- | :--- | :--- |
| `_normalize_string(s)` | Türkçe + emoji temizler, büyük harf ASCII | Yok | Yok |
| `normalize_role_string(r)` | Rol adı yazım hatalarını düzeltir | Yok | Yok |
| `_dinamik_yetki_aktif_mi()` | Her zaman True döner (Anayasa v2.1) | Yok | Yok |
| `_get_dinamik_modul_anahtari(menu_adi)` | Menü etiketinden DB anahtarı bulur (emoji-safe) | `ayarlar_moduller` | TTL 60s |
| `kullanici_yetkisi_getir_dinamik(rol, modul)` | Rol + modül için erişim türü döner | `ayarlar_yetkiler` | TTL 60s |
| `sistem_modullerini_getir()` | Aktif modül listesini (etiket, anahtar) döner | `ayarlar_moduller` | TTL 300s |
| `_get_batch_yetki_haritasi(rol_adi)` | Tüm yetkileri tek sorguda çeker, session_state'e kaydeder | `ayarlar_yetkiler` | session_state |
| `kullanici_yetkisi_var_mi(menu_adi, yetki)` | Kullanıcının modüle erişimi var mı? (Ana yetki kapısı) | 0 (batch map'ten) | session_state |
| `sistem_modullerini_ve_anahtarlarini_getir()` | Modül etiket→anahtar sözlüğü | `ayarlar_moduller` | TTL 300s |
| `audit_log_kaydet(islem, detay, kullanici)` | `sistem_loglari`'na yazar — fail-silent | `sistem_loglari` | Yok |
| `_plaintext_fallback_izni_var_mi()` | Plain-text şifre geçiş sürecini kontrol eder | `sistem_parametreleri` | Yok |
| `get_fallback_info()` | Grace period bitiş tarihini döner | `sistem_parametreleri` | Yok |
| `sifre_hashle(plain)` | bcrypt hash üretir | Yok | Yok |
| `_bcrypt_formatinda_mi(s)` | `$2b$` ile başlıyor mu? | Yok | Yok |
| `sifre_dogrula(girilen, db_sifre, kullanici)` | Dual-validate: bcrypt veya plain-text + lazy migration | `personel` (migration) | Yok |
| `_sifreyi_hashle_ve_guncelle(kullanici, plain)` | Plain-text'i bcrypt'e taşır (idempotent) | `personel` | Yok |
| `kullanici_yetkisi_getir(rol, modul)` | Eski sistem, hâlâ çalışıyor (fallback) | `ayarlar_yetkiler` | TTL 60s |
| `bolum_bazli_urun_filtrele(urun_df)` | Bölüm sorumlusu ürün filtresi | `ayarlar_yetkiler` | Yok |
| `kalici_oturum_olustur(engine, kullanici_id)` | Remember Me token oluşturur (SHA256 hash) | `sistem_oturum_izleri` | Yok |
| `kalici_oturum_dogrula(engine, raw_token)` | Token'ı doğrular, kullanıcı bilgisi döner | `sistem_oturum_izleri` + `personel` | Yok |
| `kalici_oturum_sil(engine, raw_token)` | Çıkış yaparken token siler | `sistem_oturum_izleri` | Yok |

### `logic/data_fetcher.py`

| Fonksiyon | Ne Yapar | DB Tablosu | Cache TTL |
| :--- | :--- | :--- | :--- |
| `robust_id_clean(v)` | ID değerini temizler (None/NaN güvenliği) | Yok | Yok |
| `get_hierarchy_flat(df, parent_id, prefix)` | Hiyerarşik isim listesi üretir | DataFrame'den | Yok |
| `run_query(query, params, where)` | Ham SQL çalıştırır, DataFrame döner | Herhangi | TTL 600s |
| `get_user_roles()` | **EMEKLİ** — Boş liste döner, eski uyumluluk için | Yok | TTL 3600s |
| `get_department_tree(filter_tur)` | Hiyerarşik departman listesi | `ayarlar_bolumler` | TTL 600s |
| `get_department_options_hierarchical()` | `{id: "↳ Alt Bölüm"}` selectbox için | `ayarlar_bolumler` | TTL 600s |
| `get_all_sub_department_ids(parent_id)` | Verilen departman + tüm altlarının ID'leri | `ayarlar_bolumler` | TTL 600s |
| `get_personnel_hierarchy()` | Personel listesi (departman join'li, aktif filtreli) | `personel` + `ayarlar_bolumler` | TTL 3600s |
| `cached_veri_getir(tablo_adi)` | Tablo adına göre önbellekli veri | Çeşitli (12 tablo haritası) | TTL 60s |
| `veri_getir(tablo_adi)` | `cached_veri_getir` için sarmalayıcı | — | — |
| `get_personnel_shift(personel_id, tarih)` | Personelin vardiyasını bulur | `personel_vardiya_programi` → `personel` | TTL 600s |
| `is_personnel_off(personel_id, tarih)` | Personel izinde mi? | `personel_vardiya_programi` → `personel` | TTL 600s |

**`cached_veri_getir` tablo haritası:**

| Anahtar | Çekilen Tablo | Filtre |
| :--- | :--- | :--- |
| `personel` | `personel` | aktif, pozisyon_seviye sıralı |
| `Ayarlar_Personel_V2` | `personel` + `ayarlar_bolumler` | JOIN |
| `Ayarlar_Urunler` | `ayarlar_urunler` | Tümü |
| `Depo_Giris_Kayitlari` | `depo_giris_kayitlari` | Son 50 |
| `Ayarlar_Temizlik_Plani` | `ayarlar_temizlik_plani` | — |
| `Tanim_Bolumler` | `ayarlar_bolumler` | aktif=1 |
| `Tanim_Ekipmanlar` | `tanim_ekipmanlar` | — |
| `GMP_Soru_Havuzu` | `gmp_soru_havuzu` | — |
| `Ayarlar_Bolumler` | `ayarlar_bolumler` | aktif=1, sira_no sıralı |
| `soguk_odalar` | `soguk_odalar` | id sıralı |

### `logic/zone_yetki.py`

| Fonksiyon | Ne Yapar | DB | Cache |
| :--- | :--- | :--- | :--- |
| `yetki_haritasi_yukle(engine, rol, force_refresh)` | Tüm zone+modül yetkisini DB'den yükler | `ayarlar_yetkiler` + `ayarlar_moduller` | `_YETKI_CACHE` (RAM dict) |
| `zone_girebilir_mi(zone)` | `session_state`'teki haritadan zone kontrolü | 0 | 0 (RAM) |
| `modul_gorebilir_mi(modul_anahtari)` | Modül erişim kontrolü | 0 | 0 (RAM) |
| `eylem_yapabilir_mi(modul_anahtari, eylem)` | Buton/aksiyon yetki kontrolü | 0 | 0 (RAM) |
| `varsayilan_modul_getir()` | Rol'ün açılış modülünü döner | 0 | 0 (RAM) |
| `_modul_yetkileri_getir(engine, rol)` | Yardımcı — tek sorguda tüm yetkiler | `ayarlar_yetkiler` + `ayarlar_moduller` | Yok |
| `_varsayilan_modul_bul(roller, moduller)` | Zone'a göre açılış modülü belirler | Yok | Yok |
| `sorgu_sayisini_getir()` | Debug: kaç DB sorgusu yapıldı | Yok | session_state |

### `logic/cache_manager.py`

| Fonksiyon | Ne Temizler | Ne Zaman Çağrılır |
| :--- | :--- | :--- |
| `clear_personnel_cache()` | `cached_veri_getir`, `get_personnel_hierarchy`, `get_user_roles`, `run_query`, `batch_yetki_map` | Personel kaydı yazıldıktan sonra |
| `clear_department_cache()` | `get_department_tree`, `get_department_options_hierarchical`, `cached_veri_getir`, `run_query` | Departman kaydı yazıldıktan sonra |
| `clear_all_cache()` | `st.cache_data.clear()`, `st.cache_resource.clear()`, `batch_yetki_map`, `_YETKI_CACHE` | Ayarlar/Sistem Bakımı butonundan |

### `logic/db_writer.py`

| Fonksiyon | Tablo | Kritik Not |
| :--- | :--- | :--- |
| `guvenli_kayit_ekle(tablo_adi, veri)` | `Depo_Giris_Kayitlari` veya `Urun_KPI_Kontrol` | `engine.connect()` kullanıyor (Anayasa uyarısı: `begin()` olmalı) |
| `guvenli_coklu_kayit_ekle(tablo_adi, veri_listesi)` | `Hijyen_Kontrol_Kayitlari` | Toplu batch insert |

**Not:** `db_writer.py` hâlâ `engine.connect()` kullanıyor. VAKA-003 riski var. Kritik tablolar için `engine.begin()` ile değiştirilmeli.

### `logic/alerts_logic.py`

| Fonksiyon | Ne Yapar | Cache |
| :--- | :--- | :--- |
| `get_gecikme_uyarilari(engine)` | Son 24 saatin gecikmiş SOSTS ölçümlerini kontrol eder | `session_state` — 300s (5 dk) |

### `logic/sync_handler.py`

| Fonksiyon | Ne Yapar |
| :--- | :--- |
| `render_sync_button(key_prefix)` | Sadece bilgi mesajı gösterir. **EMEKLİ** — Cloud-Primary sonrası işlevsiz |

---

## 6. GİRİŞ VE OTURUM AKIŞI

```
Tarayıcı app.py'yi açar
        │
        ▼
1. QR URL kontrolü (st.query_params)
   scanned_qr var mı?
   └── Evet → Saha_Mobil hesabıyla otomatik giriş + SOSTS'a yönlendir

2. Remember Me çerez kontrolü (cookie_manager)
   qms_remember_me çerezi var mı?
   └── Evet → kalici_oturum_dogrula(engine, token)
               Token geçerli mi?
               └── Evet → session_state'i doldur, st.rerun()
               └── Hayır → login ekranı

3. session_state.logged_in kontrolü
   └── False → login_screen() göster

login_screen() akışı:
   ├── personel tablosundan AKTİF kullanıcılar çekilir
   ├── Kullanıcı adı + şifre girilir
   ├── sifre_dogrula() çağrılır
   │     ├── bcrypt hash? → bcrypt.verify()
   │     └── plain-text? → düz karşılaştırma + lazy migration
   ├── Başarılı giriş:
   │     ├── session_state.logged_in = True
   │     ├── session_state.user = kullanici_adi
   │     ├── session_state.user_rol = rol
   │     ├── session_state.user_fullname = ad_soyad
   │     ├── session_state.user_bolum = bolum
   │     ├── yetki_haritasi_yukle() çağrılır (1 DB sorgusu)
   │     ├── active_module_key = varsayilan_modul_getir()
   │     └── (Beni Hatırla seçili ise) kalici_oturum_olustur()
   └── st.rerun()

4. Giriş sonrası yetki haritası:
   yetki_haritasi_yukle(engine, rol)
   └── ayarlar_yetkiler JOIN ayarlar_moduller → tek sorgu
   └── _YETKI_CACHE[rol] = harita (RAM'e kaydedilir)
   └── st.session_state.yetki_haritasi = harita

5. Sonraki her sayfa yüklemesinde:
   zone_girebilir_mi() / modul_gorebilir_mi() / eylem_yapabilir_mi()
   └── SIFIR DB sorgusu (RAM'deki haritadan)
```

---

## 7. YETKİ SİSTEMİ NASIL ÇALIŞIR

### İki Paralel Sistem

Sistemde iki paralel yetki kontrol mekanizması çalışıyor (geçiş sürecinde):

| Sistem | Fonksiyon | Performans | Durum |
| :--- | :--- | :--- | :--- |
| **Zone Sistemi** | `zone_girebilir_mi()`, `eylem_yapabilir_mi()` | 0 DB sorgusu | AKTİF (Birincil) |
| **Modül Sistemi** | `kullanici_yetkisi_var_mi()` | session_state batch | AKTİF (İkincil) |

### Zone Sistemi Nasıl Çalışır?

```
1. Giriş anında: yetki_haritasi_yukle(engine, rol)
   DB'den çekilen yapı:
   {
     'zones': ['ops', 'mgt'],      ← Bu rolün erişebildiği bölgeler
     'modules': {
       'kpi_kontrol': {
         'erisim': 'Düzenle',
         'eylemler': {'ekle': True, 'sil': False},
         'zone': 'mgt'
       },
       ...
     },
     'varsayilan_modul': 'kpi_kontrol'
   }

2. Her sayfa renderında (0 DB):
   zone_girebilir_mi('mgt')          → 'mgt' in session_state.yetki_haritasi['zones']
   modul_gorebilir_mi('kpi_kontrol') → modules['kpi_kontrol']['erisim'] != 'Yok'
   eylem_yapabilir_mi('kpi_kontrol', 'sil') → modules['kpi_kontrol']['eylemler']['sil']
```

### Modül Sistemi (kullanici_yetkisi_var_mi)

```
kullanici_yetkisi_var_mi("🍩 KPI & Kalite Kontrol", "Görüntüle") çağrılır

1. ADMIN rolü? → True (bypass)

2. _get_dinamik_modul_anahtari("🍩 KPI & Kalite Kontrol")
   → Emojileri temizle, normalize et
   → "kpi_kontrol" anahtarını döner

3. _get_batch_yetki_haritasi(rol)
   → İlk çağrıda DB'den çeker, session_state'e kaydeder
   → Sonraki çağrılarda session_state'ten döner (0 DB)

4. harita["KPIKONTROL"] → ('Düzenle', False)
   "Görüntüle" istendi → 'Düzenle' de yeterli → True
```

### RBAC Seviyeleri (constants.py)

| Seviye | Ad | Zone | Tipik Modüller |
| :--- | :--- | :--- | :--- |
| 0 | Yönetim Kurulu | sys | Tümü |
| 1 | Genel Müdür | sys | Tümü |
| 2 | Direktörler | mgt | Tümü yönetim |
| 3 | Müdürler | mgt | Bölüm yönetimi |
| 4 | Koordinatör / Şef | mgt+ops | Operasyon + raporlar |
| 5 | Bölüm Sorumlusu | ops | Kendi bölüm modülleri |
| 6 | Personel | ops | Giriş modülleri |
| 7 | Stajyer / Geçici | ops | Sadece görüntüleme |

---

## 8. ÖNBELLEK SİSTEMİ

### Cache Katmanları

```
Katman 1: @st.cache_resource
   └── get_engine() — Sunucu yeniden başlayana kadar tek engine
   └── Tüm DB bağlantıları bu motoru paylaşır

Katman 2: @st.cache_data (TTL tabanlı)
   └── run_query()              TTL: 600s (10 dk)
   └── get_user_roles()         TTL: 3600s (1 saat) — EMEKLİ
   └── get_department_tree()    TTL: 600s
   └── get_department_options() TTL: 600s
   └── get_all_sub_dept_ids()   TTL: 600s
   └── get_personnel_hierarchy() TTL: 3600s
   └── cached_veri_getir()      TTL: 60s (Anayasa Md.13)
   └── get_personnel_shift()    TTL: 600s
   └── is_personnel_off()       TTL: 600s
   └── kullanici_yetkisi_getir() TTL: 60s
   └── kullanici_yetkisi_getir_dinamik() TTL: 60s
   └── sistem_modullerini_getir() TTL: 300s
   └── _get_dinamik_modul_anahtari() TTL: 60s

Katman 3: session_state (Oturum boyunca)
   └── batch_yetki_map: {rol: {harita}}  — Yetki batch sorgusu
   └── yetki_haritasi: {zones, modules}  — Zone haritası
   └── sosts_gecikme_cache               — SOSTS uyarı cache

Katman 4: RAM dict (Sunucu süresince)
   └── _YETKI_CACHE: {rol: harita}       — Zone yetki RAM cache
```

### Cache Temizleme Kuralı (Anayasa Md.13)

```
✅ DOĞRU: cache_manager.py üzerinden
   clear_personnel_cache()    → personel değişikliği sonrası
   clear_department_cache()   → bölüm değişikliği sonrası
   clear_all_cache()          → Ayarlar > Sistem Bakımı butonundan

❌ YANLIŞ: Doğrudan çağrı
   cached_veri_getir.clear()  → Sadece cache_manager içinden!
```

---

## 9. VERİ YAZMA AKIŞI

### Nerede, Nasıl Yazılır?

```
UI Katmanı (ui/*.py)
        │
        ├─[Yol 1]── db_writer.guvenli_kayit_ekle()
        │            ├── Depo_Giris_Kayitlari → depo_giris_kayitlari
        │            ├── Urun_KPI_Kontrol → urun_kpi_kontrol
        │            └── (cache temizler)
        │
        ├─[Yol 2]── db_writer.guvenli_coklu_kayit_ekle()
        │            └── Hijyen_Kontrol_Kayitlari → hijyen_kontrol_kayitlari
        │
        ├─[Yol 3]── Doğrudan with engine.begin() as conn:
        │            ├── GMP denetim kayıtları
        │            ├── Temizlik kayıtları
        │            ├── MAP vardiya işlemleri (map_db.py üzerinden)
        │            └── QDMS işlemleri (belge_kayit.py vb. üzerinden)
        │
        └─[Yol 4]── modules/qdms/*.py üzerinden
                     └── gk_kaydet(), belge_olustur(), talimat_olustur()
```

### Yazma Güvenlik Kuralları

| Kural | Açıklama |
| :--- | :--- |
| `with engine.begin() as conn` | Atomik işlem — hata olursa otomatik rollback |
| UPSERT | `INSERT OR REPLACE` (SQLite) / `ON CONFLICT DO UPDATE` (PostgreSQL) |
| Audit Log | MAP düzeltmeleri + yetkisiz erişim denemelerinde `audit_log_kaydet()` çağrılır |
| Foto kanıtı | `urun_kpi_kontrol.fotograf_b64` — BRC gereği silinemez |
| Maker ≠ Checker | QDMS onay akışında aynı kişi hem giren hem onaylayan olamaz |

---

## 10. MİGRATION SİSTEMİ

### Nasıl Çalışır?

```
get_engine() çağrıldığında (ilk açılışta) otomatik çalışır:

1. Mevcut kolonlar çekilir (information_schema veya PRAGMA table_info)
2. _get_migration_list() listesi ile karşılaştırılır
3. Eksik kolon varsa → ALTER TABLE çalıştırılır
4. PostgreSQL: AUTOCOMMIT modunda (DDL transaction gerektirmez)
5. SQLite: conn.execute() ile (sessiz hata riski — VAKA-003)
```

### Mevcut Migration Listesi (connection.py)

| Tablo | Kolon | Versiyon |
| :--- | :--- | :--- |
| `urun_kpi_kontrol` | `fotograf_b64` | v3.5 |
| `sicaklik_olcumleri` | `planlanan_zaman` | v3.5 |
| `sicaklik_olcumleri` | `qr_ile_girildi` | v3.5 |
| `ayarlar_roller` | `aktif` | v3.5 |
| `personel` | `guncelleme_tarihi` | v3.5 |
| `qdms_belgeler` | `amac` | v3.5 |
| `qdms_belgeler` | `kapsam` | v3.5 |
| `qdms_belgeler` | `tanimlar` | v3.5 |
| `qdms_belgeler` | `dokumanlar` | v3.5 |
| `qdms_belgeler` | `icerik` | v3.5 |
| `qdms_gk_sorumluluklar` | `disiplin_tipi` | v3.6 |
| `qdms_gk_sorumluluklar` | `etkilesim_birimleri` | v3.6 |
| `map_vardiya` | `vardiya_sefi` | v4.0.3 |
| `map_vardiya` | `besleme_kisi` | v4.0.3 |
| `map_vardiya` | `kasalama_kisi` | v4.0.3 |
| `map_vardiya` | `hedef_hiz_paket_dk` | v4.0.3 |
| `map_vardiya` | `gerceklesen_uretim` | v4.0.3 |
| `map_vardiya` | `notlar` | v4.0.3 |

**KURAL:** Yeni kolon eklendiğinde bu listeye eklenmezse Cloud'da tablo eski kalır (ÖRÜNTÜ-02).

---

## 11. MODÜL — TABLO BAĞIMLILIK MATRİSİ

| Modül | Okuma Tabloları | Yazma Tabloları | Logic Dosyası |
| :--- | :--- | :--- | :--- |
| **Portal** | `birlesik_gorev_havuzu`, `personel` | — | data_fetcher |
| **QDMS** | `qdms_belgeler`, `qdms_gorev_karti`, `qdms_gk_*`, `qdms_talimatlar`, `qdms_revizyon_log` | `qdms_belgeler`, `qdms_gorev_karti`, `qdms_gk_*`, `qdms_talimatlar`, `qdms_okuma_onay`, `qdms_revizyon_log` | modules/qdms/* |
| **MAP Üretim** | `map_vardiya`, `map_zaman_cizelgesi`, `map_fire_kaydi`, `map_bobin_kaydi` | `map_vardiya`, `map_zaman_cizelgesi`, `map_fire_kaydi`, `map_bobin_kaydi`, `sistem_loglari` | map_db.py, map_hesap.py |
| **KPI Kontrol** | `ayarlar_urunler`, `urun_parametreleri` | `urun_kpi_kontrol` | db_writer |
| **GMP Denetimi** | `gmp_soru_havuzu`, `ayarlar_bolumler` | `gmp_denetim_kayitlari` | gmp_ui.py (direkt) |
| **Personel Hijyen** | `personel`, `ayarlar_bolumler`, `personel_vardiya_programi` | `hijyen_kontrol_kayitlari` | db_writer |
| **Temizlik** | `ayarlar_temizlik_plani`, `lokasyonlar`, `tanim_ekipmanlar` | `temizlik_kayitlari` | temizlik_ui.py (direkt) |
| **SOSTS** | `soguk_odalar`, `sicaklik_olcumleri` | `sicaklik_olcumleri` | soguk_oda_utils |
| **Raporlama** | Tüm kayıt tabloları (KPI, GMP, Hijyen, MAP, SOSTS) | — | raporlama_ui.py |
| **Performans** | `personel`, `ayarlar_bolumler` | `performans_degerledirme` | performans_db.py |
| **Günlük Görevler** | `birlesik_gorev_havuzu`, `gunluk_gorev_katalogu` | `birlesik_gorev_havuzu` | gunluk_gorev/ui.py |
| **Ayarlar** | Tüm tanım tabloları | Tüm tanım tabloları + `sistem_loglari` (okuma) | ayarlar_orchestrator (14 alt) |

---

*Son Güncelleme: 2026-03-29*
*Versiyon: 1.0 — Kaynak Koddan Birebir Üretilmiştir*
*Bu döküman `anayasa.md`, `hafiza_ozeti.md` ve `sistem_modul_analizi.md` ile birlikte Sistemin Ruhu'nu oluşturur.*
