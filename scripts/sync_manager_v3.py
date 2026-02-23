import pandas as pd
import toml
import os
import sqlite3
import logging
from sqlalchemy import create_engine, text, inspect
from datetime import datetime

import time
from sqlalchemy.exc import InternalError, OperationalError

# --- CONFIGURATION ---
LOG_FILE = "sync_v3.log"
LOCAL_DB = "sqlite:///ekleristan_local.db"
SECRETS_FILE = ".streamlit/secrets.toml"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger("SyncV3")

class SyncManagerV3:
    def __init__(self):
        self.local_engine = create_engine(LOCAL_DB)
        self.live_engine = self._init_live_engine()
        
        # TABLE_CONFIG: {table_name: (Direction, PK)}
        # Direction: 'PUSH' (Lokal->Live), 'PULL' (Live->Lokal), 'BOTH'
        self.config = {
            "personel": ("BOTH", "id"),
            "ayarlar_yetkiler": ("PULL", ("rol_adi", "modul_adi")),
            "ayarlar_roller": ("PULL", "rol_adi"),
            "ayarlar_bolumler": ("PULL", "id"),
            "soguk_odalar": ("BOTH", "id"),
            "sicaklik_olcumleri": ("PUSH", "id"),
            "olcum_plani": ("PUSH", "id"),
            "hijyen_kontrol_kayitlari": ("PUSH", "id"),
            "temizlik_kayitlari": ("PUSH", "id"),
            "gmp_denetim_kayitlari": ("PUSH", "id"),
            "ayarlar_temizlik_plani": ("PULL", "kayit_no"),
            "tanim_ekipmanlar": ("PULL", "ekipman_adi"),
            "lokasyonlar": ("PULL", "id"),
            "proses_tipleri": ("PULL", "id")
        }

    def _init_live_engine(self):
        try:
            secrets = toml.load(SECRETS_FILE)
            url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
            if url.startswith('"') and url.endswith('"'):
                url = url[1:-1]
            return create_engine(url, pool_pre_ping=True, pool_recycle=300)
        except Exception as e:
            logger.error(f"Live engine initialization failed: {e}")
            raise

    def get_data(self, engine, table):
        try:
            return pd.read_sql(f"SELECT * FROM {table}", engine)
        except Exception as e:
            logger.warning(f"Could not read table {table}: {e}")
            return pd.DataFrame()

    def sync_direction(self, table, source_engine, target_engine, pk, direction_label):
        logger.info(f"--- Syncing {table} [{direction_label}] ---")
        try:
            df_src = self.get_data(source_engine, table)
            if df_src.empty:
                logger.info(f"Source {table} is empty. Skipping.")
                return 0
            
            df_tgt = self.get_data(target_engine, table)
            
            is_composite = isinstance(pk, (list, tuple))
            pk_list = list(pk) if is_composite else [pk]
            
            # Map target for comparison
            tgt_keys = set()
            if not df_tgt.empty:
                for _, row in df_tgt.iterrows():
                    tgt_keys.add(tuple(row[p] for p in pk_list))
            
            inserts = []
            updates = []
            
            for _, row in df_src.iterrows():
                key = tuple(row[p] for p in pk_list)
                row_dict = row.to_dict()
                
                # --- TYPE CLEANING & CONVERSION ---
                params = {}
                for k, v in row_dict.items():
                    # 1. Handle NaNs
                    if pd.isna(v):
                        params[k] = None
                        continue
                    
                    # 2. Handle Timestamps (Critical for SQLite PULL)
                    if direction_label == "BULUT -> LOKAL" and (isinstance(v, pd.Timestamp) or hasattr(v, 'isoformat')):
                        params[k] = v.isoformat() if hasattr(v, 'isoformat') else str(v)
                        continue
                        
                    params[k] = v
                
                if key in tgt_keys:
                    updates.append(params)
                else:
                    inserts.append(params)
            
            # --- TRANSACT WITH RETRY (Deadlock Protection) ---
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with target_engine.begin() as conn:
                        if inserts:
                            pd.DataFrame(inserts).to_sql(table, conn, if_exists='append', index=False)
                            logger.info(f"Inserted {len(inserts)} rows into {direction_label} {table}")
                        
                        if updates:
                            all_cols = df_src.columns
                            set_cols = [c for c in all_cols if c not in pk_list and c != 'id']
                            if set_cols:
                                set_clause = ", ".join([f"{c} = :{c}" for c in set_cols])
                                where_clause = " AND ".join([f"{p} = :{p}" for p in pk_list])
                                sql = text(f"UPDATE {table} SET {set_clause} WHERE {where_clause}")
                                conn.execute(sql, updates)
                                logger.info(f"Updated {len(updates)} rows in {direction_label} {table}")
                    break # Success!
                except (InternalError, OperationalError) as e:
                    if "deadlock" in str(e).lower() and attempt < max_retries - 1:
                        logger.warning(f"Deadlock detected on {table} (Attempt {attempt+1}). Retrying in 2s...")
                        time.sleep(2)
                    else:
                        raise e
            
            return len(inserts) + len(updates)
        except Exception as e:
            logger.error(f"Sync failed for {table} [{direction_label}]: {e}")
            return 0

    def run_otonom_sync(self):
        logger.info("🚀 OTONOM SENKRONİZASYON BAŞLADI")
        processed = 0
        for table, (mode, pk) in self.config.items():
            if mode in ["PUSH", "BOTH"]:
                processed += self.sync_direction(table, self.local_engine, self.live_engine, pk, "LOKAL -> BULUT")
            
            if mode in ["PULL", "BOTH"]:
                processed += self.sync_direction(table, self.live_engine, self.local_engine, pk, "BULUT -> LOKAL")
        
        logger.info(f"🏁 Senkronizasyon Tamamlandı. Toplam İşlem: {processed}")
        return processed

if __name__ == "__main__":
    sync = SyncManagerV3()
    sync.run_otonom_sync()
