"""map_db.py — MAP Üretim Modülü CRUD Katmanı
Anayasa: Sıfır hardcode, parametreli INSERT/UPDATE, to_sql YASAK.
pd.read_sql KULLANILMAZ — SQLAlchemy 2.x native execute + pd.DataFrame.
MADDE 31: Tüm vardiya değişiklikleri audit trail'e kaydedilir.
"""
import pandas as pd
import streamlit as st
from sqlalchemy import text
from datetime import datetime
import pytz
from logic.cache_manager import CACHE_TTL
from logic.dynamic_sync import log_field_change

_TZ = pytz.timezone("Europe/Istanbul")


# ─── Yardımcı ───────────────────────────────────────────────────────────────
def _now_ts() -> str:
    return datetime.now(_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _sure_dk(baslangic: str, bitis: str):
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        delta = datetime.strptime(bitis, fmt) - datetime.strptime(baslangic, fmt)
        return round(delta.total_seconds() / 60, 2)
    except Exception:
        return None


def _read(conn, sql: str, params: dict = None) -> pd.DataFrame:
    """pd.read_sql KULLANILMAZ. SQLAlchemy 2.x tam uyumlu okuma yöntemi."""
    result = conn.execute(text(sql), params or {})
    rows = result.fetchall()
    cols = list(result.keys())
    return pd.DataFrame(rows, columns=cols)


# ─── Vardiya ─────────────────────────────────────────────────────────────────
def get_aktif_vardiya(engine, makina_no=None) -> dict | None:
    """Belirli bir makine için açık olan vardiyayı döndürür. makina_no None ise en son açılanı döner."""
    bugun = datetime.now(_TZ).strftime("%Y-%m-%d")
    columns = "id, tarih, makina_no, vardiya_no, operator_adi, durum, baslangic_saati, vardiya_sefi, besleme_kisi, kasalama_kisi, hedef_hiz_paket_dk, gerceklesen_uretim, notlar"
    if makina_no:
        sql = f"SELECT {columns} FROM map_vardiya WHERE durum='ACIK' AND tarih=:bugun AND makina_no=:m ORDER BY id DESC LIMIT 1"
        params = {"m": makina_no, "bugun": bugun}
    else:
        sql = f"SELECT {columns} FROM map_vardiya WHERE durum='ACIK' AND tarih=:bugun ORDER BY id DESC LIMIT 1"
        params = {"bugun": bugun}
        
    with engine.connect() as conn:
        df = _read(conn, sql, params)
    return df.iloc[0].to_dict() if not df.empty else None


@st.cache_data(ttl=CACHE_TTL['critical']) # v4.0.2: Navigasyon hızlandırma (Standart: Critical)
def get_bugunku_vardiyalar(_engine) -> pd.DataFrame:
    """Bugün işlem görmüş (Açık veya Kapalı) tüm makine vardiyalarını döner."""
    bugun = datetime.now(_TZ).strftime("%Y-%m-%d")
    return get_gunluk_vardiyalar(_engine, bugun)


@st.cache_data(ttl=CACHE_TTL['critical']) # v4.0.2: Tarih bazlı sorgu önbelleği (Standart: Critical)
def get_gunluk_vardiyalar(_engine, tarih: str) -> pd.DataFrame:
    """Belirli bir tarihteki tüm vardiyaları döner."""
    columns = "id, tarih, makina_no, vardiya_no, durum, baslangic_saati, operator_adi, vardiya_sefi, gerceklesen_uretim, notlar"
    sql = f"SELECT {columns} FROM map_vardiya WHERE tarih=:t ORDER BY makina_no ASC, id DESC"
    with _engine.connect() as conn:
        return _read(conn, sql, {"t": tarih})


@st.cache_data(ttl=CACHE_TTL['critical']) # v4.0.2: Aktif vardiya listesi önbelleği (Standart: Critical)
def get_tum_aktif_vardiyalar(_engine) -> pd.DataFrame:
    """Bugün açık olan tüm makine vardiyalarını tablo olarak döner."""
    bugun = datetime.now(_TZ).strftime("%Y-%m-%d")
    columns = "id, tarih, makina_no, vardiya_no, durum, baslangic_saati, operator_adi"
    sql = f"SELECT {columns} FROM map_vardiya WHERE durum='ACIK' AND tarih=:bugun ORDER BY makina_no ASC"
    with _engine.connect() as conn:
        return _read(conn, sql, {"bugun": bugun})


def get_son_kapatilan_vardiya(engine) -> dict | None:
    """Sistemdeki en son kapatılmış vardiyayı döndürür."""
    sql = "SELECT id, tarih, makina_no, vardiya_no, gerceklesen_uretim FROM map_vardiya WHERE durum='KAPALI' ORDER BY id DESC LIMIT 1"
    with engine.connect() as conn:
        df = _read(conn, sql)
    return df.iloc[0].to_dict() if not df.empty else None


def get_makina_gecmis_vardiyalar(engine, makina_no, limit=10) -> pd.DataFrame:
    """Belirli bir makinenin geçmiş (kapalı) vardiyalarını döner."""
    sql = "SELECT id, tarih, vardiya_no, gerceklesen_uretim, durum FROM map_vardiya WHERE makina_no=:m AND durum='KAPALI' ORDER BY tarih DESC, id DESC LIMIT :l"
    with engine.connect() as conn:
        return _read(conn, sql, {"m": makina_no, "l": limit})


def aç_vardiya(engine, makina_no, vardiya_no, operator_adi, acan_kullanici_id,
               vardiya_sefi, besleme, kasalama, hedef_hiz, urun_adi=None) -> int:
    """Yeni vardiya açar, id döndürür. Aynı makinede 2 açık vardiyaya izin vermez."""
    ts = _now_ts()
    bugun = ts[:10]
    params = dict(tarih=bugun, makina=makina_no, vno=int(vardiya_no),
                  bas=ts[11:16], op=operator_adi, aid=int(acan_kullanici_id or 0),
                  sef=vardiya_sefi, bes=str(besleme), kas=str(kasalama), hiz=float(hedef_hiz),
                  urun=urun_adi)
    is_pg = engine.dialect.name == 'postgresql'
    with engine.begin() as conn:
        # v5.0: Pessimistic Locking ile Çift Tıklama/Aynı Anda Vardiya Açma Önlemi
        check_sql = "SELECT id FROM map_vardiya WHERE makina_no=:m AND durum='ACIK' AND tarih=:bugun"
        if is_pg: check_sql += " FOR UPDATE"
        
        if conn.execute(text(check_sql), {"m": makina_no, "bugun": bugun}).fetchone():
            raise ValueError(f"Bu makine ({makina_no}) için zaten açık bir vardiya var! Önce kapatın.")
            
        if is_pg:
            res = conn.execute(text("""
                INSERT INTO map_vardiya
                  (tarih, makina_no, urun_adi, vardiya_no, baslangic_saati, operator_adi, acan_kullanici_id,
                   vardiya_sefi, besleme_kisi, kasalama_kisi, hedef_hiz_paket_dk, durum)
                VALUES (:tarih,:makina,:urun,:vno,:bas,:op,:aid,:sef,:bes,:kas,:hiz,'ACIK')
                RETURNING id
            """), params)
            row = res.fetchone()
            vid = int(row[0]) if row else -1
        else:
            res = conn.execute(text("""
                INSERT INTO map_vardiya
                  (tarih, makina_no, urun_adi, vardiya_no, baslangic_saati, operator_adi, acan_kullanici_id,
                   vardiya_sefi, besleme_kisi, kasalama_kisi, hedef_hiz_paket_dk, durum)
                VALUES (:tarih,:makina,:urun,:vno,:bas,:op,:aid,:sef,:bes,:kas,:hiz,'ACIK')
            """), params)
            vid = int(res.lastrowid)
    
    # v4.0.3: Önbellek temizleme (EKL-MAP-FIX-007)
    if vid > 0:
        st.cache_data.clear()
    return vid


def get_aktif_vardiya_live(engine, makina_no: str):
    """v4.0.7: Tarih duyarlı Live-Check (Hayalet vardiya önleyici)."""
    bugun = datetime.now(_TZ).strftime("%Y-%m-%d")
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, tarih, makina_no, vardiya_no, baslangic_saati, bitis_saati, operator_adi, vardiya_sefi, besleme_kisi, kasalama_kisi, hedef_hiz_paket_dk, gerceklesen_uretim, durum, notlar, olusturma_ts, guncelleme_ts, acan_kullanici_id, kapatan_kullanici_id, urun_adi FROM map_vardiya WHERE makina_no=:m AND durum='ACIK' AND tarih=:bugun"),
                           dict(m=makina_no, bugun=bugun))
        row = res.fetchone()
        return dict(row._mapping) if row else None


