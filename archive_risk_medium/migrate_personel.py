import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('ekleristan_local.db')
        cursor = conn.cursor()
        
        print("Görünüm (View) kaldırılıyor...")
        cursor.execute("DROP VIEW IF EXISTS v_organizasyon_semasi")
        
        print("Eski personel tablosu yedekleniyor...")
        cursor.execute("ALTER TABLE personel RENAME TO personel_old")
        
        print("Yeni personel tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE personel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_soyad TEXT,
                bolum TEXT,
                gorev TEXT,
                vardiya TEXT,
                durum TEXT,
                kullanici_adi TEXT,
                sifre TEXT,
                rol TEXT,
                sorumlu_bolum TEXT,
                departman_id INTEGER,
                yonetici_id INTEGER,
                pozisyon_seviye INTEGER DEFAULT 5
            )
        """)
        
        print("Veriler taşınıyor...")
        cursor.execute("""
            INSERT INTO personel (ad_soyad, bolum, gorev, vardiya, durum, kullanici_adi, sifre, rol, sorumlu_bolum, departman_id, yonetici_id, pozisyon_seviye)
            SELECT ad_soyad, bolum, gorev, vardiya, durum, kullanici_adi, CAST(sifre AS TEXT), rol, sorumlu_bolum, departman_id, yonetici_id, pozisyon_seviye 
            FROM personel_old
        """)
        
        print("Admin kullanıcısı ekleniyor...")
        # Önce Admin var mı kontrol et (ne olur ne olmaz)
        cursor.execute("SELECT COUNT(*) FROM personel WHERE kullanici_adi = 'Admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'Admin', 'AKTİF', 0)
            """)
            print("Admin başarıyla eklendi.")
        else:
            print("Admin zaten mevcuttu.")
            
        print("Organizasyon şeması görünümü (view) yeniden oluşturuluyor...")
        cursor.execute("""
            CREATE VIEW v_organizasyon_semasi AS
            SELECT 
                p.id,
                p.ad_soyad,
                p.gorev,
                p.rol,
                p.pozisyon_seviye,
                p.yonetici_id,
                y.ad_soyad as yonetici_adi,
                COALESCE(d.bolum_adi, p.bolum, 'Tanımsız') as departman,
                d.id as departman_id,
                p.kullanici_adi,
                p.durum,
                p.vardiya
            FROM personel p
            LEFT JOIN personel y ON p.yonetici_id = y.id
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
            WHERE p.ad_soyad IS NOT NULL
            ORDER BY p.pozisyon_seviye, p.ad_soyad
        """)
        
        conn.commit()
        print("Göç işlemi başarıyla tamamlandı!")
        
    except Exception as e:
        print(f"HATA: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
