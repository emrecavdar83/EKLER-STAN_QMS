from sqlalchemy import text

def get_migration_list():
    """Tüm sistem için dinamik migrasyon listesini döner."""
    return [
        ("urun_kpi_kontrol", "fotograf_b64", "ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT"),
        ("sicaklik_olcumleri", "planlanan_zaman", "ALTER TABLE sicaklik_olcumleri ADD COLUMN planlanan_zaman TIMESTAMP"),
        ("sicaklik_olcumleri", "qr_ile_girildi", "ALTER TABLE sicaklik_olcumleri ADD COLUMN qr_ile_girildi INTEGER DEFAULT 1"),
        ("ayarlar_roller", "aktif", "ALTER TABLE ayarlar_roller ADD COLUMN aktif INTEGER DEFAULT 1"),
        ("ayarlar_kullanicilar", "guncelleme_tarihi", "ALTER TABLE ayarlar_kullanicilar ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
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
        ("ayarlar_kullanicilar", "baslama_tarihi", "ALTER TABLE ayarlar_kullanicilar ADD COLUMN baslama_tarihi DATE"),
        ("ayarlar_kullanicilar", "vekil_id", "ALTER TABLE ayarlar_kullanicilar ADD COLUMN vekil_id INTEGER"),
        ("ayarlar_kullanicilar", "aktif_izinde_mi", "ALTER TABLE ayarlar_kullanicilar ADD COLUMN aktif_izinde_mi INTEGER DEFAULT 0"),
        ("ayarlar_roller", "min_seviye", "ALTER TABLE ayarlar_roller ADD COLUMN min_seviye INTEGER"),
        ("ayarlar_roller", "max_seviye", "ALTER TABLE ayarlar_roller ADD COLUMN max_seviye INTEGER"),
        # v5.8.2: Dynamic Shift Hours
        ("vardiya_tipleri", "baslangic_saati", "ALTER TABLE vardiya_tipleri ADD COLUMN baslangic_saati TEXT"),
        ("vardiya_tipleri", "bitis_saati", "ALTER TABLE vardiya_tipleri ADD COLUMN bitis_saati TEXT"),
        ("ayarlar_kullanicilar", "ayrilma_tarihi", "ALTER TABLE ayarlar_kullanicilar ADD COLUMN ayrilma_tarihi DATE"),
        ("ayarlar_kullanicilar", "ayrilma_nedeni", "ALTER TABLE ayarlar_kullanicilar ADD COLUMN ayrilma_nedeni TEXT"),
        ("ayarlar_yetkiler", "eylem_yetkileri", "ALTER TABLE ayarlar_yetkiler ADD COLUMN eylem_yetkileri TEXT"),
        # v6.3.5: QMS Standardizasyon
        ("qms_departmanlar", "durum", "ALTER TABLE qms_departmanlar ADD COLUMN durum TEXT DEFAULT 'AKTİF'"),
        ("qms_departman_turleri", "renk_kodu", "ALTER TABLE qms_departman_turleri ADD COLUMN renk_kodu VARCHAR(20)"),
        ("qms_departman_turleri", "durum", "ALTER TABLE qms_departman_turleri ADD COLUMN durum TEXT DEFAULT 'AKTİF'"),
        ("qms_departman_turleri", "kurallar_json", "ALTER TABLE qms_departman_turleri ADD COLUMN kurallar_json TEXT"),
        ("qms_departmanlar", "guncelleme_tarihi", "ALTER TABLE qms_departmanlar ADD COLUMN guncelleme_tarihi TIMESTAMP"),
        ("ayarlar_kullanicilar", "operasyonel_bolum_id", "ALTER TABLE ayarlar_kullanicilar ADD COLUMN operasyonel_bolum_id INTEGER"),
        ("ayarlar_kullanicilar", "ikincil_yonetici_id",  "ALTER TABLE ayarlar_kullanicilar ADD COLUMN ikincil_yonetici_id INTEGER"),
        ("map_vardiya", "urun_adi", "ALTER TABLE map_vardiya ADD COLUMN urun_adi TEXT"),
        # v6.1.2: System Settings Hardening (Fix Truncation)
        ("sistem_parametreleri", "deger_type_fix", "ALTER TABLE sistem_parametreleri ALTER COLUMN deger TYPE TEXT"),
        # v6.1.8: Product Categorization & Hardening
        ("ayarlar_urunler", "urun_tipi", "ALTER TABLE ayarlar_urunler ADD COLUMN urun_tipi TEXT DEFAULT 'MAMUL'"),
        ("ayarlar_urunler", "uretim_bolumu", "ALTER TABLE ayarlar_urunler ADD COLUMN uretim_bolumu TEXT"),
        ("ayarlar_yetkiler", "eylem_yetkileri_fix", "ALTER TABLE ayarlar_yetkiler ALTER COLUMN eylem_yetkileri TYPE TEXT"),
        ("sistem_loglari", "detay_json_fix", "ALTER TABLE sistem_loglari ALTER COLUMN detay_json TYPE TEXT"),
        ("map_vardiya", "notlar_fix", "ALTER TABLE map_vardiya ALTER COLUMN notlar TYPE TEXT"),
        # v6.1.9: ayarlar_urunler metadata gaps
        ("ayarlar_urunler", "versiyon_no", "ALTER TABLE ayarlar_urunler ADD COLUMN versiyon_no INTEGER DEFAULT 1"),
        ("ayarlar_urunler", "alerjen_bilgisi", "ALTER TABLE ayarlar_urunler ADD COLUMN alerjen_bilgisi TEXT"),
        ("ayarlar_urunler", "depolama_sartlari", "ALTER TABLE ayarlar_urunler ADD COLUMN depolama_sartlari TEXT"),
        ("ayarlar_urunler", "ambalaj_tipi", "ALTER TABLE ayarlar_urunler ADD COLUMN ambalaj_tipi TEXT"),
        ("ayarlar_urunler", "hedef_kitle", "ALTER TABLE ayarlar_urunler ADD COLUMN hedef_kitle TEXT"),
        ("ayarlar_urunler", "guncelleme_ts", "ALTER TABLE ayarlar_urunler ADD COLUMN guncelleme_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # v6.2.3: Seeding Hardening (UNIQUE Index critical for ON CONFLICT in Cloud)
        ("ayarlar_urunler", "urun_adi_index", "CREATE UNIQUE INDEX IF NOT EXISTS idx_ayarlar_urunler_adi ON ayarlar_urunler (urun_adi)"),
    ]

def run_migrations(conn):
    """Eksik kolonları kontrol eder ve migrasyonları uygular (Sadece PostgreSQL)."""
    existing_cols = _get_existing_columns(conn)
    mig_list = get_migration_list()
    
    for tbl, col, sql in mig_list:
        # Check logic: If second param contains 'index', we check if it runs safely without error
        is_index = "INDEX" in sql.upper()
        
        if is_index or (tbl.lower(), col.lower()) not in existing_cols:
            try:
                # v6.1.2: Standard execution (SQLite support removed)
                conn.execute(text(sql))
                if not is_index: print(f"Migration Success: {tbl}.{col}")
                else: print(f"Index Migration Applied: {tbl}")
                
                # v6.0 Standardizasyon: aktif -> durum veri göçü
                if not is_index and col == "durum":
                    try:
                        conn.execute(text(f"UPDATE {tbl} SET durum = CASE WHEN aktif = 1 THEN 'AKTİF' ELSE 'PASİF' END WHERE durum IS NULL"))
                        print(f"Data Standardized: {tbl}.durum")
                    except Exception as de:
                        print(f"Data Migration Warning ({tbl}): {de}")
            except Exception as e:
                # v6.4.0: Standardized error handling for PG
                if is_index and "already exists" in str(e).lower():
                    continue
                print(f"Migration Error ({tbl}.{col}): {e}")

def _get_existing_columns(conn):
    """Mevcut kolon listesini döner (PostgreSQL version)."""
    res = conn.execute(text("""
        SELECT table_name, column_name FROM information_schema.columns 
        WHERE table_schema = current_schema()
    """)).fetchall()
    return {(r[0].lower(), r[1].lower()) for r in res}
