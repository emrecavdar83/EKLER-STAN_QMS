import sqlite3
import os

def fix_org_data():
    db_path = 'ekleristan_local.db'
    if not os.path.exists(db_path):
        print("Veritabani bulunamadi.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("Veri duzeltme islemi basliyor...")

    # 1. Pozisyon Seviyesi Ata
    try:
        c.execute("""
        UPDATE personel
        SET pozisyon_seviye = CASE
            WHEN UPPER(rol) LIKE '%YÖNETİM KURULU%' OR UPPER(rol) LIKE '%BOARD%' THEN 0
            WHEN UPPER(rol) LIKE '%GENEL MÜDÜR%' OR UPPER(rol) LIKE '%CEO%' THEN 1
            WHEN UPPER(rol) LIKE '%DİREKTÖR%' OR UPPER(rol) LIKE '%DIRECTOR%' THEN 2
            WHEN UPPER(rol) LIKE '%MÜDÜR%' OR UPPER(rol) LIKE '%MANAGER%' THEN 2
            WHEN UPPER(gorev) LIKE '%MÜDÜR%' OR UPPER(gorev) LIKE '%MANAGER%' THEN 2
            WHEN UPPER(rol) LIKE '%SORUMLU%' OR UPPER(rol) LIKE '%ŞEF%' OR UPPER(rol) LIKE '%SUPERVISOR%' THEN 3
            WHEN UPPER(rol) LIKE '%KOORDİNATÖR%' OR UPPER(rol) LIKE '%COORDINATOR%' THEN 3
            WHEN UPPER(gorev) LIKE '%ŞEF%' OR UPPER(gorev) LIKE '%SORUMLU%' THEN 3
            WHEN UPPER(gorev) LIKE '%KOORDİNATÖR%' THEN 3
            ELSE 5
        END
        WHERE pozisyon_seviye = 5 OR pozisyon_seviye IS NULL;
        """)
        print("- Pozisyon seviyeleri guncellendi.")
    except Exception as e:
        print(f"Hata (Pozisyon): {e}")

    # 2. Departman ID Eşleştir
    try:
        c.execute("""
        UPDATE personel
        SET departman_id = (
            SELECT id 
            FROM ayarlar_bolumler 
            WHERE UPPER(TRIM(bolum_adi)) = UPPER(TRIM(personel.bolum))
            LIMIT 1
        )
        WHERE bolum IS NOT NULL 
          AND bolum != ''
          AND departman_id IS NULL;
        """)
        print("- Departman IDleri eslestirildi.")
    except Exception as e:
        print(f"Hata (Departman): {e}")

    # 3. View Yenile
    try:
        c.execute("DROP VIEW IF EXISTS v_organizasyon_semasi")
        c.execute("""
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
        WHERE p.ad_soyad IS NOT NULL AND p.durum = 'AKTİF'
        ORDER BY p.pozisyon_seviye, p.ad_soyad;
        """)
        print("- View yeniden olusturuldu.")
    except Exception as e:
        print(f"Hata (View): {e}")

    conn.commit()
    conn.close()
    print("Islem tamamlandi.")

if __name__ == "__main__":
    fix_org_data()
