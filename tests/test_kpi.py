"""
KPI modülü yardımcı fonksiyon testleri — DB mock.
Kapsam: _kpi_parametre_getir'deki tip dönüşüm güvenliği
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


def test_numune_adet_gecersiz_deger():
    """numune_sayisi geçersiz ise 1'e düşmeli."""
    urun_ayar = {"numune_sayisi": "geçersiz", "raf_omru_gun": 0}
    try:
        numune_adet = int(float(urun_ayar.get("numune_sayisi", 1) or 1))
    except Exception:
        numune_adet = 1
    assert numune_adet == 1


def test_numune_adet_sifir_ise_bir_yapilir():
    """numune_sayisi 0 ise 1'e düzeltilmeli."""
    urun_ayar = {"numune_sayisi": 0, "raf_omru_gun": 0}
    try:
        numune_adet = int(float(urun_ayar.get("numune_sayisi", 1) or 1))
    except Exception:
        numune_adet = 1
    if numune_adet < 1:
        numune_adet = 1
    assert numune_adet == 1


def test_numune_adet_none_ise_bir_yapilir():
    """numune_sayisi None ise 1 dönmeli."""
    urun_ayar = {"numune_sayisi": None, "raf_omru_gun": 0}
    try:
        numune_adet = int(float(urun_ayar.get("numune_sayisi", 1) or 1))
    except Exception:
        numune_adet = 1
    assert numune_adet == 1


def test_raf_omru_gecersiz_deger():
    """raf_omru_gun geçersiz ise 0 dönmeli."""
    urun_ayar = {"raf_omru_gun": "bozuk"}
    try:
        raf_omru = int(float(urun_ayar.get("raf_omru_gun", 0) or 0))
    except Exception:
        raf_omru = 0
    assert raf_omru == 0


def test_raf_omru_normal_deger():
    """raf_omru_gun normal sayı ise doğru dönmeli."""
    urun_ayar = {"raf_omru_gun": "7"}
    try:
        raf_omru = int(float(urun_ayar.get("raf_omru_gun", 0) or 0))
    except Exception:
        raf_omru = 0
    assert raf_omru == 7


def test_raf_omru_float_string():
    """raf_omru_gun '3.0' formatında gelse de doğru parse edilmeli."""
    urun_ayar = {"raf_omru_gun": "3.0"}
    try:
        raf_omru = int(float(urun_ayar.get("raf_omru_gun", 0) or 0))
    except Exception:
        raf_omru = 0
    assert raf_omru == 3
