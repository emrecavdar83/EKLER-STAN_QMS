
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import toml
import os
import sys
import logging
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, local_db_url="sqlite:///ekleristan_local.db", secrets_path=".streamlit/secrets.toml"):
        print("--- SyncManager v2.1 (Fix Active) Loaded ---")
        self.local_url = local_db_url
        self.secrets_path = secrets_path
        self.live_url = self._get_live_url()
        self.local_engine = create_engine(self.local_url)
        self.live_engine = create_engine(
            self.live_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Auto-detect connection drops
            pool_recycle=300     # Refresh connections every 5 mins
        )
        
        # Order matters! Independent tables first.
        self.sync_order = [
            "ayarlar_bolumler",          
            "ayarlar_roller",            
            "ayarlar_yetkiler",          
            "proses_tipleri",            
            "tanim_metotlar",            
            "ayarlar_kimyasallar",       
            "ayarlar_urunler",           
            "lokasyonlar",               
            "gmp_lokasyonlar",           
            "tanim_ekipmanlar",          
            "ayarlar_temizlik_plani",    
            "personel",                  
            "personel_vardiya_programi",
            "vekaletler"                 
        ]
        
        # Custom PK mapping (default is 'id')
        # Use tuple for composite keys
        self.pk_map = {
            "tanim_metotlar": "metot_adi", 
            "ayarlar_urunler": "urun_adi",
            "tanim_ekipmanlar": "ekipman_adi",
            "ayarlar_temizlik_plani": ("kat_bolum", "yer_ekipman"),
            "ayarlar_roller": "rol_adi",
            "ayarlar_yetkiler": ("rol_adi", "modul_adi"),
            "personel": "id",
            "personel_vardiya_programi": "id",
            "vekaletler": "id"
        }

    def _get_live_url(self):
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.secrets_path)
            if not os.path.exists(secrets_path):
                 # Try relative to current script if running from root
                 secrets_path = self.secrets_path
            
            secrets = toml.load(secrets_path)
            if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
                url = secrets["streamlit"]["DB_URL"]
            elif "DB_URL" in secrets:
                url = secrets["DB_URL"]
            else:
                raise ValueError("DB_URL not found in secrets")
                
            if url.startswith('"') and url.endswith('"'):
                url = url[1:-1]
            return url
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            raise

    def get_local_data(self, table):
        return pd.read_sql(f"SELECT * FROM {table}", self.local_engine)

    def get_live_data(self, table):
        return pd.read_sql(f"SELECT * FROM {table}", self.live_engine)

    def sync_table(self, table, pk=None, dry_run=False):
        # Determine PK
        if pk is None:
            pk = self.pk_map.get(table, "id")
            
        is_composite = isinstance(pk, (list, tuple))
        pk_str = str(pk) if not is_composite else ", ".join(pk)
            
        logger.info(f"Syncing table: {table} (PK: {pk_str})")
        
        try:
            df_local = self.get_local_data(table)
            df_live = self.get_live_data(table)
            
            # --- TYPE FIX: Postgres Boolean Mismatch ---
            # SQLite returns 1/0 for booleans, but Postgres strict binding requires True/False
            if 'aktif' in df_local.columns:
                df_local['aktif'] = df_local['aktif'].apply(lambda x: True if x in [1, '1', True] else False)
                if 'aktif' in df_live.columns:
                    df_live['aktif'] = df_live['aktif'].apply(lambda x: True if x in [1, '1', True] else False)
            
            # --- TYPE FIX: Integer/Float Cleanup for Postgres ---
            def clean_int_str(val, is_phone=False):
                if pd.isnull(val) or val == '' or str(val).lower() == 'nan':
                    return None
                try:
                    # For phone numbers, we MUST keep them as strings and avoid any float conversion if possible
                    # but if it's already a float like 5065866122.0, we convert to int then str
                    if isinstance(val, float):
                        if val.is_integer():
                            return str(int(val))
                        return str(val)
                    
                    val_str = str(val).strip()
                    if val_str.endswith('.0'):
                        return val_str[:-2]
                    return val_str
                except:
                    return str(val)

            def clean_int_val(val):
                if pd.isnull(val) or val == '' or str(val).lower() == 'nan' or str(val) == '0' or val == 0:
                    return None
                try:
                    return int(float(val))
                except:
                    return None

            for df in [df_local, df_live]:
                if df is None or df.empty: continue
                
                # 1. Sifre & Telefon No (Clean '.0' and keep as string)
                if 'sifre' in df.columns:
                     df['sifre'] = df['sifre'].apply(lambda x: clean_int_str(x))
                
                if 'telefon_no' in df.columns:
                     df['telefon_no'] = df['telefon_no'].apply(lambda x: clean_int_str(x, is_phone=True))
                
                # 2. ID Columns (Handle 70.0 -> 70, NaN -> None)
                for col in ['yonetici_id', 'departman_id', 'ana_departman_id', 'parent_id', 'ust_lokasyon_id', 'lokasyon_id', 'proses_tipi_id']:
                    if col in df.columns:
                        # CRITICAL: Cast to object first so None doesn't become NaN and ints don't become floats
                        df[col] = df[col].astype(object)
                        df[col] = df[col].apply(clean_int_val)
        except Exception as e:
            logger.error(f"Error reading table {table}: {e}")
            return {"status": "error", "message": str(e)}

        if df_local.empty:
            logger.info(f"Local table {table} is empty. Skipping.")
            return {"status": "skipped", "reason": "empty_local"}

        # Validation: Ensure PK columns exist in local
        if is_composite:
            for p in pk:
                if p not in df_local.columns:
                    logger.error(f"PK part {p} not found in local table {table}")
                    return {"status": "error", "message": f"pk_missing_{p}"}
        else:
            if pk not in df_local.columns:
                logger.error(f"PK {pk} not found in local table {table}")
                return {"status": "error", "message": "pk_missing"}

        stats = {"inserted": 0, "updated": 0, "skipped": 0}
        
        # Helper to generate key from row
        def get_key(row):
            if is_composite:
                return tuple(row[k] for k in pk)
            return row[pk]

        # Create a dictionary for live data for fast lookup
        live_map = {}
        if not df_live.empty:
            # For composite keys, set_index with list creates MultiIndex
            try:
                live_map = df_live.set_index(list(pk) if is_composite else pk).to_dict('index')
            except Exception as e:
                logger.warning(f"Failed to index live data: {e}")
                # Fallback or empty map implies all inserts (dangerous if data exists but index failed)
                pass

        updates = []
        inserts = []

        for _, row in df_local.iterrows():
            row_id = get_key(row)
            row_data = row.to_dict()
            
            # --- LAST MILE SANITIZAITON ---
            # Clean ALL fields before sending to DB driver
            for k, v in row_data.items():
                # 1. Handle NaNs
                if pd.isnull(v) or str(v).lower() == 'nan':
                    row_data[k] = None
                    continue
                
                # 2. Handle Floats that should be Ints (e.g. 70.0 -> 70)
                # If it looks like a float ending in .0, make it int
                if isinstance(v, float) and v.is_integer():
                     row_data[k] = int(v)
                     continue
                
                # 3. Handle Strings looking like floats '1234.0' (But NOT phone numbers which are long)
                if isinstance(v, str) and v.endswith('.0') and v[:-2].isdigit() and len(v) < 10:
                     row_data[k] = v[:-2]
            
            # Comparison Logic
            if row_id in live_map:
                # Exists -> Check for changes
                live_row = live_map[row_id]
                has_change = False
                
                # Check all columns present in local
                for col, val in row_data.items():
                    if col in live_row:
                        live_val = live_row[col]
                        # Robust comparison (str/None check)
                        val_str = str(val) if pd.notnull(val) else ""
                        live_val_str = str(live_val) if pd.notnull(live_val) else ""
                        
                        if val_str != live_val_str:
                            has_change = True
                            break # Optimization: one change is enough
                
                if has_change:
                    updates.append(row_data)
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                # New record
                inserts.append(row_data)
                stats["inserted"] += 1

        if dry_run:
            logger.info(f"DRY RUN: {table} -> To Insert: {len(inserts)}, To Update: {len(updates)}")
            return stats

        # Apply Changes
        with self.live_engine.begin() as conn:
            # 1. Inserts
            if inserts:
                pd.DataFrame(inserts).to_sql(table, conn, if_exists='append', index=False)
            
            # 2. Updates
            if updates:
                cols = [c for c in df_local.columns] # All cols
                
                # Construct WHERE clause
                if is_composite:
                    where_clause = " AND ".join([f"{k} = :{k}" for k in pk])
                else:
                    where_clause = f"{pk} = :{pk}"
                
                # Construct UPDATE SET clause (exclude PKs AND 'id' from SET to be safe)
                # We don't want to update the 'id' of an existing record as it might cause PK collisions
                set_cols = [c for c in cols if c not in (pk if is_composite else [pk]) and c != 'id']
                bind_cols = ", ".join([f"{col} = :{col}" for col in set_cols])
                
                sql = text(f"UPDATE {table} SET {bind_cols} WHERE {where_clause}")
                
                conn.execute(sql, updates)
        
        logger.info(f"Finished {table}: {stats}")
        return stats

    def run_full_sync(self, dry_run=False):
        results = {}
        for table in self.sync_order:
            # Check if table exists in local
            if inspect(self.local_engine).has_table(table):
                if table == "personel":
                    results[table] = self.sync_personnel_two_stage(dry_run=dry_run)
                else:
                    results[table] = self.sync_table(table, dry_run=dry_run)
            else:
                logger.warning(f"Table {table} not found locally. Skipping.")
        return results

    def sync_personnel_two_stage(self, dry_run=False):
        """Special two-stage sync for personnel to handle yonetici_id foreign key constraints."""
        table = "personel"
        pk = "id"
        logger.info(f"Syncing table: {table} (Two-Stage)")

        try:
            df_local = self.get_local_data(table)
            
            # --- PRE-PROCESSING ---
            # Type cleanup same as sync_table
            def clean_int_str(val):
                if pd.isnull(val) or val == '' or str(val).lower() == 'nan': return None
                if isinstance(val, float) and val.is_integer(): return str(int(val))
                s = str(val).strip()
                return s[:-2] if s.endswith('.0') else s

            def robust_id_clean(v):
                if pd.isnull(v) or str(v).strip() in ['0', '0.0', 'None', 'nan', '', '0.']: return None
                try: return int(float(v))
                except: return None

            df_local['telefon_no'] = df_local['telefon_no'].apply(clean_int_str)
            df_local['sifre'] = df_local['sifre'].apply(clean_int_str)
            df_local['yonetici_id'] = df_local['yonetici_id'].apply(robust_id_clean)
            df_local['departman_id'] = df_local['departman_id'].apply(robust_id_clean)

            # Stage 1: Insert/Update everything with yonetici_id = None
            df_stage1 = df_local.copy()
            df_stage1['yonetici_id'] = None
            
            # Use original sync_table logic but with custom data
            # Temporarily monkeypatch get_local_data to return our stage1 df
            original_get_local = self.get_local_data
            self.get_local_data = lambda t: df_stage1 if t == table else original_get_local(t)
            
            stats = self.sync_table(table, pk=pk, dry_run=dry_run)
            
            # Stage 2: Update yonetici_id for everyone
            if not dry_run:
                logger.info("Stage 2: Updating yonetici_id hierarchy...")
                updates = []
                for _, row in df_local.iterrows():
                    if pd.notnull(row['yonetici_id']):
                        updates.append({
                            "id": int(row['id']),
                            "yonetici_id": int(row['yonetici_id'])
                        })
                
                if updates:
                    with self.live_engine.begin() as conn:
                        sql = text(f"UPDATE {table} SET yonetici_id = :yonetici_id WHERE id = :id")
                        conn.execute(sql, updates)
                logger.info(f"Stage 2 complete: Updated {len(updates)} managers.")

            self.get_local_data = original_get_local # Restore
            return stats

        except Exception as e:
            logger.error(f"Error in two-stage sync for personnel: {e}")
            return {"status": "error", "message": str(e)}

    def dispose(self):
        """Close all database connections."""
        if self.local_engine:
            self.local_engine.dispose()
        if self.live_engine:
            self.live_engine.dispose()
        logger.info("SyncManager engines disposed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

if __name__ == "__main__":
    manager = SyncManager()
    manager.run_full_sync(dry_run=False)
