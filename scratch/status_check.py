import sys
import os
from sqlalchemy import text
import subprocess

# Add workspace to path
sys.path.append(os.getcwd())

from database.connection import get_engine

def check_status():
    print("--- SYSTEM STATUS CHECK ---")
    
    # 1. DB Check
    try:
        engine = get_engine()
        with engine.connect() as conn:
            res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
            tables = [r[0] for r in res]
            print(f"Tables found: {tables}")
            
            if 'ayarlar_kullanicilar' in tables:
                count = conn.execute(text("SELECT count(*) FROM ayarlar_kullanicilar")).scalar()
                print(f"SUCCESS: 'ayarlar_kullanicilar' exists with {count} records.")
            else:
                print("WARNING: 'ayarlar_kullanicilar' table NOT FOUND.")
                
            if 'personel' in tables:
                count = conn.execute(text("SELECT count(*) FROM personel")).scalar()
                print(f"INFO: Legacy 'personel' table still exists with {count} records.")
    except Exception as e:
        print(f"DB ERROR: {e}")

    # 2. Codebase Check (References to 'personel')
    print("\n--- CODEBASE REFERENCES ---")
    try:
        # Check how many files still contain the word 'personel' (excluding common exclusions)
        # Using git grep if available, or just a simple find/grep
        cmd = ["grep", "-r", "personel", ".", "--exclude-dir=.git", "--exclude-dir=.antigravity", "--include=*.py", "-l"]
        # On Windows, we might need a different approach or rely on git bash if available.
        # Let's try a safer way via python count.
        pers_ref_count = 0
        for root, dirs, files in os.walk('.'):
            if any(x in root for x in ['.git', '.antigravity', '__pycache__', 'node_modules', 'logs']): continue
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            if 'personel' in f.read().lower():
                                pers_ref_count += 1
                    except: pass
        print(f"Python files still referencing 'personel': {pers_ref_count}")
    except Exception as e:
        print(f"CODE CHECK ERROR: {e}")

    # 3. Log Check
    print("\n--- ERROR LOG ANALYSIS ---")
    try:
        log_path = "logs/error_blackbox.log"
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                last_lines = f.readlines()[-20:]
                print(f"Last 20 lines of log analyzed. Any 'ValueError: password cannot be longer than 72 bytes'? {'YES' if any('72 bytes' in l for l in last_lines) else 'NO'}")
        else:
            print("Log file not found.")

    except Exception as e:
        print(f"GENERAL ERROR: {e}")

if __name__ == "__main__":
    check_status()
