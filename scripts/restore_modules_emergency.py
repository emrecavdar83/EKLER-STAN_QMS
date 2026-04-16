
import sqlite3
import os
import sys

# Set encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

def restore_modules():
    db_path = 'c:/Projeler/S_program/EKLER/ekleristan_local.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Full module list from auth_logic.py
    modules = [
        ("portal", "🏠 Portal (Ana Sayfa)", 10),
        ("uretim_girisi", "🏭 Üretim Girişi", 20),
        ("map_uretim", "📦 MAP Üretim", 30),
        ("kpi_kontrol", "🍩 KPI & Kalite Kontrol", 40),
        ("gmp_denetimi", "🛡️ GMP Denetimi", 50),
        ("personel_hijyen", "🧼 Personel Hijyen", 60),
        ("temizlik_kontrol", "🧹 Temizlik Kontrol", 70),
        ("soguk_oda", "❄️ Soğuk Oda Sıcaklıkları", 80),
        ("performans_polivalans", "📈 Yetkinlik & Performans", 90),
        ("kurumsal_raporlama", "📊 Kurumsal Raporlama", 100),
        ("qdms", "📁 QDMS", 110),
        ("ayarlar", "⚙️ Ayarlar", 120)
    ]

    print("Restoring modules to ayarlar_moduller...")
    try:
        # 1. UPSERT modules
        for slug, label, order in modules:
            # Check if ON CONFLICT logic matches the schema (id is PK, slug is UNIQUE)
            cur.execute("""
                INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, aktif, sira_no)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(modul_anahtari) DO UPDATE SET
                    modul_etiketi = excluded.modul_etiketi,
                    aktif = 1,
                    sira_no = excluded.sira_no
            """, (slug, label, order))
            # Safe print
            print(f"  - Restored: {slug}")
        
        # 2. Add default permissions for ADMIN only if they don't exist
        # Rol_adi and modul_adi are the likely unique constraint members
        print("\nUpdating ADMIN permissions...")
        for slug, label, order in modules:
            try:
                cur.execute("""
                    INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu, sadece_kendi_bolumu)
                    VALUES ('ADMIN', ?, 'Düzenle', 0)
                """, (slug,))
            except sqlite3.IntegrityError:
                # Already exists, update it to ensure 'Düzenle' access
                cur.execute("""
                    UPDATE ayarlar_yetkiler SET erisim_turu = 'Düzenle' 
                    WHERE rol_adi = 'ADMIN' AND modul_adi = ?
                """, (slug,))
            
        conn.commit()
        print("\nModule restoration completed successfully.")
    except Exception as e:
        print(f"Error during restoration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    restore_modules()
