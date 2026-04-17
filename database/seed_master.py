from sqlalchemy import text
import streamlit as st

def bootstrap_all(conn):
    """Tüm başlangıç verilerini koordine eder."""
    _ensure_admin_account(conn)
    _bootstrap_modules(conn)
    _ensure_admin_permissions(conn)
    _bootstrap_qms_departments(conn)
    _bootstrap_map_parameters(conn)
    _bootstrap_system_constants(conn)
    _bootstrap_core_products(conn)
    _cleanup_old_logs(conn)

def _ensure_admin_account(conn):
    """Admin ve Saha Mobil hesaplarını garanti eder."""
    table = "ayarlar_kullanicilar"
    try:
        res = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE kullanici_adi = 'Admin'")).fetchone()
        if res[0] == 0:
            conn.execute(text(f"INSERT INTO {table} (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye) VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'ADMIN', 'AKTİF', 0)"))
        
        res_mobil = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE kullanici_adi = 'Saha_Mobil'")).fetchone()
        if res_mobil[0] == 0:
            conn.execute(text(f"INSERT INTO {table} (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye) VALUES ('SAHA MOBİL TERMİNAL', 'Saha_Mobil', 'mobil789', 'Personel', 'AKTİF', 5)"))
    except Exception as e:
        print(f"Admin Check Error: {e}")

def _ensure_admin_permissions(conn):
    """v6.8.0: ADMIN rolünün her modüle erişimini garanti altına alır (Anayasa Madde 28 Uyum)."""
    try:
        # Mevcut tüm modül anahtarlarını çek
        res = conn.execute(text("SELECT modul_anahtari FROM ayarlar_moduller WHERE aktif = 1")).fetchall()
        for row in res:
            m_key = row[0]
            # ADMIN için 'Düzenle' yetkisi ekle veya güncelle
            sql = """
                INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu, sadece_kendi_bolumu)
                VALUES ('ADMIN', :m, 'Düzenle', 0)
                ON CONFLICT (rol_adi, modul_adi) DO UPDATE SET erisim_turu = 'Düzenle'
            """
            # Not: ON CONFLICT için tablonun UNIQUE (rol_adi, modul_adi) kısıtına sahip olması gerekir.
            # Yoksa manuel kontrol yapalım.
            try:
                conn.execute(text(sql), {"m": m_key})
            except Exception:
                # Fallback: Klasik yöntem
                count = conn.execute(text("SELECT COUNT(*) FROM ayarlar_yetkiler WHERE rol_adi = 'ADMIN' AND modul_adi = :m"), {"m": m_key}).fetchone()[0]
                if count == 0:
                    conn.execute(text("INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES ('ADMIN', :m, 'Düzenle')"), {"m": m_key})
                else:
                    conn.execute(text("UPDATE ayarlar_yetkiler SET erisim_turu = 'Düzenle' WHERE rol_adi = 'ADMIN' AND modul_adi = :m"), {"m": m_key})
    except Exception as e:
        print(f"Admin Permission Bootstrap Error: {e}")

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
        # v6.1.1: Standard column names for PostgreSQL
        cols_res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'ayarlar_moduller'"))
        existing_cols = {r[0] for r in cols_res.fetchall()}
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


def _bootstrap_qms_departments(conn):
    """QMS Departman yapısı başlangıç verileri."""
    try:
        turler = [('GENEL MÜDÜRLÜK', 1), ('DİREKTÖRLÜK', 2), ('DEPARTMAN', 3), ('BRİM', 4), ('ALAN / HAT', 5)]
        for ad, sira in turler:
            sql = "INSERT INTO qms_departman_turleri (tur_adi, sira_no) VALUES (:a, :s) ON CONFLICT (tur_adi) DO NOTHING"
            conn.execute(text(sql), {"a": ad, "s": sira})
    except Exception: pass

def _bootstrap_map_parameters(conn):
    """MAP Duruş ve Fire parametreleri."""
    try:
        duruslar = ["ÜST FİLM DEĞİŞİMİ", "ALT FİLM DEĞİŞİMİ", "MOLA / YEMEK", "ARIZA / BAKIM", "DİĞER"]
        for d in duruslar:
            sql = "INSERT INTO map_durus_nedenleri (neden) VALUES (:d) ON CONFLICT (neden) DO NOTHING"
            conn.execute(text(sql), {"d": d})
    except Exception: pass

def _cleanup_old_logs(conn):
    """Eski logları temizler (v6.0: 30 gün standardı)."""
    try:
        stmt = "DELETE FROM sistem_loglari WHERE zaman < CURRENT_TIMESTAMP - INTERVAL '30 days'"
        conn.execute(text(stmt))
    except Exception: pass
def _bootstrap_system_constants(conn):
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
            sql = "INSERT INTO sistem_parametreleri (anahtar, deger, aciklama) VALUES (:k, :v, :d) ON CONFLICT (anahtar) DO NOTHING"
            conn.execute(text(sql), {"k": key, "v": val_json, "d": desc})
        except Exception as e:
            print(f"Seed Constant Error ({key}): {e}")

def _bootstrap_core_products(conn):
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
        # v6.3.2: Zırhlı Koruma - Departman atamasını sadece boşsa yap
        for urun in EKLER_LIST:
            try:
                # Ürün bazlı departman ataması (Personel tablosuna dokunmaz)
                sql = """
                    INSERT INTO ayarlar_urunler (urun_adi, urun_tipi, sorumlu_departman, raf_omru_gun, numune_sayisi, versiyon_no, guncelleme_ts)
                    VALUES (:u, 'MAMUL', 'KALİTE', 3, 3, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT (urun_adi) DO UPDATE SET urun_tipi = EXCLUDED.urun_tipi, sorumlu_departman = EXCLUDED.sorumlu_departman
                """
                conn.execute(text(sql), {"u": urun})
            except Exception as ue:
                # v6.2.3: Log individual product error but don't stop the seed
                if "constraint" in str(ue).lower() or "unique" in str(ue).lower():
                    continue # Already exists or constraint issue, skip
                print(f"Product Seed Error ({urun}): {ue}")
    except Exception as e:
        print(f"Core Product Seeding Global Error: {e}")
