import sqlite3
import pandas as pd
import os

def main():
    db_path = 'ekleristan_local.db'
    if not os.path.exists(db_path):
        print("DB yok!")
        return

    conn = sqlite3.connect(db_path)
    
    print("=== 1. MIGRATION DURUMU ===")
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(personel)")
        cols = [c[1] for c in cursor.fetchall()]
        target_cols = ['departman_id', 'yonetici_id', 'pozisyon_seviye']
        missing = [c for c in target_cols if c not in cols]
        
        if missing:
            print(f"[HATA] Eksik Kolonlar: {missing}")
        else:
            print("[OK] Tum sema kolonlari mevcut (departman_id, yonetici_id, pozisyon_seviye)")
            
        # View check
        try:
            cnt = cursor.execute("SELECT count(*) FROM v_organizasyon_semasi").fetchone()[0]
            print(f"[OK] View 'v_organizasyon_semasi' calisiyor (Satir: {cnt})")
        except Exception as e:
            print(f"[HATA] View Hatasi: {e}")

    except Exception as e:
        print(f"[HATA] DB Hatasi: {e}")

    print("\n=== 2. VERI SENKRONIZASYON DURUMU ===")
    sync_check_list = [
        ('personel', 'personel.csv'),
        ('lokasyonlar', 'lokasyonlar.csv'),
        ('ayarlar_bolumler', 'ayarlar_bolumler.csv')
    ]
    
    for table, csv_name in sync_check_list:
        csv_path = os.path.join('data_sync', csv_name)
        if os.path.exists(csv_path):
            try:
                # CSV encoding issue prevention
                try:
                    df_csv = pd.read_csv(csv_path)
                except:
                    df_csv = pd.read_csv(csv_path, encoding='cp1254') # Fallback
                
                csv_cnt = len(df_csv)
                
                try:
                    db_cnt = cursor.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    
                    diff = csv_cnt - db_cnt
                    if diff == 0:
                        icon = "[OK]"
                        state = "Senkronize"
                    elif diff > 0:
                        icon = "[UYARI]" 
                        state = f"Eksik ({diff} kayit)"
                    else:
                        icon = "[UYARI]"
                        state = f"Fazla ({abs(diff)} kayit)"
                        
                    print(f"{icon} {table.ljust(20)}: Canli(CSV)={csv_cnt:<4} | Yerel(DB)={db_cnt:<4} | Durum: {state}")
                    
                except Exception as e:
                    print(f"[HATA] {table.ljust(20)}: Tablo DB sorgu hatasi: {e}")
            except Exception as e:
                print(f"[HATA] {csv_name} okuma hatasi: {e}")
        else:
            print(f"[BILGI] {csv_name} dosyasi yok (henuz cekilmemis)")

    conn.close()

if __name__ == "__main__":
    main()
