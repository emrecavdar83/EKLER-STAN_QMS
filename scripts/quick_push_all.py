"""
Güvenli senkronizasyon: Lokal SQLite -> Bulut PostgreSQL
Operasyonel tablolarda ASLA DELETE kullanılmaz, sadece UPSERT.
Çalıştır: python scripts/quick_push_all.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import toml
import sqlalchemy
from sqlalchemy import text
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# KONFİGÜRASYON TABLOLARI: Lokal her zaman doğru kabul edilir.
# Sahadan veri girilmez, tamamen yönetici tarafından yönetilir.
# Bu tablolarda cloud temizlenip lokal yazılabilir.
# ─────────────────────────────────────────────────────────────────
CONFIG_TABLOLAR = [
    "ayarlar_bolumler",
    "ayarlar_roller",
    "ayarlar_yetkiler",
    "ayarlar_urunler",
    "ayarlar_temizlik_plani",
    "proses_tipleri",
    "tanim_metotlar",
    "tanim_ekipmanlar",
    "lokasyonlar",
    "gmp_lokasyonlar",
    "gmp_soru_havuzu",
    "personel",
    "soguk_odalar",
    "olcum_plani",
    "sistem_parametreleri",
    "urun_parametreleri",
]

# ─────────────────────────────────────────────────────────────────
# OPERASYONELvTABLOLAR: Sahadan girilen veriler burada saklanır.
# Cloud'da olan kayıt ASLA SİLİNMEZ. Sadece yeni kayıtlar eklenir.
# Primary key çakışması varsa güncellenir (UPSERT).
# ─────────────────────────────────────────────────────────────────
OPERATIONAL_TABLOLAR = [
    "sicaklik_olcumleri",
    "depo_giris_kayitlari",
    "urun_kpi_kontrol",
    "hijyen_kontrol_kayitlari",
    "temizlik_kayitlari",
    "gmp_denetim_kayitlari",
]

# Composite PK tanımları (UPSERT için conflict detection)
PK_MAP = {
    "sicaklik_olcumleri":        ("oda_id", "olcum_zamani"),
    "depo_giris_kayitlari":      ("tarih", "saat", "urun", "lot_no"),
    "urun_kpi_kontrol":          ("tarih", "saat", "urun"),
    "hijyen_kontrol_kayitlari":  ("tarih", "personel", "vardiya"),
    "temizlik_kayitlari":        ("tarih", "bolum", "islem"),
    "gmp_denetim_kayitlari":     ("tarih", "denetci"),
}


def get_engines(secrets_path=".streamlit/secrets.toml"):
    s = toml.load(secrets_path)
    cloud_url = s.get('streamlit', {}).get('DB_URL', s.get('DB_URL', ''))
    cloud_url = cloud_url.strip('"')
    local_engine = sqlalchemy.create_engine("sqlite:///ekleristan_local.db")
    cloud_engine = sqlalchemy.create_engine(cloud_url)
    return local_engine, cloud_engine


def push_config_table(tablo, local_engine, cloud_engine):
    """Konfigürasyon tabloları: cloud'u temizle, lokali yaz."""
    with local_engine.connect() as lconn:
        df = pd.read_sql(f"SELECT * FROM {tablo}", lconn)
    if df.empty:
        log.info(f"  [{tablo}] Lokal boş, atlandı.")
        return 0
    with cloud_engine.begin() as cconn:
        cconn.execute(text(f"DELETE FROM {tablo}"))
        df.to_sql(tablo, cconn, if_exists='append', index=False, method='multi')
    log.info(f"  ✅ [{tablo}] {len(df)} kayıt (config) buluta gönderildi.")
    return len(df)


def upsert_operational_table(tablo, local_engine, cloud_engine):
    """Operasyonel tablolar: sadece yeni/değişen kayıtları UPSERT et, silme yok."""
    with local_engine.connect() as lconn:
        df = pd.read_sql(f"SELECT * FROM {tablo}", lconn)
    if df.empty:
        log.info(f"  [{tablo}] Lokal boş, atlandı.")
        return 0

    pk_cols = list(PK_MAP.get(tablo, ("id",)))
    # id kolonu varsa UPSERT'ten hariç tut (otomatik artan)
    value_cols = [c for c in df.columns if c not in pk_cols and c != 'id']

    inserted = 0
    updated = 0
    skipped = 0

    with cloud_engine.begin() as cconn:
        for _, row in df.iterrows():
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row.items()}

            # Cloud'da bu kayıt var mı? (PK kontrolü)
            where = " AND ".join([f"{k} = :{k}" for k in pk_cols])
            exists = cconn.execute(
                text(f"SELECT 1 FROM {tablo} WHERE {where}"),
                {k: row_dict[k] for k in pk_cols}
            ).fetchone()

            if exists:
                if value_cols:
                    set_clause = ", ".join([f"{c} = :{c}" for c in value_cols])
                    cconn.execute(
                        text(f"UPDATE {tablo} SET {set_clause} WHERE {where}"),
                        row_dict
                    )
                    updated += 1
                else:
                    skipped += 1
            else:
                cols = [c for c in df.columns if c != 'id']
                placeholders = ", ".join([f":{c}" for c in cols])
                try:
                    cconn.execute(
                        text(f"INSERT INTO {tablo} ({', '.join(cols)}) VALUES ({placeholders})"),
                        row_dict
                    )
                    inserted += 1
                except Exception as e:
                    log.warning(f"  [{tablo}] INSERT atlandı (conflict?): {e}")
                    skipped += 1

    log.info(f"  ✅ [{tablo}] +{inserted} eklendi | ~{updated} güncellendi | {skipped} atlandı")
    return inserted + updated


def main():
    log.info("🔒 GÜVENLİ SYNC BAŞLIYOR (Operasyonel veriler SİLİNMEZ)")
    local_engine, cloud_engine = get_engines()

    toplam = 0

    log.info("\n--- KONFİGÜRASYON TABLOLARI (DELETE+INSERT) ---")
    for tablo in CONFIG_TABLOLAR:
        try:
            toplam += push_config_table(tablo, local_engine, cloud_engine)
        except Exception as e:
            log.warning(f"  ⚠️  [{tablo}] Hata: {e}")

    log.info("\n--- OPERASYONELvTABLOLAR (UPSERT - SİLME YOK) ---")
    for tablo in OPERATIONAL_TABLOLAR:
        try:
            toplam += upsert_operational_table(tablo, local_engine, cloud_engine)
        except Exception as e:
            log.warning(f"  ⚠️  [{tablo}] Hata: {e}")

    log.info(f"\n🎉 TAMAMLANDI: Toplam {toplam} kayıt işlendi.")
    log.info("ℹ️  Cloud'daki fazladan kayıtlar KORUNDU (silinmedi).")


if __name__ == "__main__":
    main()
