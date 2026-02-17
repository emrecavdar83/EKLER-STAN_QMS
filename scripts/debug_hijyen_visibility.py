from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    
    # 1. Simulate the exact query from app.py
    print("--- 1. EXECUTING APP QUERY ---")
    p_list = pd.read_sql("""
        SELECT p.ad_soyad, 
               COALESCE(d.bolum_adi, 'Tanımsız') as bolum, 
               p.vardiya, 
               p.durum 
        FROM personel p
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
        WHERE p.ad_soyad IS NOT NULL
    """, engine)
    p_list.columns = ["Ad_Soyad", "Bolum", "Vardiya", "Durum"]
    
    print(f"Total Rows: {len(p_list)}")
    
    # 2. Filter AKTİF
    p_list = p_list[p_list['Durum'].astype(str) == "AKTİF"]
    print(f"Active Rows: {len(p_list)}")
    
    # 3. Inspect specific users (Burcu, Alican, Mihrimah)
    targets = ["BURCU ŞAHİN", "ALİCAN ALİ", "MİHRİMAH ALİ", "ZUBALA MEHDİ"]
    
    print("\n--- 3. TARGET INSPECTION ---")
    for name in targets:
        # Fuzzy match or contains
        matches = p_list[p_list['Ad_Soyad'].str.contains(name.split()[0], case=False, na=False)]
        if not matches.empty:
            for _, row in matches.iterrows():
                print(f"Name: {repr(row['Ad_Soyad'])}")
                print(f"Dept: {repr(row['Bolum'])}")
                print(f"Shift: {repr(row['Vardiya'])}")
                print(f"Status: {repr(row['Durum'])}")
                print("-" * 20)
        else:
            print(f"❌ {name} NOT FOUND in DataFrame!")

    # 4. Simulate Filtering like in App
    print("\n--- 4. FILTER SIMULATION ---")
    v_sec = "GÜNDÜZ VARDİYASI"
    b_sec = "RULO PASTA"
    
    # Filter Shift
    # Check exact match vs whitespace
    print(f"Filtering for Shift: {repr(v_sec)}")
    p_v = p_list[p_list['Vardiya'] == v_sec]
    print(f"Rows after Shift Filter: {len(p_v)}")
    
    # Show who survived
    survivors = p_v['Ad_Soyad'].tolist()
    print(f"Survivors (Shift): {[s for s in survivors if 'ALİ' in s or 'BURCU' in s]}")

    # Check matches manually
    for t in targets:
        row = p_list[p_list['Ad_Soyad'].str.contains(t.split()[0], case=False)].iloc[0] if not p_list[p_list['Ad_Soyad'].str.contains(t.split()[0], case=False)].empty else None
        if row is not None:
             match = (row['Vardiya'] == v_sec)
             print(f"Does {row['Ad_Soyad']} match Shift? {match} (Val: {repr(row['Vardiya'])})")

    # Filter Dept
    print(f"\nFiltering for Dept: {repr(b_sec)}")
    p_b = p_v[p_v['Bolum'] == b_sec]
    print(f"Rows after Dept Filter: {len(p_b)}")
    
    final_names = p_b['Ad_Soyad'].tolist()
    print(f"Final List: {final_names}")

except Exception as e:
    print(e)
