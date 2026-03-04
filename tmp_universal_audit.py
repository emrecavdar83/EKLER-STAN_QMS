import sqlite3
import datetime
import sys

# Windows konsolunda Unicode hatalarını önlemek için kodlamayı manuel ayarla
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def universal_test():
    conn = sqlite3.connect('ekleristan_local.db')
    c = conn.cursor()
    
    print("=== UNIVERSAL SOSTS AUDIT (UTF-8) ===")
    
    c.execute("SELECT id, oda_adi, oda_kodu FROM soguk_odalar WHERE aktif = 1")
    rooms = c.fetchall()
    
    for id, name, code in rooms:
        print(f"\nAUDIT: {name} ({code}) [ID: {id}]")
        
        c.execute("SELECT COUNT(*) FROM olcum_plani WHERE oda_id = ?", (id,))
        slot_count = c.fetchone()[0]
        print(f"  - Plan Slot Sayisi: {slot_count}")

        c.execute("SELECT id, beklenen_zaman FROM olcum_plani WHERE oda_id = ? AND durum IN ('BEKLIYOR', 'GECIKTI') ORDER BY ABS(strftime('%s', beklenen_zaman) - strftime('%s', 'now', '+3 hours')) LIMIT 1", (id,))
        slot = c.fetchone()
        if slot:
            print(f"  - Gelecek Slot: {slot[1]}")
        else:
            print("  - [!] HATA: Eşleşen slot bulunamadı.")

if __name__ == "__main__":
    universal_test()
