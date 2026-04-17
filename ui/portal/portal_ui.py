import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date

from logic.auth_logic import sistem_modullerini_getir

# EKLERISTAN QMS - PORTAL / DASHBOARD MODULE
# Modernized Landing Page for all users.

def render_portal_module(engine):
    st.title("🏠 EKLERİSTAN QMS - Portal")
    
    user = st.session_state.get('user', '')
    user_rol = st.session_state.get('user_rol', 'Personel')
    user_fullname = st.session_state.get('user_fullname', user)
    
    st.markdown(f"### 👋 Hoş Geldiniz, {user_fullname}!")
    st.caption(f"Rolünüz: **{user_rol}** | Tarih: **{date.today().strftime('%d.%m.%Y')}**")
    
    st.markdown("---")
    
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

    st.markdown("---")
    
    # st.session_state'den modülleri (etiket, slug) çiftleri olarak al
    modul_pairs = st.session_state.get('available_modules', [])
    
    if modul_pairs:
        cols = st.columns(3)
        # Sadece portal dışındaki modülleri göster
        card_modules = [m for m in modul_pairs if m[1] != "portal"]
        
        for i, (label, slug) in enumerate(card_modules):
            with cols[i % 3]:
                # Estetik Kart Tasarımı + Buton
                if st.button(f"{label}", key=f"portal_btn_{i}", width="stretch"):
                    # v6.2.4: Only set the master key. Centralized Gatekeeper in app.py 
                    # will handle UI widget sync at the start of the next run.
                    st.session_state.active_module_key = slug
                    st.rerun()
                
                # Alt bilgi veya süsleme (Opsiyonel)
                st.markdown(f"""
                <div style="font-size: 0.8rem; color: #7f8c8d; text-align: center; margin-top: -10px; margin-bottom: 20px;">
                    Modüle Git &rarr;
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("Yetkili modüller yükleniyor...")
