import sqlite3
conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()
cursor.execute("UPDATE personel SET durum = 'Aktif' WHERE ad_soyad LIKE '%ABDULMOLIK BAROKOT%'")
conn.commit()
conn.close()
print("Fixed Abdulmolik status")
