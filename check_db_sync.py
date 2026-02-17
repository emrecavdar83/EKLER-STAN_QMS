import pandas as pd
from sqlalchemy import create_engine
import sys

# Lokal DB
local_engine = create_engine('sqlite:///C:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db')

print("=" * 60)
print("LOKAL VERİTABANI")
print("=" * 60)

print("\n1. ROLLER:")
local_roller = pd.read_sql('SELECT rol_adi FROM ayarlar_roller ORDER BY id', local_engine)
print(local_roller)

print("\n2. YETKİLER (Personel Hijyen):")
local_yetkiler = pd.read_sql("SELECT rol_adi, erisim_turu FROM ayarlar_yetkiler WHERE modul_adi='Personel Hijyen' ORDER BY rol_adi", local_engine)
print(local_yetkiler)

print("\n3. PERSONEL ROL DAĞILIMI:")
local_personel_roller = pd.read_sql("SELECT rol, COUNT(*) as adet FROM personel WHERE rol IS NOT NULL GROUP BY rol ORDER BY adet DESC", local_engine)
print(local_personel_roller)

# Canlı DB - secrets.toml yerine direkt st.secrets kullan
try:
    import streamlit as st
    if "DB_URL" in st.secrets:
        live_engine = create_engine(st.secrets["DB_URL"])
    else:
        print("\n⚠️ CANLI VERİTABANI: secrets.toml'da DB_URL bulunamadı")
        print("Streamlit çalışmıyor olabilir, manuel kontrol gerekli")
        sys.exit(0)
    
    print("\n" + "=" * 60)
    print("CANLI VERİTABANI")
    print("=" * 60)
    
    print("\n1. ROLLER:")
    live_roller = pd.read_sql('SELECT rol_adi FROM ayarlar_roller ORDER BY id', live_engine)
    print(live_roller)
    
    print("\n2. YETKİLER (Personel Hijyen):")
    live_yetkiler = pd.read_sql("SELECT rol_adi, erisim_turu FROM ayarlar_yetkiler WHERE modul_adi='Personel Hijyen' ORDER BY rol_adi", live_engine)
    print(live_yetkiler)
    
    print("\n3. PERSONEL ROL DAĞILIMI:")
    live_personel_roller = pd.read_sql("SELECT rol, COUNT(*) as adet FROM personel WHERE rol IS NOT NULL GROUP BY rol ORDER BY adet DESC", live_engine)
    print(live_personel_roller)
    
    # KARŞILAŞTIRMA
    print("\n" + "=" * 60)
    print("KARŞILAŞTIRMA")
    print("=" * 60)
    
    roller_esit = local_roller.equals(live_roller)
    yetkiler_esit = local_yetkiler.equals(live_yetkiler)
    personel_esit = local_personel_roller.equals(live_personel_roller)
    
    print(f"\n✓ ROLLER EŞİT Mİ? {'✅ EVET' if roller_esit else '❌ HAYIR'}")
    print(f"✓ YETKİLER EŞİT Mİ? {'✅ EVET' if yetkiler_esit else '❌ HAYIR'}")
    print(f"✓ PERSONEL ROLLER EŞİT Mİ? {'✅ EVET' if personel_esit else '❌ HAYIR'}")
    
    if not roller_esit or not yetkiler_esit or not personel_esit:
        print("\n⚠️ VERİTABANLARI SENKRON DEĞİL - SYNC GEREKLİ!")
    else:
        print("\n✅ TÜM VERİTABANLARI SENKRON")
    
except ImportError:
    print("\n⚠️ Streamlit import edilemedi, manuel DB URL kullanılacak")
    try:
        live_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
        live_engine = create_engine(live_url)
        
        print("\n" + "=" * 60)
        print("CANLI VERİTABANI (Manuel Bağlantı)")
        print("=" * 60)
        
        print("\n1. ROLLER:")
        live_roller = pd.read_sql('SELECT rol_adi FROM ayarlar_roller ORDER BY id', live_engine)
        print(live_roller)
        
        print("\n2. YETKİLER (Personel Hijyen):")
        live_yetkiler = pd.read_sql("SELECT rol_adi, erisim_turu FROM ayarlar_yetkiler WHERE modul_adi='Personel Hijyen' ORDER BY rol_adi", live_engine)
        print(live_yetkiler)
        
        print("\n3. PERSONEL ROL DAĞILIMI:")
        live_personel_roller = pd.read_sql("SELECT rol, COUNT(*) as adet FROM personel WHERE rol IS NOT NULL GROUP BY rol ORDER BY adet DESC", live_engine)
        print(live_personel_roller)
        
        # KARŞILAŞTIRMA
        print("\n" + "=" * 60)
        print("KARŞILAŞTIRMA")
        print("=" * 60)
        
        roller_esit = local_roller.equals(live_roller)
        yetkiler_esit = local_yetkiler.equals(live_yetkiler)
        personel_esit = local_personel_roller.equals(live_personel_roller)
        
        print(f"\n✓ ROLLER EŞİT Mİ? {'✅ EVET' if roller_esit else '❌ HAYIR'}")
        print(f"✓ YETKİLER EŞİT Mİ? {'✅ EVET' if yetkiler_esit else '❌ HAYIR'}")
        print(f"✓ PERSONEL ROLLER EŞİT Mİ? {'✅ EVET' if personel_esit else '❌ HAYIR'}")
        
        if not roller_esit or not yetkiler_esit or not personel_esit:
            print("\n⚠️ VERİTABANLARI SENKRON DEĞİL - SYNC GEREKLİ!")
        else:
            print("\n✅ TÜM VERİTABANLARI SENKRON")
            
    except Exception as e:
        print(f"\nCANLI VERİTABANI BAĞLANTI HATASI: {e}")
        
except Exception as e:
    print(f"\nBEKLENMEYEN HATA: {e}")
