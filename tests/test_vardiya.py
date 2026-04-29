"""
Vardiya Modülü Testleri (v8.0.0)
Kapsam: bit-mask encode/decode, vardiya format, modül syntax,
        Anayasa kuralları (durum geçişleri, maker/checker).
"""
import ast
import pathlib
import pytest


VARDIYA_DOSYALARI = [
    "modules/vardiya/logic.py",
    "modules/vardiya/ui.py",
    "logic/vardiya_helper.py",
    "ui/ayarlar/vardiya_tipleri_ui.py",
]


@pytest.mark.parametrize("dosya", VARDIYA_DOSYALARI)
def test_derleme_kontrolu(dosya):
    """Tüm vardiya dosyaları AST olarak parse edilebilmeli."""
    kaynak = pathlib.Path(dosya).read_text(encoding="utf-8")
    ast.parse(kaynak)


def test_durum_gecisler_mevcut():
    """Anayasa: TASLAK -> ONAY BEKLIYOR -> ONAYLANDI durumları kod içinde tanımlı."""
    kaynak = pathlib.Path("modules/vardiya/logic.py").read_text(encoding="utf-8")
    for durum in ["TASLAK", "ONAY BEKLIYOR", "ONAYLANDI"]:
        assert durum in kaynak, f"Durum kodu eksik: {durum}"


def test_maker_checker_zorunlulugu():
    """Anayasa: Veriyi giren != onaylayan. Logic'te onaylayan kontrolü var."""
    kaynak = pathlib.Path("modules/vardiya/logic.py").read_text(encoding="utf-8")
    assert "onaylayan" in kaynak.lower(), "Maker/Checker mekanizması bulunamadı"


# ─── v8.0: Bit-Mask Tests ───────────────────────────────────────────────────
def test_bitmask_encode_tek_gun():
    from logic.vardiya_helper import izin_encode
    assert izin_encode(['Pzt']) == 1
    assert izin_encode(['Paz']) == 64


def test_bitmask_encode_coklu_gun():
    from logic.vardiya_helper import izin_encode
    assert izin_encode(['Pzt', 'Sal']) == 3
    assert izin_encode(['Cmt', 'Paz']) == 96
    assert izin_encode(['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']) == 127


def test_bitmask_encode_bos():
    from logic.vardiya_helper import izin_encode
    assert izin_encode([]) == 0
    assert izin_encode(None) == 0


def test_bitmask_encode_bilinmeyen_gun():
    """Bilinmeyen kısaltma yoksayılır, hata fırlatmaz."""
    from logic.vardiya_helper import izin_encode
    assert izin_encode(['Pzt', 'XXX']) == 1


def test_bitmask_decode():
    from logic.vardiya_helper import izin_decode
    assert izin_decode(1) == ['Pzt']
    assert izin_decode(3) == ['Pzt', 'Sal']
    assert izin_decode(64) == ['Paz']
    assert izin_decode(0) == []
    assert izin_decode(127) == ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']


def test_bitmask_str():
    """izin_str: bit-mask -> kısa kullanıcı dostu string."""
    from logic.vardiya_helper import izin_str
    assert izin_str(0) == "-"
    assert izin_str(1) == "Pzt"
    assert izin_str(3) == "Pzt, Sal"
    assert izin_str(64) == "Paz"


def test_bitmask_str_tam():
    """izin_str_tam: bit-mask -> tam Türkçe gün ismi."""
    from logic.vardiya_helper import izin_str_tam
    assert izin_str_tam(0) == "-"
    assert izin_str_tam(1) == "Pazartesi"
    assert izin_str_tam(3) == "Pazartesi, Salı"
    assert izin_str_tam(64) == "Pazar"


def test_gun_izinli_mi():
    """weekday() ile bit-mask kontrol."""
    from logic.vardiya_helper import gun_izinli_mi
    assert gun_izinli_mi(1, 0) is True   # Pzt biti, Pzt günü
    assert gun_izinli_mi(1, 1) is False  # Pzt biti, Sal günü
    assert gun_izinli_mi(64, 6) is True  # Paz biti, Paz günü
    assert gun_izinli_mi(127, 3) is True # Tüm bitler, Per günü
    assert gun_izinli_mi(0, 0) is False  # Hiç bit yok


def test_encode_decode_roundtrip():
    """encode -> decode aynı liste vermeli (sıralı)."""
    from logic.vardiya_helper import izin_encode, izin_decode
    gunler = ['Pzt', 'Çar', 'Cum']
    bm = izin_encode(gunler)
    assert sorted(izin_decode(bm)) == sorted(gunler)


# ─── v8.0: Vardiya Format Tests ─────────────────────────────────────────────
def test_saat_dogrula_dogru():
    from logic.vardiya_helper import saat_dogrula
    assert saat_dogrula("07:00") is True
    assert saat_dogrula("23:59") is True
    assert saat_dogrula("00:00") is True


def test_saat_dogrula_yanlis():
    from logic.vardiya_helper import saat_dogrula
    assert saat_dogrula("7:0") is False
    assert saat_dogrula("24:00") is False
    assert saat_dogrula("12:60") is False
    assert saat_dogrula("") is False
    assert saat_dogrula(None) is False


