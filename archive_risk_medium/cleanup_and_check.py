import sqlite3
import pandas as pd

def cleanup_and_check():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Delete specified records (1, 2, 3, 4)
    ids_to_delete = (1, 2, 3, 4)
    print(f"Deleting personnel with IDs: {ids_to_delete}")
    cursor.execute(f"DELETE FROM personnel WHERE id IN {ids_to_delete}")
    deleted_count = cursor.rowcount
    conn.commit()
    print(f"Deleted {deleted_count} records.")

    # 2. Check for similarities to 'AHMAD KOURANI'
    # We look for names containing 'AHMAD' or 'KOURANI'
    print("\nSearching for similar names to 'AHMAD KOURANI'...")
    query = """
    SELECT id, ad_soyad 
    FROM personnel 
    WHERE ad_soyad LIKE '%AHMAD%' 
       OR ad_soyad LIKE '%KOURANI%'
       OR ad_soyad LIKE '%AHMET%'
    """
    similar_df = pd.read_sql(query, conn)
    
    conn.close()

    if not similar_df.empty:
        print("\nFound the following similar records:")
        print(similar_df.to_string(index=False))
    else:
        print("\nNo similar records found.")

if __name__ == "__main__":
    cleanup_and_check()
