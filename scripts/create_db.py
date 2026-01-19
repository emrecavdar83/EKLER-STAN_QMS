import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Date, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DB_URL = 'sqlite:///ekleristan_local.db'
engine = create_engine(DB_URL)
Base = declarative_base()

# --- SAHA_FORMU.PY İLE BİREBİR AYNI TABLO YAPISI ---

# 1. Ürün Ayarları (Ayarlar_Urunler)
class UrunAyarlari(Base):
    __tablename__ = 'ayarlar_urunler'
    id = Column(Integer, primary_key=True)
    urun_adi = Column(String)
    raf_omru_gun = Column(Integer)
    numune_sayisi = Column(Integer, default=3)
    # Ölçüm Tanımları
    olcum1_ad = Column(String); olcum1_min = Column(Float); olcum1_max = Column(Float)
    olcum2_ad = Column(String); olcum2_min = Column(Float); olcum2_max = Column(Float)
    olcum3_ad = Column(String); olcum3_min = Column(Float); olcum3_max = Column(Float)

# 2. Personel Listesi (Ayarlar_Personel & Ayarlar_Fabrika_Personel)
class Personel(Base):
    __tablename__ = 'personel'
    id = Column(Integer, primary_key=True)
    kullanici_adi = Column(String) # Admin girişi için
    sifre = Column(String)
    rol = Column(String)
    
    # Fabrika Personeli Detayları
    ad_soyad = Column(String)
    bolum = Column(String)
    gorev = Column(String)
    vardiya = Column(String)
    durum = Column(String, default="AKTİF") # AKTİF / PASİF

# 3. Üretim Kayıtları (Depo_Giris_Kayitlari)
class UretimKayit(Base):
    __tablename__ = 'depo_giris_kayitlari'
    id = Column(Integer, primary_key=True)
    tarih = Column(String)
    vardiya = Column(String)
    kullanici = Column(String)
    islem_tipi = Column(String) # URETIM
    urun = Column(String)
    lot_no = Column(String)
    miktar = Column(Integer)
    fire = Column(Integer)
    notlar = Column(String)
    zaman_damgasi = Column(String)

# 4. KPI Kayıtları (Urun_KPI_Kontrol)
class KPIKayit(Base):
    __tablename__ = 'urun_kpi_kontrol'
    id = Column(Integer, primary_key=True)
    tarih = Column(String)
    saat = Column(String)
    vardiya = Column(String)
    urun = Column(String)
    lot_no = Column(String)
    stt = Column(String)
    numune_no = Column(String)
    olcum1 = Column(Float); olcum2 = Column(Float); olcum3 = Column(Float)
    karar = Column(String)
    kullanici = Column(String)
    tat = Column(String)
    goruntu = Column(String)
    notlar = Column(String)

# 5. Hijyen Kayıtları (Hijyen_Kontrol_Kayitlari)
class HijyenKayit(Base):
    __tablename__ = 'hijyen_kontrol_kayitlari'
    id = Column(Integer, primary_key=True)
    tarih = Column(String)
    saat = Column(String)
    kullanici = Column(String)
    vardiya = Column(String)
    bolum = Column(String)
    personel = Column(String)
    durum = Column(String) # Sorun Yok, Gelmedi, vb.
    sebep = Column(String)
    aksiyon = Column(String)

# Tabloları Kur ve Örnek Veri Bas
def init_db():
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Örnek Kullanıcı (Giriş Yapabilmen İçin)
    if session.query(Personel).count() == 0:
        session.add(Personel(kullanici_adi="Admin", sifre="1234", rol="Admin"))
        # Örnek Fabrika Personeli (Hijyen Listesi İçin)
        session.add(Personel(ad_soyad="AHMET YILMAZ", bolum="BOMBA", vardiya="GÜNDÜZ VARDİYASI", durum="AKTİF"))
        session.add(Personel(ad_soyad="MEHMET DEMİR", bolum="BOMBA", vardiya="GÜNDÜZ VARDİYASI", durum="AKTİF"))
        
        # Örnek Ürün (Üretim Girişi İçin)
        session.add(UrunAyarlari(
            urun_adi="Klasik Ekler", 
            raf_omru_gun=3, 
            olcum1_ad="Gramaj", olcum1_min=28, olcum1_max=32,
            olcum2_ad="Dolgu", olcum2_min=15, olcum2_max=20
        ))
        session.commit()
        print("✅ Veritabanı ve Örnek Veriler Hazır.")

if __name__ == "__main__":
    init_db()