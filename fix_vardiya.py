import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_engine
from sqlalchemy import text

def fix_vardiya():
    engine = get_engine()
    
    VARDIYA_DONUSUM = {
        'GÜNDÜZ VARDİYASI': '07:00-15:00',
        'GUNDUZ VARDIYASI': '07:00-15:00',
        'GÜNDÜZ': '07:00-15:00',
        'ARA VARDİYA': '15:00-23:00',
        'ARA VARDIYA': '15:00-23:00',
        'GECE VARDİYASI': '23:00-07:00',
        'GECE VARDIYASI': '23:00-07:00',
    }
    
    tables = ['personel', 'hijyen_kontrol_kayitlari']
    total_count = 0
    
    with engine.begin() as conn:
        for t in tables:
            for old, new in VARDIYA_DONUSUM.items():
                res = conn.execute(text(f"UPDATE {t} SET vardiya=:y WHERE vardiya=:o"), {'y': new, 'o': old})
                count = getattr(res, 'rowcount', 0)
                if count > 0:
                    print(f"[{t}] {old} -> {new} ({count} kayit)")
                    total_count += count
                    
    print(f"Toplam {total_count} kayit guncellendi.")

if __name__ == '__main__':
    fix_vardiya()
