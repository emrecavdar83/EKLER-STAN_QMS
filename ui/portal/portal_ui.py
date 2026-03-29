import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date

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
                res = conn.execute(text("SELECT id FROM personel WHERE kullanici_adi = :u"), {"u": user}).fetchone()
                if res: personel_id = res[0]
            except Exception:
                pass
                
        # Görev havuzundan bugünün görevlerini çek
        try:
            with engine.connect() as conn:
                bugun = str(date.today())
                q = text("""
                    SELECT durum, COUNT(*) as sayi 
                    FROM birlesik_gorev_havuzu 
                    WHERE personel_id = :pid AND (hedef_tarih = :t OR atanma_tarihi = :t)
                    GROUP BY durum
                """)
                gorev_df = pd.read_sql(q, conn, params={"pid": personel_id, "t": bugun})
                
                bekleyen = int(gorev_df[gorev_df['durum'] == 'BEKLIYOR']['sayi'].sum()) if not gorev_df.empty else 0
                tamamlanan = int(gorev_df[gorev_df['durum'] == 'TAMAMLANDI']['sayi'].sum()) if not gorev_df.empty else 0
                
            c1, c2, c3 = st.columns(3)
            c1.metric("Bekleyen Görev", bekleyen, delta="-Acil" if bekleyen > 0 else "Tamam", delta_color="inverse")
            c2.metric("Tamamlanan Görev", tamamlanan, delta="Aferin" if tamamlanan > 0 else None)
            c3.metric("Sistem Durumu", "Aktif", "Bulut Senkronize")
        except Exception:
            st.info("Kişisel istatistiklere şu an ulaşılamıyor.")

    st.markdown("---")
    
    # 2. Modül Erişim Kartları
    st.subheader("🚀 Hızlı Erişim Modülleri")
    st.info("Erişim yetkiniz olan modüllere yan menüden veya üst açılır menüden de ulaşabilirsiniz.")
    
    # st.session_state'den modülleri al
    # Geleneksel döngü ile kart görünümleri
    modul_listesi = st.session_state.get('available_modules', [])
    
    # Eğer modul listesi boşsa veya bulunamadıysa uyarı ver
    # app.py'de available_modules'u set edeceğiz.
    
    if modul_listesi:
        cols = st.columns(3)
        # Sadece portal dışındaki modülleri göster
        card_modules = [m for m in modul_listesi if "Portal" not in m]
        
        for i, m in enumerate(card_modules):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background-color: #f8f9fa; color: #2c3e50; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid #3498db; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0; font-size: 1.1rem;">{m}</h4>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("Yetkili modüller yükleniyor...")
