import streamlit as st
import time
import pandas as pd

def get_gecikme_uyarilari(engine):
    """
    ANAYASA v3.2: SOSTS Modülü Gecikme Uyarılarını Lazy Loading ile yönetir.
    Bu modül app.py'nin açılışını hızlandırmak için soguk_oda_utils'i 
    sadece ihtiyaç duyulduğunda import eder.
    """
    try:
        # 1. Lazy Import: soguk_oda_utils en ağır modüllerden biridir, sadece burada açılır
        import soguk_oda_utils

        # ─── 13. ADAM: GLOBAL BAKIM (Her saat başı veya manuel tetikleme) ───
        current_time = time.time()
        last_maint = st.session_state.get("sosts_last_maintenance", 0)
        
        # Parametre kontrolü (Fallback logic ile)
        bakim_periyodu = 3600
        try:
            if hasattr(soguk_oda_utils, 'get_sosts_param'):
                bakim_periyodu = int(soguk_oda_utils.get_sosts_param(engine, 'sosts_bakim_periyodu_sn', '3600'))
        except: pass
        
        if (current_time - last_maint) > bakim_periyodu:
            soguk_oda_utils.plan_uret(engine)
            soguk_oda_utils.kontrol_geciken_olcumler(engine)
            st.session_state.sosts_last_maintenance = current_time

        # 2. PERFORMANS: Alert Cache (5 Dakika / 300 saniye)
        last_alert_check = st.session_state.get("sosts_last_alert_check", 0)
        if (current_time - last_alert_check) > 300:
            df_gecikme = soguk_oda_utils.get_overdue_summary(engine)
            st.session_state.sosts_gecikme_cache = df_gecikme
            st.session_state.sosts_last_alert_check = current_time
        
        df_gecikme = st.session_state.get("sosts_gecikme_cache", pd.DataFrame())
        
        if not df_gecikme.empty:
            total_gecikme = df_gecikme['gecikme_sayisi'].sum()
            oda_list = ", ".join(df_gecikme['oda_adi'].tolist())
            st.error(f"🚨 **DİKKAT:** Son 24 saatte {total_gecikme} adet gecikmiş soğuk oda ölçümü var! (Odalar: {oda_list})", icon="🚨")
            
    except Exception as e:
        # Hataları sessizce yutma, admin için logla ama UI bozma
        print(f"Alert Logic Error: {e}")
