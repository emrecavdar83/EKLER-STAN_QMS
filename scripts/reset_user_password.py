#!/usr/bin/env python3
"""
Giriş Onarım Scripti
Kullanıcının şifresini güvenli bir şekilde (bcrypt) sıfırlar.
"""
import sys
import os
from sqlalchemy import text
import bcrypt

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

def reset_password(username, new_password):
    engine = _engine_olustur()
    print(f"\n--- Şifre Sıfırlama: {username} ---")
    
    # Bcrypt ile hashle (Truncation zırhlı)
    safe_bytes = str(new_password).encode('utf-8')[:64]
    hashed = bcrypt.hashpw(safe_bytes, bcrypt.gensalt()).decode('utf-8')
    
    try:
        with engine.begin() as conn:
            # Kullanıcı var mı kontrol et
            check = conn.execute(text("SELECT id FROM personel WHERE kullanici_adi = :u"), {"u": username}).fetchone()
            if not check:
                print(f"❌ HATA: '{username}' kullanıcısı bulunamadı!")
                return False
                
            conn.execute(text("UPDATE personel SET sifre = :h, durum = 'AKTİF' WHERE kullanici_adi = :u"), 
                         {"h": hashed, "u": username})
            
            conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('SIFRE_SIFIRLAMA_MANUEL', :d)"),
                         {"d": f"'{username}' şifresi script ile sıfırlandı."})
                         
        print(f"✅ BAŞARILI: '{username}' şifresi güncellendi.")
        return True
    except Exception as e:
        print(f"❌ KRİTİK HATA: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Kullanım: python scripts/reset_user_password.py <kullanici_adi> <yeni_sifre>")
        print("Örnek  : python scripts/reset_user_password.py emre.cavdar 968574")
    else:
        reset_password(sys.argv[1], sys.argv[2])
