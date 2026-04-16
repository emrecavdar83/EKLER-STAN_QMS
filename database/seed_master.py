from sqlalchemy import text
import streamlit as st

def bootstrap_all(conn, is_pg):
    """Tüm başlangıç verilerini koordine eder."""
    _ensure_admin_account(conn, is_pg)
    _bootstrap_modules(conn)
    _bootstrap_qms_departments(conn, is_pg)
    _bootstrap_map_parameters(conn, is_pg)
    _bootstrap_system_constants(conn, is_pg)
    _bootstrap_core_products(conn, is_pg)
    _cleanup_old_logs(conn, is_pg)

def _ensure_admin_account(conn, is_pg):
    """Admin ve Saha Mobil hesaplarını garanti eder."""
    table = "public.personel" if is_pg else "personel"
    try:
        res = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE kullanici_adi = 'Admin'")).fetchone()
        if res[0] == 0:
            conn.execute(text(f"INSERT INTO {table} (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye) VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'ADMIN', 'AKTİF', 0)"))
        
        res_mobil = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE kullanici_adi = 'Saha_Mobil'")).fetchone()
        if res_mobil[0] == 0:
            conn.execute(text(f"INSERT INTO {table} (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye) VALUES ('SAHA MOBİL TERMİNAL', 'Saha_Mobil', 'mobil789', 'Personel', 'AKTİF', 5)"))
    except Exception as e:
        print(f"Admin Check Error: {e}")

def _bootstrap_modules(conn):
    """Modül listesini senkronize eder."""
    MODUL_LISTESI = [
        ("uretim_girisi", "🏭 Üretim Girişi", 10, "ops"),
        ("kpi_kontrol", "🍩 KPI & Kalite Kontrol", 20, "ops"),
        ("gmp_denetimi", "🛡️ GMP Denetimi", 30, "ops"),
        ("personel_hijyen", "🧼 Personel Hijyen", 40, "ops"),
        ("temizlik_kontrol", "🧹 Temizlik Kontrol", 50, "ops"),
        ("kurumsal_raporlama", "📊 Kurumsal Raporlama", 60, "mgt"),
        ("soguk_oda", "❄️ Soğuk Oda Sıcaklıkları", 70, "ops"),
        ("map_uretim", "📦 MAP Üretim", 80, "ops"),
        ("gunluk_gorevler", "📋 Günlük Görevler", 85, "ops"),
        ("performans_polivalans", "📈 Yetkinlik & Performans", 90, "mgt"),
        ("personel_vardiya_yonetimi", "📅 Vardiya Yönetimi", 95, "ops"),
        ("qdms", "📁 QDMS", 100, "mgt"),
        ("denetim_izi", "👁️ Denetim İzi", 105, "mgt"),
        ("anayasa", "📜 Proje Anayasası", 108, "sys"),
        ("ayarlar", "⚙️ Ayarlar", 110, "sys")
    ]
    try:
        # v6.1.1: Robust column check (SQLite/PG compatible)
        cols_res = conn.execute(text("PRAGMA table_info(ayarlar_moduller)") if eng_is_sqlite(conn) else text("SELECT column_name FROM information_schema.columns WHERE table_name = 'ayarlar_moduller'"))
        existing_cols = {r[1] if eng_is_sqlite(conn) else r[0] for r in cols_res.fetchall()}
        has_zone = 'zone' in existing_cols
        
        mevcut = {r[0] for r in conn.execute(text("SELECT modul_anahtari FROM ayarlar_moduller")).fetchall()}
        for anahtar, etiket, sira, zone in MODUL_LISTESI:
            if anahtar not in mevcut:
                if has_zone:
                    conn.execute(text("INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, zone, aktif) VALUES (:k, :e, :s, :z, 1)"), {"k": anahtar, "e": etiket, "s": sira, "z": zone})
                else:
                    conn.execute(text("INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES (:k, :e, :s, 1)"), {"k": anahtar, "e": etiket, "s": sira})
            else:
                extra_sql = ", zone = CASE WHEN zone IS NULL OR zone = '' THEN :z ELSE zone END" if has_zone else ""
                conn.execute(text(f"UPDATE ayarlar_moduller SET modul_etiketi = :e, sira_no = :s, aktif = 1 {extra_sql} WHERE modul_anahtari = :k"), {"k": anahtar, "e": etiket, "s": sira, "z": zone})
    except Exception as e:
        print(f"Module Bootstrap Error: {e}")