def kapat_vardiya(engine, vardiya_id: int, uretim: int, kapatan_kullanici_id: int):
    """
    Vardiyayı kapatır, açık zaman kayıtlarını da kapatır.
    MADDE 31: Kapanış işlemi audit trail'e kaydedilir.
    """
    ts = _now_ts()
    with engine.begin() as conn:
        # 1. Eski durum ve üretim bilgisini al
        old = conn.execute(text(
            "SELECT durum, COALESCE(gerceklesen_uretim, 0), urun_adi, baslangic_saati, tarih FROM map_vardiya WHERE id = :id"
        ), {"id": vardiya_id}).fetchone()

        old_durum = old[0] if old else None
        old_uretim = old[1] if old else 0
        eski_urun = old[2] if old else "Bilinmeyen Ürün"
        vardiya_bas_ts = f"{old[4]} {old[3]}:00" if old else ts

        # Zaman çizelgesi kaydını kapat
        acik_df = _read(conn,
            "SELECT id, baslangic_ts FROM map_zaman_cizelgesi WHERE vardiya_id=:v AND bitis_ts IS NULL",
            {"v": vardiya_id})
        for _, row in acik_df.iterrows():
            dk = _sure_dk(row['baslangic_ts'], ts)
            conn.execute(text(
                "UPDATE map_zaman_cizelgesi SET bitis_ts=:b, sure_dk=:s WHERE id=:id"),
                dict(b=ts, s=dk, id=int(row['id'])))

        # 2. Ürün geçmişini kaydet (Kapanış)
        hist = conn.execute(text(
            "SELECT COALESCE(SUM(uretim_miktari), 0) FROM map_vardiya_urun_gecmisi WHERE vardiya_id=:id"
        ), {"id": vardiya_id}).fetchone()
        logged_uretim = int(hist[0]) if hist else 0
        bu_urun_icin_uretim = max(0, uretim - logged_uretim)
        
        last_change = conn.execute(text(
            "SELECT bitis_ts FROM map_vardiya_urun_gecmisi WHERE vardiya_id=:id ORDER BY id DESC LIMIT 1"
        ), {"id": vardiya_id}).fetchone()
        urun_bas_ts = last_change[0] if last_change else vardiya_bas_ts

        conn.execute(text("""
            INSERT INTO map_vardiya_urun_gecmisi 
            (vardiya_id, urun_adi, baslangic_ts, bitis_ts, uretim_miktari, degistiren_kullanici_id, olusturma_ts)
            VALUES (:vid, :urun, :bas, :bit, :mik, :uid, :ts)
        """), dict(vid=vardiya_id, urun=eski_urun, bas=urun_bas_ts, bit=ts, mik=bu_urun_icin_uretim, uid=int(kapatan_kullanici_id or 0), ts=ts))

        # 3. Vardiyayı kapat
        conn.execute(text("""
            UPDATE map_vardiya SET durum='KAPALI', bitis_saati=:bas,
              gerceklesen_uretim=:ur, guncelleme_ts=:ts, kapatan_kullanici_id=:kid
            WHERE id=:id
        """), dict(bas=ts[11:16], ur=int(uretim), ts=ts, kid=int(kapatan_kullanici_id or 0), id=vardiya_id))

        # MADDE 31: Kapanış işlemini logla
        if old_durum:
            log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, 'durum',
                           old_durum, 'KAPALI', int(kapatan_kullanici_id or 0), 'UPDATE')
        if old_uretim != uretim:
            log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, 'gerceklesen_uretim',
                           old_uretim, uretim, int(kapatan_kullanici_id or 0), 'UPDATE')
    
    # v4.0.3: Önbellek temizleme (EKL-MAP-FIX-007)
    st.cache_data.clear()
    
    # ─── 13. ADAM: OTOMATİK RAPOR ARŞİVLEME ───
    try:
        from .map_rapor_pdf import save_map_report_to_disk
        save_map_report_to_disk(engine, vardiya_id)
    except Exception as e:
        st.warning(f"Rapor otomatik arşivlenemedi: {e}")

