
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import re

def get_engine():
    db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    return create_engine(db_url)

engine = get_engine()

def audit_timestamps():
    try:
        with engine.connect() as conn:
            query = """
            SELECT 
                o.oda_adi,
                COALESCE(p.beklenen_zaman, m.olcum_zamani) as zaman
            FROM sicaklik_olcumleri m
            JOIN soguk_odalar o ON m.oda_id = o.id
            LEFT JOIN olcum_plani p ON m.id = p.gerceklesen_olcum_id
            
            UNION ALL
            
            SELECT 
                o.oda_adi, 
                p.beklenen_zaman as zaman
            FROM olcum_plani p
            JOIN soguk_odalar o ON p.oda_id = o.id
            WHERE p.gerceklesen_olcum_id IS NULL
            """
            
            df_matris = pd.read_sql(text(query), conn)
            
            def format_aralikli_saat(dt_val):
                try:
                    dt_obj = pd.to_datetime(dt_val).floor('h')
                    end_time = dt_obj + pd.Timedelta(hours=1)
                    return f"{dt_obj.strftime('%d.%m %H:%M')}-{end_time.strftime('%H:%M')}"
                except Exception as ex:
                    return str(dt_val)

            df_matris['zaman_str'] = df_matris['zaman'].apply(format_aralikli_saat)
            
            # Find the culprits for "07:00" specifically
            target_culprits = df_matris[df_matris['zaman_str'] == "07:00"]
            if not target_culprits.empty:
                print("\n--- FOUND IT! Records with zaman_str == '07:00' ---")
                print(target_culprits.to_string())
            else:
                print("\nNo records found with zaman_str == '07:00'")
                
            # Show all unique values starting with "0"
            print("\nUnique values starting with '0':")
            print([z for z in df_matris['zaman_str'].unique() if str(z).startswith('0')])
    except Exception as e:
        print(f"Audit failed: {e}")

if __name__ == "__main__":
    audit_timestamps()
