import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
c = conn.cursor()

print("=== AKTİF ODALAR ===")
c.execute("SELECT id, oda_kodu, oda_adi FROM soguk_odalar WHERE aktif=1")
for r in c.fetchall():
    print("  ID=%s | Kod=%s | Ad=%s" % (r[0], r[1], r[2]))

print("\n=== BUGÜN 2026-03-03 KAYITLAR ===")
c.execute(
    "SELECT o.oda_adi, s.olcum_zamani, s.sicaklik_degeri, s.kaydeden_kullanici"
    " FROM sicaklik_olcumleri s JOIN soguk_odalar o ON s.oda_id=o.id"
    " WHERE DATE(s.olcum_zamani)='2026-03-03' ORDER BY s.olcum_zamani DESC"
)
rows = c.fetchall()
print("Toplam kayit: %d" % len(rows))
for r in rows:
    print("  ", r)

print("\n=== TUM ZAMANLAR SON 20 KAYIT ===")
c.execute(
    "SELECT o.oda_adi, s.olcum_zamani, s.sicaklik_degeri, s.kaydeden_kullanici"
    " FROM sicaklik_olcumleri s JOIN soguk_odalar o ON s.oda_id=o.id"
    " ORDER BY s.id DESC LIMIT 20"
)
for r in c.fetchall():
    print("  ", r)

print("\n=== PLAN DURUMU PER ODA ===")
c.execute(
    "SELECT o.oda_adi, p.durum, COUNT(*)"
    " FROM olcum_plani p JOIN soguk_odalar o ON p.oda_id=o.id"
    " GROUP BY o.oda_adi, p.durum ORDER BY o.oda_adi, p.durum"
)
for r in c.fetchall():
    print("  ", r)
