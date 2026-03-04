import sys
import os
import toml

sys.path.append('c:\\Projeler\\S_program\\EKLERİSTAN_QMS')
os.environ['STREAMLIT_SECRETS'] = 'c:\\Projeler\\S_program\\EKLERİSTAN_QMS\\.streamlit\\secrets.toml'

from database.connection import get_engine
import pandas as pd
from sqlalchemy import text, create_engine

def get_info(engine, label):
    try:
        with engine.connect() as conn:
            # Tablo Listesi
            if 'sqlite' in str(engine.url):
                tables_res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            else:
                tables_res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
            
            tables = [t[0] for t in tables_res]
            
            stats = {}
            # Kritik tabloların sayımları
            for tbl in ['personel', 'sicaklik_olcumleri', 'soguk_odalar', 'olcum_plani']:
                if tbl in tables:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                    stats[tbl] = count
                else:
                    stats[tbl] = 'YOK'
            
            return {
                'label': label,
                'tables': tables,
                'stats': stats
            }
    except Exception as e:
        return {'label': label, 'error': str(e)}

def main():
    try:
        with open('c:\\Projeler\\S_program\\EKLERİSTAN_QMS\\.streamlit\\secrets.toml', 'r', encoding='utf-8') as f:
            secrets = toml.load(f)
        
        engine_cloud = create_engine(secrets['streamlit']['DB_URL'])
        engine_local = get_engine()

        l_info = get_info(engine_local, 'LOKAL (SQLite)')
        c_info = get_info(engine_cloud, 'BULUT (PostgreSQL)')
        
        print('\n--- ANALİZ SONUCU ---')
        if 'error' in l_info:
            print(f"Lokal Hata: {l_info['error']}")
        else:
            print(f"Lokal Tablo Sayısı: {len(l_info['tables'])}")
            print(f"Lokal İstatistikler: {l_info['stats']}")

        if 'error' in c_info:
            print(f"Bulut Hata: {c_info['error']}")
        else:
            print(f"Bulut Tablo Sayısı: {len(c_info['tables'])}")
            print(f"Bulut İstatistikler: {c_info['stats']}")
            
        if 'tables' in l_info and 'tables' in c_info:
            l_set = set(l_info['tables'])
            c_set = set(c_info['tables'])
            print(f"\nLokalde olup Bulutta olmayan: {l_set - c_set}")
            print(f"Bulutta olup Lokalde olmayan: {c_set - l_set}")

    except Exception as e:
        print(f'Sistem Hatası: {e}')

if __name__ == '__main__':
    main()
