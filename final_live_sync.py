import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
import toml

# 1. LOCAL UPDATE
names_to_keep_active = [
    "BATIKAN ARSLAN",
    "HURMA DENLİYEVA",
    "YELİZ ÇAKIR",
    "MİHRİMAH ALİ"
]

def final_sync_and_activate():
    # Local connection
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("LO-KAL GÜNCELLEMELER YAPILIYOR...")
    for name in names_to_keep_active:
        cursor.execute("UPDATE personel SET durum = 'Aktif' WHERE UPPER(ad_soyad) LIKE ?", (f"%{name}%",))
        print(f"Lokal: {name} Aktif yapıldı.")
    conn.commit()
    conn.close()

    # 2. LIVE SYNC
    print("\nCANLI SİSTEM SENKRONİZASYONU BAŞLIYOR...")
    local_engine = create_engine('sqlite:///ekleristan_local.db')
    secrets = toml.load('.streamlit/secrets.toml')
    live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
    live_engine = create_engine(live_url, pool_pre_ping=True)

    table_name = "personel"
    pk_cols = ["id"]
    
    local_df = pd.read_sql(f"SELECT * FROM {table_name}", local_engine)
    live_df = pd.read_sql(f"SELECT * FROM {table_name}", live_engine)
    
    live_keys = set()
    if not live_df.empty:
        for _, row in live_df.iterrows():
            key = tuple(row[col] for col in pk_cols)
            live_keys.add(key)
    
    inserts = []
    updates = []
    
    for _, row in local_df.iterrows():
        key = tuple(row[col] for col in pk_cols)
        if key in live_keys:
            updates.append(row.to_dict())
        else:
            inserts.append(row.to_dict())
            
    with live_engine.begin() as conn_live:
        if inserts:
            insert_df = pd.DataFrame(inserts)
            insert_df = insert_df.where(pd.notnull(insert_df), None)
            insert_df.to_sql(table_name, conn_live, if_exists='append', index=False)
            print(f"Canlı: {len(inserts)} yeni personel eklendi.")
        
        if updates:
            for update_row in updates:
                where_parts = [f"{col} = :{col}" for col in pk_cols]
                where_clause = " AND ".join(where_parts)
                set_cols = [c for c in local_df.columns if c not in pk_cols]
                set_parts = [f"{col} = :{col}" for col in set_cols]
                set_clause = ", ".join(set_parts)
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                params = {k: (None if pd.isna(v) else v) for k, v in update_row.items()}
                conn_live.execute(text(sql), params)
            print(f"Canlı: {len(updates)} personel bilgisi güncellendi.")

if __name__ == "__main__":
    final_sync_and_activate()
