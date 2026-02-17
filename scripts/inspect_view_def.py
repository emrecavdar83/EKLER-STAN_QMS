import sqlite3

def inspect_view():
    try:
        conn = sqlite3.connect('ekleristan_local.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='v_organizasyon_semasi'")
        result = cursor.fetchone()
        
        if result:
            print(f"View Definition:\n{result[0]}")
        else:
            print("View 'v_organizasyon_semasi' not found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_view()
