import os
import json
import toml
import shutil
import sys
from sqlalchemy import create_engine, text

BACKUP_FILE = "qdms_refactor_backup.json"
FILES_TO_BACKUP = ["app.py", "logic/auth_logic.py"]

def get_db_engine():
    secrets = toml.load(".streamlit/secrets.toml")
    return create_engine(secrets["streamlit"]["DB_URL"])

def backup():
    print("--- BACKUP STARTED ---")
    engine = get_db_engine()
    backup_data = {"db": {"moduller": [], "yetkiler": []}, "files": {}}
    
    old_keys = ['dokuman_merkezi', 'belge_yonetimi', 'talimatlar', 'uyumluluk']
    
    with engine.connect() as conn:
        res_m = conn.execute(text("SELECT * FROM public.ayarlar_moduller WHERE modul_anahtari IN :keys"), {"keys": tuple(old_keys)}).fetchall()
        backup_data["db"]["moduller"] = [dict(r._mapping) for r in res_m]
        
        res_y = conn.execute(text("SELECT * FROM public.ayarlar_yetkiler WHERE modul_adi IN :keys"), {"keys": tuple(old_keys)}).fetchall()
        backup_data["db"]["yetkiler"] = [dict(r._mapping) for r in res_y]
    
    for f in FILES_TO_BACKUP:
        if os.path.exists(f):
            shutil.copy(f, f + ".bak")
            print(f"File backup created: {f}.bak")

    with open(BACKUP_FILE, "w", encoding="utf-8") as bf:
        json.dump(backup_data, bf, ensure_ascii=False, indent=4, default=str)
    print(f"Database backup saved to {BACKUP_FILE}")

def deploy():
    print("--- DEPLOY STARTED (ATOMIC DB) ---")
    engine = get_db_engine()
    old_keys = ['dokuman_merkezi', 'belge_yonetimi', 'talimatlar', 'uyumluluk']
    
    with engine.begin() as conn:
        # 1. Calculate 'Restrictive' perms for 'qdms' key
        # We'll fetch all unique roles that had any of the 4 perms
        roles = conn.execute(text("SELECT DISTINCT rol_adi FROM public.ayarlar_yetkiler WHERE modul_adi IN :keys"), {"keys": tuple(old_keys)}).fetchall()
        
        for r in roles:
            rol_adi = r[0]
            # Get perms for this role across the 4 modules
            perms = conn.execute(text("SELECT erisim_turu FROM public.ayarlar_yetkiler WHERE rol_adi = :r AND modul_adi IN :keys"), 
                                 {"r": rol_adi, "keys": tuple(old_keys)}).fetchall()
            
            # Restrictive logic: Yok < Görüntüle < Düzenle < Tam Yetki
            perm_levels = {"Yok": 0, "Görüntüle": 1, "Düzenle": 2, "Tam Yetki": 3}
            inv_levels = {0: "Yok", 1: "Görüntüle", 2: "Düzenle", 3: "Tam Yetki"}
            
            # Find minimum if we had all 4 (but if some missing, it's effectively 'Yok')
            if len(perms) < 4:
                min_level = 0
            else:
                min_level = min([perm_levels.get(p[0], 0) for p in perms])
            
            final_perm = inv_levels[min_level]
            
            # Special case for ADMIN (always Düzenle for navigation visibility)
            if rol_adi.upper() == 'ADMIN':
                final_perm = 'Düzenle'

            conn.execute(text("""
                INSERT INTO public.ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu)
                VALUES (:r, 'qdms', :p)
                ON CONFLICT (rol_adi, modul_adi) DO UPDATE SET erisim_turu = :p
            """), {"r": rol_adi, "p": final_perm})

        # 2. Cleanup old perms
        conn.execute(text("DELETE FROM public.ayarlar_yetkiler WHERE modul_adi IN :keys"), {"keys": tuple(old_keys)})
        
        # 3. Cleanup and Update modules
        conn.execute(text("DELETE FROM public.ayarlar_moduller WHERE modul_anahtari IN :keys"), {"keys": tuple(old_keys)})
        conn.execute(text("""
            INSERT INTO public.ayarlar_moduller (modul_anahtari, modul_etiketi, aktif, sira_no)
            VALUES ('qdms', '📁 QDMS', 1, 71)
            ON CONFLICT (modul_anahtari) DO UPDATE SET aktif = 1, sira_no = 71;
        """))
    print("Database migration finished successfully.")

def rollback():
    print("--- ROLLBACK STARTED ---")
    if not os.path.exists(BACKUP_FILE):
        print("Error: Backup file not found.")
        return

    with open(BACKUP_FILE, "r", encoding="utf-8") as bf:
        data = json.load(bf)

    engine = get_db_engine()
    with engine.begin() as conn:
        # Delete new key
        conn.execute(text("DELETE FROM public.ayarlar_moduller WHERE modul_anahtari = 'qdms'"))
        conn.execute(text("DELETE FROM public.ayarlar_yetkiler WHERE modul_adi = 'qdms'"))
        
        # Restore old modules
        for m in data["db"]["moduller"]:
            conn.execute(text("""
                INSERT INTO public.ayarlar_moduller (modul_anahtari, modul_etiketi, aktif, sira_no)
                VALUES (:ma, :me, :ak, :sn)
            """), {"ma": m["modul_anahtari"], "me": m["modul_etiketi"], "ak": m["aktif"], "sn": m["sira_no"]})
            
        # Restore old perms
        for y in data["db"]["yetkiler"]:
            conn.execute(text("""
                INSERT INTO public.ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu)
                VALUES (:ra, :ma, :et)
                ON CONFLICT (rol_adi, modul_adi) DO UPDATE SET erisim_turu = :et
            """), {"ra": y["rol_adi"], "ma": y["modul_adi"], "et": y["erisim_turu"]})

    for f in FILES_TO_BACKUP:
        if os.path.exists(f + ".bak"):
            shutil.copy(f + ".bak", f)
            print(f"File restored: {f}")
    print("Rollback finished successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python refactor_qdms_nav.py [backup|deploy|rollback]")
    elif sys.argv[1] == "backup":
        backup()
    elif sys.argv[1] == "deploy":
        deploy()
    elif sys.argv[1] == "rollback":
        rollback()
