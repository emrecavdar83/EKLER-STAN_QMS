
import os
import sys
import toml
from sqlalchemy import create_engine, text

# Set encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

def get_engine_manual():
    """Manual engine creation for scripts outside Streamlit runtime."""
    secrets_path = '.streamlit/secrets.toml'
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
        if db_url:
            print(f"Connecting to Cloud DB: {db_url.split('@')[-1]}")
            return create_engine(db_url)
    
    print("Connecting to Local SQLite DB...")
    return create_engine('sqlite:///ekleristan_local.db')

def sync_modules():
    engine = get_engine_manual()
    is_pg = 'postgresql' in str(engine.url).lower()
    
    # Standard module list
    MODUL_LISTESI = [
        ("uretim_girisi", "🏭 Üretim Girişi", 10, "ops"),
        ("kpi_kontrol", "🍩 KPI & Kalite Kontrol", 20, "ops"),
        ("gmp_denetimi", "🛡️ GMP Denetimi", 30, "ops"),
        ("personel_hijyen", "🧼 Personel Hijyen", 40, "ops"),
        ("temizlik_kontrol", "🧹 Temizlik Kontrol", 50, "ops"),
        ("kurumsal_raporlama", "📊 Kurumsal Raporlama", 60, "mgt"),
        ("soguk_oda", "❄️ Soğuk Oda Sıcaklıkları", 70, "ops"),
        ("map_uretim", "📦 MAP Üretim", 80, "ops"),
        ("gunluk_gorevler", "📋 Günlük Görevler", 85, "ops"),
        ("performans_polivalans", "📈 Yetkinlik & Performans", 90, "mgt"),
        ("personel_vardiya_yonetimi", "📅 Vardiya Yönetimi", 95, "ops"),
        ("qdms", "📁 QDMS", 100, "mgt"),
        ("denetim_izi", "👁️ Denetim İzi", 105, "mgt"),
        ("ayarlar", "⚙️ Ayarlar", 110, "sys")
    ]

    try:
        with engine.begin() as conn:
            # 1. Column check
            if is_pg:
                cols_res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'ayarlar_moduller'"))
                existing_cols = {r[0] for r in cols_res.fetchall()}
            else:
                cols_res = conn.execute(text("PRAGMA table_info(ayarlar_moduller)"))
                existing_cols = {r[1] for r in cols_res.fetchall()}
            
            has_zone = 'zone' in existing_cols
            print(f"Schema check: 'zone' column {'EXISTS' if has_zone else 'MISSING'}")

            # 2. UPSERT
            for anahtar, etiket, sira, zone in MODUL_LISTESI:
                if is_pg:
                    if has_zone:
                        sql = "INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, zone, aktif) VALUES (:k, :e, :s, :z, 1) ON CONFLICT (modul_anahtari) DO UPDATE SET modul_etiketi = :e, sira_no = :s, zone = :z, aktif = 1"
                        conn.execute(text(sql), {"k": anahtar, "e": etiket, "s": sira, "z": zone})
                    else:
                        sql = "INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES (:k, :e, :s, 1) ON CONFLICT (modul_anahtari) DO UPDATE SET modul_etiketi = :e, sira_no = :s, aktif = 1"
                        conn.execute(text(sql), {"k": anahtar, "e": etiket, "s": sira})
                else:
                    # SQLite doesn't have internal ON CONFLICT in the same way for INSERT, so use separate steps
                    check = conn.execute(text("SELECT 1 FROM ayarlar_moduller WHERE modul_anahtari = :k"), {"k": anahtar}).fetchone()
                    if not check:
                        if has_zone:
                            conn.execute(text("INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, zone, aktif) VALUES (:k, :e, :s, :z, 1)"), {"k": anahtar, "e": etiket, "s": sira, "z": zone})
                        else:
                            conn.execute(text("INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES (:k, :e, :s, 1)"), {"k": anahtar, "e": etiket, "s": sira})
                    else:
                        extra = ", zone = :z" if has_zone else ""
                        conn.execute(text(f"UPDATE ayarlar_moduller SET modul_etiketi = :e, sira_no = :s, aktif = 1 {extra} WHERE modul_anahtari = :k"), {"k": anahtar, "e": etiket, "s": sira, "z": zone})
                print(f"  - Synced: {anahtar}")

            # 3. Permissions
            print("Ensuring ADMIN permissions for map_uretim...")
            sql_perm = "INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu, sadece_kendi_bolumu) VALUES ('ADMIN', 'map_uretim', 'Düzenle', :s)"
            if is_pg: 
                sql_perm += " ON CONFLICT (rol_adi, modul_adi) DO NOTHING"
            else: 
                sql_perm = sql_perm.replace("INSERT INTO", "INSERT OR IGNORE INTO")
            
            conn.execute(text(sql_perm), {"s": False if is_pg else 0})

        print("\nSYNC SUCCESSFUL. Please refresh the application and clear cache.")
    except Exception as e:
        print(f"SYNC FAILED: {e}")

if __name__ == "__main__":
    sync_modules()
