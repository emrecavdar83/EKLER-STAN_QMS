import pandas as pd
from sqlalchemy import create_engine
import sys

# Set output encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

engine = create_engine('sqlite:///ekleristan_local.db')

def check_health():
    print("--- 🩺 PERSONEL VERİ SAĞLIĞI KONTROLÜ ---")
    
    try:
        # 1. Genel İstatistikler
        df = pd.read_sql("SELECT * FROM personel", engine)
        print(f"Toplam Personel Sayısı: {len(df)}")
        print(f"Aktif Personel Sayısı: {len(df[df['durum'] == 'AKTİF'])}")
        
        # 2. Riskli Veriler (Level NULL olanlar)
        null_level = df[df['pozisyon_seviye'].isna()]
        if not null_level.empty:
            print(f"\n⚠️ DİKKAT: Pozisyon Seviyesi Belirlenmemiş {len(null_level)} Kişi Var (Otomatik 'Personel' yapılacaklar):")
            for _, row in null_level.iterrows():
                print(f"  - {row['ad_soyad']} (ID: {row['id']})")
        else:
            print("\n✅ Harika: Tüm personellerin poziyon seviyesi tanımlı.")

        # 3. Kritik Rol Kontrolü (Yöneticiler)
        managers = df[df['pozisyon_seviye'] <= 4].sort_values('pozisyon_seviye')
        print(f"\n📊 Yönetici Listesi ({len(managers)} Kişi) - Raporda Yönetici Görünecekler:")
        print(f"{'Seviye':<8} {'Ad Soyad':<25} {'Görev (Sistemdeki)':<30} {'Rol':<20}")
        print("-" * 85)
        for _, row in managers.iterrows():
            gorev = row['gorev'] if pd.notna(row['gorev']) and str(row['gorev']).strip() != "" else "-- BOŞ --"
            print(f"{int(row['pozisyon_seviye']):<8} {row['ad_soyad']:<25} {gorev:<30} {row['rol']:<20}")
            
        print("\nℹ️ NOT: Eğer yukarıdaki listede 'Görev' kısmı '-- BOŞ --' ise, raporda 'Rol' sütunu gösterilecektir.")

        # 4. Departman Bütünlüğü Kontrolü
        print("\n--- 🏢 DEPARTMAN BAĞLANTILARI ---")
        
        # Departman tablosunu çek
        depts = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", engine)
        valid_dept_ids = set(depts['id'].unique())
        
        # Personel departmanlarını kontrol et
        # 1. Departmanı NULL olan AKTİF personeller
        no_dept = df[(df['departman_id'].isna()) & (df['durum'] == 'AKTİF')]
        if not no_dept.empty:
            print(f"⚠️ UYARI: {len(no_dept)} Aktif personelin departmanı BOŞ!")
            for _, row in no_dept.iterrows():
                print(f"  - {row['ad_soyad']}")
        else:
            print("✅ Başarılı: Tüm aktif personellerin departman kaydı var.")
            
        # 2. Departman ID'si var ama Bölüm Tablosunda Yok (Öksüz Kayıtlar)
        orphans = df[ (~df['departman_id'].isna()) & (~df['departman_id'].isin(valid_dept_ids)) ]
        if not orphans.empty:
            print(f"❌ HATA: {len(orphans)} Personelin departman ID'si geçersiz (Silinmiş departmanda kalmışlar):")
            for _, row in orphans.iterrows():
                print(f"  - {row['ad_soyad']} (Dept ID: {row['departman_id']})")
        else:
            print("✅ Başarılı: Tüm departman atamaları geçerli ve doğru okunuyor.")
            
        print(f"ℹ️ Toplam {len(valid_dept_ids)} farklı bölüm/departman sistemde tanımlı.")
        
    except Exception as e:
        print(f"Hata: {e}")


if __name__ == "__main__":
    # Write output to file for safe reading
    with open('data_health_report.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        check_health()
    sys.stdout = sys.__stdout__
    print("Health report generated: data_health_report.txt")
