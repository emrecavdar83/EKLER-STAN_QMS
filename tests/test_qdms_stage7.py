import pytest
import sys
import os
from sqlalchemy import create_engine, text

# Proje kökünü ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.schema_qdms import init_qdms_tables
from modules.qdms.belge_kayit import belge_olustur, belge_durum_guncelle, belge_getir
from modules.qdms.revizyon import revizyon_baslat, aktif_rev_getir
from modules.qdms.yayim_yonetici import belge_yayimla
from modules.qdms.talimat_yonetici import talimat_olustur, talimat_qr_ile_getir, okuma_onay_kaydet
from modules.qdms.uyumluluk_rapor import uyumluluk_ozeti_getir

@pytest.fixture
def db_conn():
    """Tüm QDMS Stage 7 için geçici in-memory DB."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE personel (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, kullanici_adi TEXT, sifre TEXT, rol TEXT, durum TEXT)"))
        conn.execute(text("INSERT INTO personel (ad_soyad, kullanici_adi, rol, durum) VALUES ('Test Admin', 'admin', 'ADMIN', 'AKTİF')"))
    init_qdms_tables(engine)
    return engine

# --- STAGE 7.1 & 7.2: KAYIT & CRUD ---
def test_full_crud(db_conn):
    res = belge_olustur(db_conn, "EKL-SO-001", "Temizlik Formu", "form", "soguk_oda", "X", 1)
    assert res['basarili'] == True
    belge = belge_getir(db_conn, "EKL-SO-001")
    assert belge['belge_adi'] == "Temizlik Formu"

# --- STAGE 7.4: REVIZYON & YAYIM ---
def test_full_lifecycle(db_conn):
    kod = "EKL-PR-001"
    belge_olustur(db_conn, kod, "Prosedür", "prosedur", "kalite", "X", 1)
    
    # incelemede -> aktif (belge_yayimla)
    belge_durum_guncelle(db_conn, kod, "incelemede", 1)
    res_yayim = belge_yayimla(db_conn, kod, 1)
    assert res_yayim['basarili'] == True
    
    # Revizyon Başlat (T2)
    res_rev = revizyon_baslat(db_conn, kod, "Güncelleme", 1, onay_verildi=True)
    assert res_rev['basarili'] == True
    assert aktif_rev_getir(db_conn, kod) == 2

# --- STAGE 7.5: TALIMATLAR ---
def test_talimat_ve_qr(db_conn):
    adimlar = [{"sira": 1, "baslik": "Hazırlık", "aciklama": "Ellerini yıka"}]
    res = talimat_olustur(db_conn, "EKL-TL-005", "El Yıkama", "hijyen", adimlar, ekipman_id=None, departman="Üretim")
    assert res['basarili'] == True
    assert "qr_token" in res
    
    talimat = talimat_qr_ile_getir(db_conn, res['qr_token'])
    assert talimat['talimat_adi'] == "El Yıkama"

def test_okuma_onay(db_conn):
    okuma_onay_kaydet(db_conn, "EKL-SO-004", 1, 1) # Personel 1 okudu
    # Hata almamalıyız

# --- STAGE 7.5: UYUMLULUK ---
def test_brc_skor_mantigi(db_conn):
    # Başlangıçta 1 aktif belgemiz olsun (EKL-SO-004 simülasyonu)
    belge_olustur(db_conn, "EKL-SO-004", "Aktif Belge", "form", "genel", "X", 1)
    belge_durum_guncelle(db_conn, "EKL-SO-004", "incelemede", 1)
    belge_yayimla(db_conn, "EKL-SO-004", 1)
    
    ozet = uyumluluk_ozeti_getir(db_conn)
    assert ozet['aktif_belge_sayisi'] >= 1
    # Başlangıç skoru beklentisi (Aktif:25 + Hiç eskimemiş:25 + Talimatlar yeni:25 = 75?)
    # Bizim algoritmada son 30 gün revizyonu da puan getiriyor. 
    # Şu an revizyon logu boş, o yüzden +0 oradan.
    # Talimat var mı? Yoksa +0? Algoritmaya göre skor simüle edelim.
    assert ozet['brc_uyum_skoru'] >= 50.0
