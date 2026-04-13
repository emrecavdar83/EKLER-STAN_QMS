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
    ensure_column("soguk_odalar", "ozel_olcum_saatleri", "TEXT")
    
    # SQLite fix: CURRENT_TIMESTAMP default can't be added via ALTER
    # We add it without default if it fails, then manually update if needed
    col_def = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if not is_sqlite else "TIMESTAMP"
    ensure_column("soguk_odalar", "guncelleme_tarihi", col_def)
    
    ensure_column("soguk_odalar", "sorumlu_personel", "VARCHAR(255)")
    ensure_column("soguk_odalar", "durum", "VARCHAR(50) DEFAULT 'AKTİF'")
    ensure_column("sicaklik_olcumleri", "is_takip", "INTEGER DEFAULT 0")

    # v6.5.2: durum tutarsızlığı migrasyonu — AKTIF → AKTİF (Türkçe İ düzeltmesi)
    try:
        with engine.begin() as conn:
            conn.execute(text("UPDATE soguk_odalar SET durum = 'AKTİF' WHERE durum = 'AKTIF' OR durum = 'Aktif'"))
    except Exception as e:
        print(f"SOSTS durum migration warning: {e}")
    ensure_column("olcum_plani", "is_takip", "INTEGER DEFAULT 0")
    ensure_column("olcum_plani", "guncelleme_zamani", "TIMESTAMP")

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
            ozel_olcum_saatleri TEXT,
            sorumlu_personel VARCHAR(255),
            durum VARCHAR(50) DEFAULT 'AKTİF',
            guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        # TABLO 1.5: soguk_oda_planlama_kurallari (Ultra-Dinamik)
        conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS soguk_oda_planlama_kurallari (
            id {id_type},
            oda_id INTEGER NOT NULL,
            kural_adi VARCHAR(100),
            baslangic_saati INTEGER NOT NULL,
            bitis_saati INTEGER NOT NULL,
            siklik INTEGER NOT NULL,
            kural_durumu VARCHAR(20) DEFAULT 'Ölçüm',
            aciklama_dof_no TEXT,
            aktif INTEGER DEFAULT 1,
            guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (oda_id) REFERENCES soguk_odalar(id)
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

        conn.execute(text("""
            INSERT INTO sistem_parametreleri (anahtar, deger, aciklama)
            VALUES ('sosts_plan_baslangic_saati', '7', 'SOSTS planlama başlangıç saati (0-23)')
            ON CONFLICT (anahtar) DO NOTHING
        """))

        conn.execute(text("""
            INSERT INTO sistem_parametreleri (anahtar, deger, aciklama)
            VALUES ('sosts_plan_saat_araligi', '24', 'SOSTS planlama kapsam aralığı (saat)')
            ON CONFLICT (anahtar) DO NOTHING
        """))

        # PERFORMANS ENDEKSLERİ: Hızlı sorgulama için
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_olcum_plani_durum ON olcum_plani (durum)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sicaklik_olcumleri_tarih ON sicaklik_olcumleri (olusturulma_tarihi)"))

@st.cache_data(ttl=600)
def get_sosts_param(_engine, key, default="3600"):
    """Sistem parametrelerini cache üzerinden döner (Performans)."""
    try:
        with _engine.connect() as conn:
            res = conn.execute(text("SELECT deger FROM sistem_parametreleri WHERE anahtar = :k"), {"k": key}).fetchone()
            return res[0] if res else default
    except Exception:
        return default

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
            except Exception:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except Exception:
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
            WHERE oda_id NOT IN (SELECT id FROM soguk_odalar WHERE durum = 'AKTİF')
            AND gerceklesen_olcum_id IS NULL 
            AND durum = 'BEKLIYOR'
        """))

        sql = text("SELECT id, oda_adi, olcum_sikligi, ozel_olcum_saatleri, durum FROM soguk_odalar WHERE durum = 'AKTİF'")
        odalar = conn.execute(sql).fetchall()
        
        # 1.6 KURALLARI ÇEK (Madde 1: Ultra-Dinamik)
        kurallar_df = pd.DataFrame()
        try:
            k_res = conn.execute(text("SELECT * FROM soguk_oda_planlama_kurallari WHERE durum = 'AKTİF'"))
            kurallar_df = pd.DataFrame([dict(r._mapping) for r in k_res.fetchall()])
        except Exception: pass
        
        simdi = _now()
        start_date = simdi.replace(hour=0, minute=0, second=0)

        # Madde 1: Dinamik Parametreler
        baslangic = int(get_sosts_param(engine, 'sosts_plan_baslangic_saati', '7'))
        aralik = int(get_sosts_param(engine, 'sosts_plan_saat_araligi', '24'))
        
        for oda in odalar:
            oda_id = oda.id
            oda_adi = oda.oda_adi
            siklik = int(oda.olcum_sikligi or 2)
            ozel_olcum_saatleri = oda.ozel_olcum_saatleri
            durum = getattr(oda, 'durum', 'AKTIF')

            # 13. ADAM: Eğer oda Arızalı veya Kullanım Dışı ise plan üretmeyi durdur
            if durum and str(durum).upper() != 'AKTIF':
                # Sadece gelecekteki bekleyenleri sil ki plan temizlensin
                conn.execute(text("DELETE FROM olcum_plani WHERE oda_id = :oid AND durum = 'BEKLIYOR' AND beklenen_zaman > :n"), {"oid": oda_id, "n": simdi})
                continue
            # TEXT: "07,15,23"

            # 1.5 PERFORMANS: Gelecek 24 saat için zaten slot varsa üretimi atla (Smart Check)
            count_sql = text("SELECT COUNT(*) FROM olcum_plani WHERE oda_id = :oid AND beklenen_zaman > :n")
            future_count = conn.execute(count_sql, {"oid": oda_id, "n": simdi}).scalar()
            
            if future_count >= (24 // int(siklik)):
                # 13. ADAM: Eğer sıklık değişmemişse atla. 
                # Sıklık değişimi kontrolü (check_sql) aşağıda devam ediyor.
                pass
            else:
                # Slot eksik, devam et
                pass

            # Oda özelinde kuralları al
            oda_kurallari = pd.DataFrame()
            if not kurallar_df.empty:
                oda_kurallari = kurallar_df[kurallar_df['oda_id'] == oda_id]

            # 2. DİNAMİK KURAL TESPİTİ VE HASH KONTROLÜ (Garantör Madde)
            # Eğer kurallar değişmişse, slot sayısı aynı kalsa bile planı sıfırla.
            import hashlib
            rules_str = ""
            if not oda_kurallari.empty:
                # Kuralları sıralı bir stringe dökerek hash al
                sorted_rules = oda_kurallari.sort_values(by='id')
                rules_str = "|".join([f"{r.baslangic_saati}-{r.bitis_saati}-{r.siklik}-{r.kural_durumu}" for _, r in sorted_rules.iterrows()])
            
            current_hash = hashlib.md5(rules_str.encode()).hexdigest()
            last_hash = getattr(oda, 'last_rule_hash', None)
            
            sıklık_degismis = False
            if current_hash != last_hash:
                sıklık_degismis = True
                # Hash'i güncelle
                conn.execute(text("UPDATE soguk_odalar SET last_rule_hash = :h WHERE id = :oid"), {"h": current_hash, "oid": oda_id})

            if not sıklık_degismis:
                # Eğer hash aynıysa, klasik sıklık kontrolü yap (Geriye dönük uyumluluk)
                check_sql = text("""
                    SELECT beklenen_zaman FROM olcum_plani 
                    WHERE oda_id = :oid AND durum = 'BEKLIYOR' AND beklenen_zaman > :n
                    ORDER BY beklenen_zaman ASC LIMIT 2
                """)
                mevcut_slotlar = conn.execute(check_sql, {"oid": oda_id, "n": simdi}).fetchall()
                
                if len(mevcut_slotlar) >= 2:
                    fark = (mevcut_slotlar[1][0] - mevcut_slotlar[0][0]).total_seconds() / 3600
                    if int(fark) != int(siklik):
                        sıklık_degismis = True

            if sıklık_degismis:
                # Sadece gelecekteki ve ölçüm yapılmamış olanları sil! (Garantili Temizlik)
                conn.execute(text("""
                    DELETE FROM olcum_plani 
                    WHERE oda_id = :oid AND durum = 'BEKLIYOR' 
                    AND beklenen_zaman > :n AND gerceklesen_olcum_id IS NULL
                """), {"oid": oda_id, "n": simdi})
                
                # Logla (Madde 3/10)
                try:
                    conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES (:t, :d)"),
                                 {"t": "SOSTS_REGEN_PLAN", "d": f"Oda ID:{oda_id} için kurallar veya sıklık değiştiği için plan güncellendi."})
                except: pass

            # 3. YENİ SLOTLARI ÜRET
            insert_data = []
            
            for d in range(gun_sayisi):
                current_day = start_date + timedelta(days=d)
                
                if not oda_kurallari.empty:
                    # RULE-BASED GENERATION (Ultra-Dinamik)
                    for _, kural in oda_kurallari.iterrows():
                        bas = int(kural['baslangic_saati'])
                        bit = int(kural['bitis_saati'])
                        s_siklik = int(kural['siklik']) or 2
                        durum = kural.get('kural_durumu', 'Ölçüm')
                        # ANAYASA v4: 00:00 Hizalı (Anchored) Slot Üretimi
                        # Slotları 00:00'a göre hizala (Örn: bas=7, siklik=4 -> Ref: 4, 8, 12... 07-08, 08-12, 12-15)
                        current_slot_start = (bas // s_siklik) * s_siklik
                        
                        while True:
                            beklenen_zaman = current_day.replace(hour=current_slot_start % 24, minute=0, second=0)
                            if current_slot_start >= 24:
                                beklenen_zaman += timedelta(days=current_slot_start // 24)
                            
                            bitis_zamani = beklenen_zaman + timedelta(hours=s_siklik)
                            
                            # Kural Sınırlarını Belirle
                            kural_bas_dt = current_day.replace(hour=bas % 24, minute=0, second=0)
                            kural_bit_dt = current_day.replace(hour=bit % 24, minute=0, second=0)
                            if bit <= bas: kural_bit_dt += timedelta(days=1)
                            
                            # Slot kuralın içinde mi? (Kısmi kesişim dahil)
                            if beklenen_zaman < kural_bit_dt and bitis_zamani > kural_bas_dt:
                                # Kırpma (Trimming)
                                effective_start = max(beklenen_zaman, kural_bas_dt)
                                effective_end = min(bitis_zamani, kural_bit_dt)
                                
                                if effective_start > simdi:
                                    s_durum = 'BEKLIYOR'
                                    if durum in ['Bakım', 'Arıza']: s_durum = 'DURDURULDU'
                                    
                                    insert_data.append({
                                        "oid": oda_id, 
                                        "t": effective_start, 
                                        "bt": effective_end,
                                        "st": s_durum
                                    })
                            
                            current_slot_start += s_siklik
                            if beklenen_zaman >= kural_bit_dt: break
                            if len(insert_data) > 200: break # Safety
                elif ozel_olcum_saatleri:
                    # Özel tanımlı saatler varsa (Legacy support)
                    try:
                        saatler = [int(s.strip()) for s in str(ozel_olcum_saatleri).split(",")]
                    except: saatler = []
                    for h in saatler:
                        beklenen_zaman = current_day.replace(hour=h % 24)
                        # Özel saatlerde bitişi +1 saat varsayalım (veya bir sonraki saate kadar)
                        bitis_zamani = beklenen_zaman + timedelta(hours=1) 
                        if beklenen_zaman > simdi:
                            insert_data.append({
                                "oid": oda_id, 
                                "t": beklenen_zaman, 
                                "bt": bitis_zamani,
                                "st": 'BEKLIYOR'
                            })
                else:
                    # Sıklık bazlı saatler (Dinamik Başlangıç ve Aralık - Fallback)
                    for h in range(baslangic, baslangic + aralik, siklik):
                        beklenen_zaman = current_day.replace(hour=h % 24)
                        if h >= 24:
                            beklenen_zaman += timedelta(days=h // 24)
                        
                        bitis_zamani = beklenen_zaman + timedelta(hours=siklik)
                        if beklenen_zaman > simdi:
                            insert_data.append({
                                "oid": oda_id, 
                                "t": beklenen_zaman, 
                                "bt": bitis_zamani,
                                "st": 'BEKLIYOR'
                            })
            
            if insert_data:
                # PERFORMANCE: bulk insert for slot speed
                sql = text("""
                    INSERT INTO olcum_plani (oda_id, beklenen_zaman, bitis_zamani, durum)
                    VALUES (:oid, :t, :bt, :st)
                    ON CONFLICT (oda_id, beklenen_zaman) DO UPDATE SET bitis_zamani = EXCLUDED.bitis_zamani
                """)
                conn.execute(sql, insert_data)
                
            # --- Madde 1: Stability Sync (SyncManager için guncelleme_tarihi zorunluluğu) ---
            conn.execute(text("UPDATE soguk_odalar SET guncelleme_tarihi = :t WHERE id = :oid"), 
                         {"t": _now(), "oid": oda_id})

def kontrol_geciken_olcumler(engine):
    """
    1. Zamanı geçen slotları GECIKTI'ye çeker. (Son 48 saate kısıtlı)
    2. 🧪 AUTO-PRUNE (v3.1.5): 24 saatten eski doldurulmamış gecikmeleri siler (Performans Zırhı)
    """
    with engine.begin() as conn:
        now = _now()
        yesterday = now - timedelta(hours=24)
        forty_eight = now - timedelta(hours=48)
        
        # 1. Gecikme İşaretleme (48 saat kısıtı kaldırıldı - TÜM GEÇMİŞİ KAPSAR)
        conn.execute(text("""
            UPDATE olcum_plani 
            SET durum = 'GECIKTI', guncelleme_zamani = :n 
            WHERE durum = 'BEKLIYOR' AND beklenen_zaman < :n
        """), {"n": now})

        # 2. KRİTİK TEMİZLİK: 24 saati geçmiş ve ölçüm yapılmamış 'GECIKTI' kayıtlarını sil
        # Bu binlerce satırlık şişmeyi ve yavaşlığı kökten çözer.
        conn.execute(text("""
            DELETE FROM olcum_plani 
            WHERE durum = 'GECIKTI' 
            AND beklenen_zaman < :y
            AND gerceklesen_olcum_id IS NULL
        """), {"y": yesterday})

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
    """
    Seçili tarih aralığındaki ölçüm matrisi verisini çeker. (00:00 - 00:00 Sabit Periyot)
    Anayasa Madde 1: Zero Hardcode.
    13. ADAM: PostgreSQL & SQLite Dual Support.
    """
    if bit_tarih is None:
        bit_tarih = bas_tarih
        
    is_pg = 'postgresql' in str(_engine.url)
    
    # 00:00:00 Sınır Değerleri
    s_dt = datetime.combine(bas_tarih, datetime.min.time())
    e_dt = datetime.combine(bit_tarih, datetime.min.time()) + timedelta(days=1)
    
    s_str = s_dt.strftime('%Y-%m-%d %H:%M:%S')
    e_str = e_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # PostgreSQL için cast operatörü, SQLite için standart string karşılaştırması
    ts_cast = "CAST(:s AS TIMESTAMP)" if is_pg else ":s"
    te_cast = "CAST(:e AS TIMESTAMP)" if is_pg else ":e"

    query = f"""
    SELECT 
        o.id as oda_id, o.oda_adi, o.min_sicaklik, o.max_sicaklik, o.sorumlu_personel,
        p.id as plan_id,
        COALESCE(m.olcum_zamani, p.beklenen_zaman) as zaman, 
        p.bitis_zamani,
        COALESCE(p.durum, 'MANUEL') as durum, 
        m.sicaklik_degeri, m.sapma_var_mi, m.sapma_aciklamasi, m.is_takip,
        p.is_takip as plan_is_takip,
        m.kaydeden_kullanici, m.olusturulma_tarihi as kayit_zamani, m.olcum_zamani as kesin_saat
    FROM sicaklik_olcumleri m
    JOIN soguk_odalar o ON m.oda_id = o.id
    LEFT JOIN olcum_plani p ON m.id = p.gerceklesen_olcum_id
    WHERE m.olcum_zamani >= {ts_cast} AND m.olcum_zamani < {te_cast}
    
    UNION ALL
    
    SELECT 
        o.id as oda_id, o.oda_adi, o.min_sicaklik, o.max_sicaklik, o.sorumlu_personel,
        p.id as plan_id,
        p.beklenen_zaman as zaman, p.bitis_zamani,
        p.durum, 
        NULL as sicaklik_degeri, NULL as sapma_var_mi, NULL as sapma_aciklamasi, NULL as is_takip,
        p.is_takip as plan_is_takip,
        NULL as kaydeden_kullanici, NULL as kayit_zamani, NULL as kesin_saat
    FROM olcum_plani p
    JOIN soguk_odalar o ON p.oda_id = o.id
    WHERE p.beklenen_zaman >= {ts_cast} AND p.beklenen_zaman < {te_cast}
    AND p.gerceklesen_olcum_id IS NULL
    
    ORDER BY oda_adi, zaman
    """

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
