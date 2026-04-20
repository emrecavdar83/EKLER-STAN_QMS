from sqlalchemy import text

def init_all_tables(conn):
    """Sistemdeki tüm tabloların kurulumunu koordine eder."""
    _pk = "SERIAL PRIMARY KEY"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    _if_not_exists = "IF NOT EXISTS"
    
    # 1. Çekirdek Sistem Tabloları
    core_tables = [
        ('ayarlar_kullanicilar', f"""CREATE TABLE {_if_not_exists} ayarlar_kullanicilar (
            id {_pk}, ad_soyad TEXT, kullanici_adi VARCHAR(50) UNIQUE NOT NULL, sifre TEXT, rol VARCHAR(50), 
            gorev TEXT, vardiya VARCHAR(50), durum VARCHAR(20) DEFAULT 'AKTİF', 
            ise_giris_tarihi DATE, izin_gunu VARCHAR(50), departman_id INTEGER, yonetici_id INTEGER, 
            pozisyon_seviye VARCHAR(50), is_cikis_tarihi DATE, ayrilma_sebebi TEXT, 
            bolum VARCHAR(100), sorumlu_bolum VARCHAR(100), kat VARCHAR(50), telefon_no VARCHAR(20), 
            servis_duragi TEXT, guncelleme_tarihi {_ts}, operasyonel_bolum_id INTEGER, 
            ikincil_yonetici_id INTEGER, baslama_tarihi DATE, vekil_id INTEGER, 
            aktif_izinde_mi INTEGER DEFAULT 0, ayrilma_tarihi DATE, ayrilma_nedeni TEXT, qms_departman_id INTEGER
        )"""),
        ('sistem_loglari', f"CREATE TABLE {_if_not_exists} sistem_loglari (id {_pk}, islem_tipi VARCHAR(50), detay TEXT, modul VARCHAR(50), kullanici_id INTEGER, detay_json TEXT, ip_adresi VARCHAR(45), cihaz_bilgisi TEXT, zaman {_ts})"),
        ('hata_loglari', f"CREATE TABLE {_if_not_exists} hata_loglari (id {_pk}, hata_kodu VARCHAR(20) UNIQUE NOT NULL, seviye VARCHAR(20) DEFAULT 'ERROR', modul VARCHAR(50), fonksiyon VARCHAR(100), hata_mesaji TEXT NOT NULL, stack_trace TEXT, context_data TEXT, ai_diagnosis TEXT, kullanici_id INTEGER, is_fixed INTEGER DEFAULT 0, zaman {_ts})"),
        ('lokasyon_tipleri', f"CREATE TABLE {_if_not_exists} lokasyon_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)"),
        ('vardiya_tipleri', f"CREATE TABLE {_if_not_exists} vardiya_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1, baslangic_saati TEXT, bitis_saati TEXT)"),
        ('qms_departman_turleri', f"""CREATE TABLE {_if_not_exists} qms_departman_turleri (
            id {_pk}, tur_adi VARCHAR(50) UNIQUE NOT NULL, renk_kodu VARCHAR(20), kurallar_json TEXT, sira_no INTEGER DEFAULT 10, durum TEXT DEFAULT 'AKTİF'
        )"""),
        ('qms_departmanlar', f"""CREATE TABLE {_if_not_exists} qms_departmanlar (
            id {_pk}, ad VARCHAR(100) NOT NULL, kod VARCHAR(50), ust_id INTEGER, ikincil_ust_id INTEGER, tur_id INTEGER, yonetici_id INTEGER, dil_anahtari VARCHAR(100), sira_no INTEGER DEFAULT 10, durum TEXT DEFAULT 'AKTİF', guncelleme_tarihi TIMESTAMP,
            FOREIGN KEY (ust_id) REFERENCES qms_departmanlar(id), FOREIGN KEY (ikincil_ust_id) REFERENCES qms_departmanlar(id),
            FOREIGN KEY (tur_id) REFERENCES qms_departman_turleri(id), FOREIGN KEY (yonetici_id) REFERENCES ayarlar_kullanicilar(id)
        )"""),
        ('sistem_parametreleri', f"CREATE TABLE {_if_not_exists} sistem_parametreleri (id {_pk}, anahtar VARCHAR(100) UNIQUE NOT NULL, deger TEXT NOT NULL, aciklama TEXT, guncelleme_ts {_ts})"),
        ('ayarlar_urunler', f"""CREATE TABLE {_if_not_exists} ayarlar_urunler (
            id {_pk}, urun_adi TEXT NOT NULL UNIQUE, urun_tipi TEXT DEFAULT 'MAMUL', sorumlu_departman TEXT, 
            uretim_bolumu TEXT, raf_omru_gun INTEGER, numune_sayisi INTEGER, 
            alerjen_bilgisi TEXT, depolama_sartlari TEXT, ambalaj_tipi TEXT, hedef_kitle TEXT,
            versiyon_no INTEGER DEFAULT 1, guncelleme_ts {_ts}
        )"""),
    ]

    # 2. Operasyonel ve Personel Tabloları
    op_tables = [
        ('personel_transfer_log', f"""CREATE TABLE {_if_not_exists} personel_transfer_log (
            id {_pk}, personel_id INTEGER NOT NULL, eski_bolum_id INTEGER, yeni_bolum_id INTEGER, islem_yapan_id INTEGER, transfer_tarihi {_ts}, durum TEXT DEFAULT 'BEKLEMEDE', transfer_tipi TEXT, neden TEXT
        )"""),
        ('personel_performans_skorlari', f"""CREATE TABLE {_if_not_exists} personel_performans_skorlari (
            id {_pk}, personel_id INTEGER NOT NULL, donem VARCHAR(20), hijyen_skoru FLOAT DEFAULT 0, hiz_skoru FLOAT DEFAULT 0, kalite_skoru FLOAT DEFAULT 0, genel_skor FLOAT DEFAULT 0, zaman {_ts}, UNIQUE(personel_id, donem)
        )"""),
        ('personel_vardiya_programi', f"""CREATE TABLE {_if_not_exists} personel_vardiya_programi (
            id {_pk}, personel_id INTEGER NOT NULL, baslangic_tarihi TEXT NOT NULL, bitis_tarihi TEXT NOT NULL, vardiya TEXT, izin_gunleri TEXT, aciklama TEXT, onay_durumu TEXT DEFAULT 'ONAYLANDI', onaylayan_id INTEGER, onay_ts {_ts}
        )"""),
        ('birlesik_gorev_havuzu', f"""CREATE TABLE {_if_not_exists} birlesik_gorev_havuzu (
            id {_pk}, personel_id INTEGER NOT NULL, bolum_id INTEGER, gorev_kaynagi VARCHAR(50) NOT NULL, kaynak_id INTEGER NOT NULL, atanma_tarihi DATE NOT NULL, hedef_tarih DATE NOT NULL, durum VARCHAR(50) DEFAULT 'BEKLIYOR', tamamlanma_tarihi DATETIME, atayan_id INTEGER
        )"""),
        ('hijyen_kontrol_kayitlari', f"""CREATE TABLE {_if_not_exists} hijyen_kontrol_kayitlari (
            id {_pk}, tarih TEXT NOT NULL, saat TEXT, kullanici TEXT, vardiya TEXT, bolum TEXT, ayarlar_kullanicilar TEXT, durum TEXT, sebep TEXT, aksiyon TEXT
        )"""),
        # Aşama 2: Audit Trails for Remaining Modules (MADDE 31 - Detaylı Değişim Loglama)
        ('vardiya_degisim_loglari', f"""CREATE TABLE {_if_not_exists} vardiya_degisim_loglari (
            id {_pk}, vardiya_id INTEGER NOT NULL REFERENCES personel_vardiya_programi(id), alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}, islem_tipi VARCHAR(50) DEFAULT 'UPDATE'
        )"""),
        ('gunluk_gorev_degisim_loglari', f"""CREATE TABLE {_if_not_exists} gunluk_gorev_degisim_loglari (
            id {_pk}, gorev_id INTEGER NOT NULL, alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}, islem_tipi VARCHAR(50) DEFAULT 'UPDATE'
        )"""),
        ('map_vardiya_degisim_loglari', f"""CREATE TABLE {_if_not_exists} map_vardiya_degisim_loglari (
            id {_pk}, map_vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id), alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}, islem_tipi VARCHAR(50) DEFAULT 'UPDATE'
        )"""),
        ('qdms_belge_degisim_detay', f"""CREATE TABLE {_if_not_exists} qdms_belge_degisim_detay (
            id {_pk}, revizyon_log_id INTEGER REFERENCES qdms_revizyon_log(id), alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}
        )"""),
        ('urun_kpi_degisim_loglari', f"""CREATE TABLE {_if_not_exists} urun_kpi_degisim_loglari (
            id {_pk}, kpi_id INTEGER NOT NULL REFERENCES urun_kpi_kontrol(id), alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, girisci_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            giris_tarihi {_ts}
        )"""),
        ('hijyen_kontrol_degisim_loglari', f"""CREATE TABLE {_if_not_exists} hijyen_kontrol_degisim_loglari (
            id {_pk}, kontrol_id INTEGER NOT NULL, alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}, islem_tipi VARCHAR(50) DEFAULT 'UPDATE'
        )"""),
        ('performans_degisim_loglari', f"""CREATE TABLE {_if_not_exists} performans_degisim_loglari (
            id {_pk}, degerlendirme_id INTEGER NOT NULL, alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}, islem_tipi VARCHAR(50) DEFAULT 'UPDATE'
        )"""),
        ('gmp_denetim_degisim_loglari', f"""CREATE TABLE {_if_not_exists} gmp_denetim_degisim_loglari (
            id {_pk}, denetim_id INTEGER NOT NULL, alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}, islem_tipi VARCHAR(50) DEFAULT 'INSERT'
        )"""),
        ('temizlik_kayitlari_degisim_loglari', f"""CREATE TABLE {_if_not_exists} temizlik_kayitlari_degisim_loglari (
            id {_pk}, temizlik_kaydı_id INTEGER NOT NULL, alan_adi VARCHAR(100) NOT NULL,
            eski_deger TEXT, yeni_deger TEXT, degistiren_kullanici_id INTEGER REFERENCES ayarlar_kullanicilar(id),
            degisim_tarihi {_ts}, islem_tipi VARCHAR(50) DEFAULT 'INSERT'
        )"""),
    ]

    # 3. MAP ve Performans Tabloları
    map_perf_tables = [
        ('map_vardiya', f"CREATE TABLE {_if_not_exists} map_vardiya (id {_pk}, tarih TEXT NOT NULL, makina_no TEXT NOT NULL DEFAULT 'MAP-01', urun_adi TEXT, vardiya_no INTEGER NOT NULL, baslangic_saati TEXT NOT NULL, bitis_saati TEXT, operator_adi TEXT NOT NULL, vardiya_sefi TEXT, besleme_kisi INTEGER, kasalama_kisi INTEGER, hedef_hiz_paket_dk FLOAT, gerceklesen_uretim INTEGER DEFAULT 0, acan_kullanici_id INTEGER, kapatan_kullanici_id INTEGER, durum TEXT DEFAULT 'ACIK', notlar TEXT, olusturma_ts {_ts}, guncelleme_ts {_ts})"),
        ('map_zaman_cizelgesi', f"CREATE TABLE {_if_not_exists} map_zaman_cizelgesi (id {_pk}, vardiya_id INTEGER NOT NULL, sira_no INTEGER NOT NULL, baslangic_ts TEXT NOT NULL, bitis_ts TEXT, sure_dk FLOAT, durum TEXT NOT NULL, neden TEXT, aciklama TEXT)"),
        ('map_fire_kaydi', f"CREATE TABLE {_if_not_exists} map_fire_kaydi (id {_pk}, vardiya_id INTEGER NOT NULL, fire_tipi TEXT NOT NULL, miktar_adet INTEGER NOT NULL, bobin_ref TEXT, aciklama TEXT, olusturma_ts {_ts})"),
        ('map_bobin_kaydi', f"CREATE TABLE {_if_not_exists} map_bobin_kaydi (id {_pk}, vardiya_id INTEGER NOT NULL, sira_no INTEGER NOT NULL, degisim_ts TEXT NOT NULL, bobin_lot TEXT NOT NULL, film_tipi TEXT DEFAULT 'Üst Film', baslangic_kg FLOAT, bitis_kg FLOAT, kullanilan_kg FLOAT, aciklama TEXT)"),
        ('map_durus_nedenleri', f"CREATE TABLE {_if_not_exists} map_durus_nedenleri (id {_pk}, neden TEXT UNIQUE NOT NULL, aktif INTEGER DEFAULT 1)"),
        ('map_fire_tipleri', f"CREATE TABLE {_if_not_exists} map_fire_tipleri (id {_pk}, fire_tipi TEXT UNIQUE NOT NULL, aktif INTEGER DEFAULT 1)"),
    ]

    # 4. QDMS (Doküman ve Görev Yönetimi) Tabloları
    qdms_tables = [
        ('qdms_belgeler', f"CREATE TABLE {_if_not_exists} qdms_belgeler (id {_pk}, belge_kodu TEXT NOT NULL UNIQUE, belge_adi TEXT NOT NULL, belge_tipi TEXT NOT NULL, alt_kategori TEXT, aktif_rev INTEGER NOT NULL DEFAULT 1, durum TEXT NOT NULL DEFAULT 'taslak', olusturan_id INTEGER, olusturma_tarihi {_ts}, guncelleme_tarihi {_ts}, aciklama TEXT, amac TEXT, kapsam TEXT, tanimlar TEXT, dokumanlar TEXT, icerik TEXT, FOREIGN KEY (olusturan_id) REFERENCES ayarlar_kullanicilar(id))"),
        ('qdms_sablonlar', f"CREATE TABLE {_if_not_exists} qdms_sablonlar (id {_pk}, belge_kodu TEXT NOT NULL, rev_no INTEGER NOT NULL DEFAULT 1, header_config TEXT NOT NULL, kolon_config TEXT NOT NULL, meta_panel_config TEXT, sayfa_boyutu TEXT DEFAULT 'A4', sayfa_yonu TEXT DEFAULT 'dikey', renk_tema TEXT, css_ek TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi {_ts}, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), UNIQUE (belge_kodu, rev_no))"),
        ('qdms_revizyon_log', f"CREATE TABLE {_if_not_exists} qdms_revizyon_log (id {_pk}, belge_kodu TEXT NOT NULL, eski_rev INTEGER, yeni_rev INTEGER NOT NULL, degisiklik_notu TEXT NOT NULL, degistiren_id INTEGER, degisiklik_tarihi {_ts}, degisiklik_tipi TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), FOREIGN KEY (degistiren_id) REFERENCES ayarlar_kullanicilar(id))"),
        ('qdms_yayim', f"CREATE TABLE {_if_not_exists} qdms_yayim (id {_pk}, belge_kodu TEXT NOT NULL, rev_no INTEGER NOT NULL, yayim_tarihi {_ts}, iptal_tarihi {_ts}, yayimlayan_id INTEGER, lokasyon_kapsam TEXT DEFAULT 'tum', yayim_notu TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), FOREIGN KEY (yayimlayan_id) REFERENCES ayarlar_kullanicilar(id))"),
        ('qdms_talimatlar', f"CREATE TABLE {_if_not_exists} qdms_talimatlar (id {_pk}, talimat_kodu TEXT NOT NULL UNIQUE, belge_kodu TEXT, talimat_adi TEXT NOT NULL, talimat_tipi TEXT NOT NULL, ekipman_id INTEGER, departman TEXT, adimlar_json TEXT, gorsel_url TEXT, qr_token TEXT UNIQUE, aktif INTEGER DEFAULT 1, rev_no INTEGER DEFAULT 1, olusturma_tarihi {_ts}, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))"),
        ('qdms_okuma_onay', f"CREATE TABLE {_if_not_exists} qdms_okuma_onay (id {_pk}, belge_kodu TEXT NOT NULL, rev_no INTEGER NOT NULL, personel_id INTEGER NOT NULL, okuma_tarihi {_ts}, onay_tipi TEXT DEFAULT 'manuel', cihaz_bilgisi TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu), FOREIGN KEY (personel_id) REFERENCES ayarlar_kullanicilar(id))"),
        ('qdms_gorev_karti', f"CREATE TABLE {_if_not_exists} qdms_gorev_karti (id {_pk}, belge_kodu TEXT NOT NULL UNIQUE, pozisyon_adi TEXT, departman TEXT, bagli_pozisyon TEXT, vekalet_eden TEXT, zone TEXT, vardiya_turu TEXT, gorev_ozeti TEXT, finansal_yetki_tl TEXT, imza_yetkisi TEXT, vekalet_kosullari TEXT, min_egitim TEXT, min_deneyim_yil INTEGER, zorunlu_sertifikalar TEXT, tercihli_nitelikler TEXT, olusturan_id INTEGER, guncelleme_ts {_ts}, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))"),
        ('qdms_gk_sorumluluklar', f"CREATE TABLE {_if_not_exists} qdms_gk_sorumluluklar (id {_pk}, belge_kodu TEXT NOT NULL, kategori TEXT, disiplin_tipi TEXT, sira_no INTEGER, sorumluluk TEXT, etkilesim_birimleri TEXT, sertifikasyon TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))"),
        ('qdms_gk_etkilesim', f"CREATE TABLE {_if_not_exists} qdms_gk_etkilesim (id {_pk}, belge_kodu TEXT NOT NULL, taraf TEXT, konu TEXT, siklik TEXT, raci_rol TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))"),
        ('qdms_gk_periyodik_gorevler', f"CREATE TABLE {_if_not_exists} qdms_gk_periyodik_gorevler (id {_pk}, gorev_adi TEXT, periyot TEXT, talimat_kodu TEXT, sertifikasyon_maddesi TEXT, onay_gerekli INTEGER DEFAULT 0, belge_kodu TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))"),
        ('qdms_gk_kpi', f"CREATE TABLE {_if_not_exists} qdms_gk_kpi (id {_pk}, belge_kodu TEXT NOT NULL, kpi_adi TEXT, olcum_birimi TEXT, hedef_deger TEXT, degerlendirme_periyodu TEXT, degerlendirici TEXT, FOREIGN KEY (belge_kodu) REFERENCES qdms_belgeler(belge_kodu))"),
    ]

    # 5. SOSTS (Soğuk Oda Takip Sistemi) Tabloları
    sosts_tables = [
        ('soguk_odalar', f"CREATE TABLE {_if_not_exists} soguk_odalar (id {_pk}, oda_kodu VARCHAR(50) UNIQUE NOT NULL, oda_adi VARCHAR(100) NOT NULL, departman VARCHAR(100), min_sicaklik DOUBLE PRECISION NOT NULL DEFAULT 0.0, max_sicaklik DOUBLE PRECISION NOT NULL DEFAULT 4.0, sapma_takip_dakika INTEGER NOT NULL DEFAULT 30, olcum_sikligi INTEGER NOT NULL DEFAULT 2, qr_token VARCHAR(100) UNIQUE, qr_uretim_tarihi TIMESTAMP, aktif INTEGER DEFAULT 1, ozel_olcum_saatleri TEXT, sorumlu_personel VARCHAR(255), durum VARCHAR(50) DEFAULT 'AKTİF', last_rule_hash VARCHAR(32), guncelleme_tarihi {_ts}, olusturulma_tarihi {_ts})"),
        ('soguk_oda_planlama_kurallari', f"CREATE TABLE {_if_not_exists} soguk_oda_planlama_kurallari (id {_pk}, oda_id INTEGER NOT NULL, kural_adi VARCHAR(100), baslangic_saati INTEGER NOT NULL, bitis_saati INTEGER NOT NULL, siklik INTEGER NOT NULL, kural_durumu VARCHAR(20) DEFAULT 'Ölçüm', aciklama_dof_no TEXT, aktif INTEGER DEFAULT 1, guncelleme_tarihi {_ts}, FOREIGN KEY (oda_id) REFERENCES soguk_odalar(id))"),
        ('sicaklik_olcumleri', f"CREATE TABLE {_if_not_exists} sicaklik_olcumleri (id {_pk}, oda_id INTEGER NOT NULL, sicaklik_degeri DOUBLE PRECISION NOT NULL, olcum_zamani {_ts}, planlanan_zaman TIMESTAMP, qr_ile_girildi INTEGER DEFAULT 1, kaydeden_kullanici VARCHAR(100), sapma_var_mi INTEGER DEFAULT 0, sapma_aciklamasi TEXT, is_takip INTEGER DEFAULT 0, olusturulma_tarihi {_ts})"),
        ('olcum_plani', f"CREATE TABLE {_if_not_exists} olcum_plani (id {_pk}, oda_id INTEGER NOT NULL, beklenen_zaman TIMESTAMP NOT NULL, bitis_zamani TIMESTAMP, gerceklesen_olcum_id INTEGER, durum VARCHAR(50) DEFAULT 'BEKLIYOR', is_takip INTEGER DEFAULT 0, guncelleme_zamani {_ts}, UNIQUE(oda_id, beklenen_zaman))"),
    ]

    # Tüm listeleri birleştir ve çalıştır
    all_sql_lists = [core_tables, op_tables, map_perf_tables, qdms_tables, sosts_tables]
    for sql_list in all_sql_lists:
        for t_name, t_sql in sql_list:
            try:
                conn.execute(text(t_sql))
            except Exception as e:
                print(f"Table Error ({t_name}): {e}")
    
    # POST-INIT: İndeksler (Performans için)
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_olcum_plani_durum ON olcum_plani (durum)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sicaklik_olcumleri_tarih ON sicaklik_olcumleri (olusturulma_tarihi)"))
    # Aşama 2: Audit Trail İndeksleri (MADDE 31)
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vardiya_degisim_vardiya_id ON vardiya_degisim_loglari(vardiya_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vardiya_degisim_tarihi ON vardiya_degisim_loglari(degisim_tarihi)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vardiya_degisim_alan ON vardiya_degisim_loglari(alan_adi)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gunluk_gorev_degisim_gorev_id ON gunluk_gorev_degisim_loglari(gorev_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gunluk_gorev_degisim_tarihi ON gunluk_gorev_degisim_loglari(degisim_tarihi)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_map_vardiya_degisim_id ON map_vardiya_degisim_loglari(map_vardiya_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_map_vardiya_degisim_tarihi ON map_vardiya_degisim_loglari(degisim_tarihi)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kpi_degisim_kpi_id ON urun_kpi_degisim_loglari(kpi_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_hijyen_degisim_kontrol_id ON hijyen_kontrol_degisim_loglari(kontrol_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gmp_degisim_denetim_id ON gmp_denetim_degisim_loglari(denetim_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gmp_degisim_tarihi ON gmp_denetim_degisim_loglari(degisim_tarihi)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_temizlik_degisim_kayit_id ON temizlik_kayitlari_degisim_loglari(temizlik_kaydı_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_temizlik_degisim_tarihi ON temizlik_kayitlari_degisim_loglari(degisim_tarihi)"))

    # 6. Güvenlik Sıkılaştırması (Supabase RLS)
    _apply_rls_hardening(conn)

def _apply_rls_hardening(conn):
    """PostgreSQL için tüm public tablolarında RLS'yi aktif eder."""
    try:
        # v6.2.3: Set a short lock timeout to avoid hanging the entire app if a table is locked
        conn.execute(text("SET LOCAL lock_timeout = '2s'"))
        
        # v6.1.2: Idempotent RLS activation
        sql_list = text("""
            SELECT c.relname 
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' 
              AND c.relkind = 'r' 
              AND c.relrowsecurity = False
        """)
        tables = conn.execute(sql_list).fetchall()
        
        for r in tables:
            t_name = r[0]
            try:
                # v5.5.0: Enable RLS. 
                # v6.2.3: Wrap in a nested try/except to continue even if one table fails
                conn.execute(text(f'ALTER TABLE "{t_name}" ENABLE ROW LEVEL SECURITY'))
                print(f"RLS Enabled: {t_name}")
            except Exception as te:
                # Logging timeout as a warning, but continuing boot
                if "timeout" in str(te).lower():
                    print(f"RLS Timeout Warning ({t_name}): Table locked, skipping RLS for now.")
                else:
                    print(f"RLS Enable Error ({t_name}): {te}")
    except Exception as e:
        print(f"RLS Hardening Global Error: {e}")

def init_performans_tables(conn):
    """Performans ve Polivalans tablolarını kurar.
    v9.0: _apply_rls_hardening duplicate çağrısı kaldırıldı (init_all_tables zaten çağırıyor).
    """
    _pk = "SERIAL PRIMARY KEY"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS performans_degerledirme (
            id {_pk}, uuid TEXT UNIQUE NOT NULL, personel_id INTEGER, calisan_adi_soyadi TEXT NOT NULL, bolum TEXT NOT NULL, gorevi TEXT NOT NULL, ise_giris_tarihi DATE,
            donem TEXT NOT NULL, degerlendirme_tarihi DATE NOT NULL, degerlendirme_yili INTEGER NOT NULL, agirlikli_toplam_puan REAL NOT NULL, polivalans_duzeyi TEXT NOT NULL, polivalans_kodu INTEGER NOT NULL,
            olusturma_tarihi {_ts}, guncelleyen_kullanici TEXT, surum INTEGER DEFAULT 1, silinmis INTEGER DEFAULT 0
        )
    """))

    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS polivalans_matris (
            id {_pk}, personel_id INTEGER, calisan_adi TEXT NOT NULL, bolum TEXT NOT NULL, gorevi TEXT NOT NULL, guncelleme_yili INTEGER NOT NULL,
            yil_ortalama REAL, polivalans_kodu INTEGER, polivalans_metni TEXT, olusturma_tarihi {_ts}
        )
    """))
    # NOT: _apply_rls_hardening() burada KASTEN çağrılmıyor.
    # init_all_tables() zaten çağırıyor. Duplicate = ~35 ekstra round trip.
