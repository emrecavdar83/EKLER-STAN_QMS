
import toml
import sqlite3
import sqlalchemy
from sqlalchemy import text

def compare_row_counts():
    tables_to_check = [
        "ayarlar_bolumler", "tanim_bolumler", "ayarlar_roller",
        "proses_tipleri", "ayarlar_urunler", "lokasyonlar",
        "temizlik_kayitlari", "urun_kpi_kontrol", "urun_parametreleri"
    ]

    # Local
    local_conn = sqlite3.connect('ekleristan_local.db')
    local_cursor = local_conn.cursor()
    
    # Live
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
    live_engine = sqlalchemy.create_engine(url.strip('\"'))
    
    print(f"{'Table':30} | {'Local':>6} | {'Live':>6} | {'Status'}")
    print("-" * 60)

    for t in tables_to_check:
        try:
            local_cursor.execute(f"SELECT count(*) FROM {t}")
            l_count = local_cursor.fetchone()[0]
        except:
            l_count = "ERR"
            
        try:
            with live_engine.connect() as conn:
                r_count = conn.execute(text(f"SELECT count(*) FROM {t}")).fetchone()[0]
        except:
            r_count = "ERR"
            
        status = "MATCH" if l_count == r_count else "DIFF"
        if l_count == "ERR" or r_count == "ERR": status = "N/A"
        
        print(f"{t:30} | {l_count:>6} | {r_count:>6} | {status}")
    
    local_conn.close()

if __name__ == "__main__":
    compare_row_counts()
