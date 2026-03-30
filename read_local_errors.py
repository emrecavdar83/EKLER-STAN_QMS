import sqlite3
import pandas as pd

def show_recent_errors():
    try:
        conn = sqlite3.connect('ekleristan_local.db')
        # En son oluşan 10 hatayı çek
        query = "SELECT zaman, hata_kodu, modul, hata_mesaji FROM hata_loglari ORDER BY zaman DESC LIMIT 10"
        df = pd.read_sql_query(query, conn)
        
        with open('RECENT_ERRORS.txt', 'w', encoding='utf-8') as f:
            if df.empty:
                f.write("Henüz yerel veritabanında kayıtlı hata bulunamadı. Lütfen Ayarlar sayfasından senkronizasyonu çalıştırın.")
            else:
                f.write(df.to_markdown())
        conn.close()
    except Exception as e:
        with open('RECENT_ERRORS.txt', 'w', encoding='utf-8') as f:
            f.write(f"Hata okunurken teknik bir sorun oluştu: {e}")

if __name__ == "__main__":
    show_recent_errors()
