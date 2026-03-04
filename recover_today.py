"""
Supabase auth.audit_log_entries ve WAL arşivinden bugün silinen verileri kurtarma.
"""
import psycopg2
from urllib.parse import unquote

DB = dict(
    host='aws-1-ap-south-1.pooler.supabase.com', port=6543,
    dbname='postgres', user='postgres.bogritpjqxcdmodxxfhv',
    password=unquote('%409083%26tprk_E'), connect_timeout=15
)

def q(sql, params=None):
    conn = psycopg2.connect(**DB)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    except Exception as e:
        return [("HATA", str(e))]
    finally:
        conn.close()

today = '2026-03-01'

print("=== auth.audit_log_entries KONTROL ===")
r = q("SELECT COUNT(*) FROM auth.audit_log_entries WHERE created_at::date = '2026-03-01'")
print(f"  Bugune ait auth log: {r}")

r = q("""
    SELECT id, payload->>'action', payload->>'actor_username', created_at
    FROM auth.audit_log_entries 
    WHERE created_at::date = '2026-03-01'
    ORDER BY created_at DESC LIMIT 20
""")
print(f"  Son auth loglar ({len(r)} kayit):")
for row in r: print(f"    {row}")

print()
print("=== INFORMATION_SCHEMA ALL SCHEMAS ===")
r = q("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('pg_catalog','information_schema')
    AND table_name ILIKE '%log%' OR table_name ILIKE '%audit%' OR table_name ILIKE '%history%'
    ORDER BY table_schema, table_name
""")
for row in r: print(f"  {row[0]}.{row[1]}")

print()
print("=== PG_SETTINGS (BACKUP/WAL) ===")
r = q("""
    SELECT name, setting FROM pg_settings 
    WHERE name IN ('wal_level','archive_mode','archive_command','max_wal_senders',
                   'hot_standby','recovery_target_time')
""")
for row in r: print(f"  {row[0]}: {row[1]}")

print()
print("=== SCHEMAS ===")
r = q("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
for row in r: print(f"  {row[0]}")

print()
print("=== vault/storage KONTROL ===")
r = q("""
    SELECT table_schema, table_name FROM information_schema.tables 
    WHERE table_schema IN ('vault','storage','_supabase','supabase_migrations')
    ORDER BY table_schema, table_name
""")
for row in r: print(f"  {row[0]}.{row[1]}")

print()
print("TAMAMLANDI")
