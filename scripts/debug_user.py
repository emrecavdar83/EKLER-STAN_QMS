#!/usr/bin/env python3
"""
Giriş Sorunu Teşhis Scripti
Kullanıcının veritabanındaki durumunu ve şifre formatını kontrol eder.
"""
import sys
import os
from sqlalchemy import text

# Ana dizini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _engine_olustur():
    try:
        import toml
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            db_url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
            if db_url:
                from sqlalchemy import create_engine
                return create_engine(db_url)
    except: pass
    from sqlalchemy import create_engine
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ekleristan_local.db')
    return create_engine(f"sqlite:///{db_path}")

def debug_user(username):
    engine = _engine_olustur()
    print(f"\n--- Kullanıcı Teşhis: {username} ---")
    
    with engine.connect() as conn:
        user = conn.execute(text("SELECT id, kullanici_adi, sifre, rol, durum FROM personel WHERE kullanici_adi = :u"), {"u": username}).fetchone()
        
    if not user:
        print(f"❌ HATA: '{username}' kullanıcısı veritabanında bulunamadı!")
        return

    uid, kname, sifre, rol, durum = user
    print(f"ID      : {uid}")
    print(f"Username: {kname}")
    print(f"Rol     : {rol}")
    print(f"Durum   : {durum}")
    
    if not sifre:
        print("Şifre   : [BOŞ / NULL]")
    elif str(sifre).startswith('$2'):
        print(f"Şifre   : [HASHED / BCRYPT] -> {sifre[:10]}...")
    else:
        print(f"Şifre   : [PLAINTEXT] -> {sifre}")

    # Fallback durumunu kontrol et
    try:
        with engine.connect() as conn:
            fb = conn.execute(text("SELECT param_degeri FROM sistem_parametreleri WHERE param_adi = 'plaintext_fallback_aktif'")).scalar()
            print(f"Fallback: {fb if fb else 'Varsayılan (True)'}")
    except:
        print("Fallback: Tablo bulunamadı (True kabul edilir)")

if __name__ == "__main__":
    target = "emre.cavdar"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    debug_user(target)
