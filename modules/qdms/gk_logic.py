"""
EKLERİSTAN QDMS — Görev Kartı (GK) Mantık Katmanı
Pozisyon tanımları ve periyodik görev otomasyonu
"""
import json
from sqlalchemy import text
from modules.qdms.belge_kayit import _exec_commit

def gk_kaydet(db_engine, veri: dict) -> dict:
    """
    Görev Kartı verilerini veritabanına kaydeder (v3.5: SQLAlchemy 2.0 Uyumlu).
    """
    # 1. Connection ve Transaction yönetimi (Anayasa 13. Adam)
    with db_engine.connect() as conn:
        with conn.begin():
            try:
                # v3.5: Cross-DB Upsert Strategy (DELETE then INSERT)
                conn.execute(text("DELETE FROM qdms_gorev_karti WHERE belge_kodu = :bk"), {"bk": veri['belge_kodu']})
                
                sql_main = text("""
                    INSERT INTO qdms_gorev_karti (
                        belge_kodu, pozisyon_adi, departman, bagli_pozisyon, vekalet_eden,
                        zone, vardiya_turu, gorev_ozeti, finansal_yetki_tl, imza_yetkisi,
                        vekalet_kosullari, min_egitim, min_deneyim_yil, zorunlu_sertifikalar,
                        tercihli_nitelikler, olusturan_id, guncelleme_ts
                    ) VALUES (
                        :bk, :pa, :dep, :bp, :ve, :zn, :vt, :go, :fy, :iy, :vk, :me, :md, :zs, :tn, :oid, CURRENT_TIMESTAMP
                    )
                """)
                
                params = {
                    "bk": veri['belge_kodu'], "pa": veri['pozisyon_adi'], "dep": veri['departman'],
                    "bp": veri.get('bagli_pozisyon'), "ve": veri.get('vekalet_eden'),
                    "zn": veri.get('zone', 'mgt'), "vt": veri.get('vardiya_turu'),
                    "go": veri['gorev_ozeti'], "fy": veri.get('finansal_yetki_tl'),
                    "iy": veri.get('imza_yetkisi'), "vk": veri.get('vekalet_kosullari'),
                    "me": veri.get('min_egitim'), "md": veri.get('min_deneyim_yil', 0),
                    "zs": json.dumps(veri.get('zorunlu_sertifikalar', [])),
                    "tn": veri.get('tercihli_nitelikler'), "oid": veri.get('olusturan_id')
                }
                
                conn.execute(sql_main, params)
                
                bk = veri['belge_kodu']
                conn.execute(text("DELETE FROM qdms_gk_sorumluluklar WHERE belge_kodu = :bk"), {"bk": bk})
                for s in veri.get('sorumluluklar', []):
                    sql_sor = text("""
                        INSERT INTO qdms_gk_sorumluluklar (
                            belge_kodu, kategori, disiplin_tipi, sira_no, sorumluluk, etkilesim_birimleri, sertifikasyon
                        ) VALUES (
                            :bk, :kat, :dt, :sn, :sor, :eb, :ser
                        )
                    """)
                    conn.execute(sql_sor, {
                        "bk": bk, "kat": s.get('kategori'), "dt": s.get('disiplin_tipi'),
                        "sn": s['sira_no'], "sor": s['sorumluluk'], 
                        "eb": s.get('etkilesim_birimleri'), "ser": s.get('sertifikasyon')
                    })
                    
                conn.execute(text("DELETE FROM qdms_gk_etkilesim WHERE belge_kodu = :bk"), {"bk": bk})
                for e in veri.get('etkilesimler', []):
                    conn.execute(text("INSERT INTO qdms_gk_etkilesim (belge_kodu, taraf, konu, siklik, raci_rol) VALUES (:bk, :tar, :kon, :sik, :rac)"),
                                {"bk": bk, "tar": e['taraf'], "kon": e['konu'], "sik": e['siklik'], "rac": e['raci_rol']})
                    
                conn.execute(text("DELETE FROM qdms_gk_periyodik_gorevler WHERE belge_kodu = :bk"), {"bk": bk})
                for g in veri.get('periyodik_gorevler', []):
                    conn.execute(text("INSERT INTO qdms_gk_periyodik_gorevler (belge_kodu, gorev_adi, periyot, talimat_kodu, sertifikasyon_maddesi, onay_gerekli) VALUES (:bk, :ga, :per, :tk, :sm, :og)"),
                                {"bk": bk, "ga": g['gorev_adi'], "per": g['periyot'], "tk": g.get('talimat_kodu'), "sm": g.get('sertifikasyon_maddesi'), "og": g.get('onay_gerekli', 0)})
                    
                conn.execute(text("DELETE FROM qdms_gk_kpi WHERE belge_kodu = :bk"), {"bk": bk})
                for k in veri.get('kpi_listesi', []):
                    conn.execute(text("INSERT INTO qdms_gk_kpi (belge_kodu, kpi_adi, olcum_birimi, hedef_deger, degerlendirme_periyodu, degerlendirici) VALUES (:bk, :ka, :ob, :hd, :dp, :der)"),
                                {"bk": bk, "ka": k['kpi_adi'], "ob": k['olcum_birimi'], "hd": k.get('hedef_deger'), "dp": k['degerlendirme_periyodu'], "der": k['degerlendirici']})
                    
                return {"basarili": True}
            except Exception as e:
                return {"basarili": False, "hata": str(e)}

