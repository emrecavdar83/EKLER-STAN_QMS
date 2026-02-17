import sqlite3
import pandas as pd

def migrate_db():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- 1. Şema Güncellemesi: Eksik Sütunları Ekleme ---")
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(personnel)")
        cols = [info[1] for info in cursor.fetchall()]
        
        if 'departman_id' not in cols:
            print("'departman_id' sütunu ekleniyor...")
            cursor.execute("ALTER TABLE personnel ADD COLUMN departman_id INTEGER DEFAULT 0")
        else:
            print("'departman_id' zaten mevcut.")

        if 'yonetici_id' not in cols:
            print("'yonetici_id' sütunu ekleniyor...")
            cursor.execute("ALTER TABLE personnel ADD COLUMN yonetici_id INTEGER DEFAULT 0")
        else:
            print("'yonetici_id' zaten mevcut.")
            
        conn.commit()
    except Exception as e:
        print(f"Tablo yapısı değiştirilirken hata oluştu: {e}")
        conn.close()
        return

    print("\n--- 2. Veri Göçü: 'bolum' alanını 'departman_id' ile eşleştirme ---")
    try:
        # Load Departments Map
        df_depts = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", conn)
        # Create a dictionary for lookup: cleaned name -> id
        # Normalize: UPPERCASE 
        dept_map = {name.upper().strip(): id for id, name in zip(df_depts['id'], df_depts['bolum_adi']) if name}
        
        print(f"'ayarlar_bolumler' tablosundan {len(dept_map)} departman yüklendi.")
        
        # Load Personnel
        df_pers = pd.read_sql("SELECT id, bolum FROM personnel", conn)
        print(f"{len(df_pers)} personel kaydı yüklendi.")
        
        updated_count = 0
        unknown_departments = set()
        
        for index, row in df_pers.iterrows():
            p_id = row['id']
            p_bolum = row['bolum']
            
            if not p_bolum:
                continue
                
            p_bolum_clean = p_bolum.upper().strip()
            
            if p_bolum_clean in dept_map:
                dept_id = int(dept_map[p_bolum_clean])
                cursor.execute("UPDATE personnel SET departman_id = ? WHERE id = ?", (dept_id, p_id))
                updated_count += 1
            else:
                unknown_departments.add(p_bolum)
        
        conn.commit()
        print(f"{updated_count} personel kaydı 'departman_id' ile başarıyla güncellendi.")
        
        # Kullanıcının "olduğu gibi kalsın" dediği bölümler
        allowed_unmapped = {
             "İDARİ PERSONEL", "KALİTE MÜDÜRÜ", "İ.K.", 
             "GIDA MÜH.", "SEVKİYAT", "EKİP SORUMLUSU"
        }
        
        real_unknowns = set()
        kept_as_is = set()
        
        for d in unknown_departments:
            if d.upper().strip() in allowed_unmapped:
                kept_as_is.add(d)
            else:
                real_unknowns.add(d)

        if real_unknowns:
            print(f"\nUYARI: Şu departmanlar eşleştirilemedi (0/NULL olarak bırakıldı):")
            for d in real_unknowns:
                print(f" - {d}")
                
        if kept_as_is:
            print(f"\nBİLGİ: Şu bölümler kullanıcı isteği üzerine olduğu gibi bırakıldı:")
            for d in kept_as_is:
                print(f" - {d}")
                
    except Exception as e:
        print(f"Veri göçü sırasında hata oluştu: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
