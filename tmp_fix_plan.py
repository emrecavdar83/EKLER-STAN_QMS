"""
SOSTS Plan Tablasu Temizleme ve Yeniden Oluşturma (Lokal SQLite)
Sorun: olcum_plani tablosunda artık aktif olmayan odalar (id:2,3,4,5) için
slot var ama aktif odalar (id:6,7,8,9) için slot yok.
"""
import sqlite3, datetime

conn = sqlite3.connect('ekleristan_local.db')
c = conn.cursor()

print("DÜZELTME ÖNCESİ PLAN DURUMU:")
c.execute("SELECT oda_id, COUNT(*) FROM olcum_plani GROUP BY oda_id ORDER BY oda_id")
for r in c.fetchall():
    c.execute("SELECT oda_adi FROM soguk_odalar WHERE id=?", (r[0],))
    oda_row = c.fetchone()
    oda_adi = oda_row[0] if oda_row else "--- TABLO'DA YOK (SİLİNMİŞ ODA) ---"
    print("  oda_id=%s | slot=%s | %s" % (r[0], r[1], oda_adi))

# Adım 1: Tamamlanmamış ve silinmiş odalara ait slotları temizle
print("\n1. Eski/geçersiz oda_id'lere ait slotlar siliniyor...")
c.execute("""
    DELETE FROM olcum_plani
    WHERE oda_id NOT IN (SELECT id FROM soguk_odalar WHERE aktif=1)
    AND gerceklesen_olcum_id IS NULL
""")
silinen = c.rowcount
print("  %d slot silindi." % silinen)

# Adım 2: Tamamlanmış (tamamlanan) ama artık var olmayan oda slotlarını temizle
c.execute("""
    DELETE FROM olcum_plani
    WHERE oda_id NOT IN (SELECT id FROM soguk_odalar WHERE aktif=1)
""")
silinen2 = c.rowcount
print("  %d ek slot silindi." % silinen2)

conn.commit()

print("\nDÜZELTME SONRASI PLAN DURUMU:")
c.execute("SELECT oda_id, COUNT(*) FROM olcum_plani GROUP BY oda_id ORDER BY oda_id")
for r in c.fetchall():
    c.execute("SELECT oda_adi FROM soguk_odalar WHERE id=?", (r[0],))
    oda_row = c.fetchone()
    oda_adi = oda_row[0] if oda_row else "BILINMIYOR"
    print("  oda_id=%s | slot=%s | %s" % (r[0], r[1], oda_adi))

print("\nBaşarıyla tamamlandı.")
