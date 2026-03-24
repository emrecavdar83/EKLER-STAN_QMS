"""
EKLERİSTAN QDMS — Görev Kartı (GK) Mantıksal Validasyon Modülü
BRCGS/IFS Gıda Güvenliği Standartları Uyumluluk Kontrolü
"""

ZORUNLU_DISIPLINLER = {
    'personel': '👥 Personel Yönetimi',
    'operasyon': '⚙️ Operasyonel Gereklilikler',
    'gida_guvenligi': '🛡️ Gıda Güvenliği & Kalite',
    'isg': '👷 İş Sağlığı ve Güvenliği',
    'cevre': '🌱 Çevre Gereklilikleri'
}

DISIPLIN_FALLBACK_TEXT = {
    'personel': "Bu pozisyonun doğrudan personel yönetim sorumluluğu bulunmamaktadır.",
    'operasyon': "Bu pozisyonun rutin dışı operasyonel bir gerekliliği bulunmamaktadır.",
    'gida_guvenligi': "Bu pozisyon gıda güvenliği ekibi üyesi değildir ancak genel hijyen kurallarına uymakla yükümlüdür.",
    'isg': "Bu pozisyonun özel bir İSG risk alanı yoktur, genel kurallar geçerlidir.",
    'cevre': "Bu pozisyonun doğrudan çevre kirliliği veya atık yönetimi etkisi bulunmamaktadır."
}

def gk_icerik_dogrula(gk_data) -> dict:
    """
    Görev kartındaki 5 disiplinin de doldurulup doldurulmadığını denetler.
    Eksik alan varsa hata listesi döner.
    """
    hata_listesi = []
    sorumluluklar = gk_data.get('sorumluluklar', [])
    
    # Mevcut disiplinleri haritala
    mevcut_tipler = {s.get('disiplin_tipi') for s in sorumluluklar if s.get('sorumluluk','').strip()}
    
    for d_tip, d_label in ZORUNLU_DISIPLINLER.items():
        if d_tip not in mevcut_tipler:
            oneri = DISIPLIN_FALLBACK_TEXT.get(d_tip, "Veri girilmelidir.")
            hata_listesi.append({
                "disiplin": d_label,
                "hata": f"{d_label} alanı boş bırakılamaz.",
                "oneri": oneri
            })
            
    return {
        "gecerli": len(hata_listesi) == 0,
        "hatalar": hata_listesi
    }
