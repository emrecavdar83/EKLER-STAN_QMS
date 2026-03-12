import pandas as pd
from sqlalchemy import create_engine, text

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

def fix_and_align():
    with engine.connect() as conn:
        # 1. Mevcut plan ve merkez tanımları çek
        plan_df = pd.read_sql("SELECT * FROM ayarlar_temizlik_plani", conn)
        lokasyonlar = pd.read_sql("SELECT id, ad, tip FROM lokasyonlar", conn)
        ekipmanlar = pd.read_sql("SELECT id, ekipman_adi FROM tanim_ekipmanlar", conn)

        # 2. Eksikleri belirle ve ekle
        missing_sections = [] # (Name, Type)
        missing_equip = []   # (Name)

        # Katlar
        for k_name in plan_df['kat'].dropna().unique():
            if k_name.strip() not in lokasyonlar[lokasyonlar['tip']=='Kat']['ad'].values:
                missing_sections.append((k_name.strip(), 'Kat'))
        
        # Bölümler
        for b_name in plan_df['kat_bolum'].dropna().unique():
            if b_name.strip() not in lokasyonlar[lokasyonlar['tip']=='Bölüm']['ad'].values:
                missing_sections.append((b_name.strip(), 'Bölüm'))

        # Ekipmanlar
        for e_name in plan_df['yer_ekipman'].dropna().unique():
            if e_name.strip() not in ekipmanlar['ekipman_adi'].values:
                missing_equip.append(e_name.strip())

        # 3. DB'ye yaz (Transaction)
        with engine.begin() as trans:
            # Eksik Kat/Bölüm ekle
            for name, tip in missing_sections:
                print(f"Adding Lokasyon: {name} ({tip})")
                trans.execute(text("INSERT INTO lokasyonlar (ad, tip, aktif) VALUES (:ad, :tip, 1)"), {"ad": name, "tip": tip})
            
            # Eksik Ekipman ekle
            for name in missing_equip:
                print(f"Adding Ekipman: {name}")
                trans.execute(text("INSERT INTO tanim_ekipmanlar (ekipman_adi) VALUES (:ad)"), {"ad": name})

        # 4. Yeniden eşleştir (Mapping)
        # Tabloları taze çek
        lokasyonlar = pd.read_sql("SELECT id, ad, tip FROM lokasyonlar", engine)
        ekipmanlar = pd.read_sql("SELECT id, ekipman_adi FROM tanim_ekipmanlar", engine)
        
        kat_map = {row['ad']: row['id'] for _, row in lokasyonlar[lokasyonlar['tip']=='Kat'].iterrows()}
        bolum_map = {row['ad']: row['id'] for _, row in lokasyonlar[lokasyonlar['tip']=='Bölüm'].iterrows()}
        ekip_map = {row['ekipman_adi']: row['id'] for _, row in ekipmanlar.iterrows()}

        with engine.begin() as trans:
            for _, row in plan_df.iterrows():
                k_id = kat_map.get(str(row['kat']).strip())
                b_id = bolum_map.get(str(row['kat_bolum']).strip())
                e_id = ekip_map.get(str(row['yer_ekipman']).strip())
                
                trans.execute(text("""
                    UPDATE ayarlar_temizlik_plani 
                    SET kat_id = :kid, bolum_id = :bid, ekipman_id = :eid, is_migrated = TRUE
                    WHERE id = :id
                """), {"kid": k_id, "bid": b_id, "eid": e_id, "id": row['id']})
        
        print("--- AUTOMATIC REPAIR COMPLETED ---")
        print(f"Updated {len(plan_df)} rows in cleaning plan.")

if __name__ == "__main__":
    fix_and_align()
