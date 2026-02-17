import sqlite3
import pandas as pd
from sqlalchemy import create_engine
import toml
import os

def check():
    local_url = "sqlite:///C:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db"
    engine = create_engine(local_url)
    
    print("### PERSONEL TABLE COLUMNS ###")
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM personel LIMIT 1", conn)
        print(df.columns.tolist())

if __name__ == "__main__":
    check()
