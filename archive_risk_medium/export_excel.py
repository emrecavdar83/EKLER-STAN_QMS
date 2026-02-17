import sqlite3
import pandas as pd
import os

def export_personnel_to_excel():
    conn = sqlite3.connect('ekleristan_local.db')
    query = """
    SELECT 
        id as 'ID',
        ad_soyad as 'Ad Soyad',
        bolum as 'Bölüm',
        gorev as 'Görev',
        vardiya as 'Vardiya',
        durum as 'Durum',
        ise_giris_tarihi as 'İşe Giriş Tarihi'
    FROM personel
    ORDER BY ad_soyad ASC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        output_file = 'personel_listesi.xlsx'
        df.to_excel(output_file, index=False)
        full_path = os.path.abspath(output_file)
        print(f"Excel dosyası oluşturuldu: {full_path}")
        print(f"Toplam Kayıt: {len(df)}")
    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    export_personnel_to_excel()
