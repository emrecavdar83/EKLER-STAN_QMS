import toml
from sqlalchemy import create_engine, text

def finalize_perms():
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets["streamlit"]["DB_URL"]
    engine = create_engine(url)
    
    with engine.begin() as conn:
        print("Fetching active roles...")
        roles = conn.execute(text("SELECT DISTINCT rol_adi FROM public.ayarlar_roller WHERE aktif=1")).fetchall()
        
        for r in roles:
            rol = r[0]
            # Rule: Managerial roles get 'Düzenle' for sidebar visibility, others get 'Görüntüle'
            # Sidebar visibility is the entry point
            perm = 'Düzenle' if rol.upper() in ['ADMIN', 'YÖNETİM KURULU', 'GENEL MÜDÜR', 'KALİTE', 'MÜDÜRLER', 'DİREKTÖRLER'] else 'Görüntüle'
            
            print(f"Mapping {rol} -> {perm}")
            conn.execute(text("""
                INSERT INTO public.ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu)
                VALUES (:r, 'qdms', :p)
                ON CONFLICT (rol_adi, modul_adi) DO UPDATE SET erisim_turu = :p
            """), {'r': rol, 'p': perm})
            
    print("All roles updated for 'qdms' key.")

if __name__ == "__main__":
    finalize_perms()
