import pandas as pd
from sqlalchemy import create_engine, text

# Local DB Connection
engine = create_engine('sqlite:///ekleristan_local.db')


# Write to file
try:
    with open('inspect_output_utf8.txt', 'w', encoding='utf-8') as f:
        f.write("--- 1. Raw Personnel Data (First 20) ---\n")
        try:
            df = pd.read_sql("SELECT id, ad_soyad, gorev, rol, pozisyon_seviye, departman_id FROM personel WHERE ad_soyad IS NOT NULL LIMIT 20", engine)
            f.write(df.to_string() + "\n")
        except Exception as e:
            f.write(f"Error reading personel table: {e}\n")

        f.write("\n--- 2. View 'v_organizasyon_semasi' Check ---\n")
        try:
            df_view = pd.read_sql("SELECT * FROM v_organizasyon_semasi LIMIT 5", engine)
            f.write(df_view.to_string() + "\n")
        except Exception as e:
            f.write(f"View not found or error: {e}\n")
            f.write("System is likely using the fallback query in app.py\n")

        f.write("\n--- 3. Fallback Query Simulation ---\n")
        try:
            sql = """
                SELECT 
                    p.id, p.ad_soyad, p.gorev, p.rol, 
                    COALESCE(d.bolum_adi, 'Tanımsız') as departman_adi,
                    COALESCE(p.pozisyon_seviye, 5) as pozisyon_seviye
                FROM personel p
                LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
                WHERE p.ad_soyad IS NOT NULL
                ORDER BY p.pozisyon_seviye ASC LIMIT 20
            """
            df_fallback = pd.read_sql(sql, engine)
            f.write(df_fallback.to_string() + "\n")
        except Exception as e:
            f.write(f"Fallback query error: {e}\n")
            
    print("Output written to inspect_output_utf8.txt")
except Exception as e:
    print(f"Error writing to file: {e}")

