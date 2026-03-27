-- UP MIGRATION: Performans Darboğazı Giderme (Indexleme)
-- Akıllı Akış (Smart Flow) tabloları için B-Tree Indeksleri

-- personnel_tasks tablosu (Matrisin ve Flow'un kalbi)
CREATE INDEX IF NOT EXISTS idx_personnel_tasks_personel_durum ON personnel_tasks(personel_id, durum);
CREATE INDEX IF NOT EXISTS idx_personnel_tasks_node_batch ON personnel_tasks(node_id, batch_id);

-- flow_nodes ve flow_edges
CREATE INDEX IF NOT EXISTS idx_flow_nodes_flow_id ON flow_nodes(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_edges_source ON flow_edges(source_node_id);

-- DOWN MIGRATION
-- DROP INDEX IF EXISTS idx_personnel_tasks_personel_durum;
-- DROP INDEX IF EXISTS idx_personnel_tasks_node_batch;
-- DROP INDEX IF EXISTS idx_flow_nodes_flow_id;
-- DROP INDEX IF EXISTS idx_flow_edges_source;
