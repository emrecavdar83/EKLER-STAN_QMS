import pytest
import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import pandas as pd
import datetime

# Tester Ajanı - Birleşik Görev Modülü Unit Testleri

@pytest.fixture
def memory_engine():
    db_path = 'test_gunluk_gorev.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        
    engine = create_engine(f"sqlite:///{db_path}")
    # Şema kurulumu
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE personel (id INTEGER PRIMARY KEY, ad_soyad TEXT, bolum_id INTEGER);
            CREATE TABLE ayarlar_bolumler (id INTEGER PRIMARY KEY, ad TEXT);
        """))
        conn.execute(text("""
            INSERT INTO ayarlar_bolumler (id, ad) VALUES (1, 'Uretim');
            INSERT INTO personel (id, ad_soyad, bolum_id) VALUES (10, 'Test User', 1);
            INSERT INTO personel (id, ad_soyad, bolum_id) VALUES (20, 'Test Manager', 1);
        """))
        # Asıl tablolar
        with open('migrations/20260328_100000_gunluk_gorev_ve_akis_init.sql', 'r', encoding='utf-8') as f:
            up_sql = f.read().split('-- DOWN MIGRATION')[0]
            for statement in up_sql.split(';'):
                if statement.strip():
                    conn.execute(text(statement))
    return engine

def test_gorev_atama_ve_mukkerrer_engelleme(memory_engine):
    from modules.gunluk_gorev.logic import periyodik_gorev_ata, personel_gorev_getir
    
    tarih = datetime.date.today()
    atama_listesi = [
        {'personel_id': 10, 'bolum_id': None, 'gorev_kaynagi': 'YONETIM', 'kaynak_id': 1, 'atanma_tarihi': tarih, 'hedef_tarih': tarih}
    ]
    # Atama yap
    periyodik_gorev_ata(memory_engine, atama_listesi)
    
    # Kontrol et
    gorevler = personel_gorev_getir(memory_engine, 10, tarih)
    assert len(gorevler) == 1
    assert gorevler.iloc[0]['durum'] == 'BEKLIYOR'
    assert gorevler.iloc[0]['gorev_kaynagi'] == 'YONETIM'

    # Mükerrer atama yap
    periyodik_gorev_ata(memory_engine, atama_listesi)
    gorevler_sonrasi = personel_gorev_getir(memory_engine, 10, tarih)
    
    # Benzersiz kısıtlama sayesinde hala 1 olmalı
    assert len(gorevler_sonrasi) == 1

def test_gorev_tamamla(memory_engine):
    from modules.gunluk_gorev.logic import periyodik_gorev_ata, gorev_tamamla, personel_gorev_getir
    
    tarih = datetime.date.today()
    atama_listesi = [
        {'personel_id': 10, 'bolum_id': None, 'gorev_kaynagi': 'PERIYODIK', 'kaynak_id': 2, 'atanma_tarihi': tarih, 'hedef_tarih': tarih}
    ]
    periyodik_gorev_ata(memory_engine, atama_listesi)
    
    gorevler = personel_gorev_getir(memory_engine, 10, tarih)
    havuz_id = int(gorevler.iloc[0]['id'])
    
    # Görevi tamamla
    gorev_tamamla(memory_engine, havuz_id, 10, sapma_notu="Sorun yok")
    
    guncel_gorevler = personel_gorev_getir(memory_engine, 10, tarih)
    assert guncel_gorevler.iloc[0]['durum'] == 'TAMAMLANDI'
    assert guncel_gorevler.iloc[0]['sapma_notu'] == 'Sorun yok'
