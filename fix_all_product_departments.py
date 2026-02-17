# -*- coding: utf-8 -*-
"""
TÜM ÜRÜNLER - DEPARTMAN ATAMASI KAPSAMLI DÜZELTMESİ
====================================================
Sorun: sorumlu_departman değerleri "YÖNETİM > ÜRETİM > KREMA" gibi 
       hiyerarşik olduğundan filtreleme doğru çalışmıyor.
Çözüm: Son segment alınarak basitleştirilecek (KREMA)

Hem LOKAL hem de CANLI veritabanında uygulanır.
"""
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import re

print("=" * 80)
print("TÜM ÜRÜNLER - DEPARTMAN ATAMASI KAPSAMLI DÜZELTMESİ")
print("=" * 80)

# --- VERİTABANI BAĞLANTILARI ---
# Lokal
local_engine = create_engine('sqlite:///ekleristan_local.db', connect_args={'check_same_thread': False})

# Canlı
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_url = live_url.strip('"')
live_engine = create_engine(live_url, pool_pre_ping=True)

def simplify_department(dept_value):
    """
    Hiyerarşik departman adını son segmente indirgrer.
    Örnek: "YÖNETİM > ÜRETİM > KREMA" -> "KREMA"
    """
    if not dept_value or pd.isna(dept_value):
        return dept_value
    
    # > ile ayrılmış parçaları al
    parts = [p.strip() for p in str(dept_value).split('>')]
    
    # Son segment (gerçek departman adı)
    result = parts[-1] if parts else dept_value
    
    # ↳ karakterini temizle
    result = result.replace('↳', '').strip()
    
    return result

def fix_database(engine, db_name):
    """Verilen veritabanında tüm ürün departman atamalarını düzeltir"""
    print(f"\n{'='*40}")
    print(f"  {db_name} VERİTABANI")
    print(f"{'='*40}")
    
    try:
        # Mevcut durumu göster
        print("\n--- DÜZELTME ÖNCESİ ---")
        df = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler ORDER BY sorumlu_departman", engine)
        
        if df.empty:
            print("⚠️ Ürün bulunamadı!")
            return
        
        print(f"Toplam ürün: {len(df)}")
        
        # Hiyerarşik olanları bul (> içerenler)
        hierarchical = df[df['sorumlu_departman'].fillna('').str.contains('>', na=False)]
        print(f"Hiyerarşik departman değeri olan: {len(hierarchical)} ürün")
        
        if not hierarchical.empty:
            print("\nHiyerarşik kayıtlar:")
            for _, row in hierarchical.iterrows():
                orig = row['sorumlu_departman']
                simple = simplify_department(orig)
                print(f"  {row['urun_adi'][:30]:30} | {orig} -> {simple}")
        
        # Düzeltmeleri uygula
        print("\n--- DÜZELTME UYGULAMASI ---")
        updated_count = 0
        
        with engine.begin() as conn:
            for _, row in df.iterrows():
                orig = row['sorumlu_departman']
                simple = simplify_department(orig)
                
                if orig != simple and simple:
                    if 'sqlite' in str(engine.url):
                        # SQLite için
                        conn.execute(text(
                            "UPDATE ayarlar_urunler SET sorumlu_departman = :new WHERE urun_adi = :urun"
                        ), {"new": simple, "urun": row['urun_adi']})
                    else:
                        # PostgreSQL için
                        conn.execute(text(
                            "UPDATE ayarlar_urunler SET sorumlu_departman = :new WHERE urun_adi = :urun"
                        ), {"new": simple, "urun": row['urun_adi']})
                    updated_count += 1
        
        print(f"✅ Güncellenen ürün sayısı: {updated_count}")
        
        # Düzeltme sonrası durumu göster
        print("\n--- DÜZELTME SONRASI ---")
        df_after = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler ORDER BY sorumlu_departman", engine)
        
        # Departman dağılımı
        print("\nDepartman Dağılımı:")
        dept_counts = df_after['sorumlu_departman'].fillna('(BOŞ)').value_counts()
        for dept, count in dept_counts.items():
            print(f"  {dept:25}: {count} ürün")
        
        print(f"\n✅ {db_name} düzeltmesi tamamlandı!")
        
    except Exception as e:
        print(f"❌ HATA ({db_name}): {e}")

# --- LOKAL VERİTABANI ---
fix_database(local_engine, "LOKAL")

# --- CANLI VERİTABANI ---
fix_database(live_engine, "CANLI")

print("\n" + "=" * 80)
print("TÜM DÜZELTMELER TAMAMLANDI!")
print("=" * 80)
print("\n💡 Kullanıcıların değişikliği görmesi için:")
print("   1. Çıkış yapıp tekrar giriş yapsınlar")
print("   2. Veya 'Sistemi Temizle' butonuna tıklasınlar")
