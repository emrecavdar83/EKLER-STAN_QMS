# -*- coding: utf-8 -*-
"""Lokal veritabanında ürün departman analizi - DOĞRU DB"""
import os
import pandas as pd
from sqlalchemy import create_engine, text

os.chdir(r"c:\Projeler\S_program\EKLERİSTAN_QMS")

# Lokal SQLite bağlantısı (app.py ile aynı)
LOCAL_DB = 'sqlite:///ekleristan_local.db'

try:
    engine = create_engine(LOCAL_DB, connect_args={'check_same_thread': False})
    
    print("=== LOKAL VERİTABANI (ekleristan_local.db) - ÜRÜN ANALİZİ ===\n")
    
    # 1. Önce tablo mevcut mu?
    with engine.connect() as conn:
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print("Mevcut tablolar:")
        print(tables['name'].tolist())
    
    # 2. Ürünlerin sorumlu_departman değerleri
    print("\n--- Tüm Ürünler ve Sorumlu Departmanları ---")
    try:
        df = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler ORDER BY urun_adi", engine)
        print(f"Toplam ürün sayısı: {len(df)}\n")
        
        for _, row in df.iterrows():
            dept = row['sorumlu_departman'] if pd.notna(row['sorumlu_departman']) else "(BOŞ)"
            print(f"  {row['urun_adi']:35} -> {dept}")
        
        # 3. Sorumlu departman dağılımı
        print("\n--- Sorumlu Departman Dağılımı ---")
        dept_counts = df['sorumlu_departman'].fillna('(BOŞ)').value_counts()
        for dept, count in dept_counts.items():
            print(f"  {dept:35}: {count} ürün")
            
    except Exception as e:
        print(f"HATA: {e}")
        
    print("\n✅ Analiz tamamlandı.")
    
except Exception as e:
    print(f"VERİTABANI HATASI: {e}")