def degistir_urun(engine, vardiya_id: int, yeni_urun: str, user_id: int = None):
    """Vardiyayı kapatmadan ürün değiştirir, önceki ürün üretimini geçmişe loglar."""
    ts = _now_ts()
    with engine.begin() as conn:
        if engine.dialect.name == 'postgresql':
            conn.execute(text("SELECT id FROM map_vardiya WHERE id=:id FOR UPDATE"), {"id": vardiya_id})
            
        old = conn.execute(text(
            "SELECT urun_adi, COALESCE(gerceklesen_uretim, 0), baslangic_saati, tarih FROM map_vardiya WHERE id=:id"
        ), {"id": vardiya_id}).fetchone()
        
        if not old:
            return
            
        eski_urun = old[0]
        if eski_urun == yeni_urun:
            return
            
        toplam_uretim = int(old[1])
        baslangic_saati = f"{old[3]} {old[2]}:00"
        
        hist = conn.execute(text(
            "SELECT COALESCE(SUM(uretim_miktari), 0) FROM map_vardiya_urun_gecmisi WHERE vardiya_id=:id"
        ), {"id": vardiya_id}).fetchone()
        logged_uretim = int(hist[0]) if hist else 0
        bu_urun_icin_uretim = max(0, toplam_uretim - logged_uretim)
        
        last_change = conn.execute(text(
            "SELECT bitis_ts FROM map_vardiya_urun_gecmisi WHERE vardiya_id=:id ORDER BY id DESC LIMIT 1"
        ), {"id": vardiya_id}).fetchone()
        urun_bas_ts = last_change[0] if last_change else baslangic_saati
        
        conn.execute(text("""
            INSERT INTO map_vardiya_urun_gecmisi 
            (vardiya_id, urun_adi, baslangic_ts, bitis_ts, uretim_miktari, degistiren_kullanici_id, olusturma_ts)
            VALUES (:vid, :urun, :bas, :bit, :mik, :uid, :ts)
        """), dict(vid=vardiya_id, urun=eski_urun, bas=urun_bas_ts, bit=ts, mik=bu_urun_icin_uretim, uid=int(user_id or 0), ts=ts))
                   
        conn.execute(text("UPDATE map_vardiya SET urun_adi = :u, son_degisiklik = :ts WHERE id = :vid"), 
                     {"u": yeni_urun, "ts": ts, "vid": vardiya_id})
        conn.execute(text("INSERT INTO map_audit_log (vardiya_id, islem, eski_deger, yeni_deger, kullanici_id, ts) "
                          "VALUES (:vid, 'ÜRÜN DEĞİŞTİRİLDİ', :eski, :yeni, :uid, :ts)"),
                     {"vid": vardiya_id, "eski": eski_urun, "yeni": yeni_urun, "uid": user_id, "ts": ts})
        conn.commit()

