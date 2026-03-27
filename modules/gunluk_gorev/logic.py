import pandas as pd
from sqlalchemy import text
from datetime import datetime

# EKLERİSTAN A.Ş. 
# Builder Backend Ajanı Tarafından Python Logic Katmanı (Max 30 Satır/Fonksiyon kuralına uygun)

def gorev_katalogu_getir(engine):
    """Tanımlı günlük görevleri getirir."""
    with engine.connect() as conn:
        return pd.read_sql(text("SELECT * FROM gunluk_gorev_katalogu WHERE aktif_mi = 1"), conn)

def periyodik_gorev_ata(engine, atama_listesi):
    """
    Toplu görev ataması yapar. atama_listesi: dict listesi
    [{'personel_id': 1, 'bolum_id': None, 'gorev_kaynagi': 'PERIYODIK', 'kaynak_id': 5, 'atanma_tarihi': '2026-03-27', 'hedef_tarih': '2026-03-27'}]
    """
    with engine.begin() as conn:
        for atama in atama_listesi:
            try:
                conn.execute(text("""
                    INSERT INTO birlesik_gorev_havuzu 
                    (personel_id, bolum_id, gorev_kaynagi, kaynak_id, atanma_tarihi, hedef_tarih, durum)
                    VALUES (:pid, :bid, :gk, :kid, :at, :ht, 'BEKLIYOR')
                """), {
                    "pid": atama['personel_id'], "bid": atama.get('bolum_id'), "gk": atama['gorev_kaynagi'],
                    "kid": atama['kaynak_id'], "at": atama['atanma_tarihi'], "ht": atama['hedef_tarih']
                })
            except Exception as e:
                # UNIQUE kısıtlamasından dolayı mükerrer olanları yoksayar (Fail-silent)
                pass

def gorev_tamamla(engine, havuz_id, personel_id, sapma_notu=""):
    """Görevi tamamlar ve Akıllı Akış ise akışı da tetikler."""
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE birlesik_gorev_havuzu 
            SET durum = 'TAMAMLANDI', tamamlanma_tarihi = CURRENT_TIMESTAMP, sapma_notu = :not
            WHERE id = :hid AND personel_id = :pid AND durum = 'BEKLIYOR'
        """), {"hid": havuz_id, "pid": personel_id, "not": sapma_notu})
        
        # Eğer bu bir AKILLI_AKIS görevi olsaydı, kaynak_id'yi flow_manager'da trigger_next_step ile tetikleyebilirdik.
        # Flow Manager çift yönlü iletişimi burada aktif edilebilir.

def personel_gorev_getir(engine, personel_id, tarih):
    """Bir personelin belirli bir gündeki (hedef_tarih) görevlerini getirir."""
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT b.*, k.ad as gorev_adi, k.kategori 
            FROM birlesik_gorev_havuzu b
            LEFT JOIN gunluk_gorev_katalogu k ON b.kaynak_id = k.id AND b.gorev_kaynagi = 'PERIYODIK'
            WHERE b.personel_id = :pid AND b.hedef_tarih = :tarih
            ORDER BY b.durum ASC
        """), conn, params={"pid": personel_id, "tarih": tarih})

def yonetici_matris_getir(engine, tarih, bolum_id=None):
    """Tüm personelin o günkü matrisini döndürür."""
    with engine.connect() as conn:
        # PANDAS pivot_table ile UI tarafında matrisleştirmek üzere ham veriyi çeker
        q = """
            SELECT b.*, p.ad_soyad, k.ad as gorev_adi
            FROM birlesik_gorev_havuzu b
            JOIN personel p ON b.personel_id = p.id
            LEFT JOIN gunluk_gorev_katalogu k ON b.kaynak_id = k.id AND b.gorev_kaynagi = 'PERIYODIK'
            WHERE b.hedef_tarih = :tarih
        """
        if bolum_id:
            q += f" AND (p.bolum_id = {bolum_id} OR b.bolum_id = {bolum_id})"
            
        return pd.read_sql(text(q), conn, params={"tarih": tarih})

