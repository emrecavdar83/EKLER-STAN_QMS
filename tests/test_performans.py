# tests/test_performans.py
import pytest
import sys
import os

# Modül yolunu ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.performans.performans_hesap import (
    mesleki_ortalama_hesapla,
    kurumsal_ortalama_hesapla,
    agirlikli_toplam_hesapla,
    polivalans_duzeyi_belirle
)

def test_agirlikli_puan_hesabi():
    # Mesleki ort. = 75, Kurumsal ort. = 85
    # Beklenen: 75*0.70 + 85*0.30 = 52.5 + 25.5 = 78.0
    result = agirlikli_toplam_hesapla(75.0, 85.0)
    assert result == 78.0

def test_polivalans_sinir_degerler():
    # 45 tam eşiği (Kod 2 olmalı)
    assert polivalans_duzeyi_belirle(45.0)["kod"] == 2
    # 44.9 (Kod 1 olmalı)
    assert polivalans_duzeyi_belirle(44.9)["kod"] == 1
    # 100 (Kod 5 olmalı)
    assert polivalans_duzeyi_belirle(100.0)["kod"] == 5

def test_eksik_kriter_hesabi():
    # Mesleki kriterlerden bazıları None ise kalanlar üzerinden ortalama almalı
    puanlar = {
        "kkd_kullanimi": 100,
        "mesleki_kriter_2": 100,
        "mesleki_kriter_3": None,
        "mesleki_kriter_4": None
    }
    # Ortalama 100 olmalı (Ağırlıklandırılmamış hali)
    # mesleki_puan = 100 * 0.7 = 70.0
    res = mesleki_ortalama_hesapla(puanlar)
    assert res == 70.0

def test_kurumsal_eksik_kriter():
    puanlar = {
        "calisma_saatleri_uyum": 50,
        "ogrenme_kabiliyeti": 50,
        "iletisim_becerisi": None
    }
    # Ortalama 50 -> 50 * 0.30 = 15.0
    res = kurumsal_ortalama_hesapla(puanlar)
    assert res == 15.0