def degistir_personel(engine, vardiya_id: int, yeni_besleme: str, yeni_kasalama: str, user_id: int = None):
    """v8.0: Vardiya devam ederken personel değişimini sağlar."""
    from sqlalchemy import text
    now = _now_ts()
    with engine.begin() as conn:
        res = conn.execute(text("SELECT besleme_kisi, kasalama_kisi FROM map_vardiya WHERE id = :vid FOR UPDATE"), {"vid": vardiya_id}).fetchone()
        if not res: return
        eski_bes = res[0]
        eski_kas = res[1]
        
        conn.execute(text("UPDATE map_vardiya SET besleme_kisi = :b, kasalama_kisi = :k, son_degisiklik = :ts WHERE id = :vid"), 
                     {"b": yeni_besleme, "k": yeni_kasalama, "ts": now, "vid": vardiya_id})
                     
        if str(eski_bes) != str(yeni_besleme):
            conn.execute(text("INSERT INTO map_audit_log (vardiya_id, islem, eski_deger, yeni_deger, kullanici_id, ts) "
                              "VALUES (:vid, 'BESLEME PERSONELİ DEĞİŞTİRİLDİ', :eski, :yeni, :uid, :ts)"),
                         {"vid": vardiya_id, "eski": str(eski_bes), "yeni": str(yeni_besleme), "uid": user_id, "ts": now})
                         
        if str(eski_kas) != str(yeni_kasalama):
            conn.execute(text("INSERT INTO map_audit_log (vardiya_id, islem, eski_deger, yeni_deger, kullanici_id, ts) "
                              "VALUES (:vid, 'KASALAMA PERSONELİ DEĞİŞTİRİLDİ', :eski, :yeni, :uid, :ts)"),
                         {"vid": vardiya_id, "eski": str(eski_kas), "yeni": str(yeni_kasalama), "uid": user_id, "ts": now})

# ─── Zaman Çizelgesi ─────────────────────────────────────────────────────────
def get_son_zaman_kaydi(engine, vardiya_id: int) -> dict | None:
    sql = "SELECT id, vardiya_id, sira_no, baslangic_ts, bitis_ts, sure_dk, durum, neden, aciklama, olusturma_ts FROM map_zaman_cizelgesi WHERE vardiya_id=:v ORDER BY sira_no DESC LIMIT 1"
    with engine.connect() as conn:
        df = _read(conn, sql, {"v": vardiya_id})
    return df.iloc[0].to_dict() if not df.empty else None


