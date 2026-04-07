from sqlalchemy import text

def init_qdms_tables(engine):
    """
    ANAYASA v3.0: QDMS Modülü için 6 yeni tabloyu güvenli (T1) şekilde oluşturur.
    Hem SQLite hem de PostgreSQL (Supabase) ile tam uyumludur.
    13. Adam Protokolü: personel(id) referansı doğrulanmıştır.
    """
    is_pg = engine.dialect.name == 'postgresql'
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _dt = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "DATETIME DEFAULT CURRENT_TIMESTAMP"
    
    tables = [
        # 1. qdms_belgeler (Core)
        f"""
        CREATE TABLE IF NOT EXISTS qdms_belgeler (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL UNIQUE,
            belge_adi           TEXT NOT NULL,
            belge_tipi          TEXT NOT NULL,
            alt_kategori        TEXT,
            aktif_rev           INTEGER NOT NULL DEFAULT 1,
            durum               TEXT NOT NULL DEFAULT 'taslak',
            olusturan_id        INTEGER,
            olusturma_tarihi    {_dt},
            guncelleme_tarihi   {_dt},
            aciklama            TEXT,
            amac               TEXT,
            kapsam             TEXT,
            tanimlar           TEXT,
            dokumanlar         TEXT,
            icerik             TEXT,
            FOREIGN KEY (olusturan_id) REFERENCES personel(id)
        )
        """,
        # 2. qdms_sablonlar
        f"""
        CREATE TABLE IF NOT EXISTS qdms_sablonlar (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            rev_no              INTEGER NOT NULL DEFAULT 1,
            header_config       TEXT NOT NULL,
            kolon_config        TEXT NOT NULL,
            meta_panel_config   TEXT,
            sayfa_boyutu        TEXT DEFAULT 'A4',
            sayfa_yonu          TEXT DEFAULT 'dikey',
            renk_tema           TEXT,
            css_ek              TEXT,
            aktif               INTEGER DEFAULT 1,
            olusturma_tarihi    {_dt},
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu),
            UNIQUE (belge_kodu, rev_no)
        )
        """,
        # 3. qdms_revizyon_log
        f"""
        CREATE TABLE IF NOT EXISTS qdms_revizyon_log (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            eski_rev            INTEGER,
            yeni_rev            INTEGER NOT NULL,
            degisiklik_notu     TEXT NOT NULL,
            degistiren_id       INTEGER,
            degisiklik_tarihi   {_dt},
            degisiklik_tipi     TEXT,
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu),
            FOREIGN KEY (degistiren_id) REFERENCES personel(id)
        )
        """,
        # 4. qdms_yayim
        f"""
        CREATE TABLE IF NOT EXISTS qdms_yayim (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            rev_no              INTEGER NOT NULL,
            yayim_tarihi        {_dt},
            iptal_tarihi        {_dt},
            yayimlayan_id       INTEGER,
            lokasyon_kapsam     TEXT DEFAULT 'tum',
            yayim_notu          TEXT,
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu),
            FOREIGN KEY (yayimlayan_id) REFERENCES personel(id)
        )
        """,
        # 5. qdms_talimatlar
        f"""
        CREATE TABLE IF NOT EXISTS qdms_talimatlar (
            id                  {_pk},
            talimat_kodu        TEXT NOT NULL UNIQUE,
            belge_kodu          TEXT,
            talimat_adi         TEXT NOT NULL,
            talimat_tipi        TEXT NOT NULL,
            ekipman_id          INTEGER,
            departman           TEXT,
            adimlar_json        TEXT,
            gorsel_url          TEXT,
            qr_token            TEXT UNIQUE,
            aktif               INTEGER DEFAULT 1,
            rev_no              INTEGER DEFAULT 1,
            olusturma_tarihi    {_dt},
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu)
        )
        """,
        # 6. qdms_okuma_onay
        f"""
        CREATE TABLE IF NOT EXISTS qdms_okuma_onay (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            rev_no              INTEGER NOT NULL,
            personel_id         INTEGER NOT NULL,
            okuma_tarihi        {_dt},
            onay_tipi           TEXT DEFAULT 'manuel',
            cihaz_bilgisi       TEXT,
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu),
            FOREIGN KEY (personel_id) REFERENCES personel(id)
        )
        """,
        # 7. qdms_gorev_karti (GK Main)
        f"""
        CREATE TABLE IF NOT EXISTS qdms_gorev_karti (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL UNIQUE,
            pozisyon_adi        TEXT,
            departman           TEXT,
            bagli_pozisyon      TEXT,
            vekalet_eden        TEXT,
            zone                TEXT,
            vardiya_turu        TEXT,
            gorev_ozeti         TEXT,
            finansal_yetki_tl   TEXT,
            imza_yetkisi        TEXT,
            vekalet_kosullari   TEXT,
            min_egitim          TEXT,
            min_deneyim_yil     INTEGER,
            zorunlu_sertifikalar TEXT,
            tercihli_nitelikler TEXT,
            olusturan_id        INTEGER,
            guncelleme_ts       {_dt},
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu)
        )
        """,
        # 8. qdms_gk_sorumluluklar (v3.6: 5-Discipline Expansion)
        f"""
        CREATE TABLE IF NOT EXISTS qdms_gk_sorumluluklar (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            kategori            TEXT, -- Eski kategori (Gıda Güvenliği, Kalite vb.)
            disiplin_tipi       TEXT, -- Yeni Enum (personel, operasyon, gida_guvenligi, isg, cevre)
            sira_no             INTEGER,
            sorumluluk          TEXT,
            etkilesim_birimleri TEXT, -- RACI bağlantılı birimler (örn: İK, Kalite)
            sertifikasyon       TEXT,
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu)
        )
        """,
        # 9. qdms_gk_etkilesim
        f"""
        CREATE TABLE IF NOT EXISTS qdms_gk_etkilesim (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            taraf               TEXT,
            konu                TEXT,
            siklik              TEXT,
            raci_rol            TEXT,
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu)
        )
        """,
        # 10. qdms_gk_periyodik_gorevler
        f"""
        CREATE TABLE IF NOT EXISTS qdms_gk_periyodik_gorevler (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            gorev_adi           TEXT,
            periyot             TEXT,
            talimat_kodu        TEXT,
            sertifikasyon_maddesi TEXT,
            onay_gerekli        INTEGER DEFAULT 0,
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu)
        )
        """,
        # 11. qdms_gk_kpi
        f"""
        CREATE TABLE IF NOT EXISTS qdms_gk_kpi (
            id                  {_pk},
            belge_kodu          TEXT NOT NULL,
            kpi_adi             TEXT,
            olcum_birimi        TEXT,
            hedef_deger         TEXT,
            degerlendirme_periyodu TEXT,
            degerlendirici      TEXT,
            FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu)
        )
        """
    ]
    
    with engine.begin() as conn:
        for sql in tables:
            try:
                conn.execute(text(sql))
            except Exception as e:
                print(f"Error creating QDMS tables: {e}")
                # Log or handle error as needed
                raise e

def get_supabase_migration_sql():
    """Supabase için SQL migration dosyasını döner."""
    # (Bu fonksiyon manuel kopyala-yapıştır için SQL üretir)
    sql_base = open(__file__, 'r').read()
    # Gerekirse burada dinamik SQL string'i de üretilebilir.
    pass
