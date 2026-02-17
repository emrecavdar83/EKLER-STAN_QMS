from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- SEARCHING MEHRİMAN ALİ ---")
        
        # 1. List Everyone in RULO PASTA (ID 22)
        print("\n--- Personnel in RULO PASTA (ID 22) ---")
        sql_dept = text("SELECT * FROM personel WHERE departman_id = 22")
        users = conn.execute(sql_dept).fetchall()
        for u in users:
            print(f"ID: {u.id}, Name: {u.ad_soyad}, Role: {u.rol}")

        # 2. Broad Search
        print("\n--- Broad Name Search (ALI) ---")
        sql_broad = text("SELECT * FROM personel WHERE ad_soyad LIKE '%ALİ%' OR ad_soyad LIKE '%ALI%'")
        matches = conn.execute(sql_broad).fetchall()
        for m in matches:
            print(f"Match: {m.ad_soyad} | DeptID: {m.departman_id}")

except Exception as e:
    print(e)