def insert_zaman_kaydi(engine, vardiya_id: int, durum: str,
                       neden: str = None, aciklama: str = None):
    """Yeni çalışma/duruş kaydı açar, önceki açık kaydı kapatır.
    Hız Optimizasyonu: Tek bir CTE veya transaction bloğuyla round-trip sayısı azaltıldı.
    """
    ts = _now_ts()
    is_pg = engine.dialect.name == 'postgresql'
    with engine.begin() as conn:
        # 1. Önceki açık kayıtları kapat
        acik_df = _read(conn,
            "SELECT id, baslangic_ts FROM map_zaman_cizelgesi WHERE vardiya_id=:v AND bitis_ts IS NULL",
            {"v": vardiya_id})
        
        for _, row in acik_df.iterrows():
            dk = _sure_dk(row['baslangic_ts'], ts)
            conn.execute(text(
                "UPDATE map_zaman_cizelgesi SET bitis_ts=:b, sure_dk=:s WHERE id=:id"),
                dict(b=ts, s=dk, id=int(row['id'])))
        
        # 2. Yeni sıra numarasını bul ve ekle
        sira_df = _read(conn,
            "SELECT COALESCE(MAX(sira_no),0)+1 AS n FROM map_zaman_cizelgesi WHERE vardiya_id=:v",
            {"v": vardiya_id})
        sira = int(sira_df.iloc[0]['n'])
        
        sql = """
            INSERT INTO map_zaman_cizelgesi(vardiya_id,sira_no,baslangic_ts,durum,neden,aciklama)
            VALUES(:vid,:sno,:ts,:dur,:ned,:acl)
        """
        if is_pg: sql += " RETURNING id"
        
        res = conn.execute(text(sql), dict(vid=vardiya_id, sno=sira, ts=ts, dur=durum, ned=neden, acl=aciklama))
        return int(res.fetchone()[0]) if is_pg else int(res.lastrowid)


def update_kumulatif_uretim(engine, vardiya_id: int, miktar: int, user_id: int = None):
    """
    Üretimi mevcut değerin üzerine kümülatif ekler.
    MADDE 31: Üretim artışı audit trail'e kaydedilir.
    """
    ts = _now_ts()
    with engine.begin() as conn:
        # Eski üretim bilgisini al
        old = conn.execute(text(
            "SELECT COALESCE(gerceklesen_uretim, 0) FROM map_vardiya WHERE id = :id"
        ), {"id": vardiya_id}).fetchone()

        old_uretim = old[0] if old else 0
        new_uretim = old_uretim + int(miktar)

        conn.execute(text("""
            UPDATE map_vardiya
            SET gerceklesen_uretim = COALESCE(gerceklesen_uretim, 0) + :m,
                guncelleme_ts = :ts
            WHERE id = :id
        """), {"m": int(miktar), "ts": ts, "id": vardiya_id})

        # MADDE 31: Üretim artışını logla
        if user_id:
            log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, 'gerceklesen_uretim',
                           old_uretim, new_uretim, int(user_id), 'UPDATE')


def set_net_uretim(engine, vardiya_id: int, yeni_toplam: int, user_id: int = None):
    """
    Net üretim miktarını doğrudan belirler (Admin Düzeltme).
    MADDE 31: Üretim düzeltmesi audit trail'e kaydedilir.
    """
    ts = _now_ts()
    with engine.begin() as conn:
        # Eski üretim bilgisini al
        old = conn.execute(text(
            "SELECT gerceklesen_uretim FROM map_vardiya WHERE id = :id"
        ), {"id": vardiya_id}).fetchone()

        old_uretim = old[0] if old else None

        conn.execute(text("""
            UPDATE map_vardiya
            SET gerceklesen_uretim = :m,
                guncelleme_ts = :ts
            WHERE id = :id
        """), {"m": int(yeni_toplam), "ts": ts, "id": vardiya_id})

        # MADDE 31: Düzeltmeyi logla
        if old_uretim != yeni_toplam:
            log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, 'gerceklesen_uretim',
                           old_uretim, yeni_toplam, int(user_id or 0), 'UPDATE')


def get_zaman_cizelgesi(engine, vardiya_id: int) -> pd.DataFrame:
    sql = """SELECT sira_no,baslangic_ts,bitis_ts,sure_dk,durum,neden,aciklama
             FROM map_zaman_cizelgesi WHERE vardiya_id=:v ORDER BY sira_no"""
    with engine.connect() as conn:
        return _read(conn, sql, {"v": vardiya_id})


def sil_son_zaman_kaydi(engine, vardiya_id: int):
    sql = """DELETE FROM map_zaman_cizelgesi WHERE id=(
               SELECT id FROM map_zaman_cizelgesi WHERE vardiya_id=:v ORDER BY sira_no DESC LIMIT 1)"""
    with engine.begin() as conn:
        conn.execute(text(sql), {"v": vardiya_id})


