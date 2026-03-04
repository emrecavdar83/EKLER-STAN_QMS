import sys
import os
import toml
import pandas as pd
from sqlalchemy import text, create_engine

# Add project to path
sys.path.append('c:\\Projeler\\S_program\\EKLERİSTAN_QMS')
os.environ['STREAMLIT_SECRETS'] = 'c:\\Projeler\\S_program\\EKLERİSTAN_QMS\\.streamlit\\secrets.toml'

from database.connection import get_engine

def get_qr_info(engine):
    with engine.connect() as conn:
        res = conn.execute(text("SELECT oda_kodu, qr_token FROM soguk_odalar WHERE aktif = 1")).fetchall()
        return pd.DataFrame([dict(r._mapping) for r in res])

try:
    with open('c:\\Projeler\\S_program\\EKLERİSTAN_QMS\\.streamlit\\secrets.toml', 'r', encoding='utf-8') as f:
        secrets = toml.load(f)
    engine_cloud = create_engine(secrets['streamlit']['DB_URL'])
    engine_local = get_engine()

    l_df = get_qr_info(engine_local)
    c_df = get_qr_info(engine_cloud)
    
    merged = pd.merge(l_df, c_df, on='oda_kodu', suffixes=('_lokal', '_bulut'))
    
    print('--- QR TOKEN KARŞILAŞTIRMASI ---')
    print(merged)
    
    mismatch = merged[merged['qr_token_lokal'] != merged['qr_token_bulut']]
    if mismatch.empty:
        print('\n✅ TÜM QR TOKENLARI EŞİT.')
    else:
        print('\n❌ FARKLI TOKENLAR TESPİT EDİLDİ:')
        print(mismatch)

except Exception as e:
    print(f'HATA: {e}')