def test_vardiya_dogrula():
    from logic.vardiya_helper import vardiya_dogrula
    assert vardiya_dogrula("07:00-15:00") is True
    assert vardiya_dogrula("23:00-07:00") is True
    assert vardiya_dogrula("GÜNDÜZ") is False
    assert vardiya_dogrula("07:00") is False


def test_vardiya_olustur():
    from logic.vardiya_helper import vardiya_olustur
    assert vardiya_olustur("07:00", "15:00") == "07:00-15:00"
    with pytest.raises(ValueError):
        vardiya_olustur("7:0", "15:00")


# ─── v8.0: Migration Sözdizimi ──────────────────────────────────────────────
def test_migration_dosyasi_parse_edilebilir():
    """Migration dosyası AST olarak parse edilmeli."""
    kaynak = pathlib.Path(
        "migrations/20260429_v8_vardiya_saat_format.py"
    ).read_text(encoding="utf-8")
    ast.parse(kaynak)


def test_migration_kritik_fonksiyonlar():
    """Migration'da beklenen iç fonksiyonlar mevcut olmalı."""
    kaynak = pathlib.Path(
        "migrations/20260429_v8_vardiya_saat_format.py"
    ).read_text(encoding="utf-8")
    for fn in ["_adim_1_yedek_tablo", "_adim_2_off_sil",
               "_adim_3_vardiya_tipleri_seed", "_adim_4_vardiya_donusum",
               "_adim_5_izin_gunleri_bitmask", "_adim_6_plan_tipi_kolon",
               "migrate"]:
        assert fn in kaynak, f"Migration fonksiyonu eksik: {fn}"


def test_migration_donusum_haritasi():
    """Migration GÜNDÜZ -> 07:00-15:00 dönüşümünü tanımlamalı."""
    kaynak = pathlib.Path(
        "migrations/20260429_v8_vardiya_saat_format.py"
    ).read_text(encoding="utf-8")
    assert "07:00-15:00" in kaynak
    assert "15:00-23:00" in kaynak
    assert "23:00-07:00" in kaynak


# ─── v8.0: GUNLUK Plan Tipi Tests (S8-c) ────────────────────────────────────
def test_haftalik_records_tek_kayit_per_personel():
    """HAFTALIK plan: her personel için TEK kayıt."""
    from modules.vardiya.ui import _haftalik_records
    import pandas as pd
    from datetime import date
    df = pd.DataFrame([
        {'id': 1, 'vardiya': '07:00-15:00', 'aciklama': ''},
        {'id': 2, 'vardiya': '15:00-23:00', 'aciklama': ''},
    ])
    records = _haftalik_records(df, date(2026, 4, 27), date(2026, 5, 3), 3, "TASLAK")
    assert len(records) == 2
    assert all(r['plan_tipi'] == 'HAFTALIK' for r in records)
    assert records[0]['izin_gunleri'] == 3


def test_gunluk_records_her_gun_ayri_kayit():
    """GUNLUK plan: tarih aralığındaki her gün için ayrı kayıt."""
    from modules.vardiya.ui import _gunluk_records
    import pandas as pd
    from datetime import date
    df = pd.DataFrame([{'id': 1, 'vardiya': '07:00-15:00', 'aciklama': ''}])
    # 7 günlük aralık, izin yok → 7 kayıt
    records = _gunluk_records(df, date(2026, 4, 27), date(2026, 5, 3), 0, "TASLAK")
    assert len(records) == 7
    assert all(r['plan_tipi'] == 'GUNLUK' for r in records)


def test_gunluk_records_izin_gununu_atlar():
    """GUNLUK plan: bit-mask ile işaretli günlerde kayıt yazılmaz."""
    from modules.vardiya.ui import _gunluk_records
    import pandas as pd
    from datetime import date
    df = pd.DataFrame([{'id': 1, 'vardiya': '07:00-15:00', 'aciklama': ''}])
    # 27 Nisan 2026 = Pazartesi (weekday=0)
    # bit-mask 1 (Pzt) → Pzt günü atlanır → 6 kayıt (Sal-Paz)
    records = _gunluk_records(df, date(2026, 4, 27), date(2026, 5, 3), 1, "TASLAK")
    assert len(records) == 6


def test_gunluk_records_coklu_personel():
    """GUNLUK plan: N personel × M çalışma günü = N*M kayıt."""
    from modules.vardiya.ui import _gunluk_records
    import pandas as pd
    from datetime import date
    df = pd.DataFrame([
        {'id': 1, 'vardiya': '07:00-15:00', 'aciklama': ''},
        {'id': 2, 'vardiya': '15:00-23:00', 'aciklama': ''},
        {'id': 3, 'vardiya': '23:00-07:00', 'aciklama': ''},
    ])
    # 7 gün, 3 personel, hiç izin yok → 21 kayıt
    records = _gunluk_records(df, date(2026, 4, 27), date(2026, 5, 3), 0, "ONAY BEKLIYOR")
    assert len(records) == 21
    # Her personelin 7 kaydı olmalı
    p1_count = sum(1 for r in records if r['personel_id'] == 1)
    assert p1_count == 7
