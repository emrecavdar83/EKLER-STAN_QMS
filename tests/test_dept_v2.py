"""
dept_logic unit testleri — DB bağlantısı gerektirmez.
Tüm engine/connection çağrıları mock'lanmıştır.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from logic.dept_logic import bolum_kodu_uret, miras_tip_guncelle, pasife_al_ve_aktar


def _mock_engine(connect_results=None, begin_results=None):
    """Test engine factory: connect() ve begin() için kontrollü sonuçlar döner."""
    engine = MagicMock()

    # connect() context manager
    mock_conn = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    if connect_results:
        mock_conn.execute.side_effect = connect_results

    # begin() context manager
    mock_trans = MagicMock()
    engine.begin.return_value.__enter__ = MagicMock(return_value=mock_trans)
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    if begin_results:
        mock_trans.execute.side_effect = begin_results

    return engine, mock_conn, mock_trans


# ── bolum_kodu_uret ─────────────────────────────────────────────────────────

def test_bolum_kodu_uret_varsayilan():
    """ust_id verilmezse GEN- prefix kullanılır."""
    engine, conn, _ = _mock_engine()
    conn.execute.return_value.fetchone.return_value = (5,)  # MAX(id) = 5

    kod = bolum_kodu_uret(engine)

    assert kod == "GEN-06"


def test_bolum_kodu_uret_ust_id_ile():
    """Geçerli ust_id verildiğinde üst birimin ilk 2 harfi prefix olur."""
    engine, conn, _ = _mock_engine()

    # 1. çağrı: üst birimin adını döner, 2. çağrı: MAX(id) döner
    conn.execute.return_value.fetchone.side_effect = [
        ("ÜRETİM",),
        (4,),
    ]

    kod = bolum_kodu_uret(engine, ust_id=2)

    assert kod.startswith("ÜR-")
    assert kod == "ÜR-05"


def test_bolum_kodu_uret_ust_bulunamazsa_gen():
    """ust_id verilir ama DB'de bulunamazsa GEN- fallback kullanılır."""
    engine, conn, _ = _mock_engine()

    conn.execute.return_value.fetchone.side_effect = [
        None,   # üst birim yok
        (2,),   # MAX(id) = 2
    ]

    kod = bolum_kodu_uret(engine, ust_id=99)

    assert kod == "GEN-03"


# ── miras_tip_guncelle ──────────────────────────────────────────────────────

def test_miras_tip_guncelle_alt_birimsiz():
    """Alt birimi olmayan departmanda sadece UPDATE çalışır, rekürsyon yok."""
    engine, conn, trans = _mock_engine()
    trans.execute.return_value.fetchall.return_value = []  # alt birim yok

    miras_tip_guncelle(engine, ust_id=1, yeni_tip_id=2)

    # UPDATE çağrıldı mı?
    assert trans.execute.call_count == 2  # UPDATE + SELECT


def test_miras_tip_guncelle_rekursif():
    """Alt birimi olan departmanda rekürsif güncelleme yapılır."""
    engine = MagicMock()
    cagrı_sayaci = [0]

    def begin_factory():
        cagrı_sayaci[0] += 1
        trans = MagicMock()
        # 1. çağrı: child [10] döner → rekürsyon tetiklenir
        # 2. çağrı: child [] döner → rekürsyon durur
        if cagrı_sayaci[0] == 1:
            trans.execute.return_value.fetchall.return_value = [(10,)]
        else:
            trans.execute.return_value.fetchall.return_value = []
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=trans)
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    engine.begin.side_effect = begin_factory

    miras_tip_guncelle(engine, ust_id=1, yeni_tip_id=3)

    assert engine.begin.call_count == 2  # root + 1 child


# ── pasife_al_ve_aktar ───────────────────────────────────────────────────────

def test_pasife_al_ve_aktar_basarili():
    """Normal akış: personel üst birime taşınır, departman pasife alınır."""
    engine, conn, trans = _mock_engine()
    trans.execute.return_value.fetchone.return_value = (1,)  # ust_id = 1

    basarili, mesaj = pasife_al_ve_aktar(engine, dept_id=5)

    assert basarili is True
    assert "pasife alındı" in mesaj
    assert trans.execute.call_count == 3  # SELECT ust_id + UPDATE personel + UPDATE dept


def test_pasife_al_ve_aktar_kok_departman():
    """Kök departman (ust_id=None) pasife alınamaz."""
    engine, conn, trans = _mock_engine()
    trans.execute.return_value.fetchone.return_value = (None,)

    basarili, mesaj = pasife_al_ve_aktar(engine, dept_id=1)

    assert basarili is False
    assert "Kök departman" in mesaj


def test_pasife_al_ve_aktar_kayit_yoksa():
    """DB'de departman kaydı yoksa hata döner."""
    engine, conn, trans = _mock_engine()
    trans.execute.return_value.fetchone.return_value = None

    basarili, mesaj = pasife_al_ve_aktar(engine, dept_id=999)

    assert basarili is False
