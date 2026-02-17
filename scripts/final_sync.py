import sqlite3
import re

def normalize_name_for_sync(name):
    if not name: return ""
    # Remove extra spaces inside
    name = re.sub(r'\s+', ' ', str(name)).strip()
    return name.upper().replace('İ','I').replace('Ğ','G').replace('Ü','U').replace('Ş','S').replace('Ö','O').replace('Ç','C').replace(' ','')

def final_sync():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("--- NİHAİ TEMİZLİK VE SENKRONİZASYON (182 HEDEF) ---")
    
    # 1. İsimlerdeki çift boşlukları ve gereksiz boşlukları temizle
    cursor.execute("SELECT id, ad_soyad FROM personel")
    rows = cursor.fetchall()
    for pid, name in rows:
        clean_name = re.sub(r'\s+', ' ', name).strip()
        if clean_name != name:
            cursor.execute("UPDATE personel SET ad_soyad = ? WHERE id = ?", (clean_name, pid))
            print(f"İsim düzeltildi: '{name}' -> '{clean_name}'")

    # 2. Master Listeyi Oku (182 kişi)
    master_names_norm = []
    try:
        with open('personnel_update_20260131.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:] # Header
            for line in lines:
                parts = line.split('\t')
                if len(parts) > 1:
                    master_names_norm.append(normalize_name_for_sync(parts[1]))
    except Exception as e:
        print(f"Hata: {e}")

    # 3. Senkronize Et (Master'da yoksa PASİF yap)
    cursor.execute("SELECT id, ad_soyad FROM personel WHERE durum = 'AKTİF'")
    db_rows = cursor.fetchall()
    deactivated = 0
    for pid, name in db_rows:
        if normalize_name_for_sync(name) not in master_names_norm:
            cursor.execute("UPDATE personel SET durum = 'PASİF' WHERE id = ?", (pid,))
            deactivated += 1
            print(f"Pasife alındı: {name}")

    conn.commit()
    
    # 4. Sayım
    cursor.execute("SELECT COUNT(*) FROM personel WHERE durum = 'AKTİF'")
    final_count = cursor.fetchone()[0]
    print(f"\nSonuç: {final_count} aktif personel (Master: {len(master_names_norm)})")
    
    conn.close()

if __name__ == "__main__":
    final_sync()
