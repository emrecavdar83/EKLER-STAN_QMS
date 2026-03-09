import sys
import unittest.mock as mock

# Mock Streamlit to prevent it from crashing the test outside of server context.
st_mock = mock.MagicMock()
def mock_columns(spec):
    length = len(spec) if isinstance(spec, (list, tuple)) else spec
    return [mock.MagicMock() for _ in range(length)]
st_mock.columns.side_effect = mock_columns
st_mock.container.return_value.__enter__.return_value = mock.MagicMock()
st_mock.expander.return_value.__enter__.return_value = mock.MagicMock()
st_mock.form.return_value.__enter__.return_value = mock.MagicMock()
sys.modules['streamlit'] = st_mock
st_mock.session_state = {"nav_personel": "📅 Vardiya Çalışma Programı"}

from database.connection import get_engine
import ui.ayarlar.personel_ui as p_ui
from logic.data_fetcher import run_query

engine = get_engine()

print("--- TESTING SHADOW TABLES FETCHERS ---")
try:
    vardiya_list = p_ui._get_vardiya_tipleri()
    assert len(vardiya_list) >= 3, "Vardiya listesi boş!"

    izin_list = p_ui._get_izin_gun_tipleri()
    assert len(izin_list) >= 8, "İzin listesi boş!"
except Exception as e:
    sys.exit(1)

print("--- TESTING UI RENDER FUNCTIONS WITH MOCKS ---")
try:
    dept_mock = {1: "Üretim", 2: "Depo"}
    yonetici_mock = {1: "Ahmet Usta"}
    
    # Just test if calling them throws unhandled Exceptions.
    print("Test _render_vardiya_programi")
    st_mock.selectbox.return_value = 1  # select secilen_bolum_id = 1
    p_ui._render_vardiya_programi(engine, dept_mock)
    
    print("Test _render_personel_form")
    st_mock.radio.return_value = "➕ Yeni Personel Ekle"
    p_ui._render_personel_form(engine, dept_mock, yonetici_mock)

    print("Test _render_personel_listesi")
    p_ui._render_personel_listesi(engine, dept_mock, yonetici_mock)
    
    print("Test render_kullanici_tab")
    p_ui.render_kullanici_tab(engine)
    
    print("BASARILI: Butun UI render fonksiyonlari try-except zirhlariyla testten basariyla gecti.")
    
except Exception as e:
    import traceback
    with open("c:/Projeler/S_program/EKLERİSTAN_QMS/test_err.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
    print("❌ HATA DETAYLARI test_err.txt DOSYASINA YAZILDI")
    sys.exit(1)
