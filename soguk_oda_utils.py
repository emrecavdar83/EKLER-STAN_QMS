# SOSTS Modul - V: 2026-02-24-1530-Atomic
# EKLERISTAN QMS - SOSTS Modülü - Yardımcı Fonksiyonlar

import streamlit as st
import qrcode
import uuid
import io
import os
import zipfile
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 0. TABLO YÖNETİMİ (EVRENSEL ŞEMA)
# -----------------------------------------------------------------------------

def init_sosts_tables(engine):
    """Bulut veya Yerel veritabanında eksik tabloları ve sütunları evrensel SQL ile oluşturur/günceller."""
    is_sqlite = engine.dialect.name == 'sqlite'
    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
    
    with engine.begin() as conn:
        # TABLO 1: soguk_odalar
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS soguk_odalar (
            id {id_type},
            oda_kodu VARCHAR(50) UNIQUE NOT NULL,
            oda_adi VARCHAR(100) NOT NULL,
            departman VARCHAR(100),
            min_sicaklik DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            max_sicaklik DOUBLE PRECISION NOT NULL DEFAULT 4.0,
            sapma_takip_dakika INTEGER NOT NULL DEFAULT 30,
            olcum_sikligi INTEGER NOT NULL DEFAULT 2,
            qr_token VARCHAR(100) UNIQUE,
            qr_uretim_tarihi TIMESTAMP,
            aktif INTEGER DEFAULT 1,
            olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # MIGRATION: olcum_sikligi sütunu kontrolü (Eski sürümler için)
        try:
            conn.execute(text("SELECT olcum_sikligi FROM soguk_odalar LIMIT 1"))
        except Exception:
            # Sütun yoksa ekle (Postgres / SQLite uyumlu basitleştirilmiş ALTER)
            try:
                conn.execute(text("ALTER TABLE soguk_odalar ADD COLUMN olcum_sikligi INTEGER DEFAULT 2"))
            except Exception as e:
                print(f"Migration error (olcum_sikligi): {e}")

        # TABLO 2: sicaklik_olcumleri
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS sicaklik_olcumleri (
            id {id_type},
            oda_id INTEGER NOT NULL,
            sicaklik_degeri DOUBLE PRECISION NOT NULL,
            olcum_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            planlanan_zaman TIMESTAMP,
            qr_ile_girildi INTEGER DEFAULT 1,
            kaydeden_kullanici VARCHAR(100),
            sapma_var_mi INTEGER DEFAULT 0,
            sapma_aciklamasi TEXT,
            olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # TABLO 3: olcum_plani
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS olcum_plani (
            id {id_type},
            oda_id INTEGER NOT NULL,
            beklenen_zaman TIMESTAMP NOT NULL,
            gerceklesen_olcum_id INTEGER,
            durum VARCHAR(50) DEFAULT 'BEKLIYOR',
            guncelleme_zamani TIMESTAMP,
            UNIQUE(oda_id, beklenen_zaman)
        )
        """))

        # TABLO 4: sistem_parametreleri (Zero Hardcode - Madde 1)
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS sistem_parametreleri (
            anahtar VARCHAR(100) PRIMARY KEY,
            deger VARCHAR(255) NOT NULL,
            aciklama TEXT,
            guncelleme_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        # Default Değerler (Eğer yoksa)
        conn.execute(text("""
            INSERT INTO sistem_parametreleri (anahtar, deger, aciklama)
            VALUES ('sosts_bakim_periyodu_sn', '3600', 'SOSTS rutin bakım periyodu (saniye)')
            ON CONFLICT (anahtar) DO NOTHING
        """))

        # PERFORMANS ENDEKSLERİ: Hızlı sorgulama için
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_olcum_plani_durum ON olcum_plani (durum)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sicaklik_olcumleri_tarih ON sicaklik_olcumleri (olusturulma_tarihi)"))

# -----------------------------------------------------------------------------
# 1. QR YÖNETİMİ
# -----------------------------------------------------------------------------

def qr_uret(engine, oda_id):
    """UUID token tabanlı QR üretir. SQLAlchemy motorunu kullanır."""
    with engine.begin() as conn:
        # Oda bilgisini çek
        res = conn.execute(text("SELECT oda_adi, oda_kodu, qr_token FROM soguk_odalar WHERE id = :oid"), {"oid": oda_id}).fetchone()
        
        if not res:
            return None
            
        token = res[2] # qr_token
        # Eğer token yoksa üret ve DB'ye işle
        if not token:
            token = str(uuid.uuid4())
            conn.execute(text("UPDATE soguk_odalar SET qr_token = :t, qr_uretim_tarihi = :d WHERE id = :oid"), 
                         {"t": token, "d": datetime.now(), "oid": oda_id})
            
        base_url = "https://ekler-stan-qms.streamlit.app" # Cloud linki
        qr_content = f"{base_url}/?scanned_qr={token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        width, height = qr_img.size
        
        # Metin çizimi
        dummy_img = Image.new('RGB', (1, 1), 'white')
        draw = ImageDraw.Draw(dummy_img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            
        text_str = f"{res[0]} ({res[1]})"
        left, top, right, bottom = draw.textbbox((0, 0), text_str, font=font)
        text_w, text_h = right - left, bottom - top

        final_width = max(width, text_w + 40)
        final_height = height + 80

        new_img = Image.new('RGB', (final_width, final_height), 'white')
        qr_x = (final_width - width) // 2
        new_img.paste(qr_img, (qr_x, 0))
        
        draw = ImageDraw.Draw(new_img)
        text_x = (final_width - text_w) // 2
        draw.text((text_x, height + 15), text_str, fill="black", font=font)
        
        img_byte_arr = io.BytesIO()
        new_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

def qr_toplu_yazdir(engine, oda_id_listesi):
    """Seçilen odaların QR kodlarını bir ZIP arşivinde toplar."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for oda_id in oda_id_listesi:
            img_data = qr_uret(engine, oda_id)
            if img_data:
                with engine.connect() as conn:
                    code = conn.execute(text("SELECT oda_kodu FROM soguk_odalar WHERE id = :id"), {"id": oda_id}).scalar()
                    zip_file.writestr(f"QR_{code}.png", img_data.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

# -----------------------------------------------------------------------------
# 2. ZAMANLAMA VE PLANLAMA
# -----------------------------------------------------------------------------

def plan_uret(engine, gun_sayisi=7):
    """
    Aktif odalar için ölçüm planı (slotları) üretir.
    ATOMIC INSERT: ON CONFLICT yapısı ile transaction zehirlenmesi önlenir.
    """
    with engine.begin() as conn:
        odalar = conn.execute(text("SELECT id, olcum_sikligi FROM soguk_odalar WHERE aktif = 1")).fetchall()
        
        # PERFORMANS: Sadece gelecek 2 gün için plan üret (7 gün çok fazlaydı)
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        gun_sayisi = 2 
        
        # Hazırlık: Eklenecek verileri bir listede topla (Bulk Insert)
        insert_data = []
        for oda in odalar:
            oda_id = oda[0]
            siklik = oda[1] or 2 # olcum_sikligi
            for d in range(gun_sayisi):
                current_day = start_date + timedelta(days=d)
                # Saat aralığı: 06:00 - 23:00
                for h in range(6, 24, siklik):
                    beklenen_zaman = current_day.replace(hour=h)
                    insert_data.append({
                        "oid": oda_id, 
                        "t": beklenen_zaman
                    })
        
        if insert_data:
            # SQL Yapısı: ON CONFLICT yapısı ile mükerrer kayıtlar atlanır
            sql = text("""
                INSERT INTO olcum_plani (oda_id, beklenen_zaman, durum)
                VALUES (:oid, :t, 'BEKLIYOR')
                ON CONFLICT (oda_id, beklenen_zaman) DO NOTHING
            """)
            conn.execute(sql, insert_data) # SQLAlchemy toplu veriyi otomatik bulk yapar

def kontrol_geciken_olcumler(engine):
    """Zamanı geçen slotları GECIKTI'ye çeker. (Son 48 saate kısıtlı - Performans)"""
    with engine.begin() as conn:
        now = datetime.now()
        yesterday = now - timedelta(hours=48)
        conn.execute(text("""
            UPDATE olcum_plani 
            SET durum = 'GECIKTI', guncelleme_zamani = :n 
            WHERE durum = 'BEKLIYOR' AND beklenen_zaman < :n
            AND beklenen_zaman > :y
        """), {"n": now, "y": yesterday})

# -----------------------------------------------------------------------------
# 3. VERİ ERİŞİM (CRUD)
# -----------------------------------------------------------------------------

def kaydet_olcum(engine, oda_id, sicaklik, kullanici, plan_id=None, qr_mi=1, takip_suresi=None):
    """Sıcaklık ölçümünü kaydeder."""
    with engine.begin() as conn:
        # Limitler
        limit = conn.execute(text("SELECT min_sicaklik, max_sicaklik FROM soguk_odalar WHERE id = :oid"), {"oid": oda_id}).fetchone()
        
        sapma = 0
        if limit and (sicaklik < limit[0] or sicaklik > limit[1]):
            sapma = 1
            
        # 1. Kaydet
        conn.execute(text("""
            INSERT INTO sicaklik_olcumleri (oda_id, sicaklik_degeri, kaydeden_kullanici, sapma_var_mi, qr_ile_girildi, planlanan_zaman)
            VALUES (:oid, :v, :k, :s, :qr, :t)
        """), {"oid": oda_id, "v": sicaklik, "k": kullanici, "s": sapma, "qr": qr_mi, "t": datetime.now()})
        
        # Son ID alma (PostgreSQL ve SQLite uyumlu method)
        olcum_id = conn.execute(text("SELECT MAX(id) FROM sicaklik_olcumleri")).scalar()
        
        # 2. Planı Güncelle
        if plan_id:
            conn.execute(text("""
                UPDATE olcum_plani 
                SET gerceklesen_olcum_id = :oid, durum = 'TAMAMLANDI', guncelleme_zamani = :t
                WHERE id = :pid
            """), {"oid": olcum_id, "t": datetime.now(), "pid": plan_id})
        
        # 3. Otomatik Takip Görevi
        if sapma and takip_suresi:
            yeni_zaman = datetime.now() + timedelta(minutes=takip_suresi)
            conn.execute(text("""
                INSERT INTO olcum_plani (oda_id, beklenen_zaman, durum) 
                VALUES (:oid, :t, 'BEKLIYOR')
            """), {"oid": oda_id, "t": yeni_zaman})
            
        return sapma

@st.cache_data(ttl=300) # 5 dakika önbellek
def get_overdue_summary(engine_url):
    """Gecikmiş ölçümlerin özetini döner."""
    from sqlalchemy import create_engine
    engine = create_engine(engine_url)
    try:
        query = """
            SELECT o.oda_adi, COUNT(p.id) as gecikme_sayisi
            FROM olcum_plani p
            JOIN soguk_odalar o ON p.oda_id = o.id
            WHERE p.durum = 'GECIKTI'
            GROUP BY o.oda_adi
        """
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            return df
    except Exception as e:
        print(f"Error in get_overdue_summary: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60) # 1 dakika cache
def get_matrix_data(engine_url, sel_date):
    """Günlük ölçüm matrisi verisini çeker. Planlı ve plansız tüm ölçümleri kapsar."""
    from sqlalchemy import create_engine
    engine = create_engine(engine_url)
    start_dt = datetime.combine(sel_date, datetime.min.time())
    end_dt = datetime.combine(sel_date, datetime.max.time())
    
    # Hem planlı hem de manuel girişleri getiren hibrit sorgu
    query = """
    SELECT 
        o.oda_adi, 
        COALESCE(p.beklenen_zaman, m.olcum_zamani) as zaman, 
        COALESCE(p.durum, 'MANUEL') as durum, 
        m.sicaklik_degeri
    FROM sicaklik_olcumleri m
    JOIN soguk_odalar o ON m.oda_id = o.id
    LEFT JOIN olcum_plani p ON m.id = p.gerceklesen_olcum_id
    WHERE m.olcum_zamani BETWEEN :s AND :e
    
    UNION ALL
    
    SELECT 
        o.oda_adi, 
        p.beklenen_zaman as zaman, 
        p.durum, 
        NULL as sicaklik_degeri
    FROM olcum_plani p
    JOIN soguk_odalar o ON p.oda_id = o.id
    WHERE p.beklenen_zaman BETWEEN :s AND :e 
    AND p.gerceklesen_olcum_id IS NULL
    
    ORDER BY oda_adi, zaman
    """
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params={"s": start_dt, "e": end_dt})
    except Exception as e:
        print(f"Error in get_matrix_data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300) # 5 dakika trend cache
def get_trend_data(engine_url, oda_id):
    """Oda trend verisini çeker (Cache'li)."""
    from sqlalchemy import create_engine
    engine = create_engine(engine_url)
    # Son 30 günlük veriyi çek veya limit ekle (Performans)
    query = """
        SELECT m.olcum_zamani, m.sicaklik_degeri, m.sapma_var_mi, o.min_sicaklik, o.max_sicaklik
        FROM sicaklik_olcumleri m JOIN soguk_odalar o ON m.oda_id = o.id
        WHERE m.oda_id = :t 
        AND m.olcum_zamani >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY m.olcum_zamani ASC
    """
    # SQLite desteği için (Lokal testlerde hata vermemesi için)
    if 'sqlite' in str(engine.url):
        query = query.replace("m.olcum_zamani >= CURRENT_DATE - INTERVAL '30 days'", "m.olcum_zamani >= date('now', '-30 days')")

    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params={"t": oda_id})
    except Exception:
        return pd.DataFrame()
