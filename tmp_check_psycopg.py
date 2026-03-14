import psycopg2
from psycopg2.extras import RealDictCursor

# Cloud DB URL parts
# postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
CONN_STR = "host=aws-1-ap-south-1.pooler.supabase.com port=6543 dbname=postgres user=postgres.bogritpjqxcdmodxxfhv password=@9083&tprk_E"

def check_cloud():
    try:
        conn = psycopg2.connect(CONN_STR)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("--- ALL ACTIVE SHIFTS (ANY DATE) ---")
        cur.execute("SELECT id, tarih, makina_no, operator_adi, durum, olusturma_ts FROM map_vardiya WHERE durum='ACIK' ORDER BY id DESC")
        rows = cur.fetchall()
        for r in rows:
            print(r)
            
        print("\n--- LAST 5 SHIFTS ---")
        cur.execute("SELECT id, tarih, makina_no, operator_adi, durum, olusturma_ts FROM map_vardiya ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        for r in rows:
            print(r)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Postgres Error: {e}")

if __name__ == "__main__":
    check_cloud()
