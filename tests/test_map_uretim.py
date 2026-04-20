import ast
import pathlib
import pytest

MAP_DOSYALARI = [
    "ui/map_uretim/map_db.py",
    "ui/map_uretim/map_uretim.py",
    "ui/map_uretim/map_hesap.py",
    "ui/map_uretim/map_rapor_pdf.py",
]

@pytest.mark.parametrize("dosya", MAP_DOSYALARI)
def test_derleme_kontrolu(dosya):
    """Her MAP dosyası hatasız derlenmeli."""
    kaynak = pathlib.Path(dosya).read_text(encoding="utf-8")
    ast.parse(kaynak)  # SyntaxError yoksa geçer

@pytest.mark.parametrize("dosya", MAP_DOSYALARI)
def test_global_st_cagri_yok(dosya):
    """Anayasa Madde 19: st.* çağrısı global scope'da olmaz."""
    kaynak = pathlib.Path(dosya).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Module):
            for ifade in dugum.body:
                assert not (
                    isinstance(ifade, ast.Expr) and
                    isinstance(getattr(ifade, 'value', None), ast.Call) and
                    hasattr(getattr(ifade.value, 'func', None), 'attr') and
                    getattr(ifade.value.func, 'id', '') == 'st'
                ), f"{dosya}: Global st.* çağrısı bulundu"

def test_map_db_kritik_fonksiyonlar():
    """map_db.py içinde beklenen kritik fonksiyonlar tanımlı olmalı."""
    kaynak = pathlib.Path("ui/map_uretim/map_db.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    fonksiyon_adlari = {d.name for d in ast.walk(agac) if isinstance(d, ast.FunctionDef)}
    beklenenler = ["aç_vardiya", "kapat_vardiya"]
    for beklenen in beklenenler:
        assert any(beklenen in f for f in fonksiyon_adlari), \
            f"Kritik fonksiyon bulunamadı: {beklenen}"
