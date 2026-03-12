from sqlalchemy import create_engine, text
import pandas as pd

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

with engine.connect() as conn:
    # 1. Mevcut Plan Verileri
    plan_df = pd.read_sql("SELECT id, kat, kat_bolum, yer_ekipman FROM ayarlar_temizlik_plani", engine)
    
    # 2. Merkez Tanımlar
    lok_df = pd.read_sql("SELECT id, ad, tip FROM lokasyonlar", engine)
    ekip_df = pd.read_sql("SELECT ekipman_adi, bagli_bolum FROM tanim_ekipmanlar", engine)
    
    print("--- MEVCUT PLAN LOKASYON ANALİZİ ---")
    plan_df['kat_exists'] = plan_df['kat'].isin(lok_df[lok_df['tip']=='Kat']['ad'])
    plan_df['bolum_exists'] = plan_df['kat_bolum'].isin(lok_df[lok_df['tip']=='Bölüm']['ad'])
    plan_df['ekipman_exists'] = plan_df['yer_ekipman'].isin(ekip_df['ekipman_adi'])
    
    print(plan_df)
    
    print("\n--- LOKASYON TABLOSU ÖZET ---")
    print(lok_df['tip'].value_counts())
    
    print("\n--- EŞLEŞMEYENLER ---")
    missing_kat = plan_df[~plan_df['kat_exists']]['kat'].unique()
    missing_bol = plan_df[~plan_df['bolum_exists']]['kat_bolum'].unique()
    missing_ekip = plan_df[~plan_df['ekipman_exists']]['yer_ekipman'].unique()
    
    print(f"Eşleşmeyen Katlar: {missing_kat}")
    print(f"Eşleşmeyen Bölümler: {missing_bol}")
    print(f"Eşleşmeyen Ekipmanlar: {missing_ekip}")
