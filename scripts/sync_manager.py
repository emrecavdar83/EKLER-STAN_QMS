import logging
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import toml
import os
import sys
import json
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
        self.ensure_queue_table()
        
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
            "vekaletler",
            "sistem_parametreleri",
            "soguk_odalar",
            "sicaklik_olcumleri",
            "olcum_plani"
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
            "vekaletler": "id",
            "sistem_parametreleri": "anahtar",
            "soguk_odalar": "id",
            "sicaklik_olcumleri": "id",
            "olcum_plani": "id"
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
        with self.local_engine.connect() as conn:
            res = conn.execute(text(f"SELECT * FROM {table}"))
            return [dict(row._mapping) for row in res.fetchall()]

    def get_live_data(self, table):
        with self.live_engine.connect() as conn:
            res = conn.execute(text(f"SELECT * FROM {table}"))
            return [dict(row._mapping) for row in res.fetchall()]

    def sync_table(self, table, pk=None, dry_run=False):
        if pk is None:
            pk = self.pk_map.get(table, "id")
            
        is_composite = isinstance(pk, (list, tuple))
        pk_str = str(pk) if not is_composite else ", ".join(pk)
            
        logger.info(f"Syncing table: {table} (PK: {pk_str})")
        
        try:
            logger.info(f"[{table}] Fetching local data...")
            local_data = self.get_local_data(table)
            logger.info(f"[{table}] Fetching live data...")
            live_data = self.get_live_data(table)
            
            logger.info(f"[{table}] Found Local: {len(local_data)}, Live: {len(live_data)}")
            
            if not local_data:
                logger.info(f"Local table {table} is empty. Skipping.")
                return {"status": "skipped", "reason": "empty_local"}

            pk_list = list(pk) if is_composite else [pk]

            # Map live data for comparison
            live_map = {}
            for row in live_data:
                key = tuple(row[k] for k in pk_list) if is_composite else row[pk]
                live_map[key] = row
                
            updates = []
            inserts = []
            stats = {"inserted": 0, "updated": 0, "skipped": 0}

            for row in local_data:
                key = tuple(row[k] for k in pk_list) if is_composite else row[pk]
                
                # Pre-processing for Postgres/SQLite compatibility
                for k, v in row.items():
                    if v == "" or str(v).lower() == 'nan': row[k] = None
                    # Boolean fix
                    if k == 'aktif' and v is not None:
                        row[k] = True if v in [1, True, 'True'] else False

                if key in live_map:
                    live_row = live_map[key]
                    has_change = False
                    for col, val in row.items():
                        if col in live_row:
                            # Robust comparison
                            v1 = str(val) if val is not None else ""
                            v2 = str(live_row[col]) if live_row[col] is not None else ""
                            if v1 != v2:
                                has_change = True
                                break
                    if has_change:
                        updates.append(row)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    inserts.append(row)
                    stats["inserted"] += 1

            if dry_run:
                logger.info(f"DRY RUN: {table} -> To Insert: {len(inserts)}, To Update: {len(updates)}")
                return stats

            # Apply Changes
            with self.live_engine.begin() as conn:
                # 1. Inserts
                if inserts:
                    cols = [c for c in inserts[0].keys() if c != 'id']
                    placeholders = ", ".join([f":{c}" for c in cols])
                    sql = text(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})")
                    conn.execute(sql, inserts)
                
                # 2. Updates
                if updates:
                    cols = list(updates[0].keys())
                    where_clause = " AND ".join([f"{k} = :{k}" for k in pk_list]) if is_composite else f"{pk} = :{pk}"
                    set_cols = [c for c in cols if c not in pk_list and c != 'id']
                    bind_cols = ", ".join([f"{col} = :{col}" for col in set_cols])
                    sql = text(f"UPDATE {table} SET {bind_cols} WHERE {where_clause}")
                    conn.execute(sql, updates)
                
                # 3. DELETES (Sync Local -> Live)
                local_keys = set(tuple(row[k] for k in pk_list) if is_composite else row[pk] for row in local_data)
                live_keys = set(tuple(row[k] for k in pk_list) if is_composite else row[pk] for row in live_data)
                to_delete_keys = live_keys - local_keys

                if to_delete_keys:
                    # SAFETY CHECK: If local is empty, do NOT delete from live automatically
                    if not local_data:
                        logger.warning(f"SAFETY TRIGGERED: Local table {table} is empty. Skipping DELETE on LIVE to prevent data loss.")
                    else:
                        logger.info(f"Detected {len(to_delete_keys)} records to DELETE on LIVE (Symmetric Twin).")
                        if dry_run:
                            logger.info(f"DRY RUN: Would delete keys {to_delete_keys} from {table} on LIVE.")
                        else:
                            delete_data = []
                            for k in to_delete_keys:
                                if is_composite:
                                    delete_data.append(dict(zip(pk_list, k)))
                                else:
                                    delete_data.append({pk: k})
                            
                            where_clause = " AND ".join([f"{k} = :{k}" for k in pk_list]) if is_composite else f"{pk} = :{pk}"
                            sql = text(f"DELETE FROM {table} WHERE {where_clause}")
                            conn.execute(sql, delete_data)
                            logger.info(f"Successfully deleted {len(to_delete_keys)} records from {table} on LIVE.")
                            stats["deleted"] = len(to_delete_keys)
            
            logger.info(f"Finished {table}: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error syncing table {table}: {e}")
            return {"status": "error", "message": str(e)}

    def pull_table(self, table, pk=None, dry_run=False):
        """Pulls data from Cloud (Live) to Local SQLite (Bi-directional Mirror)."""
        if pk is None:
            pk = self.pk_map.get(table, "id")
            
        is_composite = isinstance(pk, (list, tuple))
        pk_str = str(pk) if not is_composite else ", ".join(pk)
            
        logger.info(f"Pulling table: {table} (PK: {pk_str})")
        
        try:
            live_data = self.get_live_data(table)
            local_data = self.get_local_data(table)
            
            if not live_data:
                logger.info(f"Live table {table} is empty. Skipping.")
                return {"status": "skipped", "reason": "empty_live"}

            pk_list = list(pk) if is_composite else [pk]

            # Map local data
            local_map = {}
            for row in local_data:
                key = tuple(row[k] for k in pk_list) if is_composite else row[pk]
                local_map[key] = row
                
            updates = []
            inserts = []
            stats = {"pulled_new": 0, "pulled_updated": 0, "skipped": 0}

            for row in live_data:
                key = tuple(row[k] for k in pk_list) if is_composite else row[pk]
                
                # Pre-processing for SQLite
                for k, v in row.items():
                    if v == "" or str(v).lower() == 'nan': row[k] = None
                    if k == 'aktif' and v is not None:
                        row[k] = 1 if v in [True, 1, 'True'] else 0

                if key in local_map:
                    local_row = local_map[key]
                    has_change = False
                    for col, val in row.items():
                        if col in local_row:
                            v1 = str(val) if val is not None else ""
                            v2 = str(local_row[col]) if local_row[col] is not None else ""
                            if v1 != v2:
                                has_change = True
                                break
                    if has_change:
                        updates.append(row)
                        stats["pulled_updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    inserts.append(row)
                    stats["pulled_new"] += 1

            if dry_run:
                logger.info(f"DRY RUN (PULL): {table} -> To Insert: {len(inserts)}, To Update: {len(updates)}")
                return stats

            # Apply to Local
            with self.local_engine.begin() as conn:
                if inserts:
                    cols = list(inserts[0].keys())
                    placeholders = ", ".join([f":{c}" for c in cols])
                    sql = text(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})")
                    conn.execute(sql, inserts)
                if updates:
                    cols = list(updates[0].keys())
                    where_clause = " AND ".join([f"{k} = :{k}" for k in pk_list]) if is_composite else f"{pk} = :{pk}"
                    set_cols = [c for c in cols if c not in pk_list and c != 'id']
                    bind_cols = ", ".join([f"{col} = :{col}" for col in set_cols])
                    sql = text(f"UPDATE {table} SET {bind_cols} WHERE {where_clause}")
                    conn.execute(sql, updates)

                # 3. DELETES (Pull Live -> Local)
                live_keys = set(tuple(row[k] for k in pk_list) if is_composite else row[pk] for row in live_data)
                local_keys = set(tuple(row[k] for k in pk_list) if is_composite else row[pk] for row in local_data)
                to_delete_keys = local_keys - live_keys

                if to_delete_keys:
                    # SAFETY CHECK: If live is empty, do NOT delete from local automatically
                    if not live_data:
                        logger.warning(f"SAFETY TRIGGERED: Live table {table} is empty. Skipping DELETE on LOCAL to prevent data loss.")
                    else:
                        logger.info(f"Detected {len(to_delete_keys)} records to DELETE on LOCAL (Symmetric Twin).")
                        if dry_run:
                            logger.info(f"DRY RUN: Would delete keys {to_delete_keys} from {table} on LOCAL.")
                        else:
                            delete_data = []
                            for k in to_delete_keys:
                                if is_composite:
                                    delete_data.append(dict(zip(pk_list, k)))
                                else:
                                    delete_data.append({pk: k})
                                    
                            where_clause = " AND ".join([f"{k} = :{k}" for k in pk_list]) if is_composite else f"{pk} = :{pk}"
                            sql = text(f"DELETE FROM {table} WHERE {where_clause}")
                            conn.execute(sql, delete_data)
                            logger.info(f"Successfully deleted {len(to_delete_keys)} records from {table} on LOCAL.")
                            stats["pulled_deleted"] = len(to_delete_keys)
            
            logger.info(f"Finished Pull {table}: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error pulling table {table}: {e}")
            return {"status": "error", "message": str(e)}

    def sync_personnel_two_stage(self, dry_run=False):
        """Special two-stage sync for personnel to handle yonetici_id foreign key constraints."""
        table = "personel"
        pk = "id"
        logger.info(f"Syncing table: {table} (Two-Stage)")

        try:
            local_data = self.get_local_data(table)
            
            # --- PRE-PROCESSING ---
            for row in local_data:
                # Phone fix
                if 'telefon_no' in row and row['telefon_no']:
                    s = str(row['telefon_no']).strip()
                    row['telefon_no'] = s[:-2] if s.endswith('.0') else s
                # Sifre fix
                if 'sifre' in row and row['sifre']:
                    s = str(row['sifre']).strip()
                    row['sifre'] = s[:-2] if s.endswith('.0') else s
                
                # ID Clean logic
                for col in ['yonetici_id', 'departman_id']:
                    if col in row and row[col]:
                        try: row[col] = int(float(row[col]))
                        except: row[col] = None

            # Stage 1: Insert/Update everything with yonetici_id = None
            stage1_data = [dict(row) for row in local_data]
            for row in stage1_data: row['yonetici_id'] = None
            
            # Monkeypatch get_local_data to return our stage1 data
            original_get_local = self.get_local_data
            self.get_local_data = lambda t: stage1_data if t == table else original_get_local(t)
            
            # 1. PULL (Live -> Local)
            pull_stats = self.pull_table(table, pk=pk, dry_run=dry_run)
            
            # 2. PUSH (Local -> Live)
            push_stats = self.sync_table(table, pk=pk, dry_run=dry_run)
            
            stats = {"pull": pull_stats, "push": push_stats}
            
            # Stage 2: Update yonetici_id
            if not dry_run:
                logger.info("Stage 2: Updating yonetici_id hierarchy...")
                updates = []
                for row in local_data:
                    if row['yonetici_id']:
                        updates.append({"id": int(row['id']), "yonetici_id": int(row['yonetici_id'])})
                
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

    def ensure_sosts_tables(self):
        """Ensures that SOSTS tables exist in the local database to prevent OperationalErrors."""
        logger.info("Checking/Initializing SOSTS tables in local database...")
        try:
            from soguk_oda_utils import init_sosts_tables
            init_sosts_tables(self.local_engine)
            logger.info("Local SOSTS tables verified.")
        except ImportError:
            logger.warning("soguk_oda_utils not found. Skipping auto-initialization.")
        except Exception as e:
            logger.error(f"Failed to initialize local tables: {e}")

    def run_full_sync(self, dry_run=False):
        """Executes a full bi-directional sync for all tables in sync_order."""
        logger.info(f"--- STARTING FULL SYNC (Dry Run: {dry_run}) ---")
        self.ensure_sosts_tables()
        
        results = {}
        for table in self.sync_order:
            if table == "personel":
                res = self.sync_personnel_two_stage(dry_run=dry_run)
            else:
                # 1. Pull from Live to Local (Symmetric Twin: Get updates first)
                pull_res = self.pull_table(table, dry_run=dry_run)
                # 2. Sync from Local to Live (Symmetric Twin: Push local changes)
                push_res = self.sync_table(table, dry_run=dry_run)
                res = {"pull": pull_res, "push": push_res}
            
            results[table] = res
        
        logger.info("--- FULL SYNC COMPLETED ---")
        return results

    def dispose(self):
        """Close all database connections."""
        if self.local_engine:
            self.local_engine.dispose()
        if self.live_engine:
            self.live_engine.dispose()
        logger.info("SyncManager engines disposed.")

    def ensure_queue_table(self):
        """Creates the sync_queue table in the local SQLite database."""
        with self.local_engine.begin() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tablo_adi VARCHAR(100) NOT NULL,
                islem_tipi VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
                kayit_verisi TEXT, -- JSON format
                olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                durum VARCHAR(20) DEFAULT 'bekliyor', -- bekliyor, tamamlandi, failed, basarisiz
                deneme_sayisi INTEGER DEFAULT 0
            )
            """))

    def baglanti_var_mi(self):
        """Checks if the cloud database (Supabase/Postgres) is reachable with a simple ping."""
        logger.debug("Checking cloud connection...")
        try:
            with self.live_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.debug("Cloud connection OK.")
                return True
        except Exception as e:
            logger.warning(f"Cloud connection failed: {e}")
            return False

    def kuyruga_ekle(self, tablo, islem_tipi, veri):
        """Adds an operation to the local sync queue."""
        try:
            with self.local_engine.begin() as conn:
                conn.execute(text("""
                INSERT INTO sync_queue (tablo_adi, islem_tipi, kayit_verisi, durum)
                VALUES (:t, :i, :v, 'bekliyor')
                """), {"t": tablo, "i": islem_tipi, "v": json.dumps(veri)})
            logger.info(f"Kuyruğa eklendi: {islem_tipi} -> {tablo}")
        except Exception as e:
            logger.error(f"Kuyruğa ekleme hatası: {e}")

    def kuyrugu_isle(self):
        """Processes pending items in the sync queue if connection is available."""
        logger.info("Kuyruk işleme kontrolü başlatıldı...")
        if not self.baglanti_var_mi():
            logger.warning("Bulut bağlantısı yok. Kuyruk işleme atlandı.")
            return

        logger.info("Bekleyen kayıtlar sorgulanıyor...")
        with self.local_engine.connect() as conn:
            res = conn.execute(text("""
                SELECT id, tablo_adi, islem_tipi, kayit_verisi, deneme_sayisi 
                FROM sync_queue 
                WHERE (durum = 'bekliyor' OR durum = 'failed') AND deneme_sayisi < 3
                ORDER BY olusturma_zamani ASC
            """))
            rows = res.fetchall()
            items = [dict(row._mapping) for row in rows]

        if not items:
            logger.info("İşlenecek kuyruk öğesi yok.")
            return

        logger.info(f"{len(items)} kuyruk öğesi işleniyor...")
        for item in items:
            try:
                logger.info(f"İşleniyor: ID {item['id']} ({item['islem_tipi']} {item['tablo_adi']})")
                veri = json.loads(item['kayit_verisi'])
                tablo = item['tablo_adi']
                islem = item['islem_tipi'].upper()
                pk = self.pk_map.get(tablo, "id")

                # PostgreSQL normalization (active -> boolean)
                if 'aktif' in veri and veri['aktif'] is not None:
                    veri['aktif'] = True if veri['aktif'] in [True, 1, 'True', '1'] else False
                
                with self.live_engine.begin() as live_conn:
                    if islem == 'INSERT':
                        cols = [c for c in veri.keys() if c != 'id']
                        placeholders = ", ".join([f":{c}" for c in cols])
                        sql = text(f"INSERT INTO {tablo} ({', '.join(cols)}) VALUES ({placeholders})")
                        live_conn.execute(sql, veri)
                    elif islem == 'UPDATE':
                        cols = list(veri.keys())
                        pk_list = list(pk) if isinstance(pk, (list, tuple)) else [pk]
                        where_clause = " AND ".join([f"{k} = :{k}" for k in pk_list])
                        set_cols = [c for c in cols if c not in pk_list and c != 'id']
                        bind_cols = ", ".join([f"{col} = :{col}" for col in set_cols])
                        sql = text(f"UPDATE {tablo} SET {bind_cols} WHERE {where_clause}")
                        live_conn.execute(sql, veri)
                    elif islem == 'DELETE':
                        pk_list = list(pk) if isinstance(pk, (list, tuple)) else [pk]
                        where_clause = " AND ".join([f"{k} = :{k}" for k in pk_list])
                        sql = text(f"DELETE FROM {tablo} WHERE {where_clause}")
                        live_conn.execute(sql, veri)
                
                with self.local_engine.begin() as local_conn:
                    local_conn.execute(text("UPDATE sync_queue SET durum = 'tamamlandi' WHERE id = :id"), {"id": item['id']})
                logger.info(f"Kuyruk öğesi {item['id']} başarıyla işlendi.")

            except Exception as e:
                logger.error(f"Kuyruk öğesi {item['id']} hata: {e}")
                new_deneme = item['deneme_sayisi'] + 1
                new_durum = 'failed' if new_deneme < 3 else 'basarisiz'
                
                with self.local_engine.begin() as local_conn:
                    local_conn.execute(text("""
                        UPDATE sync_queue 
                        SET deneme_sayisi = :d, durum = :s 
                        WHERE id = :id
                    """), {"d": new_deneme, "s": new_durum, "id": item['id']})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

if __name__ == "__main__":
    manager = SyncManager()
    manager.run_full_sync(dry_run=False)
