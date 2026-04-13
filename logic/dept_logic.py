from sqlalchemy import text
import pandas as pd
import json

def bolum_kodu_uret(engine, ust_id=None):
    """XX-YY formatında (Örn: UR-05) otomatik departman kodu üretir."""
    prefix = "GEN" # Varsayılan: Genel
    if ust_id and ust_id > 0:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT ad FROM qms_departmanlar WHERE id = :i"), {"i": ust_id}).fetchone()
            if res:
                ad = str(res[0]).upper()
                # Ana bölüm tespiti (İlk 2 harf)
                prefix = ad[:2] if len(ad) >= 2 else ad
    
    with engine.connect() as conn:
        res = conn.execute(text("SELECT MAX(id) FROM qms_departmanlar")).fetchone()
        next_id = (res[0] if res[0] else 0) + 1
    
    return f"{prefix}-{next_id:02d}"

def miras_tip_guncelle(engine, ust_id, yeni_tip_id):
    """Üst birim tipi değiştiğinde alt birimleri rekürsif olarak günceller (Madde 3 uyumlu)."""
    with engine.begin() as conn:
        # Alt birimlerin tipini güncelle
        sql = text("UPDATE qms_departmanlar SET tur_id = :t, guncelleme_tarihi = CURRENT_TIMESTAMP WHERE ust_id = :u")
        conn.execute(sql, {"t": yeni_tip_id, "u": ust_id})
        
        # Bir alt seviyeyi bul ve rekürsif ilerle
        res = conn.execute(text("SELECT id FROM qms_departmanlar WHERE ust_id = :u"), {"u": ust_id})
        children = [r[0] for r in res.fetchall()]
        
    for child_id in children:
        miras_tip_guncelle(engine, child_id, yeni_tip_id)

def pasife_al_ve_aktar(engine, dept_id, user_id=0):
    """Bölümü pasife almadan önce personeli üst birime aktarır (Madde 4)."""
    with engine.begin() as conn:
        # Üst birimi bul
        res = conn.execute(text("SELECT ust_id FROM qms_departmanlar WHERE id = :i"), {"i": dept_id}).fetchone()
        parent_id = res[0] if res else None
        
        if not parent_id:
            return False, "Kök departman pasife alınamaz (Üst birimi yok)."

        # 1. Personelleri aktar
        conn.execute(text("UPDATE personel SET qms_departman_id = :p WHERE qms_departman_id = :d"), 
                     {"p": parent_id, "d": dept_id})
        
        # 2. Bölümü pasife al
        conn.execute(text("UPDATE qms_departmanlar SET durum = 'PASİF', guncelleme_tarihi = CURRENT_TIMESTAMP WHERE id = :i"), 
                     {"i": dept_id})
        
    return True, "Bölüm pasife alındı, personeller üst amirliğe aktarıldı."

def matrix_kontrol(engine, dept_id, ikincil_ust_id):
    """Matrix bağlantısı için tür bazlı eşleşme kontrolü yapar (Madde 13)."""
    with engine.connect() as conn:
        sql = "SELECT tur_id FROM qms_departmanlar WHERE id IN (:d, :i)"
        res = conn.execute(text(sql), {"d": dept_id, "i": ikincil_ust_id}).fetchall()
        
    if len(res) < 2: return True # Veri bulunamadıysa geç
    return res[0][0] == res[1][0] # Türler aynı mı?

def hiyerarşi_kural_dogrula(engine, child_type_id, parent_id=None):
    """
    v5.8.3: Hiyerarşik Kısıtlamalar (Emre Bey'in talebi)
    parent_id None veya 0 ise 'KÖK' izin kontrolü yapılır.
    """
    with engine.connect() as conn:
        # 1. Kendi türümüzün kurallarını al
        c_res = conn.execute(text("SELECT tur_adi, kurallar_json FROM qms_departman_turleri WHERE id = :i"), {"i": child_type_id}).fetchone()
        if not c_res: return True, ""
        
        c_ad, c_rules_raw = c_res
        try:
            c_rules = json.loads(c_rules_raw) if c_rules_raw else {}
        except Exception:
            c_rules = {}

        # 2. Üst birim kontrolü
        if not parent_id or parent_id == 0:
            can_be_root = c_rules.get("can_be_root", True) # Varsayılan: Evet (Geriye dönük uyum)
            if not can_be_root:
                return False, f"⚠️ '{c_ad}' türündeki birimler en üst seviyede (Kök) olamaz. Lütfen bir üst birim seçin."
            return True, ""

        # 3. Üst birim türünü bul
        p_res = conn.execute(text("""
            SELECT t.id, t.tur_adi 
            FROM qms_departmanlar d 
            JOIN qms_departman_turleri t ON d.tur_id = t.id 
            WHERE d.id = :i
        """), {"i": parent_id}).fetchone()
        
        if not p_res: return True, "" # Üst birim var ama türü yoksa izin ver
        
        p_type_id, p_type_ad = p_res
        allowed_parents = c_rules.get("allowed_parent_types", []) # List of type IDs or Names
        
        if not allowed_parents:
            return True, "" # Kural tanımlanmamışsa herkes her yere bağlanabilir (Özgürlük)

        # ID veya İsim bazlı kontrol
        if p_type_id in allowed_parents or p_type_ad in allowed_parents:
            return True, ""
            
        return False, f"⚠️ '{c_ad}' türündeki bir birim, '{p_type_ad}' altına bağlanamaz. İzin verilen üst türler: {', '.join(map(str, allowed_parents))}"
