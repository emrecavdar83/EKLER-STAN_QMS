# SOSTS Modul - V: 2026-03-04-1000-SOZamanRapor
# EKLERISTAN QMS - SOSTS Modülü - Yardımcı Fonksiyonlar

import streamlit as st
import qrcode
import uuid
import io
import os
import zipfile
import pandas as pd
import pytz
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

_TZ_IST = pytz.timezone('Europe/Istanbul')

def _now():
    """Bulut ortamında doğru Türkiye saatini döndürür (UTC+3)."""
    return datetime.now(_TZ_IST).replace(tzinfo=None, microsecond=0)

# -----------------------------------------------------------------------------
# 0. TABLO YÖNETİMİ (EVRENSEL ŞEMA)
# -----------------------------------------------------------------------------

def init_sosts_tables(engine):
    """Bulut veya Yerel veritabanında eksik tabloları ve sütunları evrensel SQL ile oluşturur/günceller."""
    from sqlalchemy import inspect
    is_sqlite = engine.dialect.name == 'sqlite'
    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
    
    # --- 13. ADAM SIFIR RİSK: PostgreSQL Transaction Abort Koruması ---
    # Postgres'te hata alan bir SELECT tüm transaction'ı bozar. Bu yüzden inspect kullanıyoruz.
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Sütun bazlı migrasyonları güvenli yapalım
    def ensure_column(table_name, column_name, column_def):
        if table_name in existing_tables:
            cols = [c['name'] for c in inspector.get_columns(table_name)]
            if column_name not in cols:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
                except Exception as e:
                    print(f"Migration error ({table_name}.{column_name}): {e}")

    ensure_column("soguk_odalar", "olcum_sikligi", "INTEGER DEFAULT 2")
    ensure_column("sicaklik_olcumleri", "is_takip", "INTEGER DEFAULT 0")
    ensure_column("olcum_plani", "is_takip", "INTEGER DEFAULT 0")

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
            is_takip INTEGER DEFAULT 0,
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
            is_takip INTEGER DEFAULT 0,
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
        
        # Metin çizimi - Font Boyutu Hesaplama (QR Genişliğine Uygun Punto)
        text_str = f"{res[0]} ({res[1]})"
        target_w = width # QR kodun genisligi
        
        font_size = 40 # Üst limitsiz büyük başla
        font = None
        while font_size > 10:
            try:
                # Windows için Arial, Linux (Cloud) için DejaVu denemesi
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                    break
            
            # Yazı genişliğini kontrol et
            left, top, right, bottom = ImageDraw.Draw(Image.new('RGB', (1,1))).textbbox((0, 0), text_str, font=font)
            text_w = (right - left)
            if text_w <= target_w:
                break
            font_size -= 1

        # Son hesaplanan genişlik/yükseklik
        left, top, right, bottom = ImageDraw.Draw(Image.new('RGB', (1,1))).textbbox((0, 0), text_str, font=font)
        text_w, text_h = right - left, bottom - top

        final_width = max(width, text_w + 20)
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

