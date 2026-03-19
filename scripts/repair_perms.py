import toml
from sqlalchemy import create_engine, text

def repair():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    
    with engine.begin() as conn:
        print("1. Repairing public.ayarlar_moduller...")
        # Ensure modules exist
        conn.execute(text("""
        INSERT INTO public.ayarlar_moduller (modul_anahtari, modul_etiketi, aktif, sira_no) VALUES
        ('dokuman_merkezi', '📖 Doküman Merkezi', 1, 71),
        ('belge_yonetimi',  '📂 Belge Yönetimi',  1, 72),
        ('talimatlar',      '📖 Talimatlar',      1, 73),
        ('uyumluluk',       '✅ Uyumluluk',       1, 74)
        ON CONFLICT (modul_anahtari) DO UPDATE SET aktif = 1;
        """))
        
        print("2. Repairing public.ayarlar_yetkiler for ADMIN...")
        # Get all module keys
        res = conn.execute(text("SELECT modul_anahtari FROM public.ayarlar_moduller")).fetchall()
        for r in res:
            m_key = r[0]
            conn.execute(text("""
            INSERT INTO public.ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu)
            VALUES ('ADMIN', :m, 'Düzenle')
            ON CONFLICT DO NOTHING;
            """), {"m": m_key})
            
            # Explicitly update existing ones that might show 'Yok'
            conn.execute(text("""
            UPDATE public.ayarlar_yetkiler SET erisim_turu = 'Düzenle' 
            WHERE UPPER(rol_adi) = 'ADMIN' AND modul_adi = :m AND erisim_turu = 'Yok'
            """), {"m": m_key})

        print("3. Special update for Admin-level Management Roles...")
        conn.execute(text("""
        UPDATE public.ayarlar_yetkiler SET erisim_turu = 'Tam Yetki' 
        WHERE rol_adi IN ('Yönetim Kurulu', 'Genel Müdür') AND modul_adi IN ('dokuman_merkezi','belge_yonetimi','talimatlar','uyumluluk')
        """))

    print("Repair completed.")

if __name__ == "__main__":
    repair()
