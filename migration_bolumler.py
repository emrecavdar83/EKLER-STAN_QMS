import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- AYARLAR ---
DB_URL = os.environ.get("DB_URL", 'sqlite:///ekleristan_local.db')
engine = create_engine(DB_URL)

def migrate_bolumler():
    print("=" * 50)
    print("BÖLÜM YÖNETİMİ MİGRASYON SCRIPTI")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # 1. ayarlar_bolumler tablosunu oluştur
            print("\n[1/4] ayarlar_bolumler tablosu oluşturuluyor...")
            
            # PostgreSQL vs SQLite uyumluluğu
            pk_def = "INTEGER PRIMARY KEY AUTOINCREMENT"
            if engine.dialect.name == 'postgresql':
                pk_def = "SERIAL PRIMARY KEY"
            
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS ayarlar_bolumler (
                    id {pk_def},
                    bolum_adi TEXT NOT NULL UNIQUE,
                    aktif INTEGER DEFAULT 1,
                    sira_no INTEGER DEFAULT 0,
                    aciklama TEXT
                )
            """))
            conn.commit()
            print("   [OK] Tablo olusturuldu")
            
            # 2. Varsayılan bölümleri ekle
            print("\n[2/4] Varsayilan bolumler ekleniyor...")
            
            varsayilan_bolumler = [
                ("PATAŞU", 1),
                ("KEK", 2),
                ("KREMA", 3),
                ("PROFİTEROL", 4),
                ("RULO PASTA", 5),
                ("BOMBA", 6),
                ("TEMİZLİK", 7),
                ("BULAŞIK", 8),
                ("DEPO", 9)
            ]
            
            # Mevcut bölümleri kontrol et
            mevcut = conn.execute(text("SELECT COUNT(*) FROM ayarlar_bolumler")).scalar()
            
            if mevcut == 0:
                for bolum_adi, sira in varsayilan_bolumler:
                    try:
                        conn.execute(text("""
                            INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
                            VALUES (:b, 1, :s, 'Uretim bolumu')
                        """), {"b": bolum_adi, "s": sira})
                    except Exception as e:
                        print(f"   ! {bolum_adi} zaten mevcut veya hata: {e}")
                conn.commit()
                print(f"   [OK] {len(varsayilan_bolumler)} bolum eklendi")
            else:
                print(f"   [INFO] Tabloda zaten {mevcut} bolum var, atlanıyor")
            
            # 3. Mevcut personel kayıtlarındaki bölümleri kontrol et ve ekle
            print("\n[3/4] Mevcut personel kayitlarindaki bolumler kontrol ediliyor...")
            
            try:
                # Personel tablosundaki benzersiz bölümleri al
                personel_bolumleri = pd.read_sql(
                    "SELECT DISTINCT bolum FROM personel WHERE bolum IS NOT NULL AND bolum != ''", 
                    engine
                )
                
                if not personel_bolumleri.empty:
                    eklenen = 0
                    for bolum in personel_bolumleri['bolum'].unique():
                        try:
                            # Eğer bu bölüm ayarlar_bolumler'de yoksa ekle
                            conn.execute(text("""
                                INSERT INTO ayarlar_bolumler (bolum_adi, aktif, sira_no, aciklama)
                                SELECT :b, 1, 100, 'Mevcut kayitlardan alindi'
                                WHERE NOT EXISTS (
                                    SELECT 1 FROM ayarlar_bolumler WHERE bolum_adi = :b
                                )
                            """), {"b": bolum})
                            eklenen += 1
                        except:
                            pass
                    conn.commit()
                    print(f"   [OK] Mevcut kayitlardan {eklenen} yeni bolum eklendi")
                else:
                    print("   [INFO] Personel tablosunda bolum bilgisi bulunamadi")
            except Exception as e:
                print(f"   ! Personel bolumleri kontrol hatasi: {e}")
            
            # 4. Özet bilgi
            print("\n[4/4] Migrasyon ozeti:")
            toplam = conn.execute(text("SELECT COUNT(*) FROM ayarlar_bolumler")).scalar()
            aktif = conn.execute(text("SELECT COUNT(*) FROM ayarlar_bolumler WHERE aktif = 1")).scalar()
            print(f"   * Toplam bolum sayisi: {toplam}")
            print(f"   * Aktif bolum sayisi: {aktif}")
            
            # Tüm bölümleri listele
            bolumler = pd.read_sql("SELECT bolum_adi, aktif, sira_no FROM ayarlar_bolumler ORDER BY sira_no", engine)
            print("\n   Bolum Listesi:")
            for idx, row in bolumler.iterrows():
                durum = "[+]" if row['aktif'] == 1 else "[-]"
                print(f"   {durum} {row['sira_no']:2d}. {row['bolum_adi']}")
        
        print("\n" + "=" * 50)
        print("MIGRASYON BASARIYLA TAMAMLANDI!")
        print("=" * 50)
        print("\nSimdi uygulamayi baslatabilirsiniz:")
        print("  streamlit run app.py")
        
    except Exception as e:
        print(f"\n[HATA]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_bolumler()
