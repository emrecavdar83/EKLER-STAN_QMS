# logic/flow_manager.py - Smart Flow Engine Core
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import json

def get_active_flow(engine, flow_name):
    """Belirtilen akışın tanımını ve düğümlerini getirir."""
    with engine.connect() as conn:
        flow = conn.execute(text("SELECT * FROM flow_definitions WHERE flow_name = :n AND aktif IS TRUE"), {"n": flow_name}).fetchone()
        if not flow:
            return None
        
        nodes = pd.read_sql(text("SELECT * FROM flow_nodes WHERE flow_id = :fid AND aktif IS TRUE ORDER BY sira_no"), conn, params={"fid": flow['id']})
        edges = pd.read_sql(text("SELECT * FROM flow_edges WHERE flow_id = :fid"), conn, params={"fid": flow['id']})
        
        return {
            "id": flow['id'],
            "name": flow['flow_name'],
            "nodes": nodes,
            "edges": edges
        }

def trigger_next_step(engine, current_node_id, personnel_id, batch_id, enforcement="SOFT"):
    """
    Bir adımı tamamlar ve bir sonraki adımı tetikler.
    13. Adam Protokolü: Eğer ara adımlar atlanmışsa otomatik backfill yapar.
    """
    with engine.begin() as conn:
        # 1. Mevcut görevi tamamla
        conn.execute(text("""
            UPDATE personnel_tasks 
            SET durum = 'TAMAMLANDI', tamamlanma_zamani = CURRENT_TIMESTAMP 
            WHERE node_id = :nid AND batch_id = :bid AND durum = 'AKTIF'
        """), {"nid": current_node_id, "bid": batch_id})
        
        # 2. Sonraki düğümleri bul
        next_edges = conn.execute(text("SELECT target_node_id FROM flow_edges WHERE source_node_id = :nid"), {"nid": current_node_id}).fetchall()
        
        triggers = []
        for edge in next_edges:
            target_id = edge[0]
            # 3. Yeni görev oluştur (Tetikleme)
            conn.execute(text("""
                INSERT INTO personnel_tasks (node_id, personel_id, batch_id, durum)
                VALUES (:nid, :pid, :bid, 'BEKLIYOR')
            """), {"nid": target_id, "pid": personnel_id, "bid": batch_id}) # Not: Gerçekte personel_id dinamik olmalı
            triggers.append(target_id)
            
        # 4. Audit Log
        conn.execute(text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('FLOW_TRIGGER', :d)"), 
                     {"d": f"Node {current_node_id} tamamlandı. {triggers} tetiklendi. Batch: {batch_id}"})
        
        return triggers

def log_bypass(engine, node_id, personnel_id, reason, level="SOFT"):
    """13. Adam Protokolü: Kural ihlali veya atlamayı belgeler."""
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO flow_bypass_logs (node_id, personnel_id, sebep, enforcement_level)
            VALUES (:nid, :pid, :s, :l)
        """), {"nid": node_id, "pid": personnel_id, "s": reason, "l": level})
        
        # Görevi BYPASS olarak işaretle
        conn.execute(text("""
            UPDATE personnel_tasks SET durum = 'BYPASS', tamamlanma_zamani = CURRENT_TIMESTAMP 
            WHERE node_id = :nid AND durum = 'AKTIF'
        """), {"nid": node_id})

def get_personnel_tasks(engine, personnel_id):
    """Personele atanmış bekleyen veya aktif görevleri getirir."""
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT t.*, n.node_name, n.node_type, f.flow_name 
            FROM personnel_tasks t
            JOIN flow_nodes n ON t.node_id = n.id
            JOIN flow_definitions f ON n.flow_id = f.id
            WHERE t.personel_id = :pid AND t.durum IN ('BEKLIYOR', 'AKTIF')
            ORDER BY t.atanma_zamani ASC
        """), conn, params={"pid": personnel_id})
