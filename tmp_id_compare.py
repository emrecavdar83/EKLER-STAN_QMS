import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
c = conn.cursor()

print("=== 1. KAYIT EDİLEN ODA ID'LERİ (sicaklik_olcumleri) ===")
c.execute("""
    SELECT s.oda_id, o.oda_adi, o.oda_kodu, COUNT(*) as kayit_sayisi, MAX(s.olcum_zamani) as son_kayit
    FROM sicaklik_olcumleri s
    LEFT JOIN soguk_odalar o ON s.oda_id = o.id
    GROUP BY s.oda_id, o.oda_adi, o.oda_kodu
    ORDER BY s.oda_id
""")
kayit_idler = c.fetchall()
for r in kayit_idler:
    print("  oda_id=%-3s | oda_adi=%-40s | oda_kodu=%-15s | kayit=%s | son=%s" % r)

print("\n=== 2. RAPORDA KULLANILAN ODA ID'LERİ (soguk_odalar - aktif) ===")
c.execute("SELECT id, oda_adi, oda_kodu, aktif FROM soguk_odalar ORDER BY id")
rapor_odalar = c.fetchall()
for r in rapor_odalar:
    aktif_str = "AKTİF" if r[3] == 1 else "PASİF"
    print("  id=%-3s | oda_adi=%-40s | oda_kodu=%-15s | %s" % (r[0], r[1], r[2], aktif_str))

print("\n=== 3. PLAN ID'LERİ (olcum_plani - hangi oda_id'ler var) ===")
c.execute("""
    SELECT p.oda_id, o.oda_adi, COUNT(*) as slot_sayisi, 
           SUM(CASE WHEN p.gerceklesen_olcum_id IS NOT NULL THEN 1 ELSE 0 END) as tamamlanan
    FROM olcum_plani p
    LEFT JOIN soguk_odalar o ON p.oda_id = o.id
    GROUP BY p.oda_id, o.oda_adi
    ORDER BY p.oda_id
""")
for r in c.fetchall():
    print("  oda_id=%-3s | %-40s | toplam_slot=%-5s | tamamlanan=%s" % r)

print("\n=== 4. UYUMSUZ ID KONTROLÜ ===")
# Kayıt var ama soguk_odalar'da olmayan ID'ler
c.execute("""
    SELECT DISTINCT s.oda_id 
    FROM sicaklik_olcumleri s
    WHERE s.oda_id NOT IN (SELECT id FROM soguk_odalar)
""")
orphans = c.fetchall()
if orphans:
    print("  UYARI: Tabloda karşılığı olmayan oda_id'ler:", orphans)
else:
    print("  Tüm kayıtlar geçerli oda_id'lere sahip - uyumsuzluk yok.")

print("\n=== 5. get_matrix_data SORGUSU SİMÜLASYONU (bugün) ===")
import datetime
bugun = datetime.date.today()
s_str = bugun.strftime('%Y-%m-%d 00:00:00')
e_str = (bugun + datetime.timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
print("  Sorgu aralığı: %s → %s" % (s_str, e_str))
c.execute("""
    SELECT o.id as oda_id, o.oda_adi, COUNT(*) as kayit
    FROM sicaklik_olcumleri m
    JOIN soguk_odalar o ON m.oda_id = o.id
    WHERE m.olcum_zamani >= ? AND m.olcum_zamani < ?
    GROUP BY o.id, o.oda_adi
""", (s_str, e_str))
rows = c.fetchall()
if rows:
    for r in rows:
        print("  oda_id=%-3s | %-40s | kayit=%s" % r)
else:
    print("  BUGÜN HİÇ KAYIT YOK (bu tarih aralığında veri döndürülmüyor)")
