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

def test_guvenli_coklu_kayit_ekle_delete_before_insert():
    """guvenli_coklu_kayit_ekle fonksiyonunun kayıttan önce eski kayıtları temizlediği test edilir."""
    from logic.db_writer import guvenli_coklu_kayit_ekle
    
    with patch("database.connection.get_engine") as mock_get_engine:
        # Mock connection and transaction setup
        mock_conn = mock_get_engine.return_value.begin.return_value.__enter__.return_value
        
        # Test verisi: tarih, saat, kullanici, vardiya, bolum, personel, durum, sebep, aksiyon
        veri_listesi = [
            ["2026-06-15", "09:27", "test_user", "07:00-15:00", "BOMBA", "YELİZ ÇAKIR", "Gelmedi", "Habersiz Gelmedi", "İK Bilgilendirildi"]
        ]
        
        # Mock execution returning ID
        mock_res = mock_conn.execute.return_value
        mock_res.fetchone.return_value = [1] # id = 1
        
        with patch("logic.db_writer.log_field_change") as mock_log:
            res = guvenli_coklu_kayit_ekle("Hijyen_Kontrol_Kayitlari", veri_listesi)
            
            assert res is True
            # DELETE sql sorgusunun çağrıldığı doğrulanır
            calls = mock_conn.execute.call_args_list
            delete_called = False
            for call in calls:
                sql_obj = call[0][0]
                if "DELETE FROM hijyen_kontrol_kayitlari" in str(sql_obj):
                    delete_called = True
                    # Parametre doğrulaması
                    params = call[0][1]
                    assert params["t"] == "2026-06-15"
                    assert params["v"] == "07:00-15:00"
                    assert params["b"] == "BOMBA"
            
            assert delete_called is True
