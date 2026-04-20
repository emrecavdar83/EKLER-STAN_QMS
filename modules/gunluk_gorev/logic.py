import pandas as pd
from sqlalchemy import text
from datetime import datetime
from logic.dynamic_sync import log_field_change

# EKLERİSTAN A.Ş.
# Builder Backend Ajanı Tarafından Python Logic Katmanı (Max 30 Satır/Fonksiyon kuralına uygun)

def gorev_katalogu_getir(engine):
    """Tanımlı günlük görevleri getirir."""
    with engine.connect() as conn:
        return pd.read_sql(text("SELECT * FROM gunluk_gorev_katalogu WHERE aktif_mi = 1"), conn)

def periyodik_gorev_ata(engine, atama_listesi, atayan_id=None):
    """
    Toplu görev ataması yapar. MADDE 31: Görev ataması audit trail'e kaydedilir.
    [{'personel_id': 1, 'bolum_id': None, 'gorev_kaynagi': 'PERIYODIK', 'kaynak_id': 5, 'atanma_tarihi': '2026-03-27', 'hedef_tarih': '2026-03-27'}]
    """
    with engine.begin() as conn:
        for atama in atama_listesi:
            try:
                res = conn.execute(text("""
                    INSERT INTO birlesik_gorev_havuzu
                    (personel_id, bolum_id, gorev_kaynagi, kaynak_id, atanma_tarihi, hedef_tarih, durum)
                    VALUES (:pid, :bid, :gk, :kid, :at, :ht, 'BEKLIYOR')
                    RETURNING id
                """), {
                    "pid": atama['personel_id'], "bid": atama.get('bolum_id'), "gk": atama['gorev_kaynagi'],
                    "kid": atama['kaynak_id'], "at": atama['atanma_tarihi'], "ht": atama['hedef_tarih']
                })
                new_id = res.fetchone()[0]

                # MADDE 31: Yeni görev atamasını logla
                if atayan_id:
                    log_field_change(conn, 'gunluk_gorev_degisim_loglari', new_id, 'durum',
                                   'YENI', 'BEKLIYOR', atayan_id, 'INSERT')
            except Exception as e:
                # UNIQUE kısıtlamasından dolayı mükerrer olanları yoksayar (Fail-silent)
                pass

def gorev_tamamla(engine, havuz_id, personel_id, sapma_notu=""):
    """
    Görevi tamamlar.
    MADDE 31: Görev tamamlama işlemi audit trail'e kaydedilir.
    """
    with engine.begin() as conn:
        # Eski durumu al
        old = conn.execute(text(
            "SELECT durum FROM birlesik_gorev_havuzu WHERE id = :id AND personel_id = :pid"
        ), {"id": havuz_id, "pid": personel_id}).fetchone()

        if old and old[0] == 'BEKLIYOR':
            old_status = old[0]
            # Görevi tamamla
            conn.execute(text("""
                UPDATE birlesik_gorev_havuzu
                SET durum = 'TAMAMLANDI', tamamlanma_tarihi = CURRENT_TIMESTAMP, sapma_notu = :not
                WHERE id = :hid AND personel_id = :pid AND durum = 'BEKLIYOR'
            """), {"hid": havuz_id, "pid": personel_id, "not": sapma_notu})

            # MADDE 31: Değişiklikleri logla
            log_field_change(conn, 'gunluk_gorev_degisim_loglari', havuz_id, 'durum',
                           old_status, 'TAMAMLANDI', personel_id, 'UPDATE')

def manuel_gorev_ata(engine, atama_verisi):
    """
    Yöneticinin manuel görev atamasını yapar. MADDE 31: Görev ataması audit trail'e kaydedilir.
    atama_verisi: {'personel_ids': [], 'v_tipi': 'KATALOG'/'AD-HOC', 'kaynak_id': int/None, 'ad_ozel': str/None, 'tarih': str, 'oncelik': str, 'atayan_id': int}
    """
    with engine.begin() as conn:
        for pid in atama_verisi['personel_ids']:
            res = conn.execute(text("""
                INSERT INTO birlesik_gorev_havuzu
                (personel_id, gorev_kaynagi, kaynak_id, ad_ozel, v_tipi, atanma_tarihi, hedef_tarih, durum, oncelik, atayan_id)
                VALUES (:pid, 'MANUEL', :kid, :ad, :vt, :bugun, :tarih, 'BEKLIYOR', :onc, :a_id)
                RETURNING id
            """), {
                "pid": pid, "kid": atama_verisi.get('kaynak_id'), "ad": atama_verisi.get('ad_ozel'),
                "vt": atama_verisi['v_tipi'], "bugun": datetime.now().strftime('%Y-%m-%d'),
                "tarih": atama_verisi['tarih'], "onc": atama_verisi.get('oncelik', 'NORMAL'),
                "a_id": atama_verisi.get('atayan_id')
            })
            new_id = res.fetchone()[0]

            # MADDE 31: Manuel görev atamasını logla
            atayan_id = atama_verisi.get('atayan_id')
            if atayan_id:
                log_field_change(conn, 'gunluk_gorev_degisim_loglari', new_id, 'durum',
                               'YENI', 'BEKLIYOR', atayan_id, 'INSERT')

