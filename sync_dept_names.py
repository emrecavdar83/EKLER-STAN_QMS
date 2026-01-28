from sqlalchemy import create_engine, text

import sys
sys.stdout.reconfigure(encoding='utf-8')

# Veritabanı bağlantısı
engine = create_engine('sqlite:///ekleristan_local.db')

def sync_department_names():
    """
    Personel tablosundaki departman isimlerini, ID'lere göre ayarlar_bolumler tablosundan günceller.
    Bu, ID değişikliği olmayan ancak isim düzeltmesi yapılan durumlarda (örn: 'Üretim ' -> 'Üretim')
    personel listesinin doğru görünmesini sağlar.
    """
    print("[BILGI] Departman isimleri esitleniyor...")
    
    with engine.connect() as conn:
        # 1. Departman ID ve İsimlerini al
        depts = conn.execute(text("SELECT id, bolum_adi FROM ayarlar_bolumler")).fetchall()
        dept_map = {d[0]: d[1] for d in depts}
        
        print(f"   -> {len(dept_map)} departman bulundu.")
        
        # 2. Personel tablosunu ID'ye göre güncelle
        updated_count = 0
        for d_id, d_name in dept_map.items():
            # ID'si eslesen personelin bolum bilgisini guncelle
            # 'departman_adi' kolonu yoksa sadece 'bolum'u guncelle
            sql = text("UPDATE personel SET bolum = :d_name WHERE departman_id = :d_id")
            result = conn.execute(sql, {"d_name": d_name, "d_id": d_id})
            updated_count += result.rowcount
            
        conn.commit()
        print(f"   [OK] {updated_count} personel kaydi guncellendi.")

if __name__ == "__main__":
    sync_department_names()
