# VERİTABANI KURALLARI VE ENVANTERİ
**EKLERİSTAN QMS v3.2 | Sync Master ve Builder bu dosyayı okur.**

---

## MİMARİ

```
SQLite (WAL modu)          ←→          Supabase PostgreSQL
ekleristan_local.db               public schema (60+ tablo)
      ↕
Symmetric Twin Sync
(logic/sync_manager.py)
```

**NOT:** SOS birimi DB'de `ID = 18` olarak tanımlıdır. Hardcode yazma — `CONSTANTS.SOS_BIRIM_ID` kullan.

---

## LOKAL ŞEMA DOSYALARI

### database/schema_qdms.py
| Tablo | Satır |
|---|---|
| `qdms_gk_kpi` | 16 |
| `qdms_gk_form` | 72 |
| `qdms_gk_form_yanit` | 144 |
| `qdms_gk_plan` | 183 |

### database/connection.py
- `sistem_loglari`
- `lokasyon_tipleri`
- `vardiya_tipleri`
- `map_vardiya`

---

## SUPABASE CANLI TABLOLAR (public schema)

### Ana Sistem
| Tablo | Notlar |
|---|---|
| `personel` | 358 kayıt — **PROTECTED** |
| `ayarlar_bolumler` | Bölüm tanımları |
| `ayarlar_yetkiler` | RBAC — **PROTECTED** |
| `ayarlar_moduller` | Tüm sabitler buradan gelir |
| `sistem_parametreleri` | Grace Period, oturum — **PROTECTED** |

### QDMS & Kalite
| Tablo | Notlar |
|---|---|
| `qdms_belgeler` | Aktif belgeler — **PROTECTED** |
| `qdms_talimatlar` | |
| `qdms_gk_kpi` | Lokal + Supabase senkron |
| `qdms_gk_form` | Lokal + Supabase senkron |
| `qdms_gk_plan` | Lokal + Supabase senkron |
| `qdms_revizyon_log` | |
| `qdms_yayim` | |
| `qdms_okuma_onay` | |
| `hijyen_kontrol_kayitlari` | |
| `gmp_denetim_kayitlari` | |

### MAP & Üretim
| Tablo | Notlar |
|---|---|
| `map_bobin_kaydi` | |
| `map_fire_kaydi` | |
| `map_vardiya` | |
| `map_zaman_cizelgesi` | |
| `sicaklik_olcumleri` | |

### Akış & Flow
| Tablo | Notlar |
|---|---|
| `flow_definitions` | |
| `flow_nodes` | |
| `flow_edges` | |

---

## PROTECTED TABLOLAR

Bu tablolara **Sync Master dokunmadan önce ekstra insan onayı alır:**

```
personel              → 358 kayıt, kritik
ayarlar_yetkiler      → RBAC, güvenlik kritik
sistem_parametreleri  → Grace Period, oturum ayarları
qdms_belgeler         → aktif belgeler
```

---

## SYNC KURALLARI

1. `sync_log_preview.txt` üretilmeden sync **başlatılamaz**
2. Dry Run sonucu insan tarafından **onaylanmalı**
3. Protected tablo değişikliğinde **ek onay formu** doldurulacak
4. Hata durumunda → **dur, raporla, sync yapma**
5. UPSERT stratejisi kullan — DELETE-INSERT yasak