def gk_getir(db_engine, belge_kodu: str) -> dict:
    """Görev kartı verilerini SQLAlchemy 2.0 ile getirir."""
    with db_engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM qdms_gorev_karti WHERE belge_kodu = :bk"), {"bk": belge_kodu}).fetchone()
        if not res: return None
        
        data = dict(res._mapping)
        data['zorunlu_sertifikalar'] = json.loads(data['zorunlu_sertifikalar'])
        
        # Alt tablolar
        data['sorumluluklar'] = [dict(r._mapping) for r in conn.execute(text("SELECT * FROM qdms_gk_sorumluluklar WHERE belge_kodu = :bk ORDER BY sira_no"), {"bk": belge_kodu}).fetchall()]
        data['etkilesimler'] = [dict(r._mapping) for r in conn.execute(text("SELECT * FROM qdms_gk_etkilesim WHERE belge_kodu = :bk"), {"bk": belge_kodu}).fetchall()]
        data['periyodik_gorevler'] = [dict(r._mapping) for r in conn.execute(text("SELECT * FROM qdms_gk_periyodik_gorevler WHERE belge_kodu = :bk"), {"bk": belge_kodu}).fetchall()]
        data['kpi_listesi'] = [dict(r._mapping) for r in conn.execute(text("SELECT * FROM qdms_gk_kpi WHERE belge_kodu = :bk"), {"bk": belge_kodu}).fetchall()]
        
        return data

def gorev_karti_onayla(db_conn, belge_kodu: str, onay_verildi: bool = False) -> dict:
    """
    Görev Kartı aktife alınırken:
    1. QDMS durum -> 'aktif' (belge_kayit üzerinden yapilmali)
    2. Personele bağlıysa periyodik görevleri aktar
    13. Adam: onay_verildi zorunlu — T2 işlem.
    """
    if not onay_verildi:
        return {'basarili': False, 'hata': 'T2 onayı zorunlu — onay_verildi=True olmalı.'}
    
    # İleride burada periyodik_gorevleri_aktar(engine, belge_kodu, personel_id) çağırılacak.
    return {"basarili": True, "mesaj": "Görev Kartı onaylandı (Otomatik görev atama pasif)."}

def periyodik_gorevleri_aktar(engine, belge_kodu: str, personel_id: int) -> dict:
    """
    PASİF (Kullanıcı Talebi: Aktif olarak kullanmayalım).
    İleride onaylandığında qdms_gk_periyodik_gorevler -> gorev_tanimlar aktarımı yapacak.
    """
    return {"basarili": True, "mesaj": "Otomatik görev atama şu an geliştirme aşamasındadır (Pasif)."}