def manuel_zaman_ekle(engine, vardiya_id: int, bas: str, bit: str,
                      durum: str, neden: str, aciklama: str, tarih: str):
    """Manuel mod: saat stringleri (HH:MM) ile kayıt ekler."""
    bas_ts = f"{tarih} {bas}:00"
    bit_ts = f"{tarih} {bit}:00"
    dk = _sure_dk(bas_ts, bit_ts)
    with engine.begin() as conn:
        sira_df = _read(conn,
            "SELECT COALESCE(MAX(sira_no),0)+1 AS n FROM map_zaman_cizelgesi WHERE vardiya_id=:v",
            {"v": vardiya_id})
        sira = int(sira_df.iloc[0]['n'])
        conn.execute(text("""
            INSERT INTO map_zaman_cizelgesi(vardiya_id,sira_no,baslangic_ts,bitis_ts,sure_dk,durum,neden,aciklama)
            VALUES(:vid,:sno,:bas,:bit,:dk,:dur,:ned,:acl)
        """), dict(vid=vardiya_id, sno=sira, bas=bas_ts, bit=bit_ts, dk=dk,
                   dur=durum, ned=neden, acl=aciklama))


# ─── Bobin ───────────────────────────────────────────────────────────────────
def get_aktif_bobin(engine, vardiya_id: int, film_tipi: str) -> dict | None:
    """Verilen film tipi için henüz kapatılmamış (bitis_kg IS NULL) bobini döner."""
    sql = "SELECT id, degisim_ts, bobin_lot, baslangic_kg FROM map_bobin_kaydi WHERE vardiya_id=:v AND film_tipi=:tip AND bitis_kg IS NULL ORDER BY sira_no DESC LIMIT 1"
    with engine.connect() as conn:
        df = _read(conn, sql, {"v": vardiya_id, "tip": film_tipi})
    return df.iloc[0].to_dict() if not df.empty else None


def baslat_bobin(engine, vardiya_id: int, lot: str, film_tipi: str,
                 baslangic_kg: float, aciklama: str = None, user_id: int = None):
    """Sadece yeni bobini takar (Bitis KG ve kullanılan miktar boştur)."""
    ts = _now_ts()
    with engine.begin() as conn:
        sira_df = _read(conn,
            "SELECT COALESCE(MAX(sira_no),0)+1 AS n FROM map_bobin_kaydi WHERE vardiya_id=:v",
            {"v": vardiya_id})
        sira = int(sira_df.iloc[0]['n'])
        res = conn.execute(text("""
            INSERT INTO map_bobin_kaydi(vardiya_id, sira_no, degisim_ts, bobin_lot, film_tipi,
                                       baslangic_kg, bitis_kg, kullanilan_kg, aciklama)
            VALUES(:vid, :sno, :ts, :lot, :tip, :bas, NULL, NULL, :acl)
            RETURNING id
        """), dict(vid=vardiya_id, sno=sira, ts=ts, lot=lot, tip=film_tipi,
                   bas=float(baslangic_kg), acl=aciklama))

        bobin_id = res.fetchone()[0] if res.fetchone() else None

        if user_id and bobin_id:
            log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, f'bobin_{bobin_id}_lot',
                           'YENI', lot, int(user_id), 'INSERT')


