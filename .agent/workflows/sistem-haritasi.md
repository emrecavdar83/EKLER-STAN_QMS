---
description: Tam veritabanı, modül ve fonksiyon haritası — Ajan GPS'i
---

# EKLERİSTAN QMS — Sistem Haritası (Hızlı Referans)

> Bu dosya çağrıldığında ajan, tam haritayı okuyarak işe başlar.
> Detaylı analiz: `.antigravity/musbet/hafiza/sistem_haritasi.md`

---

## 🗄️ VERİTABANI TABLOSU (40 Tablo)

### Çekirdek (DOKUNULMAZ)
| Tablo | PK | Kritik FK | Kullanan |
|-------|----|----|----------|
| `personel` | id | departman_id → ayarlar_bolumler | Auth, Ayarlar, Tüm modüller |
| `ayarlar_bolumler` | id | ana_departman_id → self | Ayarlar, OrgChart |
| `ayarlar_moduller` | modul_anahtari | — | Sidebar, Zone, Bootstrap |
| `ayarlar_yetkiler` | id | modul_adi → ayarlar_moduller | Auth, Zone |
| `ayarlar_urunler` | id | — | Üretim, KPI, MAP |
| `sistem_parametreleri` | param_adi | — | Auth, SOSTS, Global |
| `sistem_loglari` | id | — | Audit, tüm modüller |

### MAP Modülü
| Tablo | FK |
|-------|----|
| `map_vardiya` | acan_kullanici_id → personel(id) |
| `map_zaman_cizelgesi` | vardiya_id → map_vardiya(id) |
| `map_fire_kaydi` | vardiya_id → map_vardiya(id) |
| `map_bobin_kaydi` | vardiya_id → map_vardiya(id) |

### QDMS (11 tablo)
`qdms_belgeler` · `qdms_sablonlar` · `qdms_revizyon_log` · `qdms_yayim` · `qdms_talimatlar` · `qdms_okuma_onay` · `qdms_gorev_karti` · `qdms_gk_sorumluluklar` · `qdms_gk_etkilesim` · `qdms_gk_periyodik_gorevler` · `qdms_gk_kpi`
> Tüm QDMS tabloları `belge_kodu` ile `qdms_belgeler` tablosuna bağlıdır.

### Günlük Görevler
| Tablo | FK |
|-------|----|
| `gunluk_gorev_katalogu` | — |
| `gunluk_periyodik_kurallar` | personel_id → personel(id) |
| `birlesik_gorev_havuzu` | personel_id → personel(id) |

### Operasyonel
`depo_giris_kayitlari` · `urun_kpi_kontrol` · `gmp_soru_havuzu` · `hijyen_kontrol_kayitlari` · `ayarlar_temizlik_plani` · `soguk_odalar` · `sicaklik_olcumleri` · `performans_degerledirme`

### Flow Engine (AKTİF DEĞİL)
`flow_definitions` · `flow_nodes` · `flow_edges` · `flow_bypass_logs` · `personnel_tasks`

---

## 📦 MODÜL → DOSYA HARİTASI

| Modül | Ana Dosya | DB Katmanı | Logic |
|-------|----------|------------|-------|
| Üretim Girişi | `ui/uretim_ui.py` | `logic/db_writer.py` | `logic/data_fetcher.py` |
| KPI & Kalite | `ui/kpi_ui.py` | `logic/db_writer.py` | `logic/data_fetcher.py` |
| GMP Denetimi | `ui/gmp_ui.py` | doğrudan SQL | `logic/data_fetcher.py` |
| Personel Hijyen | `ui/hijyen_ui.py` | `logic/db_writer.py` | `logic/data_fetcher.py` |
| Temizlik Kontrol | `ui/temizlik_ui.py` | doğrudan SQL | `logic/data_fetcher.py` |
| Raporlama | `ui/raporlama_ui.py` | — (read-only) | `logic/data_fetcher.py` |
| Soğuk Oda | `ui/soguk_oda_ui.py` | `soguk_oda_utils.py` | `logic/alerts_logic.py` |
| MAP Üretim | `ui/map_uretim/map_uretim.py` | `ui/map_uretim/map_db.py` | `ui/map_uretim/map_hesap.py` |
| Günlük Görevler | `modules/gunluk_gorev/ui.py` | `modules/gunluk_gorev/logic.py` | `modules/gunluk_gorev/schema.py` |
| Performans | `ui/performans/performans_sayfasi.py` | `ui/performans/performans_db.py` | `ui/performans/performans_hesap.py` |
| QDMS | `ui/qdms_ui.py` | `modules/qdms/*.py` | `database/schema_qdms.py` |
| Ayarlar | `ui/ayarlar/ayarlar_orchestrator.py` | `logic/settings_logic.py` | `logic/cache_manager.py` |
| Profilim | `ui/profil_ui.py` | doğrudan SQL | `logic/auth_logic.py` |

---

## 🔑 YETKİ MİMARİSİ (3 Katman — 0 DB Sorgusu)

```
Katman 1: zone_girebilir_mi(zone)      → Bölge kapısı (ops/mgt/sys)
Katman 2: modul_gorebilir_mi(modul)    → Sidebar görünürlük
Katman 3: eylem_yapabilir_mi(modul,e)  → Buton seviyesi
```

Tüm kontroller `st.session_state['yetki_haritasi']` üzerinden RAM'den yapılır.
Harita oturum başında `logic/zone_yetki.py → yetki_haritasi_yukle()` ile 1 kez yüklenir.

---

## ⚠️ BİLİNEN RİSKLER

- ❌ `auth_logic.py:414` → `sevcanalbas` hardcoded (VAKA-006)
- ⚠️ 8 fonksiyon 30 satır limitini aşıyor
- ⚠️ 8/13 modülün test dosyası yok
- ⚠️ Flow Engine 5 tablosu ölü kod

> Detaylı risk analizi: `.antigravity/musbet/hafiza/sistem_haritasi.md` Bölüm 7
