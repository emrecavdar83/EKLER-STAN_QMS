
# scripts/migrate_hierarchy_20260325.py
"""
Hiyerarşi Migration: Personel Sayılı Geçiş (REVİZE-v2)
- Unique Violation hatalarını önlemek için isim bazlı kontroller eklendi.
- Existing IDs (18, 44, 48 etc.) logic robust hale getirildi.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from database.connection import get_engine

def migrate():
    engine = get_engine()
    with engine.begin() as conn:

        # ── ADIM 1: YENİ ANA GRUPLARI OLUŞTUR ──────────────────────────
        # HACI NADİR → ÜRETİM (2) altına
        conn.execute(text("""
            INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, aktif)
            SELECT 'HACI NADİR', 2, 1
            WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'HACI NADİR')
        """))

        # TEMİZLİK GRUBU → ÜRETİM (2) altına
        conn.execute(text("""
            INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, aktif)
            SELECT 'TEMİZLİK GRUBU', 2, 1
            WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'TEMİZLİK GRUBU')
        """))

        # ── ADIM 2: HACI NADİR ALTINA BAKLAVA OLUŞTUR ───────────────────
        conn.execute(text("""
            INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, aktif)
            SELECT 'BAKLAVA', id, 1
            FROM ayarlar_bolumler WHERE bolum_adi = 'HACI NADİR'
            AND NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'BAKLAVA')
        """))

        # ── ADIM 3: EKLERİSTAN (32) ALTINA MAP OLUŞTUR ──────────────────
        conn.execute(text("""
            INSERT INTO ayarlar_bolumler (bolum_adi, ana_departman_id, aktif)
            SELECT 'MAP', 32, 1
            WHERE NOT EXISTS (SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = 'MAP')
        """))

        # ── ADIM 4: ID 32 → EKLERİSTAN olarak yeniden adlandır ──────────
        conn.execute(text("""
            UPDATE ayarlar_bolumler SET bolum_adi = 'EKLERİSTAN'
            WHERE id = 32 AND bolum_adi = 'EKLER'
        """))

        # ── ADIM 5: EKLERİSTAN ALT BİRİMLERİ (Özel Durum: SOS çakışması) ──
        # SOS Zaten 18'de var. 44'ü de 32 altına taşıyalım ama adını çakışmasın diye 'EKLER SOS' bırakabiliriz 
        # veya 18'i de 32 altına alıp merge edebiliriz.
        
        # 1. Mevcut SOS'u (ID 18) EKLERİSTAN (32) altına al
        conn.execute(text("UPDATE ayarlar_bolumler SET ana_departman_id = 32 WHERE id = 18"))
        
        # 2. ID 44 (EKLER SOS) ismini koruyalım ve 32 altına alalım (Unique Violation önlendi)
        conn.execute(text("UPDATE ayarlar_bolumler SET ana_departman_id = 32 WHERE id = 44"))
        
        # 3. Diğerlerini taşı (Mükerrerlik yoksa isimlerini kurumsallaştır)
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'MAGNOLİA', ana_departman_id = 32 WHERE id = 48"))
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'TERAZİ', ana_departman_id = 32 WHERE id = 55"))
        conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'DONUK', ana_departman_id = 32 WHERE id = 57"))

        # ── ADIM 6: HACI NADİR ALTINA TAŞI ──────────────────────────────
        conn.execute(text("""
            UPDATE ayarlar_bolumler
            SET ana_departman_id = (SELECT id FROM ayarlar_bolumler WHERE bolum_adi = 'HACI NADİR')
            WHERE id IN (27, 62)
        """))
        # ID 61 (TEK PASTA)
        conn.execute(text("""
            UPDATE ayarlar_bolumler
            SET bolum_adi = 'TEK PASTA',
                ana_departman_id = (SELECT id FROM ayarlar_bolumler WHERE bolum_adi = 'HACI NADİR')
            WHERE id = 61
        """))

        # ── ADIM 7: TEMİZLİK GRUBU ALTINA TAŞI ─────────────────────────
        conn.execute(text("""
            UPDATE ayarlar_bolumler
            SET ana_departman_id = (SELECT id FROM ayarlar_bolumler WHERE bolum_adi = 'TEMİZLİK GRUBU')
            WHERE id IN (39, 7, 8)
        """))

        print("✅ Hiyerarşi migration (REVİZE-v2) başarıyla tamamlandı.")

        # ── DOĞRULAMA SORGUSU ────────────────────────────────────────────
        result = conn.execute(text("""
            SELECT b.id, b.bolum_adi, p.bolum_adi as ust_birim
            FROM ayarlar_bolumler b
            LEFT JOIN ayarlar_bolumler p ON b.ana_departman_id = p.id
            WHERE b.id IN (18, 27, 32, 44, 48, 55, 57, 61, 62, 7, 8, 39)
               OR b.bolum_adi IN ('HACI NADİR', 'TEMİZLİK GRUBU', 'BAKLAVA', 'MAP')
            ORDER BY b.id
        """))
        print("\n── Doğrulama ──")
        for row in result:
            print(f"  ID {row[0]:>3} | {row[1]:<25} → {row[2] or 'KÖK'}")

if __name__ == '__main__':
    migrate()