def kapat_ve_degistir_bobin(engine, vardiya_id: int, aktif_bobin_id: int, film_tipi: str, 
                            eski_bitis_kg: float, teorik_ambalaj_gr: float, gerceklesen_uretim: int, 
                            yeni_lot: str, yeni_baslangic_kg: float, aciklama: str = None, user_id: int = None):
    """Eski bobini kapatıp kullanılan kg'yi hesaplar, artığı otomatik fireye atar ve yeni bobini başlatır."""
    ts = _now_ts()
    with engine.begin() as conn:
        # 1. Eski bobini kapat ve kullanılanı hesapla
        old = conn.execute(text("SELECT baslangic_kg FROM map_bobin_kaydi WHERE id=:id"), {"id": aktif_bobin_id}).fetchone()
        bas_kg = float(old[0]) if old and old[0] is not None else 0.0
        kullanilan_kg = round(bas_kg - float(eski_bitis_kg), 2)
        
        conn.execute(text("""
            UPDATE map_bobin_kaydi SET bitis_kg=:bit, kullanilan_kg=:kul WHERE id=:id
        """), dict(bit=float(eski_bitis_kg), kul=kullanilan_kg, id=aktif_bobin_id))
        
        # 2. Otomatik Fire Hesaplama
        # Kullanılan bobin miktarı (kg) * 1000 = Gram. Teorik üretim = gerceklesen_uretim * teorik_ambalaj_gr.
        if teorik_ambalaj_gr > 0:
            harcanan_gr = kullanilan_kg * 1000
            teorik_harcanan_gr = float(gerceklesen_uretim) * teorik_ambalaj_gr
            fire_gr = max(0.0, harcanan_gr - teorik_harcanan_gr)
            fire_adet = int(fire_gr / teorik_ambalaj_gr)
            
            if fire_adet > 0:
                fire_tipi_db = "Film Değişimi Fire"
                sql_check = "SELECT id, miktar_adet FROM map_fire_kaydi WHERE vardiya_id=:vid AND fire_tipi=:tip LIMIT 1"
                res = conn.execute(text(sql_check), {"vid": vardiya_id, "tip": fire_tipi_db}).fetchone()
                if res:
                    new_miktar = int(res[1]) + fire_adet
                    conn.execute(text("UPDATE map_fire_kaydi SET miktar_adet = :m WHERE id = :id"), {"m": new_miktar, "id": int(res[0])})
                else:
                    conn.execute(text("""
                        INSERT INTO map_fire_kaydi(vardiya_id,fire_tipi,miktar_adet,aciklama)
                        VALUES(:vid,:tip,:mik,:acl)
                    """), dict(vid=vardiya_id, tip=fire_tipi_db, mik=fire_adet, acl=f"Otomatik (Bobin {aktif_bobin_id})"))
        
        # 3. Yeni Bobini Ekle
        sira_df = _read(conn, "SELECT COALESCE(MAX(sira_no),0)+1 AS n FROM map_bobin_kaydi WHERE vardiya_id=:v", {"v": vardiya_id})
        sira = int(sira_df.iloc[0]['n'])
        
        res = conn.execute(text("""
            INSERT INTO map_bobin_kaydi(vardiya_id, sira_no, degisim_ts, bobin_lot, film_tipi, baslangic_kg, aciklama)
            VALUES(:vid, :sno, :ts, :lot, :tip, :bas, :acl)
            RETURNING id
        """), dict(vid=vardiya_id, sno=sira, ts=ts, lot=yeni_lot, tip=film_tipi, bas=float(yeni_baslangic_kg), acl=aciklama))
        
        bobin_id = res.fetchone()[0] if res.fetchone() else None

        if user_id and bobin_id:
            log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, f'bobin_{bobin_id}_lot', 'YENI', yeni_lot, int(user_id), 'INSERT')



def get_bobinler(engine, vardiya_id: int) -> pd.DataFrame:
    with engine.connect() as conn:
        return _read(conn,
            "SELECT id, degisim_ts, bobin_lot, film_tipi, kullanilan_kg FROM map_bobin_kaydi WHERE vardiya_id=:v ORDER BY sira_no",
            {"v": vardiya_id})


# ─── Fire ────────────────────────────────────────────────────────────────────
def insert_fire(engine, vardiya_id: int, fire_tipi: str, miktar: int,
                bobin_ref: str = None, aciklama: str = None, user_id: int = None):
    """
    Fireyi mevcut tipin üzerine kümülatif ekler veya yeni kayıt açar.
    MADDE 31: Fire kaydı audit trail'e kaydedilir.
    """
    with engine.begin() as conn:
        # Önce bu tipte bir fire kaydı var mı bak
        sql_check = "SELECT id, miktar_adet FROM map_fire_kaydi WHERE vardiya_id=:vid AND fire_tipi=:tip LIMIT 1"
        res = conn.execute(text(sql_check), {"vid": vardiya_id, "tip": fire_tipi}).fetchone()

        if res:
            # Varsa üzerine ekle
            fire_id = int(res[0])
            old_miktar = int(res[1])
            new_miktar = old_miktar + int(miktar)

            conn.execute(text("UPDATE map_fire_kaydi SET miktar_adet = :m WHERE id = :id"),
                         {"m": new_miktar, "id": fire_id})

            # MADDE 31: Fire artışını logla
            if user_id:
                log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, f'fire_{fire_tipi}_miktar',
                               old_miktar, new_miktar, int(user_id), 'UPDATE')
        else:
            # Yoksa yeni ekle
            res = conn.execute(text("""
                INSERT INTO map_fire_kaydi(vardiya_id,fire_tipi,miktar_adet,bobin_ref,aciklama)
                VALUES(:vid,:tip,:mik,:bref,:acl)
                RETURNING id
            """), dict(vid=vardiya_id, tip=fire_tipi, mik=int(miktar), bref=bobin_ref, acl=aciklama))

            fire_id = res.fetchone()[0] if res.fetchone() else None

            # MADDE 31: Yeni fire kaydını logla
            if user_id and fire_id:
                log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, f'fire_{fire_tipi}',
                               'YENI', miktar, int(user_id), 'INSERT')


