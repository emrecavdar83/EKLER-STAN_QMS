import psycopg2
from urllib.parse import unquote
from collections import defaultdict

DB = dict(
    host='aws-1-ap-south-1.pooler.supabase.com', port=6543,
    dbname='postgres', user='postgres.bogritpjqxcdmodxxfhv',
    password=unquote('%409083%26tprk_E'), connect_timeout=15
)
today = '2026-03-01'

def q(sql, params=None):
    conn = psycopg2.connect(**DB)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        return rows
    except Exception as e:
        return [("HATA", str(e))]
    finally:
        conn.close()

# ---- ODALAR ----
print("=== SOGUK ODALAR ===")
odalar = q("SELECT id, oda_adi, min_sicaklik, max_sicaklik, aktif FROM soguk_odalar ORDER BY id")
for o in odalar:
    print(f"  [{o[0]}] {o[1][:45]} | {o[2]}/{o[3]}C | aktif:{o[4]}")

# ---- TABLOLAR ----
print("\n=== TABLOLAR ===")
tables = q("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")
for t in tables:
    cnt = q(f"SELECT COUNT(*) FROM {t[0]}")
    print(f"  {t[0]}: {cnt[0][0]}")

# ---- sapma tipi ----
dtype = q("SELECT data_type FROM information_schema.columns WHERE table_name='sicaklik_olcumleri' AND column_name='sapma_var_mi'")
print(f"\nsapma_var_mi tipi: {dtype[0][0] if dtype else '?'}")

# ---- SON 30 GUN SICAKLIK ----
print("\n=== SON 30 GUN SICAKLIK (gune gore) ===")
rows = q("""
    SELECT olcum_zamani::date as gun, COUNT(*) as adet
    FROM sicaklik_olcumleri
    WHERE olcum_zamani >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY gun ORDER BY gun DESC
""")
if rows and rows[0][0] != "HATA":
    for r in rows: print(f"  {r[0]}: {r[1]} olcum")
else:
    print(f"  {rows}")

# ---- SON 30 GUN KPI ----
print("\n=== SON 30 GUN KPI ===")
rows = q("""
    SELECT tarih::date, COUNT(*) FROM urun_kpi_kontrol
    WHERE tarih::date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY tarih::date ORDER BY tarih::date DESC
""")
if rows and rows[0][0] != "HATA":
    for r in rows: print(f"  {r[0]}: {r[1]}")
else:
    print(f"  {rows}")

# ---- SON 30 GUN URETIM ----
print("\n=== SON 30 GUN URETIM ===")
rows = q("""
    SELECT tarih::date, COUNT(*) FROM depo_giris_kayitlari
    WHERE tarih::date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY tarih::date ORDER BY tarih::date DESC
""")
if rows and rows[0][0] != "HATA":
    for r in rows: print(f"  {r[0]}: {r[1]}")
else:
    # text olarak dene
    rows2 = q("SELECT tarih, COUNT(*) FROM depo_giris_kayitlari GROUP BY tarih ORDER BY tarih DESC LIMIT 15")
    for r in rows2: print(f"  {r[0]}: {r[1]}")

# ---- SON 3 GUN SOSTS SAATLIK ----
print("\n=== SON 3 GUN SOSTS SAATLIK DAGILIM ===")
rows = q("""
    SELECT s.olcum_zamani::date as gun,
           EXTRACT(HOUR FROM s.olcum_zamani)::int as saat,
           o.oda_adi, COUNT(*) as adet
    FROM sicaklik_olcumleri s
    JOIN soguk_odalar o ON s.oda_id = o.id
    WHERE s.olcum_zamani >= CURRENT_DATE - INTERVAL '3 days'
    GROUP BY gun, saat, o.oda_adi
    ORDER BY gun DESC, saat, o.oda_adi
""")
if rows and rows[0][0] != "HATA":
    cur_day = None
    for r in rows:
        if r[0] != cur_day:
            cur_day = r[0]
            print(f"  --- {cur_day} ---")
        print(f"    {r[1]:02d}:00 | {r[2][:35]}: {r[3]} olcum")
else:
    print(f"  {rows}")

# ---- OLCUM PLANI ----
print("\n=== OLCUM PLANI ===")
plan = q("""
    SELECT p.oda_id, o.oda_adi, p.planlanan_saat
    FROM olcum_plani p JOIN soguk_odalar o ON p.oda_id=o.id
    ORDER BY p.oda_id, p.planlanan_saat
""")
if plan and plan[0][0] != "HATA":
    grp = defaultdict(list)
    for oid, oadi, saat in plan:
        grp[(oid, oadi[:35])].append(str(saat)[:5])
    for (oid, oadi), saatler in sorted(grp.items()):
        print(f"  [{oid}] {oadi}: {saatler}")

    print(f"\n  Toplam plan satiri: {len(plan)}")

    # BUGUN PLAN vs GERCEK
    print("\n=== BUGUN PLAN vs GERCEK ===")
    pv = q("""
        SELECT p.oda_id, o.oda_adi, p.planlanan_saat,
               s.id, s.sicaklik_degeri, s.olcum_zamani
        FROM olcum_plani p
        JOIN soguk_odalar o ON p.oda_id = o.id
        LEFT JOIN sicaklik_olcumleri s
            ON s.oda_id = p.oda_id
            AND s.olcum_zamani::date = '2026-03-01'
            AND ABS(EXTRACT(EPOCH FROM (s.olcum_zamani::time - p.planlanan_saat::time)) / 60) < 90
        ORDER BY p.oda_id, p.planlanan_saat
    """)
    if pv and pv[0][0] != "HATA":
        giren = sum(1 for r in pv if r[3] is not None)
        eksik = sum(1 for r in pv if r[3] is None)
        print(f"  Beklenen: {len(pv)} | Giren: {giren} | EKSIK: {eksik}")
        for r in pv:
            durum = f"OK | {r[4]}C @ {r[5]}" if r[3] else "*** EKSIK ***"
            print(f"  [{r[0]}] {r[1][:35]} | {str(r[2])[:5]} | {durum}")
    else:
        print(f"  {pv}")
else:
    print(f"  {plan}")

# ---- SON KAYIT ZAMANLARI ----
print("\n=== TUM TABLOLARIN SON KAYIT ZAMANI ===")
son_kayitlar = [
    ("sicaklik_olcumleri", "SELECT MAX(olcum_zamani) FROM sicaklik_olcumleri"),
    ("urun_kpi_kontrol",   "SELECT MAX(tarih::text) FROM urun_kpi_kontrol"),
    ("depo_giris_kayitlari", "SELECT MAX(tarih::text) FROM depo_giris_kayitlari"),
    ("hijyen_kontrol_kayitlari", "SELECT MAX(tarih::text) FROM hijyen_kontrol_kayitlari"),
    ("temizlik_kayitlari", "SELECT MAX(tarih::text) FROM temizlik_kayitlari"),
    ("gmp_denetim_kayitlari", "SELECT MAX(tarih::text) FROM gmp_denetim_kayitlari"),
]
for tablo, sql in son_kayitlar:
    r = q(sql)
    print(f"  {tablo}: {r[0][0] if r else '?'}")

print("\n=== TARAMA TAMAMLANDI ===")
