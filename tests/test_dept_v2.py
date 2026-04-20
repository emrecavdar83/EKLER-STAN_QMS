import pytest
from sqlalchemy import text
from database.connection import get_engine
from logic.dept_logic import bolum_kodu_uret, miras_tip_guncelle, pasife_al_ve_aktar

pytestmark = pytest.mark.skipif(True, reason="Integration test - requires live DB")

@pytest.fixture
def db_engine():
    return get_engine()

def test_bolum_kodu_uret(db_engine):
    # Test prefix generation
    code = bolum_kodu_uret(db_engine)
    assert "GEN-" in code
    
    # Test parent-based prefix (If parent 'ÜRETİM' exists)
    # This is an integration test, assumes DB has data
    code_ur = bolum_kodu_uret(db_engine, ust_id=2) # ID 2 is ÜRETIM in seed
    assert "ÜR-" in code_ur or "GE-" in code_ur

def test_miras_tip_guncelle(db_engine):
    # Test recursive update
    # 1. Root update (ID 1)
    new_type = 2 # KALITE
    miras_tip_guncelle(db_engine, 1, new_type)
    
    with db_engine.connect() as conn:
        res = conn.execute(text("SELECT tur_id FROM qms_departmanlar WHERE ust_id = 1")).fetchall()
        for r in res:
            assert r[0] == new_type

def test_pasife_al_ve_aktar(db_engine):
    # 1. Create a dummy dept and personnel
    with db_engine.begin() as conn:
        conn.execute(text("INSERT INTO qms_departmanlar (ad, ust_id, durum) VALUES ('TEST DEPT', 1, 'AKTİF')"))
        res = conn.execute(text("SELECT id FROM qms_departmanlar WHERE ad = 'TEST DEPT'")).fetchone()
        test_id = res[0]
        
        conn.execute(text("INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, durum, qms_departman_id) VALUES ('Test Pers', 'tst', '123', 'Personel', 'AKTİF', :d)"), {"d": test_id})
    
    # 2. Run deactivation
    success, msg = pasife_al_ve_aktar(db_engine, test_id)
    assert success is True
    
    # 3. Check if personnel moved to parent (ID 1)
    with db_engine.connect() as conn:
        res = conn.execute(text("SELECT qms_departman_id FROM personel WHERE kullanici_adi = 'tst'")).fetchone()
        assert res[0] == 1
        
        res_dept = conn.execute(text("SELECT durum FROM qms_departmanlar WHERE id = :i"), {"i": test_id}).fetchone()
        assert res_dept[0] == 'PASİF'
        
    # Cleanup
    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM personel WHERE kullanici_adi = 'tst'"))
        conn.execute(text("DELETE FROM qms_departmanlar WHERE id = :i"), {"i": test_id})