def get_fire_kayitlari(engine, vardiya_id: int) -> pd.DataFrame:
    with engine.connect() as conn:
        return _read(conn,
            "SELECT id, fire_tipi, miktar_adet, aciklama, olusturma_ts FROM map_fire_kaydi WHERE vardiya_id=:v ORDER BY id",
            {"v": vardiya_id})


def set_fire_miktar(engine, fire_id: int, yeni_miktar: int, user_id: int = None):
    """
    Fire miktarını doğrudan belirler (Admin Düzeltme).
    MADDE 31: Fire düzeltmesi audit trail'e kaydedilir.
    """
    with engine.begin() as conn:
        # Eski değeri al
        old = conn.execute(text(
            "SELECT miktar_adet, vardiya_id FROM map_fire_kaydi WHERE id = :id"
        ), {"id": int(fire_id)}).fetchone()

        old_miktar = old[0] if old else None
        vardiya_id = old[1] if old else None

        conn.execute(text("UPDATE map_fire_kaydi SET miktar_adet = :m WHERE id = :id"),
                     {"m": int(yeni_miktar), "id": int(fire_id)})

        # MADDE 31: Düzeltmeyi logla
        if user_id and vardiya_id and old_miktar != yeni_miktar:
            log_field_change(conn, 'map_vardiya_degisim_loglari', vardiya_id, f'fire_{fire_id}_miktar',
                           old_miktar, yeni_miktar, int(user_id), 'UPDATE')


def sil_fire_kaydi(engine, fire_id: int):
    """Fire kaydını tamamen siler (Admin Düzeltme)."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM map_fire_kaydi WHERE id = :id"), {"id": int(fire_id)})

# ─── Çoklu Makine Raporlaması ────────────────────────────────────────────────
def get_related_vardiya_ids(engine, current_vardiya_id: int) -> list:
    """Aynı tarih ve vardiya numarasındaki tüm makine vardiya ID'lerini döndürür (13. Adam)."""
    try:
        with engine.connect() as conn:
            # Önce mevcut vardiyanın tarih ve vardiya_no bilgisini al
            sql_base = "SELECT tarih, vardiya_no FROM map_vardiya WHERE id = :id"
            base_res = conn.execute(text(sql_base), {"id": current_vardiya_id}).fetchone()
            
            if not base_res:
                return [current_vardiya_id]
                
            tarih, vardiya_no = base_res[0], base_res[1]
            
            # Bu tarih ve vardiya_no'ya sahip tüm makineleri sıralı getir
            sql_all = "SELECT id FROM map_vardiya WHERE tarih = :t AND vardiya_no = :v ORDER BY makina_no ASC"
            all_res = conn.execute(text(sql_all), {"t": tarih, "v": vardiya_no}).fetchall()
            
            return [int(r[0]) for r in all_res]
    except Exception as e:
        import streamlit as st
        st.error(f"Vardiya ilişkisi bulunamadı: {e}")
        return [current_vardiya_id]

# ─── Sistem Parametreleri (Zero Hardcode) ────────────────────────────────────
@st.cache_data(ttl=CACHE_TTL['critical'])
def get_map_durus_nedenleri(_engine) -> list:
    """Veritabanından aktif MAP duruş nedenlerini çeker."""
    try:
        sql = "SELECT neden FROM map_durus_nedenleri WHERE durum = 'AKTİF' ORDER BY neden ASC"
        with _engine.connect() as conn:
            df = _read(conn, sql)
        if not df.empty:
            return df['neden'].tolist()
    except Exception:
        pass
    # Fallback (Veritabanı tablosu henüz oluşmadıysa)
    return [
        "ARIZA / BAKIM", "ALT FİLM DEĞİŞİMİ", "DİĞER", "MOLA / YEMEK",
        "SETUP / AYAR", "TEMİZLİK / SANİTASYON", "ÜRETİM BEKLEME", "ÜST FİLM DEĞİŞİMİ"
    ]

@st.cache_data(ttl=CACHE_TTL['critical'])
def get_map_fire_tipleri(_engine) -> list:
    """Veritabanından aktif MAP fire tiplerini çeker."""
    try:
        sql = "SELECT fire_tipi FROM map_fire_tipleri WHERE durum = 'AKTİF' ORDER BY fire_tipi ASC"
        with _engine.connect() as conn:
            df = _read(conn, sql)
        if not df.empty:
            return df['fire_tipi'].tolist()
    except Exception:
        pass
    # Fallback
    return [
        "Besleme Hatası", "Bobin Başı Fire", "Bobin Sonu Fire", "Diğer", 
        "Film Değişimi Fire", "Gaz Hatası", "Operatör Hatası", "Sızdırmazlık / Kaçak", "Yırtık / Delik Film"
    ]

