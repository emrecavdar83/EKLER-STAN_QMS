import pytest
import sys
import os
from sqlalchemy import create_engine

# Proje kökünü ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.schema_qdms import init_qdms_tables
from modules.qdms.belge_kayit import belge_kod_dogrula, belge_olustur, belge_durum_guncelle, belge_getir
from modules.qdms.sablon_motor import kolon_genislik_dogrula
from modules.qdms.revizyon import revizyon_baslat, aktif_rev_getir
from modules.qdms.yayim_yonetici import belge_yayimla

@pytest.fixture
def db_conn():
    """Test için geçici bir in-memory SQLite veritabanı oluşturur."""
    engine = create_engine("sqlite:///:memory:")
    # Gerekli tabloları oluştur
    with engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE TABLE personel (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT, kullanici_adi TEXT, sifre TEXT, rol TEXT, durum TEXT)"))
        conn.execute(text("INSERT INTO personel (ad_soyad, kullanici_adi, rol, durum) VALUES ('Test Admin', 'admin', 'ADMIN', 'AKTİF')"))
    
    init_qdms_tables(engine)
    return engine

def test_belge_kod_format():
    """EKL-SO-004 ✅, SO-004 ❌, EKL-XX-001 ❌ format testi."""
    assert belge_kod_dogrula("EKL-SO-004") == True
    assert belge_kod_dogrula("EKL-TL-001") == True
    assert belge_kod_dogrula("SO-004") == False      # prefix eksik
    assert belge_kod_dogrula("EKL-XX-001") == False  # geçersiz tip
    assert belge_kod_dogrula("EKL-SO-4") == False    # 3 hane değil

def test_kolon_genislik_toplam():
    """%100 = True, %99 = False genişlik testi."""
    config_ok = [{"ad": "A", "genislik_yuzde": 50}, {"ad": "B", "genislik_yuzde": 50}]
    config_fail = [{"ad": "A", "genislik_yuzde": 50}, {"ad": "B", "genislik_yuzde": 49}]
    assert kolon_genislik_dogrula(config_ok) == True
    assert kolon_genislik_dogrula(config_fail) == False

def test_durum_gecis_gecersiz(db_conn):
    """aktif -> taslak geçişi yasak (❌)."""
    # Önce bir belge oluştur
    belge_olustur(db_conn, "EKL-SO-004", "Test Belgesi", "form", "soguk_oda", "Açıklama", 1)
    
    # Durumu aktif yap
    belge_durum_guncelle(db_conn, "EKL-SO-004", "aktif", 1)
    
    # Aktiften taslağa geri dönüşü dene
    sonuc = belge_durum_guncelle(db_conn, "EKL-SO-004", "taslak", 1)
    assert sonuc['basarili'] == False
    assert "geçersiz" in sonuc['hata'].lower()

def test_belge_olustur_crud(db_conn):
    """Oluştur, getir, listele (CRUD) testi."""
    res = belge_olustur(db_conn, "EKL-SO-005", "CRUD Test", "talimat", "uretim", "Test", 1)
    assert res['basarili'] == True
    
    belge = belge_getir(db_conn, "EKL-SO-005")
    assert belge is not None
    assert belge['belge_adi'] == "CRUD Test"

def test_revizyon_baslat_t2(db_conn):
    """revizyon_baslat() T2 koruması ve rev+1 testi."""
    belge_olustur(db_conn, "EKL-SO-006", "Rev Test", "form", "soguk_oda", "X", 1)
    
    # 1. Onaysız deneme (T2 koruması)
    res = revizyon_baslat(db_conn, "EKL-SO-006", "Not", 1, onay_verildi=False)
    assert res['basarili'] == False
    assert "onay" in res['hata'].lower()
    
    # 2. Onaylı deneme
    res = revizyon_baslat(db_conn, "EKL-SO-006", "İlk Revizyon", 1, onay_verildi=True)
    assert res['basarili'] == True
    assert aktif_rev_getir(db_conn, "EKL-SO-006") == 2
    
def test_durum_makinesi_gecisleri(db_conn):
    """taslak -> incelemede -> aktif geçiş testi."""
    kod = "EKL-SO-007"
    belge_olustur(db_conn, kod, "Durum Test", "form", "soguk_oda", "X", 1)
    
    # taslak -> aktif (Geçersiz, arada inceleme olmalı)
    res = belge_yayimla(db_conn, kod, 1) # belge_yayimla incelemede -> aktif yapar
    assert res['basarili'] == False
    
    # taslak -> incelemede
    u_res = belge_durum_guncelle(db_conn, kod, "incelemede", 1)
    assert u_res['basarili'] == True, f"Durum guncelleme hatasi: {u_res.get('hata')}"
    
    # incelemede -> aktif
    res = belge_yayimla(db_conn, kod, 1)
    assert res['basarili'] == True, f"Yayımlama hatası: {res.get('hata')}"
    
    belge = belge_getir(db_conn, kod)
    assert belge['durum'] == 'aktif'
