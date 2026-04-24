"""
EKLERİSTAN QDMS — Şablon Motor
Format tanımlarını okur, doğrular, HTML şablonunu hazırlar
"""
import json
from sqlalchemy import text

VARSAYILAN_HEADER_CONFIG = {
    "logo": {"konum": "sol", "genislik_px": 180, "sirket_adi_goster": True, "sirket_adi": "EKLERİSTAN A.Ş."},
    "baslik_blok": {"konum": "merkez", "ana_baslik_font_px": 18, "alt_baslik_font_px": 13, "alt_baslik_renk": "#c0392b"},
    "kod_blok": {"konum": "sag", "belge_kodu_goster": True, "rev_goster": True, "baski_tarihi_goster": True, "baski_tarihi_format": "%d.%m.%Y %H:%M"}
}

VARSAYILAN_KOLON_CONFIG_SOGUK_ODA = [
    {"ad": "Aralık",   "genislik_yuzde": 8,  "tip": "zaman_dilimi", "bold": False},
    {"ad": "Saat",     "genislik_yuzde": 9,  "tip": "saat",         "bold": True},
    {"ad": "Değer",    "genislik_yuzde": 9,  "tip": "sicaklik",     "bold": False},
    {"ad": "Durum",    "genislik_yuzde": 12, "tip": "durum_badge",  "bold": False},
    {"ad": "Personel", "genislik_yuzde": 52, "tip": "personel_tam", "bold": False},
    {"ad": "Mühür",    "genislik_yuzde": 10, "tip": "saat_kopya",   "bold": False}
]

# v3.5: Görev Kartı (GK) Yapı Tanımı
VARSAYILAN_GK_YAPISI = {
    "bolumler": [
        {"no": 1, "ad": "Belge Kimliği",              "zorunlu": True},
        {"no": 2, "ad": "Pozisyon Profili",            "zorunlu": True},
        {"no": 3, "ad": "Görev Özeti",                 "zorunlu": True},
        {"no": 4, "ad": "Sorumluluk Alanları",         "zorunlu": True},
        {"no": 5, "ad": "Yetki Sınırları",             "zorunlu": True},
        {"no": 6, "ad": "Süreçler Arası Etkileşim",   "zorunlu": True},
        {"no": 7, "ad": "Periyodik Görev Listesi",     "zorunlu": True},
        {"no": 8, "ad": "Nitelik ve Yetkinlik",        "zorunlu": True},
        {"no": 9, "ad": "Performans Göstergeleri",     "zorunlu": False},
        {"no": 10,"ad": "Onay ve İmza",                "zorunlu": True},
    ],
    "sertifikasyon_maddeleri": [
        "BRC 1.1", "BRC 3.3", "BRC 3.5", "BRC 7.1",
        "IFS 3.3", "IFS 5.1", "IFS 6.1",
        "FSSC 22000 Md.5", "FSSC 22000 Md.9.2", "FSSC 22000 Md.9.3"
    ]
}

def kolon_genislik_dogrula(kolon_config: list) -> bool:
    """Toplam genişlik yüzde = 100 olmalı."""
    toplam = sum(k.get("genislik_yuzde", 0) for k in kolon_config)
    return abs(toplam - 100) < 0.01

def sablon_kaydet(db_conn, belge_kodu, rev_no, header_config, kolon_config, meta_panel_config, **kwargs):
    if not kolon_genislik_dogrula(kolon_config):
        return {"basarili": False, "hata": "Kolon genişlik toplamı %100 olmalıdır."}
    
    sql = text("""
        INSERT INTO qdms_sablonlar (belge_kodu, rev_no, header_config, kolon_config, meta_panel_config, sayfa_boyutu, sayfa_yonu, renk_tema, css_ek)
        VALUES (:kod, :rev, :hc, :kc, :mpc, :sb, :sy, :rt, :css)
    """)
    try:
        params = {
            "kod": belge_kodu, "rev": rev_no, 
            "hc": json.dumps(header_config), "kc": json.dumps(kolon_config), "mpc": json.dumps(meta_panel_config),
            "sb": kwargs.get('sayfa_boyutu', 'A4'), "sy": kwargs.get('sayfa_yonu', 'dikey'),
            "rt": json.dumps(kwargs.get('renk_tema', {})), "css": kwargs.get('css_ek', '')
        }
        if hasattr(db_conn, 'begin'):
            with db_conn.begin() as conn:
                conn.execute(sql, params)
        else:
            db_conn.execute(sql, params)
        return {"basarili": True}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def sablon_guncelle(db_conn, belge_kodu, rev_no, header_config, kolon_config, meta_panel_config, **kwargs):
    """Mevcut şablonu günceller."""
    if not kolon_genislik_dogrula(kolon_config):
        return {"basarili": False, "hata": "Kolon genişlik toplamı %100 olmalıdır."}
    
    sql = text("""
        UPDATE qdms_sablonlar 
        SET header_config = :hc, kolon_config = :kc, meta_panel_config = :mpc,
            sayfa_boyutu = :sb, sayfa_yonu = :sy, renk_tema = :rt, css_ek = :css
        WHERE belge_kodu = :kod AND rev_no = :rev
    """)
    try:
        params = {
            "kod": belge_kodu, "rev": rev_no, 
            "hc": json.dumps(header_config), "kc": json.dumps(kolon_config), "mpc": json.dumps(meta_panel_config),
            "sb": kwargs.get('sayfa_boyutu', 'A4'), "sy": kwargs.get('sayfa_yonu', 'dikey'),
            "rt": json.dumps(kwargs.get('renk_tema', {})), "css": kwargs.get('css_ek', '')
        }
        if hasattr(db_conn, 'begin'):
            with db_conn.begin() as conn:
                conn.execute(sql, params)
        else:
            db_conn.execute(sql, params)
        return {"basarili": True}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def sablon_getir(db_conn, belge_kodu, rev_no=None):
    if rev_no:
        sql = text("SELECT id, belge_kodu, rev_no, header_config, kolon_config, meta_panel_config, sayfa_boyutu, sayfa_yonu, renk_tema, css_ek, aktif, olusturma_tarihi FROM qdms_sablonlar WHERE belge_kodu = :kod AND rev_no = :rev")
        p = {"kod": belge_kodu, "rev": rev_no}
    else:
        sql = text("SELECT id, belge_kodu, rev_no, header_config, kolon_config, meta_panel_config, sayfa_boyutu, sayfa_yonu, renk_tema, css_ek, aktif, olusturma_tarihi FROM qdms_sablonlar WHERE belge_kodu = :kod AND aktif = 1 ORDER BY rev_no DESC LIMIT 1")
        p = {"kod": belge_kodu}
        
    if hasattr(db_conn, 'connect'):
        with db_conn.connect() as conn:
            res = conn.execute(sql, p).fetchone()
    else:
        res = db_conn.execute(sql, p).fetchone()
    
    if res:
        data = dict(res._mapping)
        data['header_config'] = json.loads(data['header_config'])
        data['kolon_config'] = json.loads(data['kolon_config'])
        data['meta_panel_config'] = json.loads(data['meta_panel_config'])
        return data
    return None

def sablon_html_olustur(sablon, veri):
    return f"<html><body><h1>{sablon['belge_kodu']}</h1><p>Veri: {len(veri.get('satirlar', []))} satir</p></body></html>"
