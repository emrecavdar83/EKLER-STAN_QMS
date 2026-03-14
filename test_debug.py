import traceback
from sqlalchemy import text
from database.connection import get_engine
import sys
from unittest.mock import MagicMock

# Bypass streamlit and reportlab before importing
sys.modules['streamlit'] = MagicMock()
mock_rl = MagicMock()
sys.modules['reportlab'] = mock_rl
sys.modules['reportlab.lib'] = mock_rl
sys.modules['reportlab.lib.colors'] = mock_rl
sys.modules['reportlab.lib.pagesizes'] = mock_rl
sys.modules['reportlab.lib.styles'] = mock_rl
sys.modules['reportlab.platypus'] = mock_rl
sys.modules['reportlab.lib.units'] = mock_rl

from ui.map_uretim import map_db, map_rapor_pdf

def debug_run():
    engine = get_engine()
    print("Engine connected.")
    
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, makina_no, operator_adi FROM map_vardiya ORDER BY id DESC LIMIT 5")).fetchall()
        print("Last 5 shifts:", res)
        if not res:
            return
            
        # Target the very last one
        v_id = int(res[0][0])
        print("Testing with ID:", v_id)
        
    try:
        from ui.map_uretim import map_hesap
        
        related_ids = map_db.get_related_vardiya_ids(engine, v_id)
        print("Related IDs:", related_ids)
        
        # Step through uret_is_raporu_html logic manually!
        master_content = ""
        for r_id in related_ids:
            print("Processing ID:", r_id)
            
            with engine.connect() as conn:
                df_v = map_db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": r_id})
                if df_v.empty: 
                    print("df_v empty")
                    continue
                v = df_v.iloc[0].to_dict()
                
            print("Data loaded for", r_id, "-", type(v['vardiya_sefi']))
            
            ozet = map_hesap.hesapla_sure_ozeti(engine, r_id)
            print("Ozet computed:", ozet)
            uretim = map_hesap.hesapla_uretim(engine, r_id)
            print("Uretim computed:", uretim)
            duruslar = map_hesap.hesapla_durus_ozeti(engine, r_id)
            print("Duruslar computed:", len(duruslar))
            fireler = map_hesap.hesapla_fire_ozeti(engine, r_id)
            print("Fireler computed:", len(fireler))
            df_b = map_db.get_bobinler(engine, r_id)
            print("Bobin rows:", len(df_b))
            df_z = map_db.get_zaman_cizelgesi(engine, r_id)
            print("Zaman rows:", len(df_z))
            
            # Formatting part
            z_trs = ""
            for _, r in df_z.iterrows():
                b = r.get('baslangic_ts')
                bit = r.get('bitis_ts')
                if b: b = str(b)[11:16]
                if bit: bit = str(bit)[11:16]
                else: bit = "-"
                z_trs += f"<tr><td>{r['sira_no']}</td><td>{b}</td><td>{bit}</td><td>{r['sure_dk']}</td><td>{r['durum']}</td><td>{r.get('neden') or '-'}</td></tr>"
            
            print("Zaman formatted")
            
            b_trs = ""
            for _, r in df_b.iterrows():
                b_trs += f"<tr><td>{str(r['degisim_ts'])[11:16]}</td><td>{r['bobin_lot']}</td>...</tr>"
                
            print("Bobin formatted:", len(b_trs))
            print("Makina block formatting starts")
            
            machine_summary = f"Summary: {uretim['gerceklesen_uretim']}"
            
            makina_block = f"""
            v_no: {v.get('makina_no')}
            operator: {v.get('operator_adi')}
            sef: {v.get('vardiya_sefi') or '-'}
            """
            
            print("Block done!")

    except Exception as e:
        print("EXCEPTION DETECTED:")
        print(traceback.format_exc())

if __name__ == "__main__":
    debug_run()
    print("SCRIPT FINISHED NORMALLY.")