def plan_uret(engine, gun_sayisi=2):
    """
    Aktif odalar için ölçüm planı (slotları) üretir.
    Anayasa Madde 6: UPSERT/Atomic.
    13. ADAM: Dinamik Sıklık Kontrolü ve Güvenli Silme.
    """
    with engine.begin() as conn:
        # 1. GÜVENLİK: Artık aktif olmayan odaların planlarını sil (Sadece ölçüm yapılmamış olanlar!)
        conn.execute(text("""
            DELETE FROM olcum_plani 
            WHERE oda_id NOT IN (SELECT id FROM soguk_odalar WHERE aktif = 1)
            AND gerceklesen_olcum_id IS NULL 
            AND durum = 'BEKLIYOR'
        """))

        odalar = conn.execute(text("SELECT id, olcum_sikligi FROM soguk_odalar WHERE aktif = 1")).fetchall()
        
        simdi = _now()
        start_date = simdi.replace(hour=0, minute=0, second=0)
        
        for oda in odalar:
            oda_id = oda[0]
            siklik = oda[1] or 2 

            # 2. DİNAMİK SIKLIK KONTROLÜ (13. Adam Güvenlik Zırhı)
            # Gelecekteki planlanan saat aralıklarını kontrol et. 
            # Eğer mevcut BEKLIYOR slotları güncel 'siklik' değerine uymuyorsa, temizle ve yeniden kur.
            check_sql = text("""
                SELECT beklenen_zaman FROM olcum_plani 
                WHERE oda_id = :oid AND durum = 'BEKLIYOR' AND beklenen_zaman > :n
                ORDER BY beklenen_zaman ASC LIMIT 2
            """)
            mevcut_slotlar = conn.execute(check_sql, {"oid": oda_id, "n": simdi}).fetchall()
            
            sıklık_degismis = False
            if len(mevcut_slotlar) >= 2:
                fark = (mevcut_slotlar[1][0] - mevcut_slotlar[0][0]).total_seconds() / 3600
                if int(fark) != int(siklik):
                    sıklık_degismis = True

            if sıklık_degismis:
                # Sadece gelecekteki ve ölçüm yapılmamış olanları sil! (Çift Kilitleme)
                conn.execute(text("""
                    DELETE FROM olcum_plani 
                    WHERE oda_id = :oid AND durum = 'BEKLIYOR' 
                    AND beklenen_zaman > :n AND gerceklesen_olcum_id IS NULL
                """), {"oid": oda_id, "n": simdi})
                
                # Logla (Madde 3/10)
                try:
                    conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES (:t, :d)"),
                                 {"t": "SOSTS_REGEN_PLAN", "d": f"Oda ID:{oda_id} için sıklık değişimi ({siklik} sa) nedeniyle plan güncellendi."})
                except: pass

            # 3. YENİ SLOTLARI ÜRET
            insert_data = []
            for d in range(gun_sayisi):
                current_day = start_date + timedelta(days=d)
                for h in range(6, 24, siklik):
                    beklenen_zaman = current_day.replace(hour=h)
                    if beklenen_zaman > simdi:
                        insert_data.append({"oid": oda_id, "t": beklenen_zaman})
            
            if insert_data:
                sql = text("""
                    INSERT INTO olcum_plani (oda_id, beklenen_zaman, durum)
                    VALUES (:oid, :t, 'BEKLIYOR')
                    ON CONFLICT (oda_id, beklenen_zaman) DO NOTHING
                """)
                conn.execute(sql, insert_data)

def kontrol_geciken_olcumler(engine):
    """Zamanı geçen slotları GECIKTI'ye çeker. (Son 48 saate kısıtlı - Performans)"""
    with engine.begin() as conn:
        now = _now()
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

def kaydet_olcum(engine, oda_id, sicaklik, kullanici, plan_id=None, qr_mi=1, takip_suresi=None, aciklama=None, is_takip_gorevi=0):
    """Sıcaklık ölçümünü kaydeder."""
    with engine.begin() as conn:
        # Limitler
        limit = conn.execute(text("SELECT min_sicaklik, max_sicaklik FROM soguk_odalar WHERE id = :oid"), {"oid": oda_id}).fetchone()
        
        sapma = 0
        if limit and (sicaklik < limit[0] or sicaklik > limit[1]):
            sapma = 1
            
        # 0. Plan Zamanını Al (Eşleşme için)
        p_zaman = None
        if plan_id:
            p_zaman = conn.execute(text("SELECT beklenen_zaman FROM olcum_plani WHERE id = :pid"), {"pid": plan_id}).scalar()
            
        # 1. Kaydet
        conn.execute(text("""
            INSERT INTO sicaklik_olcumleri (oda_id, sicaklik_degeri, kaydeden_kullanici, sapma_var_mi, sapma_aciklamasi, is_takip, qr_ile_girildi, planlanan_zaman, olcum_zamani, olusturulma_tarihi)
            VALUES (:oid, :v, :k, :s, :ack, :ist, :qr, :t, :oz, :ot)
        """), {"oid": oda_id, "v": sicaklik, "k": kullanici, "s": sapma, "ack": aciklama or "", "ist": is_takip_gorevi, "qr": qr_mi, "t": p_zaman or _now(), "oz": _now(), "ot": _now()})
        
        # Son ID alma (PostgreSQL ve SQLite uyumlu method)
        olcum_id = conn.execute(text("SELECT MAX(id) FROM sicaklik_olcumleri")).scalar()
        
        # 2. Planı Güncelle
        if plan_id:
            conn.execute(text("""
                UPDATE olcum_plani 
                SET gerceklesen_olcum_id = :oid, durum = 'TAMAMLANDI', guncelleme_zamani = :t
                WHERE id = :pid
            """), {"oid": olcum_id, "t": _now(), "pid": plan_id})
        
        # 3. Otomatik Takip Görevi
        if sapma and takip_suresi:
            yeni_zaman = _now() + timedelta(minutes=takip_suresi)
            conn.execute(text("""
                INSERT INTO olcum_plani (oda_id, beklenen_zaman, durum, is_takip) 
                VALUES (:oid, :t, 'BEKLIYOR', 1)
            """), {"oid": oda_id, "t": yeni_zaman})
            
        return sapma

