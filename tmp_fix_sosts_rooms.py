import sys
import os
import toml

sys.path.append('c:\\Projeler\\S_program\\EKLERİSTAN_QMS')
os.environ['STREAMLIT_SECRETS'] = 'c:\\Projeler\\S_program\\EKLERİSTAN_QMS\\.streamlit\\secrets.toml'

from database.connection import get_engine
import pandas as pd
from sqlalchemy import text, create_engine

gercek_odalar = [
    { 'oda_kodu': 'DONUK-1', 'oda_adi': '-18 DONUK DEPO', 'min_sicaklik': -24.0, 'max_sicaklik': -18.0 },
    { 'oda_kodu': 'DONUK-2', 'oda_adi': '-18 DONUK DEPO 2', 'min_sicaklik': -24.0, 'max_sicaklik': -18.0 },
    { 'oda_kodu': 'SOGODA-1', 'oda_adi': 'SOĞUK ODA 1', 'min_sicaklik': 0.0, 'max_sicaklik': 4.0 },
    { 'oda_kodu': 'SOGODA-2', 'oda_adi': 'SOĞUK ODA 2', 'min_sicaklik': 0.0, 'max_sicaklik': 4.0 },
    { 'oda_kodu': 'SOGODA-3', 'oda_adi': 'SOĞUK ODA KREMA YARI MAMÜL EKLER', 'min_sicaklik': 0.0, 'max_sicaklik': 4.0 }
]

def veritabani_duzenle(engine, ortam_adi):
    print(f'\n=== {ortam_adi} DÜZENLENİYOR ===')
    with engine.begin() as conn:
        # Tüm odaları pasife al
        conn.execute(text('UPDATE soguk_odalar SET aktif = 0'))
        print('Eski odalar pasife alındı.')
        
        for oda in gercek_odalar:
            res = conn.execute(text('SELECT id FROM soguk_odalar WHERE oda_kodu = :kodu OR oda_adi = :adi'), {'kodu': oda['oda_kodu'], 'adi': oda['oda_adi']}).fetchone()
            if res:
                conn.execute(text('UPDATE soguk_odalar SET aktif = 1, oda_adi = :adi, oda_kodu = :kodu, min_sicaklik = :mnt, max_sicaklik = :mxt WHERE id = :oid'), {
                    'adi': oda['oda_adi'], 'kodu': oda['oda_kodu'], 'mnt': oda['min_sicaklik'], 'mxt': oda['max_sicaklik'], 'oid': res[0]
                })
                print(f'GÜNCELLENDİ: {oda["oda_adi"]}')
            else:
                conn.execute(text('INSERT INTO soguk_odalar (oda_kodu, oda_adi, min_sicaklik, max_sicaklik, aktif) VALUES (:kodu, :adi, :mnt, :mxt, 1)'), {
                    'adi': oda['oda_adi'], 'kodu': oda['oda_kodu'], 'mnt': oda['min_sicaklik'], 'mxt': oda['max_sicaklik']
                })
                print(f'EKLENDİ: {oda["oda_adi"]}')

        # Eski gereksiz planları ve ölçümleri temizle (soft delete / hard delete plan)
        conn.execute(text('DELETE FROM olcum_plani WHERE oda_id IN (SELECT id FROM soguk_odalar WHERE aktif = 0)'))
        print('Pasif odaların bekleyen planları silindi.')

        # Sonucu doğrula
        sonuc = pd.read_sql(text('SELECT id, oda_kodu, oda_adi, min_sicaklik, max_sicaklik, aktif FROM soguk_odalar WHERE aktif = 1 ORDER BY oda_adi'), conn)
        print(f'{ortam_adi} AKTİF ODALAR:')
        print(sonuc.to_string())

def main():
    try:
        with open('c:\\Projeler\\S_program\\EKLERİSTAN_QMS\\.streamlit\\secrets.toml', 'r', encoding='utf-8') as f:
            secrets = toml.load(f)
        
        # Bulut Engine
        engine_cloud = create_engine(secrets['streamlit']['DB_URL'])
        # Lokal Engine
        engine_local = get_engine()
        
        veritabani_duzenle(engine_cloud, 'BULUT (POSTGRESQL)')
        veritabani_duzenle(engine_local, 'LOKAL (SQLITE)')
        
    except Exception as e:
        print(f'HATA: {e}')

if __name__ == '__main__':
    main()
