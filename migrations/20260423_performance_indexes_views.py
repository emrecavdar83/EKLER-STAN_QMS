"""
Migration: Performans Index'leri ve v_aktif_personel VIEW
Tarih: 2026-04-23
Sebep: SQL Skill analizi — eksik index'ler ve SELECT * yükü azaltma
"""
from sqlalchemy import text


def migrate(engine):
    is_pg = engine.dialect.name == "postgresql"
    stmts = []

    # --- INDEX'LER ---
    # sistem_loglari: her sayfada ORDER BY zaman ve WHERE modul/kullanici_id filtresi
    stmts += [
        "CREATE INDEX IF NOT EXISTS idx_sistem_loglari_zaman      ON sistem_loglari(zaman DESC)",
        "CREATE INDEX IF NOT EXISTS idx_sistem_loglari_modul      ON sistem_loglari(modul)",
        "CREATE INDEX IF NOT EXISTS idx_sistem_loglari_kullanici  ON sistem_loglari(kullanici_id)",
    ]

    # hata_loglari: ORDER BY zaman DESC + is_fixed filtresi
    stmts += [
        "CREATE INDEX IF NOT EXISTS idx_hata_loglari_zaman   ON hata_loglari(zaman DESC)",
        "CREATE INDEX IF NOT EXISTS idx_hata_loglari_modul   ON hata_loglari(modul)",
        "CREATE INDEX IF NOT EXISTS idx_hata_loglari_fixed   ON hata_loglari(is_fixed)",
    ]

    # ayarlar_kullanicilar: yetki kontrolleri rol+durum+departman sorgularında
    stmts += [
        "CREATE INDEX IF NOT EXISTS idx_kullanicilar_rol    ON ayarlar_kullanicilar(rol)",
        "CREATE INDEX IF NOT EXISTS idx_kullanicilar_durum  ON ayarlar_kullanicilar(durum)",
        "CREATE INDEX IF NOT EXISTS idx_kullanicilar_dept   ON ayarlar_kullanicilar(qms_departman_id)",
    ]

    # qdms_okuma_onay: belge okuma sorgularında composite index şart
    stmts += [
        "CREATE INDEX IF NOT EXISTS idx_okuma_onay_belge_personel ON qdms_okuma_onay(belge_kodu, personel_id)",
    ]

    # performans_degerledirme: personel+dönem bazlı sorgular
    stmts += [
        "CREATE INDEX IF NOT EXISTS idx_perf_personel_donem ON performans_degerledirme(personel_id, donem)",
    ]

    # sicaklik_olcumleri ve olcum_plani: oda_id her sorguda
    stmts += [
        "CREATE INDEX IF NOT EXISTS idx_olcum_oda_zaman ON sicaklik_olcumleri(oda_id, olusturulma_tarihi DESC)",
        "CREATE INDEX IF NOT EXISTS idx_plan_oda_id     ON olcum_plani(oda_id)",
    ]

    # --- VIEW: v_aktif_personel ---
    # data_fetcher.py'deki 3 farklı personel sorgusunu tek noktaya toplar
    if is_pg:
        stmts.append("DROP VIEW IF EXISTS v_aktif_personel")
        stmts.append("""
CREATE VIEW v_aktif_personel AS
SELECT
    p.id,
    p.ad_soyad,
    p.kullanici_adi,
    p.rol,
    p.gorev,
    p.durum,
    p.pozisyon_seviye,
    COALESCE(p.vardiya, 'GUNDUZ VARDIYASI') AS vardiya,
    p.yonetici_id,
    p.qms_departman_id                      AS departman_id,
    p.operasyonel_bolum_id,
    p.ikincil_yonetici_id,
    p.ise_giris_tarihi,
    p.telefon_no,
    p.servis_duragi,
    d.ad                                    AS departman_adi
FROM ayarlar_kullanicilar p
LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id
WHERE p.kullanici_adi IS NOT NULL
  AND p.durum = 'AKTİF'
""")

    with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        for stmt in stmts:
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                    print(f"[OK] {stmt[:80]}...")
                except Exception as e:
                    print(f"[SKIP] {str(e)[:100]}")

    print("[DONE] 20260423_performance_indexes_views migration tamamlandı.")


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.connection import get_engine
    migrate(get_engine())
