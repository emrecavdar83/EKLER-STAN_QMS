import ast
import pathlib
import pytest

VARDIYA_DOSYALARI = [
    "modules/vardiya/logic.py",
    "modules/vardiya/ui.py",
]

@pytest.mark.parametrize("dosya", VARDIYA_DOSYALARI)
def test_derleme_kontrolu(dosya):
    kaynak = pathlib.Path(dosya).read_text(encoding="utf-8")
    ast.parse(kaynak)

def test_durum_gecisler_mevcut():
    """Anayasa: TASLAK → ONAY BEKLIYOR → ONAYLANDI durumları kod içinde tanımlı."""
    kaynak = pathlib.Path("modules/vardiya/logic.py").read_text(encoding="utf-8")
    for durum in ["TASLAK", "ONAY BEKLIYOR", "ONAYLANDI"]:
        assert durum in kaynak, f"Durum kodu eksik: {durum}"

def test_maker_checker_zorunlulugu():
    """Anayasa: Veriyi giren ≠ onaylayan. Logic dosyasında kontrol mevcut olmalı."""
    kaynak = pathlib.Path("modules/vardiya/logic.py").read_text(encoding="utf-8")
    assert "onaylayan" in kaynak.lower(), "Maker/Checker mekanizması bulunamadı"
