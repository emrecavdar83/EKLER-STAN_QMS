import toml
from sqlalchemy import create_engine, inspect

def check_live_tables():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    inspector = inspect(engine)
    schemas = inspector.get_schema_names()
    print(f"Schemas: {schemas}")
    for s in schemas:
        tables = inspector.get_table_names(schema=s)
        print(f"Tables in schema '{s}':")
        for t in tables:
            if 'qdms' in t or 'ayarlar' in t:
                print(f"- {t}")

if __name__ == "__main__":
    check_live_tables()
