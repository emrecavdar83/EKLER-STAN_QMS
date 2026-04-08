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
                res = conn.execute(text("SELECT id FROM personel WHERE kullanici_adi = :u"), {"u": user}).fetchone()
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
            # v6.3.1: SQLAlchemy 2.0 + Pandas 3.13 Fix (TypeError Bypass)
            gorev_df = pd.read_sql(q, engine, params={"pid": personel_id, "t": bugun})
            
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
        
        # Mapping hazırlığı
        pairs = sistem_modullerini_getir()
        pairs.append(("👤 Profilim", "profilim"))
        label_to_slug = {p[0]: p[1] for p in pairs}
        
        for i, m in enumerate(card_modules):
            with cols[i % 3]:
                # Estetik Kart Tasarımı + Buton
                if st.button(f"{m}", key=f"portal_btn_{i}", use_container_width=True):
                    slug = label_to_slug.get(m)
                    if slug:
                        # v4.3.7: Sadece Master Key'i değiştiriyoruz. 
                        # app.py'deki Index-Controlled sistem geri kalanını (Menu/HIZLI) hatasız halledecek.
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
