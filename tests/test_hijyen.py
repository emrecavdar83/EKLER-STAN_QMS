"""
Personel Hijyen modülü birim testleri.
"""
import pytest
from unittest.mock import patch
from constants import get_hijyen_sebepleri, get_hijyen_aksiyonlari

def test_get_hijyen_sebepleri_fallback():
    """DB bağlantısı yokken veya parametre bulunamazsa fallback listesi dönmeli."""
    with patch("constants._get_db_param") as mock_get_param:
        # DB sorgusu başarısız olursa _get_db_param fallback'i döndürür
        mock_get_param.side_effect = lambda key, fallback: fallback
        
        # Test cache temizleme (mock öncesi cache'lenmiş olmasını önlemek için decorator'ı aşmak)
        # st.cache_data conftest.py'de mocklandığı için direkt çağrı yapılabilir.
        res = get_hijyen_sebepleri()
        
        assert "Yıllık İzin" in res["Gelmedi"]
        assert "Raporlu" in res["Gelmedi"]
        # Fallback listesinde Haftalık İzin olmamalıdır
        assert "Haftalık İzin" not in res["Gelmedi"]

def test_get_hijyen_sebepleri_dynamic():
    """DB bağlantısı varken ve parametre tanımlıyken dinamik liste (Haftalık İzin dahil) dönmeli."""
    mock_db_val = {
        "Gelmedi": ["Seçiniz...", "Yıllık İzin", "Raporlu", "Habersiz Gelmedi", "Ücretsiz İzin", "Haftalık İzin"],
        "Sağlık Riski": ["Seçiniz...", "Ateş", "İshal", "Öksürük", "Açık Yara", "Bulaşıcı Şüphe"],
        "Hijyen Uygunsuzluk": ["Seçiniz...", "Kirli Önlük", "Sakal Tıraşı", "Bone/Maske Eksik", "Yasaklı Takı"]
    }
    with patch("constants._get_db_param", return_value=mock_db_val):
        res = get_hijyen_sebepleri()
        
        assert "Haftalık İzin" in res["Gelmedi"]
        assert "Yıllık İzin" in res["Gelmedi"]
        assert len(res["Gelmedi"]) == 6

def test_get_hijyen_aksiyonlari_dynamic():
    """DB bağlantısı varken ve parametre tanımlıysa dinamik aksiyon listesi dönmeli."""
    mock_db_val = {
        "Gelmedi": ["İK Bilgilendirildi", "Tutanak Tutuldu", "Bilgi Dahilinde"],
        "Sağlık Riski": ["Üretim Md. Bilgi Verildi", "Eve Gönderildi", "Revire Yönlendirildi", "Maskeli Çalışıyor"],
        "Hijyen Uygunsuzluk": ["Personel Uyarıldı", "Uygunsuzluk Giderildi", "Eğitim Verildi"]
    }
    with patch("constants._get_db_param", return_value=mock_db_val):
        res = get_hijyen_aksiyonlari()
        
        assert "İK Bilgilendirildi" in res["Gelmedi"]
        assert "Eve Gönderildi" in res["Sağlık Riski"]
