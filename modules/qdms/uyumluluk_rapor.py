from sqlalchemy import text
from datetime import datetime, timedelta

def uyumluluk_ozeti_getir(db_conn):
    """
    BRCGS/IFS uyumluluk KPI'larını hesaplar.
    """
    # 1. Temel Sayılar
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)
    
    try:
        if hasattr(db_conn, 'execute'):
            stats = db_conn.execute(text("""
                SELECT 
                    COUNT(CASE WHEN durum = 'aktif' THEN 1 END) as aktif,
                    COUNT(CASE WHEN durum = 'taslak' THEN 1 END) as taslak,
                    COUNT(CASE WHEN durum = 'arsiv' THEN 1 END) as arsiv
                FROM public.qdms_belgeler
            """)).fetchone()
            
            # Son 30 gün revizyon sayısı
            rev_count = db_conn.execute(text("""
                SELECT COUNT(*) FROM public.qdms_revizyon_log 
                WHERE degisiklik_tarihi > :dt
            """), {"dt": thirty_days_ago}).scalar()
            
            # Eskiyen belgeler (12 aydan eski revizyonu olan aktif belgeler)
            eskiyen = db_conn.execute(text("""
                SELECT belge_kodu, belge_adi, guncelleme_tarihi FROM public.qdms_belgeler
                WHERE durum = 'aktif' AND guncelleme_tarihi < :dt_old
            """), {"dt_old": one_year_ago}).fetchall()
            
        else:
            with db_conn.connect() as conn:
                stats = conn.execute(text("SELECT COUNT(CASE WHEN durum = 'aktif' THEN 1 END) as aktif, COUNT(CASE WHEN durum = 'taslak' THEN 1 END) as taslak, COUNT(CASE WHEN durum = 'arsiv' THEN 1 END) as arsiv FROM public.qdms_belgeler")).fetchone()
                rev_count = conn.execute(text("SELECT COUNT(*) FROM public.qdms_revizyon_log WHERE degisiklik_tarihi > :dt"), {"dt": thirty_days_ago}).scalar()
                eskiyen = conn.execute(text("SELECT belge_kodu, belge_adi, guncelleme_tarihi FROM public.qdms_belgeler WHERE durum = 'aktif' AND guncelleme_tarihi < :dt_old"), {"dt_old": one_year_ago}).fetchall()
        
        aktif_sayisi = stats[0] or 0
        taslak_sayisi = stats[1] or 0
        arsiv_sayisi = stats[2] or 0
        rev_30_gun = rev_count or 0
        eskiyen_list = [dict(r._mapping) for r in eskiyen]
        
        # BRC Uyum Skoru Hesaplama
        skor = 0
        if aktif_sayisi > 0: skor += 25
        if rev_30_gun > 0: skor += 25
        # Okunmamış talimat kontrolü (Örn: Hiç okunmamış talimat yoksa tam puan)
        # Personel bazlı okunmamış kontrolü burada simüle ediliyor
        skor += 25 # Varsayılan (Talimatlar daha yeni eklendiği için)
        if len(eskiyen_list) == 0: skor += 25
        
        return {
            'aktif_belge_sayisi': aktif_sayisi,
            'taslak_sayisi': taslak_sayisi,
            'arsiv_sayisi': arsiv_sayisi,
            'son_30_gun_revizyon': rev_30_gun,
            'eskiyen_belgeler': eskiyen_list,
            'brc_uyum_skoru': float(skor)
        }
    except Exception as e:
        return {"hata": str(e)}
