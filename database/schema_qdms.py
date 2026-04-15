from sqlalchemy import text

def _s_qdms_core_tables(_pk, _dt):
    """QDMS ana doküman ve revizyon yapılarını tanımlar."""
    return [
        f"CREATE TABLE IF NOT EXISTS qdms_belgeler (id {_pk}, belge_kodu TEXT NOT NULL UNIQUE, belge_adi TEXT NOT NULL, belge_tipi TEXT NOT NULL, alt_kategori TEXT, aktif_rev INTEGER NOT NULL DEFAULT 1, durum TEXT NOT NULL DEFAULT 'taslak', olusturan_id INTEGER, olusturma_tarihi {_dt}, guncelleme_tarihi {_dt}, aciklama TEXT, amac TEXT, kapsam TEXT, tanimlar TEXT, dokumanlar TEXT, icerik TEXT, FOREIGN KEY (olusturan_id) REFERENCES personel(id))",
        f"CREATE TABLE IF NOT EXISTS qdms_sablonlar (id {_pk}, belge_kodu TEXT NOT NULL, rev_no INTEGER NOT NULL DEFAULT 1, header_config TEXT NOT NULL, kolon_config TEXT NOT NULL, meta_panel_config TEXT, sayfa_boyutu TEXT DEFAULT 'A4', sayfa_yonu TEXT DEFAULT 'dikey', renk_tema TEXT, css_ek TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi {_dt}, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), UNIQUE (belge_kodu, rev_no))",
        f"CREATE TABLE IF NOT EXISTS qdms_revizyon_log (id {_pk}, belge_kodu TEXT NOT NULL, eski_rev INTEGER, yeni_rev INTEGER NOT NULL, degisiklik_notu TEXT NOT NULL, degistiren_id INTEGER, degisiklik_tarihi {_dt}, degisiklik_tipe TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), FOREIGN KEY (degistiren_id) REFERENCES personel(id))"
    ]

def _s_qdms_workflow_tables(_pk, _dt):
    """Yayım ve onay süreçlerini tanımlar."""
    return [
        f"CREATE TABLE IF NOT EXISTS qdms_yayim (id {_pk}, belge_kodu TEXT NOT NULL, rev_no INTEGER NOT NULL, yayim_tarihi {_dt}, iptal_tarihi {_dt}, yayimlayan_id INTEGER, lokasyon_kapsam TEXT DEFAULT 'tum', yayim_notu TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), FOREIGN KEY (yayimlayan_id) REFERENCES personel(id))",
        f"CREATE TABLE IF NOT EXISTS qdms_talimatlar (id {_pk}, talimat_kodu TEXT NOT NULL UNIQUE, belge_kodu TEXT, talimat_adi TEXT NOT NULL, talimat_tipi TEXT NOT NULL, ekipman_id INTEGER, departman TEXT, adimlar_json TEXT, gorsel_url TEXT, qr_token TEXT UNIQUE, aktif INTEGER DEFAULT 1, rev_no INTEGER DEFAULT 1, olusturma_tarihi {_dt}, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))",
        f"CREATE TABLE IF NOT EXISTS qdms_okuma_onay (id {_pk}, belge_kodu TEXT NOT NULL, rev_no INTEGER NOT NULL, personel_id INTEGER NOT NULL, okuma_tarihi {_dt}, onay_tipi TEXT DEFAULT 'manuel', cihaz_bilgisi TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), FOREIGN KEY (personel_id) REFERENCES personel(id))"
    ]

def _s_qdms_gk_tables(_pk, _dt):
    """Görev Kartı (GK) ve buna bağlı KPI/Sorumluluk tablolarını tanımlar."""
    return [
        f"CREATE TABLE IF NOT EXISTS qdms_gorev_karti (id {_pk}, belge_kodu TEXT NOT NULL UNIQUE, pozisyon_adi TEXT, departman TEXT, bagli_pozisyon TEXT, vekalet_eden TEXT, zone TEXT, vardiya_turu TEXT, gorev_ozeti TEXT, finansal_yetki_tl TEXT, imza_yetkisi TEXT, vekalet_kosullari TEXT, min_egitim TEXT, min_deneyim_yil INTEGER, zorunlu_sertifikalar TEXT, tercihli_nitelikler TEXT, olusturan_id INTEGER, guncelleme_ts {_dt}, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))",
        f"CREATE TABLE IF NOT EXISTS qdms_gk_sorumluluklar (id {_pk}, belge_kodu TEXT NOT NULL, kategori TEXT, disiplin_tipi TEXT, sira_no INTEGER, sorumluluk TEXT, etkilesim_birimleri TEXT, sertifikasyon TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))",
        f"CREATE TABLE IF NOT EXISTS qdms_gk_etkilesim (id {_pk}, belge_kodu TEXT NOT NULL, taraf TEXT, konu TEXT, siklik TEXT, raci_rol TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))",
        f"CREATE TABLE IF NOT EXISTS qdms_gk_periyodik_gorevler (id {_pk}, belge_kodu TEXT NOT NULL, gorev_adi TEXT, periyot TEXT, talimat_kodu TEXT, sertifikasyon_maddesi TEXT, onay_gerekli INTEGER DEFAULT 0, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))",
        f"CREATE TABLE IF NOT EXISTS qdms_gk_kpi (id {_pk}, belge_kodu TEXT NOT NULL, kpi_adi TEXT, olcum_birimi TEXT, hedef_deger TEXT, degerlendirme_periyodu TEXT, degerlendirici TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))"
    ]

def init_qdms_tables(engine):
    """ANAYASA v5.0: QDMS Modülü tablolarını modüler helper'lar ile oluşturur."""
    is_pg = engine.dialect.name == 'postgresql'
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _dt = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "DATETIME DEFAULT CURRENT_TIMESTAMP"
    
    tables = _s_qdms_core_tables(_pk, _dt) + \
             _s_qdms_workflow_tables(_pk, _dt) + \
             _s_qdms_gk_tables(_pk, _dt)
    
    with engine.begin() as conn:
        for sql in tables:
            try: conn.execute(text(sql))
            except Exception as e:
                print(f"Error creating QDMS tables: {e}")
                raise e

def get_supabase_migration_sql():
    """Supabase için SQL migration dosyasını döner. Placeholder."""
    pass
