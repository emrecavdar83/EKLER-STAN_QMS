import sqlite3

tables = ['personel', 'personnel', 'hijyen_kontrol_kayitlari', 'depo_giris_kayitlari', 'urun_kpi_kontrol', 'personel_vardiya_programi']
conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

print("--- Vardiya Verisi Kontrolü ---")
for t in tables:
    try:
        cursor.execute(f"SELECT distinct vardiya FROM {t}")
        results = cursor.fetchall()
        print(f"{t}: {[r[0] for r in results]}")
    except Exception as e:
        print(f"{t}: Hata - {e}")

conn.close()
