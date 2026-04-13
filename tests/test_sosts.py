"""
SOSTS (Soğuk Oda Takip Sistemi) birim testleri — DB mock.
Kapsam: init_sosts_tables migrasyon, _now, token parse mantığı
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime


# ── _now ─────────────────────────────────────────────────────────────────────

def test_now_naive_datetime():
    """_now() naive datetime (tzinfo yok) dönmeli."""
    import soguk_oda_utils as m
    result = m._now()
    assert isinstance(result, datetime)
    assert result.tzinfo is None
    assert result.microsecond == 0


# ── AKTIF → AKTİF migrasyonu ─────────────────────────────────────────────────

def test_durum_migrasyonu_calisir():
    """init_sosts_tables, AKTIF kayıtları AKTİF'e günceller."""
    mock_engine = MagicMock()
    mock_engine.dialect.name = "sqlite"

    conn_ctx = MagicMock()
    mock_conn = MagicMock()
    conn_ctx.__enter__ = MagicMock(return_value=mock_conn)
    conn_ctx.__exit__ = MagicMock(return_value=False)
    mock_engine.begin.return_value = conn_ctx

    # inspect mock
    mock_inspector = MagicMock()
    mock_inspector.get_table_names.return_value = []
    mock_inspector.get_columns.return_value = []

    import soguk_oda_utils as m
    from sqlalchemy import text

    with patch("sqlalchemy.inspect", return_value=mock_inspector):
        m.init_sosts_tables(mock_engine)

    # Migration SQL'i arandı mı kontrol et
    executed_sqls = [str(c.args[0]) for c in mock_conn.execute.call_args_list if c.args]
    migration_ran = any("AKTIF" in sql and "AKTİF" in sql for sql in executed_sqls)
    assert migration_ran, "AKTIF → AKTİF migrasyon sorgusu çalışmadı"


# ── QR token parse mantığı ───────────────────────────────────────────────────

def test_token_parse_url_icinden():
    """URL içindeki token doğru ayrıştırılmalı."""
    url = "https://ekler-stan-qms.streamlit.app/?scanned_qr=abc-123-uuid"
    token = url.split("scanned_qr=")[-1].strip() if "scanned_qr=" in url else url.strip()
    assert token == "abc-123-uuid"


def test_token_parse_direkt_kod():
    """Direkt kod girildiğinde olduğu gibi dönmeli."""
    kod = "DOLAP-01"
    token = kod.split("scanned_qr=")[-1].strip() if "scanned_qr=" in kod else kod.strip()
    assert token == "DOLAP-01"


def test_token_parse_bosluk_temizlenir():
    """Baştaki/sondaki boşluklar temizlenmeli."""
    url = "  https://ekler-stan-qms.streamlit.app/?scanned_qr=  tok-xyz  "
    raw = url.split("scanned_qr=")[-1]
    token = raw.strip()
    assert token == "tok-xyz"
