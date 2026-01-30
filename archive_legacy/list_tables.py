import pandas as pd
from sqlalchemy import create_engine, inspect

LOCAL_DB_URL = 'sqlite:///ekleristan_local.db'
engine = create_engine(LOCAL_DB_URL)

inspector = inspect(engine)
tables = inspector.get_table_names()

print("Tables in ekleristan_local.db:")
for table in tables:
    print(f"- {table}")
