import os, sys
sys.path.append(os.getcwd())
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine

def cloud_cleanup():
    print("Initiating Cloud Cleanup Protocol (Faz 3)...")
    engine = get_engine()
    is_pg = engine.dialect.name == 'postgresql'
    
    if not is_pg:
        print("Error: Not connected to Cloud (PostgreSQL). Operation aborted.")
        return

    try:
        with engine.connect() as conn:
            # ADIM 1: Eski satirlari temizle
            print("ADIM 1: Deleting legacy (aktif=0) rows...")
            delete_sql = """
                DELETE FROM ayarlar_moduller
                WHERE aktif = 0
                AND modul_anahtari IN (
                    'uretim_girisi', 'kpi_kontrol', 'gmp_denetimi',
                    'personel_hijyen', 'temizlik_kontrol',
                    'kurumsal_raporlama', 'soguk_oda', 'ayarlar'
                )
            """
            result = conn.execute(text(delete_sql))
            deleted_count = result.rowcount
            print(f"DONE: {deleted_count} rows deleted (Expected: 8).")
            
            # ADIM 2: Aktif satirlari dogrula
            print("\nADIM 2: Verifying active (aktif=1) rows...")
            verify_sql = "SELECT id, modul_anahtari, modul_etiketi, sira_no, aktif FROM ayarlar_moduller WHERE aktif = 1 ORDER BY sira_no"
            df = pd.read_sql(text(verify_sql), conn)
            active_count = len(df)
            print(f"DONE: {active_count} active rows found (Expected: 11).")
            
            print("\nActive Table Snapshot (Safe Print):")
            print(df.to_string(index=False).encode('ascii', errors='replace').decode())
            
            # Record results to a file for report
            with open("faz3_cloud_report.txt", "w", encoding="utf-8") as rf:
                rf.write("FAZ 3: CLOUD CLEANUP REPORT\n")
                rf.write("-" * 30 + "\n")
                rf.write(f"Deleted Rows (aktif=0): {deleted_count}\n")
                rf.write(f"Active Rows (aktif=1): {active_count}\n")
                rf.write("\nFinal Modul List:\n")
                rf.write(df.to_string(index=False))
            
            conn.commit()
            print("\nCleanup Successful. Reports saved to faz3_cloud_report.txt")
            
    except Exception as e:
        print(f"Cleanup Failed: {e}")

if __name__ == "__main__":
    cloud_cleanup()
