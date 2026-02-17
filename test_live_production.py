# -*- coding: utf-8 -*-
"""
Canlı Veritabanı - Saat Kolonu Doğrulama
PostgreSQL'de saat kolonunun varlığını ve bir test kaydı eklenip eklenemediğini kontrol eder.
"""
import pandas as pd
from sqlalchemy import create_engine, text
import toml
from datetime import datetime

# Canlı veritabanı bağlantısı
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
if live_url:
    live_url = live_url.strip('"')
else:
    print("❌ Canlı veritabanı URL'si bulunamadı!")
    exit(1)

live_engine = create_engine(live_url, pool_pre_ping=True)

print("=" * 60)
print("CANLI VERİTABANI - SAAT KOLONU TEST")
print("=" * 60)

try:
    # 1. Kolon kontrolü
    print("\n1️⃣ Kolon Kontrolü")
    with live_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'depo_giris_kayitlari'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        
        print("Mevcut kolonlar:")
        saat_exists = False
        for col in columns:
            print(f"  - {col[0]:20} ({col[1]})")
            if col[0] == 'saat':
                saat_exists = True
        
        if saat_exists:
            print("\n✅ 'saat' kolonu mevcut!")
        else:
            print("\n❌ 'saat' kolonu bulunamadı!")
            exit(1)
    
    # 2. Test kaydı ekleme
    print("\n2️⃣ Test Kaydı Ekleme")
    test_data = {
        'tarih': '2026-02-07',
        'saat': '14:15',
        'vardiya': 'GÜNDÜZ VARDİYASI',
        'kullanici': 'test_canli',
        'islem_tipi': 'URETIM',
        'urun': 'TEST - CANLI',
        'lot_no': 'CANLI-TEST-001',
        'miktar': 50,
        'fire': 2,
        'notlar': 'Canlı ortam test kaydı\nSaat alanı ile\nÇok satırlı not testi',
        'zaman_damgasi': str(datetime.now())
    }
    
    with live_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO depo_giris_kayitlari 
            (tarih, saat, vardiya, kullanici, islem_tipi, urun, lot_no, miktar, fire, notlar, zaman_damgasi)
            VALUES (:tarih, :saat, :vardiya, :kullanici, :islem_tipi, :urun, :lot_no, :miktar, :fire, :notlar, :zaman_damgasi)
        """), test_data)
    
    print("✅ Test kaydı başarıyla eklendi!")
    
    # 3. Kaydı kontrol et
    print("\n3️⃣ Kayıt Doğrulama")
    df = pd.read_sql(text("""
        SELECT id, tarih, saat, vardiya, urun, lot_no, miktar, fire, notlar
        FROM depo_giris_kayitlari
        WHERE lot_no = 'CANLI-TEST-001'
    """), live_engine)
    
    if not df.empty:
        print("Kaydedilen veri:")
        print(df.to_string(index=False))
    else:
        print("❌ Kayıt bulunamadı!")
    
    # 4. Test kaydını temizle
    print("\n4️⃣ Temizlik")
    with live_engine.begin() as conn:
        result = conn.execute(text("""
            DELETE FROM depo_giris_kayitlari 
            WHERE lot_no = 'CANLI-TEST-001'
        """))
        print(f"🧹 {result.rowcount} test kaydı silindi.")
    
    print("\n" + "=" * 60)
    print("✅ CANLI ORTAM TESTİ BAŞARILI!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ HATA: {e}")
    import traceback
    traceback.print_exc()
