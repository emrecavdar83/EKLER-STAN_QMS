# modules/performans/performans_hesap.py
from .performans_sabitleri import AGIRLIKLAR, POLIVALANS_ESLIKLERI, MESLEKI_KRITERLER, KURUMSAL_KRITERLER

def _ortalama_al(puanlar: dict, kriter_listesi: list) -> float:
    """Genel ortalama hesaplayıcı."""
    gecerli_puanlar = [puanlar[k] for k in kriter_listesi if k in puanlar and puanlar[k] is not None]
    if not gecerli_puanlar:
        return 0.0
    return sum(gecerli_puanlar) / len(gecerli_puanlar)

def mesleki_ortalama_hesapla(puanlar: dict) -> float:
    """Mesleki kriterlerin ham ortalamasını (0-100) hesaplar."""
    ort = _ortalama_al(puanlar, MESLEKI_KRITERLER)
    return round(ort, 2)

def kurumsal_ortalama_hesapla(puanlar: dict) -> float:
    """Kurumsal kriterlerin ham ortalamasını (0-100) hesaplar."""
    ort = _ortalama_al(puanlar, KURUMSAL_KRITERLER)
    return round(ort, 2)

def agirlikli_toplam_hesapla(mesleki_ort: float, kurumsal_ort: float) -> float:
    """Mesleki (%70) ve Kurumsal (%30) ağırlıkları uygulayarak toplam puanı hesaplar."""
    m_puan = mesleki_ort * AGIRLIKLAR["mesleki_teknik"]
    k_puan = kurumsal_ort * AGIRLIKLAR["kurumsal"]
    return round(m_puan + k_puan, 2)

def polivalans_duzeyi_belirle(toplam_puan: float) -> dict:
    """Puanı polivalans eşikleriyle eşleştirir."""
    for kod, veri in POLIVALANS_ESLIKLERI.items():
        if veri["min"] <= toplam_puan < veri["maks"]:
            return veri
    # 100 puan durumu (Üst sınır dahil değilse)
    if toplam_puan >= 100:
        return POLIVALANS_ESLIKLERI[5]
    return POLIVALANS_ESLIKLERI[1]

def yil_ortalama_hesapla(d1_puan: float, d2_puan: float | None) -> float:
    """Yıllık ortalamayı hesaplar."""
    if d2_puan is None:
        return d1_puan
    return round((d1_puan + d2_puan) / 2, 2)
