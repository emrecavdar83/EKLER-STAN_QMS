import sys
import os
from unittest.mock import MagicMock

# Mock Streamlit before importing anything that uses it
st = MagicMock()
st.secrets = {"DB_URL": "sqlite:///ekleristan_local.db"}
st.cache_resource = lambda f: f
st.cache_data = lambda **kwargs: lambda f: f
sys.modules["streamlit"] = st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_engine
from logic.flow_manager import get_active_flow, trigger_next_step, log_bypass
from sqlalchemy import text

engine = get_engine()

def test_flow_setup():
    print("--- 🔬 Akış Motoru Testi Başlatılıyor ---")
    with engine.begin() as conn:
        # 0. Sistem Loglari Tablosu (Varsa dokunma)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sistem_loglari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                islem_tipi VARCHAR(50),
                detay TEXT,
                zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Temizlik
        conn.execute(text("DELETE FROM flow_definitions"))
        conn.execute(text("DELETE FROM flow_nodes"))
        conn.execute(text("DELETE FROM flow_edges"))
        conn.execute(text("DELETE FROM personnel_tasks"))
        conn.execute(text("DELETE FROM flow_bypass_logs"))
        
        # 1. Akış Tanımla
        conn.execute(text("INSERT INTO flow_definitions (flow_name, urun_grubu) VALUES ('Test Akışı', 'Ekler')"))
        flow_id = conn.execute(text("SELECT id FROM flow_definitions WHERE flow_name='Test Akışı'")).fetchone()[0]
        
        # 2. Düğümleri Ekle
        conn.execute(text("INSERT INTO flow_nodes (flow_id, node_name, node_type, sira_no) VALUES (:fid, 'Pişirme', 'PROSES', 10)"), {"fid": flow_id})
        conn.execute(text("INSERT INTO flow_nodes (flow_id, node_name, node_type, sira_no) VALUES (:fid, 'Hızlı Soğutma', 'ÖLÇÜM', 20)"), {"fid": flow_id})
        
        n1 = conn.execute(text("SELECT id FROM flow_nodes WHERE node_name='Pişirme'")).fetchone()[0]
        n2 = conn.execute(text("SELECT id FROM flow_nodes WHERE node_name='Hızlı Soğutma'")).fetchone()[0]
        
        # 3. Bağlantı Kur
        conn.execute(text("INSERT INTO flow_edges (flow_id, source_node_id, target_node_id) VALUES (:fid, :s, :t)"), {"fid": flow_id, "s": n1, "t": n2})
        
        # 4. İlk Görevi Başlat
        conn.execute(text("INSERT INTO personnel_tasks (node_id, personel_id, batch_id, durum) VALUES (:nid, 1, 'BATCH-001', 'AKTIF')"), {"nid": n1})
        
    print("✅ Akış yapısı başarıyla kuruldu.")

    # 5. Tetikleme Testi
    print("🧪 Adım 1 tamamlanıyor, Tetikleme kontrol ediliyor...")
    triggers = trigger_next_step(engine, n1, 1, 'BATCH-001')
    
    if n2 in triggers:
        print(f"✅ Başarılı: Düğüm {n2} tetiklendi.")
    else:
        print(f"❌ Hata: Tetikleme başarısız.")

    # 6. Görev Kontrolü
    with engine.connect() as conn:
        task = conn.execute(text("SELECT durum FROM personnel_tasks WHERE node_id = :nid AND batch_id = 'BATCH-001'"), {"nid": n2}).fetchone()
        if task and task[0] == 'BEKLIYOR':
            print("✅ Başarılı: Sonraki görev 'BEKLIYOR' durumunda oluşturuldu.")
        else:
            print("❌ Hata: Görev durumu yanlış.")

if __name__ == "__main__":
    try:
        test_flow_setup()
        print("--- 🎉 Test Başarıyla Tamamlandı ---")
    except Exception as e:
        print(f"--- 💥 Test Hatası: {e} ---")
