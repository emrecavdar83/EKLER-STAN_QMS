import streamlit as st
from sqlalchemy import text
from sqlalchemy import text
# from database.connection import get_engine # v6.8.9: Lazy Load and circular fix
from logic.cache_manager import clear_personnel_cache

# engine = get_engine() # v6.8.9: Lazy Load and circular fix

def guvenli_kayit_ekle(tablo_adi, veri):
    """Veritabanına tekli kayıt ekleyen güvenli wrapper (Atomik)."""
    try:
        from database.connection import get_engine
        # ANAYASA v4.0: engine.begin() ile otomatik commit/rollback
        with get_engine().begin() as conn:
            if tablo_adi == "Depo_Giris_Kayitlari":
                sql = """INSERT INTO depo_giris_kayitlari (tarih, saat, vardiya, kullanici, islem_tipi, urun, lot_no, miktar, fire, notlar, zaman_damgasi)
                         VALUES (:t, :sa, :v, :k, :i, :u, :l, :m, :f, :n, :z)"""
                params = {"t":veri[0], "sa":veri[1], "v":veri[2], "k":veri[3], "i":veri[4], "u":veri[5], "l":veri[6], "m":veri[7], "f":veri[8], "n":veri[9], "z":veri[10]}
                conn.execute(text(sql), params)

            elif tablo_adi == "Urun_KPI_Kontrol":
                sql = """INSERT INTO urun_kpi_kontrol 
                         (tarih, saat, vardiya, urun, lot_no, stt, numune_no, 
                          olcum1, olcum2, olcum3, karar, kullanici, 
                          tat, goruntu, notlar, fotograf_yolu, fotograf_b64)
                         VALUES (:t, :sa, :v, :u, :l, :stt, :num, 
                                 :o1, :o2, :o3, :karar, :kul, 
                                 :tat, :gor, :notlar, :foto, :foto_b64)"""
                params = {
                    "t": veri[0], "sa": veri[1], "v": veri[2], "u": veri[3],
                    "l": veri[5], "stt": veri[6], "num": veri[7],
                    "o1": veri[8], "o2": veri[9], "o3": veri[10],
                    "karar": veri[11], "kul": veri[12],
                    "tat": veri[16], "gor": veri[17], "notlar": veri[18],
                    "foto": veri[19] if len(veri) > 19 else None,
                    "foto_b64": veri[20] if len(veri) > 20 else None
                }
                conn.execute(text(sql), params)

        # SEÇİCİ CACHE TEMİZLEME (İşlem başarılıysa)
        clear_personnel_cache()
        return True

    except Exception as e:
        st.error(f"SQL Hatası (İşlem Geri Alındı): {e}")
        return False

def guvenli_coklu_kayit_ekle(tablo_adi, veri_listesi):
    """Veritabanına toplu kayıt ekleyen güvenli wrapper (Atomik)."""
    if not veri_listesi: return False
    try:
        from database.connection import get_engine
        with get_engine().begin() as conn:
            if tablo_adi == "Hijyen_Kontrol_Kayitlari":
                sql = """INSERT INTO hijyen_kontrol_kayitlari (tarih, saat, kullanici, vardiya, bolum, personel, durum, sebep, aksiyon)
                         VALUES (:t, :s, :k, :v, :b, :p, :d, :se, :a)"""
                
                # Parametre listesini hazırla (Batch Execute)
                batch_params = [
                    {"t":r[0], "s":r[1], "k":r[2], "v":r[3], "b":r[4], "p":r[5], "d":r[6], "se":r[7], "a":r[8]}
                    for r in veri_listesi
                ]
                conn.execute(text(sql), batch_params)
                return True
    except Exception as e:
        st.error(f"Toplu Kayıt Hatası (İşlem Geri Alındı): {e}")
        return False
    return False
