import os
import sys

# Proje dizinini sys.path'e ekle ki 'database' modülü bulunabilsin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_engine
from sqlalchemy import text
from logic.security.password import sifre_hashle, _bcrypt_formatinda_mi

def migrate_passwords():
    engine = get_engine()
    
    with engine.begin() as conn:
        # 1. Plaintext fallback parametrelerini sil
        print("Sistem parametreleri temizleniyor...")
        conn.execute(text("DELETE FROM sistem_parametreleri WHERE anahtar IN ('plaintext_fallback_aktif', 'fallback_bitis_tarihi')"))
        
        # 2. Plaintext şifreleri bul ve hashle
        print("Tüm kullanıcı şifreleri kontrol ediliyor...")
        kullanicilar = conn.execute(text("SELECT id, kullanici_adi, sifre FROM ayarlar_kullanicilar WHERE sifre IS NOT NULL")).fetchall()
        
        guncellenen = 0
        for k in kullanicilar:
            k_id = k[0]
            k_adi = k[1]
            sifre = k[2]
            
            if not _bcrypt_formatinda_mi(sifre):
                print(f"Kullanıcı '{k_adi}' (ID: {k_id}) için plaintext şifre tespit edildi, güncelleniyor...")
                yeni_sifre = sifre_hashle(sifre)
                conn.execute(
                    text("UPDATE ayarlar_kullanicilar SET sifre = :sifre WHERE id = :id"),
                    {"sifre": yeni_sifre, "id": k_id}
                )
                guncellenen += 1
                
        print(f"Bitti! Toplam {guncellenen} kullanıcının şifresi native bcrypt formatına güncellendi.")

if __name__ == "__main__":
    migrate_passwords()
