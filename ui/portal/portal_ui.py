import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date

# EKLERISTAN QMS - PORTAL / DASHBOARD MODULE
# Modernized Landing Page for all users.

def render_portal_module(engine):
    """v6.3.5: Redundant başlık/karşılama kaldırıldı — TopBar zaten gösteriyor."""
    user = st.session_state.get('user', '')
    personel_id = 1

    # 1. Hızlı İstatistikler (Günlük Görevler)
    with st.container():
        st.subheader("📋 Günlük Özet")
        
        # Kullanıcının ID'sini bulalım
        personel_id = 1 # Fallback
        with engine.connect() as conn:
            try:
                res = conn.execute(text("SELECT id FROM ayarlar_kullanicilar WHERE kullanici_adi = :u"), {"u": user}).fetchone()
                if res: personel_id = res[0]
            except Exception:
                pass
                
        # Görev havuzundan bugünün görevlerini çek
        try:
            bugun = str(date.today())
            q = text("""
                SELECT durum, COUNT(*) as sayi 
                FROM birlesik_gorev_havuzu 
                WHERE personel_id = :pid AND (hedef_tarih = :t OR atanma_tarihi = :t)
                GROUP BY durum
            """)
            # v6.3.2: Manual Fetch Bypass (Pandas 3.13 / SQLAlchemy 2.0.x TypeError Fix)
            with engine.connect() as conn:
                res = conn.execute(q, params={"pid": personel_id, "t": bugun})
                gorev_df = pd.DataFrame(res.fetchall(), columns=res.keys())
            
            bekleyen = int(gorev_df[gorev_df['durum'] == 'BEKLIYOR']['sayi'].sum()) if not gorev_df.empty else 0
            tamamlanan = int(gorev_df[gorev_df['durum'] == 'TAMAMLANDI']['sayi'].sum()) if not gorev_df.empty else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Bekleyen Görev", bekleyen, delta="-Acil" if bekleyen > 0 else "Tamam", delta_color="inverse")
            c2.metric("Tamamlanan Görev", tamamlanan, delta="Aferin" if tamamlanan > 0 else None)
            c3.metric("Sistem Durumu", "Aktif", "Bulut Senkronize")
        except Exception:
            st.info("Kişisel istatistiklere şu an ulaşılamıyor.")

