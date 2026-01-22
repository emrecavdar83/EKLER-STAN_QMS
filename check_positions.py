from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('sqlite:///ekleristan_local.db')

print("=" * 60)
print("YONETIM HIYERARSISI (Pozisyon Seviye 0-3)")
print("=" * 60)

df = pd.read_sql("""
    SELECT ad_soyad, gorev, rol, pozisyon_seviye 
    FROM personel 
    WHERE pozisyon_seviye <= 3 
    ORDER BY pozisyon_seviye
""", engine)

if df.empty:
    print("\nHIC YONETICI BULUNAMADI!")
    print("Muhtemelen rol/gorev alanlarinda 'MUDUR' kelimesi yok.")
else:
    print(f"\nToplam {len(df)} yonetici bulundu:\n")
    print(df.to_string(index=False))

print("\n" + "=" * 60)
print("TUM PERSONEL POZISYON DAGILIMI")
print("=" * 60)

summary = pd.read_sql("""
    SELECT 
        pozisyon_seviye,
        COUNT(*) as kisi_sayisi
    FROM personel
    WHERE ad_soyad IS NOT NULL
    GROUP BY pozisyon_seviye
    ORDER BY pozisyon_seviye
""", engine)

print("\n")
for _, row in summary.iterrows():
    seviye = int(row['pozisyon_seviye'])
    sayi = int(row['kisi_sayisi'])
    
    kategori = {
        0: "Yonetim Kurulu",
        1: "Genel Mudur",
        2: "Mudurler",
        3: "Sef/Koordinator"
    }.get(seviye, "Personel")
    
    print(f"Seviye {seviye} ({kategori}): {sayi} kisi")