def gorev_iptal_et(engine, havuz_id, iptal_eden_id, iptal_notu):
    """
    Görevi iptal eder (Silmez, durum=IPTAL yapar).
    MADDE 31: Görev iptal işlemi audit trail'e kaydedilir.
    """
    with engine.begin() as conn:
        # Eski durumu al
        old = conn.execute(text(
            "SELECT durum FROM birlesik_gorev_havuzu WHERE id = :id"
        ), {"id": havuz_id}).fetchone()

        if old and old[0] == 'BEKLIYOR':
            old_status = old[0]
            # Görevi iptal et
            conn.execute(text("""
                UPDATE birlesik_gorev_havuzu
                SET durum = 'IPTAL', iptal_notu = :not, iptal_eden_id = :ied
                WHERE id = :hid AND durum = 'BEKLIYOR'
            """), {"hid": havuz_id, "not": iptal_notu, "ied": iptal_eden_id})

            # MADDE 31: Değişiklikleri logla
            log_field_change(conn, 'gunluk_gorev_degisim_loglari', havuz_id, 'durum',
                           old_status, 'IPTAL', iptal_eden_id, 'UPDATE')

def personel_gorev_getir(engine, personel_id, tarih):
    """Bir personelin belirli bir gündeki (hedef_tarih) görevlerini getirir."""
    with engine.connect() as conn:
        try:
            return pd.read_sql(text("""
                SELECT b.*, k.ad as gorev_adi, k.kategori 
                FROM birlesik_gorev_havuzu b
                LEFT JOIN gunluk_gorev_katalogu k ON b.kaynak_id = k.id AND b.gorev_kaynagi IN ('PERIYODIK', 'KATALOG')
                WHERE b.personel_id = :pid 
                  AND (b.atanma_tarihi = :tarih OR b.hedef_tarih = :tarih)
                ORDER BY b.durum ASC
            """), conn, params={"pid": personel_id, "tarih": tarih})
        except Exception as e:
            return pd.DataFrame([{"id": 999, "durum": "BEKLIYOR", "gorev_adi": "SİSTEM HATASI", "kategori": "HATA", "gorev_kaynagi": "DB", "atanma_tarihi": "Hata", "tamamlanma_tarihi": None, "sapma_notu": str(e)}])

def yonetici_matris_getir(engine, tarih, bolum_id=None):
    """Tüm personelin o günkü matrisini döndürür."""
    with engine.connect() as conn:
        # PANDAS pivot_table ile UI tarafında matrisleştirmek üzere ham veriyi çeker
        q = """
            SELECT b.*, p.ad_soyad, k.ad as gorev_adi
            FROM birlesik_gorev_havuzu b
            JOIN ayarlar_kullanicilar p ON b.personel_id = p.id
            LEFT JOIN gunluk_gorev_katalogu k ON b.kaynak_id = k.id AND b.gorev_kaynagi IN ('PERIYODIK', 'KATALOG')
            WHERE (b.atanma_tarihi = :tarih OR b.hedef_tarih = :tarih)
        """
        if bolum_id:
            q += f" AND (p.departman_id = {bolum_id} OR b.bolum_id = {bolum_id})"
            
        try:
            return pd.read_sql(text(q), conn, params={"tarih": tarih})
        except Exception as e:
            return pd.DataFrame([{"ad_soyad": "HATA", "gorev_adi": str(e), "gorev_kaynagi": "ERROR", "durum": "ERROR", "sapma_notu": ""}])

def periyodik_kural_ekle(engine, kural_verisi):
    """Tekrarlı görev kuralı ekler."""
    with engine.begin() as conn:
        for pid in kural_verisi['personel_ids']:
            conn.execute(text("""
                INSERT INTO gunluk_periyodik_kurallar 
                (personel_id, kaynak_tipi, kaynak_id, ad_ozel, oncelik, periyot_tipi, periyot_detay)
                VALUES (:pid, :kt, :kid, :ad, :onc, :pt, :pd)
            """), {
                "pid": pid, "kt": kural_verisi['kaynak_tipi'], "kid": kural_verisi.get('kaynak_id'),
                "ad": kural_verisi.get('ad_ozel'), "onc": kural_verisi.get('oncelik', 'NORMAL'),
                "pt": kural_verisi['periyot_tipi'], "pd": kural_verisi.get('periyot_detay', '{}')
            })

def periyodik_motor_calistir(engine):
    """Her sayfa açılışında bekleyen periyodik görevleri enjekte eder."""
    bugun = datetime.now().strftime('%Y-%m-%d')
    with engine.connect() as conn:
        kurallar = conn.execute(text("SELECT * FROM gunluk_periyodik_kurallar WHERE aktif_mi = 1")).fetchall()
        
    for k in kurallar:
        # Önce bu kural bugün için zaten atandı mı kontrol et
        with engine.connect() as conn:
            check = conn.execute(text("""
                SELECT id FROM birlesik_gorev_havuzu 
                WHERE personel_id = :pid AND hedef_tarih = :bugun 
                AND gorev_kaynagi = 'PERIYODIK' AND kaynak_id = :kid AND COALESCE(ad_ozel, '') = :ad
            """), {"pid": k.personel_id, "bugun": bugun, "kid": k.kaynak_id, "ad": k.ad_ozel or ""}).fetchone()
            
            if check: continue
            
        # Atama yap
        with engine.begin() as conn:
            try:
                conn.execute(text("""
                    INSERT INTO birlesik_gorev_havuzu 
                    (personel_id, gorev_kaynagi, kaynak_id, ad_ozel, v_tipi, atanma_tarihi, hedef_tarih, durum, oncelik)
                    VALUES (:pid, 'PERIYODIK', :kid, :ad, :vt, :bugun, :bugun, 'BEKLIYOR', :onc)
                """), {
                    "pid": k.personel_id, "kid": k.kaynak_id, "ad": k.ad_ozel,
                    "vt": k.kaynak_tipi, "bugun": bugun, "onc": k.oncelik
                })
            except: pass

