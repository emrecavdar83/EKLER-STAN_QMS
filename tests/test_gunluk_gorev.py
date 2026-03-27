import unittest
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, date

from modules.gunluk_gorev.logic import (
    gorev_katalogu_getir,
    periyodik_gorev_ata,
    gorev_tamamla,
    personel_gorev_getir,
    yonetici_matris_getir
)

class TestGunlukGorev(unittest.TestCase):
    def setUp(self):
        # In-memory SQLite for isolated testing
        self.engine = create_engine('sqlite:///:memory:')
        with self.engine.begin() as conn:
            # Create mock schema for tests
            conn.execute(text("""
                CREATE TABLE personel (
                    id INTEGER PRIMARY KEY,
                    ad_soyad TEXT,
                    bolum_id INTEGER
                )
            """))
            conn.execute(text("""
                CREATE TABLE gunluk_gorev_katalogu (
                    id INTEGER PRIMARY KEY,
                    ad TEXT,
                    kategori TEXT,
                    aktif_mi INTEGER
                )
            """))
            conn.execute(text("""
                CREATE TABLE birlesik_gorev_havuzu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    personel_id INTEGER,
                    bolum_id INTEGER,
                    gorev_kaynagi TEXT,
                    kaynak_id INTEGER,
                    atanma_tarihi TEXT,
                    hedef_tarih TEXT,
                    durum TEXT,
                    tamamlanma_tarihi TIMESTAMP,
                    sapma_notu TEXT,
                    UNIQUE(personel_id, hedef_tarih, gorev_kaynagi, kaynak_id)
                )
            """))
            
            # Seed mock data
            conn.execute(text("INSERT INTO personel (id, ad_soyad, bolum_id) VALUES (1, 'Test User', 10)"))
            conn.execute(text("INSERT INTO personel (id, ad_soyad, bolum_id) VALUES (2, 'Test User 2', 10)"))
            conn.execute(text("INSERT INTO gunluk_gorev_katalogu (id, ad, kategori, aktif_mi) VALUES (5, 'Test Görevi', 'Test', 1)"))
            conn.execute(text("INSERT INTO gunluk_gorev_katalogu (id, ad, kategori, aktif_mi) VALUES (6, 'Pasif Görev', 'Test', 0)"))
            
    def test_gorev_katalogu_getir(self):
        df = gorev_katalogu_getir(self.engine)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['id'], 5)
        
    def test_periyodik_gorev_ata_ve_getir(self):
        today = str(date.today())
        atama_listesi = [{
            'personel_id': 1, 'bolum_id': 10, 'gorev_kaynagi': 'PERIYODIK', 
            'kaynak_id': 5, 'atanma_tarihi': today, 'hedef_tarih': today
        }]
        # Happy Path
        periyodik_gorev_ata(self.engine, atama_listesi)
        df_personel = personel_gorev_getir(self.engine, 1, today)
        self.assertEqual(len(df_personel), 1)
        self.assertEqual(df_personel.iloc[0]['durum'], 'BEKLIYOR')
        
        # Edge case: Mukerrer atama fail-silent mi calisiyor?
        periyodik_gorev_ata(self.engine, atama_listesi)
        df_personel2 = personel_gorev_getir(self.engine, 1, today)
        self.assertEqual(len(df_personel2), 1) # Mukerrer atama atlandi, ayni 1 kayit.
        
    def test_gorev_tamamla(self):
        today = str(date.today())
        atama_listesi = [{
            'personel_id': 1, 'bolum_id': 10, 'gorev_kaynagi': 'PERIYODIK', 
            'kaynak_id': 5, 'atanma_tarihi': today, 'hedef_tarih': today
        }]
        periyodik_gorev_ata(self.engine, atama_listesi)
        
        # Olan durumu cek
        df_personel = personel_gorev_getir(self.engine, 1, today)
        havuz_id = int(df_personel.iloc[0]['id'])
        
        # Tamamla
        gorev_tamamla(self.engine, havuz_id, 1, sapma_notu="Test not")
        df_son = personel_gorev_getir(self.engine, 1, today)
        
        self.assertEqual(df_son.iloc[0]['durum'], 'TAMAMLANDI')
        self.assertEqual(df_son.iloc[0]['sapma_notu'], 'Test not')
        
    def test_edge_case_bos_atama(self):
        try:
            periyodik_gorev_ata(self.engine, [])
        except Exception as e:
            self.fail(f"Boş atama listesi exception fırlattı: {e}")
            
    def test_yonetici_matrisi(self):
        today = str(date.today())
        atama_listesi = [{
            'personel_id': 1, 'bolum_id': 10, 'gorev_kaynagi': 'PERIYODIK', 
            'kaynak_id': 5, 'atanma_tarihi': today, 'hedef_tarih': today
        }, {
            'personel_id': 2, 'bolum_id': 10, 'gorev_kaynagi': 'EKSTRA', 
            'kaynak_id': 99, 'atanma_tarihi': today, 'hedef_tarih': today
        }]
        periyodik_gorev_ata(self.engine, atama_listesi)
        df_matris = yonetici_matris_getir(self.engine, today)
        self.assertEqual(len(df_matris), 2)
        
        # Bolum fitresi
        df_b = yonetici_matris_getir(self.engine, today, 10)
        self.assertEqual(len(df_b), 2)
        
        # Olmayan bolum
        df_b2 = yonetici_matris_getir(self.engine, today, 99)
        self.assertEqual(len(df_b2), 0)

if __name__ == '__main__':
    unittest.main()