def eng_is_sqlite(conn):
    """Bağlantının SQLite olup olmadığını kontrol eder."""
    try:
        return 'sqlite' in str(conn.engine.url).lower()
    except:
        return True # Fallback to SQLite assumption

def _bootstrap_qms_departments(conn, is_pg):
    """QMS Departman yapısı başlangıç verileri."""
    try:
        turler = [('GENEL MÜDÜRLÜK', 1), ('DİREKTÖRLÜK', 2), ('DEPARTMAN', 3), ('BRİM', 4), ('ALAN / HAT', 5)]
        for ad, sira in turler:
            sql = "INSERT INTO qms_departman_turleri (tur_adi, sira_no) VALUES (:a, :s)"
            if is_pg: sql += " ON CONFLICT (tur_adi) DO NOTHING"
            else: sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
            conn.execute(text(sql), {"a": ad, "s": sira})
    except Exception: pass

def _bootstrap_map_parameters(conn, is_pg):
    """MAP Duruş ve Fire parametreleri."""
    try:
        duruslar = ["ÜST FİLM DEĞİŞİMİ", "ALT FİLM DEĞİŞİMİ", "MOLA / YEMEK", "ARIZA / BAKIM", "DİĞER"]
        for d in duruslar:
            sql = "INSERT INTO map_durus_nedenleri (neden) VALUES (:d)"
            if is_pg: sql += " ON CONFLICT (neden) DO NOTHING"
            else: sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
            conn.execute(text(sql), {"d": d})
    except Exception: pass

def _cleanup_old_logs(conn, is_pg):
    """Eski logları temizler (v6.0: 30 gün standardı)."""
    try:
        # P0: Sadeleştirme kapsamında 90 günden 30 güne düşürüldü
        if is_pg: stmt = "DELETE FROM sistem_loglari WHERE zaman < CURRENT_TIMESTAMP - INTERVAL '30 days'"
        else: stmt = "DELETE FROM sistem_loglari WHERE zaman < datetime('now', '-30 days')"
        conn.execute(text(stmt))
    except Exception: pass
def _bootstrap_system_constants(conn, is_pg):
    """POSITION_LEVELS ve VARDIYA_LISTESI sabitlerini DB'ye taşır."""
    import json
    constants_to_seed = [
        ('POSITION_LEVELS', {
            "0": {"name": "Yönetim Kurulu", "icon": "🏛️", "color": "#1A5276", "permissions": ["admin", "all_departments", "strategic"]},
            "1": {"name": "Genel Müdür", "icon": "👑", "color": "#2874A6", "permissions": ["admin", "all_departments", "operational"]},
            "2": {"name": "Direktörler", "icon": "📊", "color": "#3498DB", "permissions": ["multi_department", "strategic_operations"]},
            "3": {"name": "Müdürler", "icon": "💼", "color": "#5DADE2", "permissions": ["department_admin", "sub_departments"]},
            "4": {"name": "Koordinatör / Şef", "icon": "🎯", "color": "#85C1E9", "permissions": ["unit_admin", "team_management"]},
            "5": {"name": "Bölüm Sorumlusu", "icon": "⭐", "color": "#A3E4D7", "permissions": ["team_management", "basic_access"]},
            "6": {"name": "Personel", "icon": "👥", "color": "#D4E6F1", "permissions": ["own_records", "basic_access"]},
            "7": {"name": "Stajyer/Geçici", "icon": "📝", "color": "#ECF0F1", "permissions": ["view_only"]}
        }, "Kurumsal pozisyon ve yetki seviyeleri"),
        ('VARDIYA_LISTESI', ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], "Sistem genelinde kullanılan vardiya listesi"),
        ('URUN_KATEGORILERI', ["MAMUL", "YARI MAMUL", "HAMMADDE"], "Ürün tipleri ve kategorileri")
    ]
    
    for key, val, desc in constants_to_seed:
        try:
            val_json = json.dumps(val, ensure_ascii=False)
            sql = "INSERT INTO sistem_parametreleri (anahtar, deger, aciklama) VALUES (:k, :v, :d)"
            if is_pg: sql += " ON CONFLICT (anahtar) DO NOTHING"
            else: sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
            conn.execute(text(sql), {"k": key, "v": val_json, "d": desc})
        except Exception as e:
            print(f"Seed Constant Error ({key}): {e}")

