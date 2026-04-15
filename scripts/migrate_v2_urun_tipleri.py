import sqlite3
import os

DB_PATH = "ekleristan_local.db"

def add_column_safe(cursor, table_name, column_name, column_type, default_val=None):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_val is not None:
                if isinstance(default_val, str): query += f" DEFAULT '{default_val}'"
                else: query += f" DEFAULT {default_val}"
            cursor.execute(query)
            print(f"SUCCESS: {table_name} table '{column_name}' column added.")
    except Exception as e: print(f"ERROR: '{column_name}' addition failed: {e}")

def run_migration():
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. urun_tipi kolonu (MAMUL / YARI MAMUL)
    add_column_safe(cursor, "ayarlar_urunler", "urun_tipi", "TEXT", default_val="MAMUL")

    # 2. sistem_parametreleri - Ürün Kategorileri
    cursor.execute("SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'urun_kategorileri'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO sistem_parametreleri (anahtar, deger, aciklama)
            VALUES ('urun_kategorileri', '["MAMUL", "YARI MAMUL"]', 'Ürün tipi seçenekleri (Dinamik Selectbox)')
        """)
        print("SUCCESS: sistem_parametreleri: 'urun_kategorileri' added.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migration()
