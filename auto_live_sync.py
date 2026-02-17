import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

# Engines
local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

def safe_sync_table(table_name, pk_cols):
    print(f"\nSyncing: {table_name}")
    try:
        local_df = pd.read_sql(f"SELECT * FROM {table_name}", local_engine)
        live_df = pd.read_sql(f"SELECT * FROM {table_name}", live_engine)
        
        if local_df.empty:
            return {"status": "skipped", "reason": "empty_local"}
        
        if isinstance(pk_cols, str):
            pk_cols = [pk_cols]
        
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
        
        with live_engine.begin() as conn:
            if inserts:
                insert_df = pd.DataFrame(inserts)
                insert_df = insert_df.where(pd.notnull(insert_df), None)
                insert_df.to_sql(table_name, conn, if_exists='append', index=False)
            
            if updates:
                for update_row in updates:
                    where_parts = [f"{col} = :{col}" for col in pk_cols]
                    where_clause = " AND ".join(where_parts)
                    set_cols = [c for c in local_df.columns if c not in pk_cols]
                    set_parts = [f"{col} = :{col}" for col in set_cols]
                    set_clause = ", ".join(set_parts)
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                    params = {k: (None if pd.isna(v) else v) for k, v in update_row.items()}
                    conn.execute(text(sql), params)
        
        return {"status": "success", "inserted": len(inserts), "updated": len(updates)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("CANLI SYNC BAŞLIYOR (Otomatik)")
    res_personel = safe_sync_table("personel", "id")
    print(f"Personel Sync Sonucu: {res_personel}")