def _bootstrap_core_products(conn, is_pg):
    """v6.1.8: Temel Ekler ürünlerini (33 adet) ve Mamul/Yarı Mamul ayrımını tohumlar."""
    EKLER_LIST = [
        "BITTER ÇIKOLATALI EKLER", "LOTUS EKLER", "KLASİK EKLER", "ANTEP FISTIKLI EKLER",
        "TİREMİSU EKLER", "FINDIKLI EKLER", "KİTKAT EKLER", "FRAMBUAZLI EKLER",
        "BEYAZ ÇIKOLATALI EKLER", "KARAMELLİ EKLER", "BADEMLİ EKLER", "AMBER EKLER",
        "VİŞNE EKLER", "YABAN MERSİNİ-LİMON KARMA EKLER", "ÇİLEK-BÖĞÜRTLEN KARMA EKLER",
        "MUZ-MOCHA KARMA EKLER", "KARADUT-PORTAKAL KARMA EKLER", "VİŞNE-HİNDİSTAN CEVİZİ KARMA EKLER",
        "ANANAS-KESTANE KARMA EKLER", "ELMA-İNCİR KARMA EKLER", "BÖĞÜRTLEN EKLER",
        "ÇİLEK EKLER", "BALKABAĞI-TAHİN EKLER", "YABAN MERSİNİ EKLER", "MUZ EKLER",
        "HİNDİSTAN CEVİZİ EKLER", "PORTAKAL EKLER", "MOCHA EKLER", "İNCİR-CEVİZ EKLER",
        "KESTANE EKLER", "KARADUT EKLER", "ANANAS EKLER", "ELMA-TARÇIN EKLER"
    ]
    try:
        # Varsayılan departman bul (Üretim içeren ilk birim)
        res_dept = conn.execute(text("SELECT ad FROM qms_departmanlar WHERE ad LIKE '%ÜRETİM%' OR ad LIKE '%PASTANE%' LIMIT 1")).fetchone()
        default_dept = res_dept[0] if res_dept else "GIDA ÜRETİM"
        
        for urun in EKLER_LIST:
            try:
                sql = """
                    INSERT INTO ayarlar_urunler (urun_adi, urun_tipi, sorumlu_departman, raf_omru_gun, numune_sayisi, versiyon_no, guncelleme_ts)
                    VALUES (:u, 'MAMUL', :d, 3, 3, 1, CURRENT_TIMESTAMP)
                """
                if is_pg: 
                    sql += " ON CONFLICT (urun_adi) DO UPDATE SET urun_tipi = EXCLUDED.urun_tipi, sorumlu_departman = EXCLUDED.sorumlu_departman"
                else: 
                    # SQLite ON CONFLICT fallback
                    sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
                
                conn.execute(text(sql), {"u": urun, "d": default_dept})
            except Exception as ue:
                # v6.2.3: Log individual product error but don't stop the seed
                if "constraint" in str(ue).lower() or "unique" in str(ue).lower():
                    continue # Already exists or constraint issue, skip
                print(f"Product Seed Error ({urun}): {ue}")
    except Exception as e:
        print(f"Core Product Seeding Global Error: {e}")