@st.cache_data(ttl=300) # 5 dakika önbellek
def get_overdue_summary(_engine):
    """Gecikmiş ölçümlerin özetini döner."""
    try:
        query = """
            SELECT o.oda_adi, COUNT(p.id) as gecikme_sayisi
            FROM olcum_plani p
            JOIN soguk_odalar o ON p.oda_id = o.id
            WHERE p.durum = 'GECIKTI'
            GROUP BY o.oda_adi
        """
        with _engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            return df
    except Exception as e:
        print(f"Error in get_overdue_summary: {e}")
        return pd.DataFrame()

def get_matrix_data(_engine, bas_tarih, bit_tarih=None):
    """Seçili tarih aralığındaki ölçüm matrisi verisini çeker. Planlı ve plansız tüm ölçümleri kapsar."""
    if bit_tarih is None:
        bit_tarih = bas_tarih
    start_dt = datetime.combine(bas_tarih, datetime.min.time())
    end_dt = datetime.combine(bit_tarih, datetime.max.time())
    
    # En robust (sağlam) tarih filtresi: Range comparison (>= ve <)
    # Bu yöntem hem Postgres hem SQLite için %100 güvenlidir.
    query = """
    SELECT 
        o.id as oda_id,
        o.oda_adi,
        o.min_sicaklik,
        o.max_sicaklik,
        o.sorumlu_personel,
        p.id as plan_id,
        COALESCE(m.olcum_zamani, p.beklenen_zaman) as zaman, 
        COALESCE(p.durum, 'MANUEL') as durum, 
        m.sicaklik_degeri,
        m.sapma_var_mi,
        m.sapma_aciklamasi,
        m.is_takip,
        p.is_takip as plan_is_takip,
        m.kaydeden_kullanici,
        m.olusturulma_tarihi as kayit_zamani,
        m.olcum_zamani as kesin_saat
    FROM sicaklik_olcumleri m
    JOIN soguk_odalar o ON m.oda_id = o.id
    LEFT JOIN olcum_plani p ON m.id = p.gerceklesen_olcum_id
    WHERE m.olcum_zamani >= :s AND m.olcum_zamani < :e
    
    UNION ALL
    
    SELECT 
        o.id as oda_id,
        o.oda_adi, 
        o.min_sicaklik,
        o.max_sicaklik,
        o.sorumlu_personel,
        p.id as plan_id,
        p.beklenen_zaman as zaman, 
        p.durum, 
        NULL as sicaklik_degeri,
        NULL as sapma_var_mi,
        NULL as sapma_aciklamasi,
        NULL as is_takip,
        p.is_takip as plan_is_takip,
        NULL as kaydeden_kullanici,
        NULL as kayit_zamani,
        NULL as kesin_saat
    FROM olcum_plani p
    JOIN soguk_odalar o ON p.oda_id = o.id
    WHERE p.beklenen_zaman >= :s AND p.beklenen_zaman < :e 
    AND p.gerceklesen_olcum_id IS NULL
    
    ORDER BY oda_adi, zaman
    """
    
    # Parametreleri standart string formatına çevir (SQLite ve Postgres tam uyumu için)
    s_dt = datetime.combine(bas_tarih, datetime.min.time())
    e_dt = datetime.combine(bit_tarih, datetime.min.time()) + timedelta(days=1)
    s_str = s_dt.strftime('%Y-%m-%d %H:%M:%S')
    e_str = e_dt.strftime('%Y-%m-%d %H:%M:%S')

    try:
        with _engine.connect() as conn:
            return pd.read_sql(text(query), conn, params={"s": s_str, "e": e_str})
    except Exception as e:
        print(f"Error in get_matrix_data: {e}")
        return pd.DataFrame()

def get_trend_data(_engine, oda_id):
    """Oda trend verisini çeker."""
    
    # Postgres için daha güvenli tarih filtresi
    query = """
        SELECT m.olcum_zamani, m.sicaklik_degeri, m.sapma_var_mi, o.min_sicaklik, o.max_sicaklik
        FROM sicaklik_olcumleri m JOIN soguk_odalar o ON m.oda_id = o.id
        WHERE m.oda_id = :t 
        AND m.olcum_zamani >= (CURRENT_DATE - INTERVAL '30 days')
        ORDER BY m.olcum_zamani ASC
    """
    if 'sqlite' in str(_engine.url):
        query = query.replace("(CURRENT_DATE - INTERVAL '30 days')", "date('now', '-30 days')")

    try:
        with _engine.connect() as conn:
            return pd.read_sql(text(query), conn, params={"t": int(oda_id)})
    except Exception:
        return pd.DataFrame()
