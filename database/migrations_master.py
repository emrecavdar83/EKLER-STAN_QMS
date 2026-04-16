from sqlalchemy import text

def get_migration_list():
    """Tüm sistem için dinamik migrasyon listesini döner."""
    return [
        ("urun_kpi_kontrol", "fotograf_b64", "ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT"),
        ("sicaklik_olcumleri", "planlanan_zaman", "ALTER TABLE sicaklik_olcumleri ADD COLUMN planlanan_zaman TIMESTAMP"),
        ("sicaklik_olcumleri", "qr_ile_girildi", "ALTER TABLE sicaklik_olcumleri ADD COLUMN qr_ile_girildi INTEGER DEFAULT 1"),
        ("ayarlar_roller", "aktif", "ALTER TABLE ayarlar_roller ADD COLUMN aktif INTEGER DEFAULT 1"),
        ("personel", "guncelleme_tarihi", "ALTER TABLE personel ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # v3.5: BRCGS Columns for Documents
        ("qdms_belgeler", "amac", "ALTER TABLE qdms_belgeler ADD COLUMN amac TEXT"),
        ("qdms_belgeler", "kapsam", "ALTER TABLE qdms_belgeler ADD COLUMN kapsam TEXT"),
        ("qdms_belgeler", "tanimlar", "ALTER TABLE qdms_belgeler ADD COLUMN tanimlar TEXT"),
        ("qdms_belgeler", "dokumanlar", "ALTER TABLE qdms_belgeler ADD COLUMN dokumanlar TEXT"),
        ("qdms_belgeler", "icerik", "ALTER TABLE qdms_belgeler ADD COLUMN icerik TEXT"),
        # v3.6: GK Discipline Expansion
        ("qdms_gk_sorumluluklar", "disiplin_tipi", "ALTER TABLE qdms_gk_sorumluluklar ADD COLUMN disiplin_tipi TEXT"),
        ("qdms_gk_sorumluluklar", "etkilesim_birimleri", "ALTER TABLE qdms_gk_sorumluluklar ADD COLUMN etkilesim_birimleri TEXT"),
        # v4.0.3: MAP Schema Gaps
        ("map_vardiya", "vardiya_sefi", "ALTER TABLE map_vardiya ADD COLUMN vardiya_sefi TEXT"),
        ("map_vardiya", "besleme_kisi", "ALTER TABLE map_vardiya ADD COLUMN besleme_kisi INTEGER"),
        ("map_vardiya", "kasalama_kisi", "ALTER TABLE map_vardiya ADD COLUMN kasalama_kisi INTEGER"),
        ("map_vardiya", "hedef_hiz_paket_dk", "ALTER TABLE map_vardiya ADD COLUMN hedef_hiz_paket_dk FLOAT"),
        ("map_vardiya", "gerceklesen_uretim", "ALTER TABLE map_vardiya ADD COLUMN gerceklesen_uretim INTEGER DEFAULT 0"),
        ("map_vardiya", "notlar", "ALTER TABLE map_vardiya ADD COLUMN notlar TEXT"),
        # v4.0.6: Global Activity Tracker expansion
        ("sistem_loglari", "modul", "ALTER TABLE sistem_loglari ADD COLUMN modul VARCHAR(50)"),
        ("sistem_loglari", "kullanici_id", "ALTER TABLE sistem_loglari ADD COLUMN kullanici_id INTEGER"),
        ("sistem_loglari", "detay_json", "ALTER TABLE sistem_loglari ADD COLUMN detay_json TEXT"),
        ("sistem_loglari", "ip_adresi", "ALTER TABLE sistem_loglari ADD COLUMN ip_adresi VARCHAR(45)"),
        ("sistem_loglari", "cihaz_bilgisi", "ALTER TABLE sistem_loglari ADD COLUMN cihaz_bilgisi TEXT"),
        # v5.8.1: Personel Expansion
        ("personel", "baslama_tarihi", "ALTER TABLE personel ADD COLUMN baslama_tarihi DATE"),
        ("personel", "vekil_id", "ALTER TABLE personel ADD COLUMN vekil_id INTEGER"),
        ("personel", "aktif_izinde_mi", "ALTER TABLE personel ADD COLUMN aktif_izinde_mi INTEGER DEFAULT 0"),
        ("ayarlar_roller", "min_seviye", "ALTER TABLE ayarlar_roller ADD COLUMN min_seviye INTEGER"),
        ("ayarlar_roller", "max_seviye", "ALTER TABLE ayarlar_roller ADD COLUMN max_seviye INTEGER"),
        # v5.8.2: Dynamic Shift Hours
        ("vardiya_tipleri", "baslangic_saati", "ALTER TABLE vardiya_tipleri ADD COLUMN baslangic_saati TEXT"),
        ("vardiya_tipleri", "bitis_saati", "ALTER TABLE vardiya_tipleri ADD COLUMN bitis_saati TEXT"),
        ("personel", "ayrilma_tarihi", "ALTER TABLE personel ADD COLUMN ayrilma_tarihi DATE"),
        ("personel", "ayrilma_nedeni", "ALTER TABLE personel ADD COLUMN ayrilma_nedeni TEXT"),
        ("ayarlar_yetkiler", "eylem_yetkileri", "ALTER TABLE ayarlar_yetkiler ADD COLUMN eylem_yetkileri TEXT"),
        # v6.3.5: QMS Standardizasyon
        ("qms_departmanlar", "durum", "ALTER TABLE qms_departmanlar ADD COLUMN durum TEXT DEFAULT 'AKTİF'"),
        ("qms_departman_turleri", "renk_kodu", "ALTER TABLE qms_departman_turleri ADD COLUMN renk_kodu VARCHAR(20)"),
        ("qms_departman_turleri", "durum", "ALTER TABLE qms_departman_turleri ADD COLUMN durum TEXT DEFAULT 'AKTİF'"),
        ("qms_departman_turleri", "kurallar_json", "ALTER TABLE qms_departman_turleri ADD COLUMN kurallar_json TEXT"),
        ("qms_departmanlar", "guncelleme_tarihi", "ALTER TABLE qms_departmanlar ADD COLUMN guncelleme_tarihi TIMESTAMP"),
        ("personel", "operasyonel_bolum_id", "ALTER TABLE personel ADD COLUMN operasyonel_bolum_id INTEGER"),
        ("personel", "ikincil_yonetici_id",  "ALTER TABLE personel ADD COLUMN ikincil_yonetici_id INTEGER"),
        ("map_vardiya", "urun_adi", "ALTER TABLE map_vardiya ADD COLUMN urun_adi TEXT"),
        # v6.1.2: System Settings Hardening (Fix Truncation)
        ("sistem_parametreleri", "deger_type_fix", "ALTER TABLE sistem_parametreleri ALTER COLUMN deger TYPE TEXT"),
    ]

def run_migrations(conn, is_pg):
    """Eksik kolonları kontrol eder ve migrasyonları uygular."""
    existing_cols = _get_existing_columns(conn, is_pg)
    mig_list = get_migration_list()
    
    for tbl, col, sql in mig_list:
        if (tbl.lower(), col.lower()) not in existing_cols:
            try:
                # v6.1.2: Environment-specific check for ALTER TYPE
                if "ALTER COLUMN" in sql.upper() and not is_pg:
                    continue # SQLite does not support ALTER COLUMN TYPE
                
                conn.execute(text(sql))
                print(f"Migration Success: {tbl}.{col}")
                
                # v6.0 Standardizasyon: aktif -> durum veri göçü
                if col == "durum":
                    try:
                        conn.execute(text(f"UPDATE {tbl} SET durum = CASE WHEN aktif = 1 THEN 'AKTİF' ELSE 'PASİF' END WHERE durum IS NULL"))
                        print(f"Data Standardized: {tbl}.durum")
                    except Exception as de:
                        print(f"Data Migration Warning ({tbl}): {de}")
            except Exception as e:
                print(f"Migration Error ({tbl}.{col}): {e}")

def _get_existing_columns(conn, is_pg):
    """Mevcut kolon listesini döner."""
    if is_pg:
        res = conn.execute(text("""
            SELECT table_name, column_name FROM information_schema.columns 
            WHERE table_schema = current_schema()
        """)).fetchall()
        return {(r[0].lower(), r[1].lower()) for r in res}
    
    all_cols = []
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    for t_row in tables:
        t_name = t_row[0]
        c_res = conn.execute(text(f"PRAGMA table_info({t_name})")).fetchall()
        for c in c_res:
            all_cols.append((t_name.lower(), c[1].lower()))
    return set(all_cols)
