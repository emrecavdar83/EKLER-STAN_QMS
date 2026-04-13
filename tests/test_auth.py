"""
Auth modülü birim testleri — DB bağlantısı yok, tamamen mock.
Kapsam: sifre_hashle, sifre_dogrula, _bcrypt_formatinda_mi, _plaintext_fallback_izni_var_mi
"""
import pytest
from unittest.mock import patch, MagicMock


# ── Yardımcılar ──────────────────────────────────────────────────────────────

def _import_auth():
    """auth_logic'i her testte temiz import eder (cache sorunlarını önler)."""
    import importlib
    import logic.auth_logic as m
    return m


# ── _bcrypt_formatinda_mi ─────────────────────────────────────────────────────

def test_bcrypt_format_tespiti():
    m = _import_auth()
    assert m._bcrypt_formatinda_mi("$2b$12$abc") is True
    assert m._bcrypt_formatinda_mi("$2a$10$xyz") is True
    assert m._bcrypt_formatinda_mi("12345") is False
    assert m._bcrypt_formatinda_mi("") is False


# ── sifre_hashle ──────────────────────────────────────────────────────────────

def test_sifre_hashle_bcrypt_uretir():
    m = _import_auth()
    fake_hash = "$2b$12$fakehashabcdefghijklmnopqrstuvwx"
    with patch.object(m, "passlib_bcrypt") as mock_bcrypt:
        mock_bcrypt.hash.return_value = fake_hash
        h = m.sifre_hashle("test123")
    assert h == fake_hash
    assert m._bcrypt_formatinda_mi(h), "Hash bcrypt formatında olmalı"


def test_sifre_hashle_bos_none_doner():
    m = _import_auth()
    assert m.sifre_hashle("") is None
    assert m.sifre_hashle(None) is None


def test_sifre_hashle_uzun_sifre_kesilir():
    """72 karakterden uzun şifre 64 byte'a kesilip hashlenmeli."""
    m = _import_auth()
    fake_hash = "$2b$12$fakehashabcdefghijklmnopqrstuvwx"
    captured = {}
    def mock_hash(val):
        captured["val"] = val
        return fake_hash
    with patch.object(m, "passlib_bcrypt") as mock_bcrypt:
        mock_bcrypt.hash.side_effect = mock_hash
        h = m.sifre_hashle("A" * 100)
    # bcrypt'e giden şifre en fazla 64 byte olmalı
    assert len(captured.get("val", "").encode("utf-8")) <= 64
    assert h == fake_hash


# ── sifre_dogrula ─────────────────────────────────────────────────────────────

def test_sifre_dogrula_bcrypt_dogru():
    m = _import_auth()
    fake_hash = "$2b$12$fakehashabcdefghijklmnopqrstuvwx"
    with patch.object(m, "passlib_bcrypt") as mock_bcrypt:
        mock_bcrypt.verify.return_value = True
        result = m.sifre_dogrula("sifre456", fake_hash)
    assert result is True


def test_sifre_dogrula_bcrypt_yanlis():
    m = _import_auth()
    fake_hash = "$2b$12$fakehashabcdefghijklmnopqrstuvwx"
    with patch.object(m, "passlib_bcrypt") as mock_bcrypt:
        mock_bcrypt.verify.return_value = False
        result = m.sifre_dogrula("yanlis", fake_hash)
    assert result is False


def test_sifre_dogrula_plaintext_fallback_aktif():
    """Fallback aktifken plain-text karşılaştırma çalışmalı."""
    m = _import_auth()
    with patch.object(m, "_plaintext_fallback_izni_var_mi", return_value=True), \
         patch.object(m, "_sifreyi_hashle_ve_guncelle", return_value=True):
        assert m.sifre_dogrula("12345", "12345") is True
        assert m.sifre_dogrula("yanlis", "12345") is False


def test_sifre_dogrula_plaintext_fallback_kapali():
    """Fallback kapalıyken plain-text eşleşmesi reddedilmeli."""
    m = _import_auth()
    with patch.object(m, "_plaintext_fallback_izni_var_mi", return_value=False):
        assert m.sifre_dogrula("12345", "12345") is False


def test_sifre_dogrula_bos_db_sifre():
    m = _import_auth()
    assert m.sifre_dogrula("herhangi", "") is False
    assert m.sifre_dogrula("herhangi", None) is False
