import toml
import os
import sqlite3
from sqlalchemy import create_engine, text
import pandas as pd
import re

def normalize(name):
    if not name: return ""
    name = str(name).upper().strip()
    tr_map = str.maketrans("İĞÜŞÖÇ", "IGUSOC")
    name = name.translate(tr_map)
    return re.sub(r'[^A-Z0-9]', '', name)

def get_live_engine():
    secrets_path = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
    secrets = toml.load(secrets_path)
    url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    return create_engine(url)

def run_cleanup_and_sync():
    print("--- CANLI VERİTABANI SENKRONİZASYON (V2 - FK KONTROLLÜ) ---")
    
    local_conn = sqlite3.connect('ekleristan_local.db')
    local_active = pd.read_sql("SELECT * FROM personel WHERE durum = 'AKTİF'", local_conn)
    local_conn.close()
    
    live_engine = get_live_engine()
    
    with live_engine.begin() as conn:
        print("Aşama 1: Personelleri yonetici_id olmadan (NULL) yükleme/güncelleme...")
        
        for _, row in local_active.iterrows():
            p_data = row.to_dict()
            p_id = p_data.pop('id')
            
            # yonetici_id'yi yedekle ve NULL yap (FK hatasını önlemek için)
            actual_manager_id = p_data.get('yonetici_id')
            p_data['yonetici_id'] = None
            
            # Sütunları hazırla
            cols = ", ".join(p_data.keys())
            placeholders = ", ".join([f":{k}" for k in p_data.keys()])
            update_stmt = ", ".join([f"{k} = EXCLUDED.{k}" for k in p_data.keys()])
            
            sql = text(f"""
                INSERT INTO personel (id, {cols}) 
                VALUES ({p_id}, {placeholders})
                ON CONFLICT (id) DO UPDATE SET {update_stmt}
            """)
            conn.execute(sql, p_data)

        print("Aşama 2: Yönetici ilişkilerini (yonetici_id) güncelleme...")
        for _, row in local_active.iterrows():
            if pd.notna(row['yonetici_id']):
                conn.execute(
                    text("UPDATE personel SET yonetici_id = :yid WHERE id = :pid"),
                    {"yid": int(row['yonetici_id']), "pid": int(row['id'])}
                )

    print("\n[OK] Canlı veritabanı senkronizasyonu BAŞARIYLA tamamlandı.")
    
    with live_engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*) FROM personel WHERE durum = 'AKTİF'")).fetchone()[0]
        print(f"Canlıdaki Son Aktif Personel Sayısı: {res}")

if __name__ == "__main__":
    run_cleanup_and_sync()
