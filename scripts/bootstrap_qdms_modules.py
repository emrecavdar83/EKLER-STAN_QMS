from sqlalchemy import text
import sys
import os

sys.path.append(os.getcwd())
from database.connection import get_engine

def bootstrap_modules():
    engine = get_engine()
    print("Modüller kaydediliyor...")
    try:
        with engine.connect() as conn:
            # Modülleri ekle
            conn.execute(text("INSERT OR IGNORE INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES ('qdms_merkez', '📋 Doküman Merkezi', 80, 1)"))
            conn.execute(text("INSERT OR IGNORE INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES ('qdms_admin', '⚙️ Belge Yönetimi', 81, 1)"))
            
            # Yetkileri ekle
            y_data = [
                ('ADMIN', 'qdms_merkez', 'Düzenle'),
                ('ADMIN', 'qdms_admin', 'Düzenle'),
                ('KALITE SORUMLUSU', 'qdms_merkez', 'Düzenle'),
                ('KALITE SORUMLUSU', 'qdms_admin', 'Düzenle'),
                ('OPERATOR', 'qdms_merkez', 'Görüntüle')
            ]
            
            for rol, mod, erisim in y_data:
                conn.execute(text("INSERT OR IGNORE INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (:r, :m, :e)"), {"r": rol, "m": mod, "e": erisim})
            
            conn.commit()
        print("BOOTSTRAP SUCCESS")
    except Exception as e:
        print(f"BOOTSTRAP FAILED: {str(e)}")

if __name__ == "__main__":
    bootstrap_modules()
