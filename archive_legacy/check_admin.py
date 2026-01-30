from app import engine
import pandas as pd
from sqlalchemy import text

try:
    df = pd.read_sql("SELECT id, ad_soyad, kullanici_adi, rol, pozisyon_seviye FROM personel WHERE rol='Admin'", engine)
    print("Mevcut Adminler:")
    print(df.to_string())
    
    # EMRE ÇAVDAR var mı kontrol et
    emre_var = not df[df['ad_soyad'].str.contains("EMRE ÇAVDAR", case=False, na=False)].empty
    print(f"\nEMRE ÇAVDAR Admin mi?: {emre_var}")
    
except Exception as e:
    print(f"Hata: {e}")
