import pandas as pd
from sqlalchemy import create_engine
import sys

# Set output encoding to utf-8 for Windows console compatibility
sys.stdout.reconfigure(encoding='utf-8')

engine = create_engine('sqlite:///ekleristan_local.db')

# Write to file
try:
    with open('hakan_utf8.txt', 'w', encoding='utf-8') as f:
        try:
            df = pd.read_sql("SELECT * FROM personel WHERE ad_soyad LIKE '%Hakan Özalp%'", engine)
            if df.empty:
                f.write("No record found for Hakan Özalp")
            else:
                f.write(df.T.to_string())
        except Exception as e:
            f.write(f"Error: {e}")
    print("Output written to hakan_utf8.txt")
except Exception as e:
    print(f"Error writing to file: {e}")

