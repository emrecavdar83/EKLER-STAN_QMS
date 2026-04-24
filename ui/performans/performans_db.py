# modules/performans/performans_db.py
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import uuid
from logic.dynamic_sync import log_field_change

def _read(conn, sql, params=None):
    """DB okuma yardımcısı."""
    return pd.read_sql(text(sql), conn, params=params)

_UP_SQL = """
    UPDATE performans_degerledirme SET
        calisan_adi_soyadi=:calisan_adi_soyadi, bolum=:bolum, gorevi=:gorevi,
        ise_giris_tarihi=:ise_giris_tarihi, degerlendirme_tarihi=:degerlendirme_tarihi,
        kkd_kullanimi=:kkd_kullanimi, mesleki_kriter_2=:mesleki_kriter_2,
        mesleki_kriter_3=:mesleki_kriter_3, mesleki_kriter_4=:mesleki_kriter_4,
        mesleki_kriter_5=:mesleki_kriter_5, mesleki_kriter_6=:mesleki_kriter_6,
        mesleki_kriter_7=:mesleki_kriter_7, mesleki_kriter_8=:mesleki_kriter_8,
        mesleki_ortalama_puan=:mesleki_ortalama_puan,
        calisma_saatleri_uyum=:calisma_saatleri_uyum, ogrenme_kabiliyeti=:ogrenme_kabiliyeti,
        iletisim_becerisi=:iletisim_becerisi, problem_cozme=:problem_cozme,
        kalite_bilinci=:kalite_bilinci, ise_baglilik_aidiyet=:ise_baglilik_aidiyet,
        ekip_calismasi_uyum=:ekip_calismasi_uyum, verimli_calisma=:verimli_calisma,
        kurumsal_ortalama_puan=:kurumsal_ortalama_puan,
        agirlikli_toplam_puan=:agirlikli_toplam_puan, polivalans_duzeyi=:polivalans_duzeyi,
        polivalans_kodu=:polivalans_kodu, yorum=:yorum, degerlendiren_adi=:degerlendiren_adi,
        guncelleyen_kullanici=:guncelleyen_kullanici, surum=:surum,
        onceki_puan=:onceki_puan, sync_durumu='bekliyor'
    WHERE id=:target_id
"""

_INS_SQL = """
    INSERT INTO performans_degerledirme (
        uuid, personel_id, calisan_adi_soyadi, bolum, gorevi, ise_giris_tarihi,
        donem, degerlendirme_tarihi, degerlendirme_yili,
        kkd_kullanimi, mesleki_kriter_2, mesleki_kriter_3, mesleki_kriter_4,
        mesleki_kriter_5, mesleki_kriter_6, mesleki_kriter_7, mesleki_kriter_8,
        mesleki_ortalama_puan, calisma_saatleri_uyum, ogrenme_kabiliyeti,
        iletisim_becerisi, problem_cozme, kalite_bilinci, ise_baglilik_aidiyet,
        ekip_calismasi_uyum, verimli_calisma, kurumsal_ortalama_puan,
        agirlikli_toplam_puan, polivalans_duzeyi, polivalans_kodu,
        yorum, degerlendiren_adi, guncelleyen_kullanici
    ) VALUES (
        :uuid, :personel_id, :calisan_adi_soyadi, :bolum, :gorevi, :ise_giris_tarihi,
        :donem, :degerlendirme_tarihi, :degerlendirme_yili,
        :kkd_kullanimi, :mesleki_kriter_2, :mesleki_kriter_3, :mesleki_kriter_4,
        :mesleki_kriter_5, :mesleki_kriter_6, :mesleki_kriter_7, :mesleki_kriter_8,
        :mesleki_ortalama_puan, :calisma_saatleri_uyum, :ogrenme_kabiliyeti,
        :iletisim_becerisi, :problem_cozme, :kalite_bilinci, :ise_baglilik_aidiyet,
        :ekip_calismasi_uyum, :verimli_calisma, :kurumsal_ortalama_puan,
        :agirlikli_toplam_puan, :polivalans_duzeyi, :polivalans_kodu,
        :yorum, :degerlendiren_adi, :guncelleyen_kullanici
    ) RETURNING id
"""


