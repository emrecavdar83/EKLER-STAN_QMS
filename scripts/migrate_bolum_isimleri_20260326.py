
# scripts/migrate_bolum_isimleri_20260326.py
"""
Departman Adı Düzeltmeleri - Tur 2
Kaynak: claudes_plan.md (26.03.2026)
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from database.connection import get_engine

def migrate():
    engine = get_engine()
    with engine.begin() as conn:

        # 1. YAŞ PASTA → HACI NADİR (ID 66 tahmini veya isim bazlı çekim)
        # Tablo envanterinden HACI NADİR'in ID'sini dinamik bulalım
        conn.execute(text("""
            UPDATE ayarlar_bolumler
            SET ana_departman_id = (SELECT id FROM ayarlar_bolumler WHERE bolum_adi = 'HACI NADİR' LIMIT 1)
            WHERE id = 60
        """))

        # 2. YARI MAMÜL ön adları
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'YARI MAMÜL PATAÇU'      WHERE id = 11"))
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'YARI MAMÜL PANDİSPANYA' WHERE id = 12"))
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'YARI MAMÜL KREMA'       WHERE id = 13"))
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'YARI MAMÜL SOS'         WHERE id = 18"))

        print('✅ Değişiklikler uygulandı.')

        # Doğrulama
        r = conn.execute(text("""
            SELECT b.id, b.bolum_adi, p.bolum_adi as ust
            FROM ayarlar_bolumler b
            LEFT JOIN ayarlar_bolumler p ON b.ana_departman_id = p.id
            WHERE b.id IN (11, 12, 13, 18, 60)
            ORDER BY b.id
        """))
        print('\n── Doğrulama ──')
        for row in r:
            print(f'  ID {row[0]:>3} | {row[1]:<35} → {row[2] or "KÖK"}')

if __name__ == '__main__':
    migrate()
