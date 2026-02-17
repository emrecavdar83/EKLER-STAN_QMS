import sqlite3
import pandas as pd

DB_PATH = "ekleristan_local.db"

def auto_assign_managers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("--- Yonetici Atama Islemi Basliyor ---")

    # 1. Mevcut Yoneticileri (Seviye < 5) Tespit Et
    # Dictionary: {DepartmanID: {Level: PersonelID}}
    managers_by_dept = {}
    
    # Seviyesi 5'ten kucuk olanlari cek (Mudur, Sef vb.)
    df_managers = pd.read_sql("SELECT id, departman_id, pozisyon_seviye FROM personel WHERE pozisyon_seviye < 5 AND durum='AKTİF'", conn)
    
    for _, row in df_managers.iterrows():
        dept = row['departman_id']
        lvl = row['pozisyon_seviye']
        pid = row['id']
        
        if dept not in managers_by_dept:
            managers_by_dept[dept] = {}
        
        # Ayni seviyede birden fazla kisi varsa sonuncuyu alir (Simdilik basit mantik)
        managers_by_dept[dept][lvl] = pid

    print(f"Yonetici Bulunan Departman Sayisi: {len(managers_by_dept)}")

    # 2. Departman Hiyerarsisini Cek
    # Dictionary: {AltDeptID: UstDeptID}
    df_depts = pd.read_sql("SELECT id, ana_departman_id FROM ayarlar_bolumler", conn)
    dept_parents = {}
    for _, row in df_depts.iterrows():
        if pd.notna(row['ana_departman_id']) and row['ana_departman_id'] > 0:
            dept_parents[row['id']] = int(row['ana_departman_id'])

    # 3. Personellere Yonetici Ata
    # HEDEF: Kendi departmanindaki EN DUSUK seviyeli yoneticiye bagla (Orn: Sef'e).
    # Sef yoksa Mudur'e bagla.
    # Hicbiri yoksa UST departmanin Mudurune bagla.
    
    df_staff = pd.read_sql("SELECT id, departman_id, pozisyon_seviye FROM personel WHERE durum='AKTİF'", conn)
    
    updates = []
    
    for _, row in df_staff.iterrows():
        pid = row['id']
        dept = row['departman_id']
        lvl = row['pozisyon_seviye']
        
        # Yoneticiye ihtiyaci olmayanlar (Seviye 0 veya 1 - Yonetim Kurulu / CEO)
        if lvl <= 1:
            continue

        assigned_manager_id = 0
        
        # A. Kendi Departmanindaki Yoneticiler
        if dept in managers_by_dept:
            dept_mgrs = managers_by_dept[dept]
            # Kendi seviyesinden daha dusuk (daha kidemli) birini bul
            for mgr_lvl in sorted(dept_mgrs.keys(), reverse=True): # 4, 3, 2... diye bak (En yakin amir)
                if mgr_lvl < lvl:
                    assigned_manager_id = dept_mgrs[mgr_lvl]
                    break
        
        # B. Kendi departmaninda bulamazsak, ANA departmana bak
        if assigned_manager_id == 0:
            current_dept = dept
            # 3 seviye yukari cikabiliriz
            for _ in range(3):
                if current_dept in dept_parents:
                    parent_dept = dept_parents[current_dept]
                    if parent_dept in managers_by_dept:
                        parent_mgrs = managers_by_dept[parent_dept]
                        # Parent departmandaki en kidemsiz yoneticiyi sec (Genelde o departmanin amiri)
                        # Ama garantilemek icin en yuksek rakamli (en dusuk kidemli) yoneticiyi alalim
                        # Orn: Uretim (Mudur lvl 3, Sef lvl 4) -> Sefe baglasin
                        # DUZELTME: Ust departmana baglaniyorsak direkt o departmanin BASINA (en dusuk level) baglanmali
                        # Cunku Krema bolumu -> Uretim Mudurune baglanir.
                        min_lvl = min(parent_mgrs.keys())
                        assigned_manager_id = parent_mgrs[min_lvl]
                        break
                    current_dept = parent_dept
                else:
                    break

        if assigned_manager_id > 0 and assigned_manager_id != pid:
             updates.append((int(assigned_manager_id), int(pid)))

    # 4. Guncellemeleri Uygula
    print(f"Toplam {len(updates)} personele yonetici atanacak.")
    
    cursor.executemany("UPDATE personel SET yonetici_id = ? WHERE id = ?", updates)
    conn.commit()
    
    # View'i guncellemek icin tekrar fix scriptinin view kismini calistirmaya gerek yok, view dinamik.
    # Ancak cache temizligi gerekebilir.
    
    conn.close()
    print("Islem Tamamlandi.")

if __name__ == "__main__":
    auto_assign_managers()