def _degerlendirme_guncelle(conn, d, old):
    d['surum']      = int(old['surum']) + 1
    d['onceki_puan'] = float(old['agirlikli_toplam_puan'])
    d['target_id']  = int(old['id'])
    conn.execute(text(_UP_SQL), d)
    uid = int(d.get('guncelleyen_kullanici', 0)) if d.get('guncelleyen_kullanici') else 0
    log_field_change(conn, 'performans_degisim_loglari', d['target_id'],
                     'agirlikli_toplam_puan', str(old['agirlikli_toplam_puan']),
                     str(d.get('agirlikli_toplam_puan')), uid, 'UPDATE')


def _degerlendirme_ekle(conn, d):
    d['uuid'] = str(uuid.uuid4())
    row = conn.execute(text(_INS_SQL), d).fetchone()
    if row:
        uid = int(d.get('guncelleyen_kullanici', 0)) if d.get('guncelleyen_kullanici') else 0
        log_field_change(conn, 'performans_degisim_loglari', row[0],
                         'agirlikli_toplam_puan', 'YENI', str(d.get('agirlikli_toplam_puan')), uid, 'INSERT')


def degerlendirme_kaydet(engine, d: dict) -> tuple[bool, str]:
    """UPSERT: aynı personel+donem+yil varsa güncelle, yoksa ekle. Audit trail tutulur."""
    try:
        with engine.begin() as conn:
            mevcut = _read(conn,
                "SELECT id, agirlikli_toplam_puan, surum FROM performans_degerledirme "
                "WHERE personel_id=:pid AND donem=:dn AND degerlendirme_yili=:yil AND silinmis=0",
                {"pid": d['personel_id'], "dn": d['donem'], "yil": d['degerlendirme_yili']})
            if not mevcut.empty:
                _degerlendirme_guncelle(conn, d, mevcut.iloc[0])
            else:
                _degerlendirme_ekle(conn, d)
        return True, "Başarıyla kaydedildi."
    except Exception as e:
        return False, f"Veritabanı hatası: {e}"

def degerlendirme_listele(engine, filtreler: dict = None) -> pd.DataFrame:
    """Filtrelere göre değerlendirmeleri listeler."""
    sql = (
        "SELECT id, uuid, personel_id, calisan_adi_soyadi, bolum, gorevi, "
        "ise_giris_tarihi, donem, degerlendirme_tarihi, degerlendirme_yili, "
        "agirlikli_toplam_puan, polivalans_duzeyi, polivalans_kodu, "
        "olusturma_tarihi, guncelleyen_kullanici, surum, silinmis "
        "FROM performans_degerledirme WHERE silinmis = 0"
    )
    params = {}
    if filtreler:
        if filtreler.get('bolum'):
            sql += " AND bolum = :bolum"
            params['bolum'] = filtreler['bolum']
        if filtreler.get('yil'):
            sql += " AND degerlendirme_yili = :yil"
            params['yil'] = filtreler['yil']
    sql += " ORDER BY degerlendirme_tarihi DESC"
    with engine.connect() as conn:
        return _read(conn, sql, params)

def personel_listesi_getir(engine):
    """Entegre Personel Listesi: ayarlar_bolumler ile join edilerek getirilir."""
    # Anayasa v5.8.16: Şema uyumlu join
    sql = """
        SELECT p.id, p.ad_soyad, b.ad as bolum, p.rol as gorev, p.ise_giris_tarihi 
        FROM ayarlar_kullanicilar p
        LEFT JOIN qms_departmanlar b ON p.qms_departman_id = b.id
        WHERE p.durum = 'AKTİF' 
        ORDER BY p.ad_soyad
    """
    with engine.connect() as conn:
        return _read(conn, sql)

def bolum_listesi_getir(engine):
    """Mevcut 'ayarlar_bolumler' tablosundan beslenir."""
    sql = "SELECT ad as bolum_adi FROM qms_departmanlar WHERE aktif != 0 ORDER BY ad"
    with engine.connect() as conn:
        df = _read(conn, sql)
        return df['bolum_adi'].tolist() if not df.empty else []

def matris_verisi_getir(engine, yil: int) -> pd.DataFrame:
    """Polivalans matrisi için yıla göre tüm değerlendirmeleri getirir."""
    sql = """
        SELECT calisan_adi_soyadi, bolum, polivalans_kodu,
               polivalans_duzeyi, agirlikli_toplam_puan, donem
        FROM performans_degerledirme
        WHERE degerlendirme_yili = :yil AND silinmis = 0
        ORDER BY bolum, calisan_adi_soyadi, donem
    """
    with engine.connect() as conn:
        return _read(conn, sql, {"yil": yil})
