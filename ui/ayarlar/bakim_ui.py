import streamlit as st
from datetime import datetime
from logic.sosts_bakim import sosts_bakim_calistir, son_bakim_zamani_getir

def render_bakim_tab(engine):
    """Sistem Bakımı ve Manuel Tetikleyiciler Arayüzü."""
    st.subheader("🔧 Sistem Bakım ve Optimizasyon")
    st.write("Aşağıdaki araçlar, sistemin arka plan görevlerini manuel olarak tetiklemenizi sağlar.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### ❄️ SOSTS (Soğuk Oda Takip Sistemi) Bakımı")
        st.info("Bu işlem; ölçüm planlarını yeniler, geciken ölçümleri tespit eder ve kritik uyarıları hazırlar.")
        
        son_bakim = son_bakim_zamani_getir(engine)
        if son_bakim:
            gecen = datetime.now() - son_bakim
            if gecen.total_seconds() > 86400:  # 24 saat
                st.error(f"⚠️ **KRİTİK:** Son bakım {son_bakim.strftime('%d.%m.%Y %H:%M')} tarihinde yapılmış. 24 saatlik süre aşılmış!")
            else:
                st.success(f"✅ Son bakım zamanı: {son_bakim.strftime('%d.%m.%Y %H:%M')}")
        else:
            st.warning("⚠️ Bakım henüz hiç çalıştırılmadı veya sistem parametresi bulunamadı.")
            
        if st.button("▶️ SOSTS Bakımını Şimdi Çalıştır", type="primary", use_container_width=True):
            with st.spinner("Ölçüm planları güncelleniyor ve gecikmeler analiz ediliyor..."):
                res = sosts_bakim_calistir(engine, st.session_state.get('user', 'ADMIN'))
            if res['basarili']:
                st.toast("✅ Bakım başarıyla tamamlandı!", icon="✅")
                st.rerun()
            else:
                st.error(f"❌ Bakım sırasında bir hata oluştu: {res.get('hata')}")

    with col2:
        st.markdown("### 📊 Sistem Durumu")
        if son_bakim:
            st.metric("Son Bakımdan Beri", f"{gecen.seconds // 3600} saat { (gecen.seconds // 60) % 60} dk")
        st.caption("Not: Sayfa yükleme hızını korumak için bu işlemler artık otomatik çalışmamaktadır.")
