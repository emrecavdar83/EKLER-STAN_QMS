
import pandas as pd
from sqlalchemy import create_engine, text

# --- MOCK STREAMLIT ---
class MockSessionState:
    def __init__(self):
        self.user_rol = ""
        self.user_bolum = ""
        self.user = ""

st_session_state = MockSessionState()

def bolum_bazli_urun_filtrele(urun_df):
    """Bölüm Sorumlusu için ürün listesini hiyerarşik olarak filtreler"""
    user_rol = str(st_session_state.user_rol).upper()
    user_bolum = st_session_state.user_bolum
    
    print(f"DEBUG: User Rol='{user_rol}', User Bolum='{user_bolum}'")
    
    rol_upper = user_rol.upper()
    bolum_upper = str(user_bolum).upper()
    user_id_str = str(st_session_state.user).strip()
    
    if user_rol in ['ADMIN', 'YÖNETİM', 'GIDA MÜHENDİSİ'] or \
       'KALİTE' in rol_upper or \
       'KALİTE' in bolum_upper or \
       'LABORATUVAR' in bolum_upper or \
       user_id_str == 'sevcanalbas':
        return urun_df
    
    # Robust check for check here (mimicking app.py but simplified since user_bolum is string now)
    if (user_rol in ['VARDIYA AMIRI', 'VARDIYA AMİRİ']) and not user_bolum:
        return urun_df
    
    if 'sorumlu_departman' in urun_df.columns and user_bolum:
        try:
            mask_bos = urun_df['sorumlu_departman'].isna() | \
                       (urun_df['sorumlu_departman'] == '') | \
                       (urun_df['sorumlu_departman'].astype(str).str.lower() == 'none')
            
            # Debugging the contains logic
            print("DEBUG: Checking 'sorumlu_departman' contains user_bolum...")
            
            # Let's verify line by line for a few items
            for idx, row in urun_df.head(5).iterrows():
                dept = str(row['sorumlu_departman'])
                match = user_bolum.lower() in dept.lower() # Logic in app: str.contains(user_bolum, case=False)
                # print(f"  Product: {row['urun_adi']}, Dept: '{dept}' vs User: '{user_bolum}' => Match: {match}")

            mask_eslesme = urun_df['sorumlu_departman'].astype(str).str.contains(str(user_bolum), case=False, na=False)
            
            filtreli = urun_df[mask_bos | mask_eslesme]
            print(f"DEBUG: Filtered {len(urun_df)} -> {len(filtreli)}")
            return filtreli
            
        except Exception as e:
            print(f"DEBUG: Exception {e}")
            return urun_df

    elif 'uretim_bolumu' in urun_df.columns and user_bolum:
        return urun_df[urun_df['uretim_bolumu'].astype(str).str.upper() == str(user_bolum).upper()]
    
    return urun_df

# --- RUN SIMULATION ---
db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

with engine.connect() as conn:
    print("Fetching Products...")
    urun_df = pd.read_sql("SELECT * FROM ayarlar_urunler", conn)
    
    print("Fetching User 'mihrimah.ali'...")
    p_df = pd.read_sql("SELECT p.*, d.bolum_adi as bolum FROM personel p LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id WHERE p.kullanici_adi = 'mihrimah.ali'", conn)
    
    if p_df.empty:
        print("User not found!")
    else:
        u_data = p_df.iloc[0] # Series
        
        # Handle duplicate columns robustly like app.py
        raw_bolum = u_data['bolum'] 
        user_bolum_str = ""
        
        if isinstance(raw_bolum, (pd.Series, list)):
            # If Series, pick first one (personel table)
            # BUT NOW IT IS FIXED, SO IT SHOULD BE CLEAN "RULO PASTA"
            val = raw_bolum.iloc[0] if hasattr(raw_bolum, 'iloc') else raw_bolum[0]
            user_bolum_str = str(val)
        else:
            user_bolum_str = str(raw_bolum) if raw_bolum else ""
            
        st_session_state.user = u_data['kullanici_adi']
        st_session_state.user_rol = u_data['rol']
        st_session_state.user_bolum = user_bolum_str
        
        filtered = bolum_bazli_urun_filtrele(urun_df)
        print("\n--- RESULTS FOR MIHRIMAH ALI ---")
        print(filtered[['urun_adi', 'sorumlu_departman']].to_string())

