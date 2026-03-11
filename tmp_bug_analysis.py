import pandas as pd
from sqlalchemy import text
from database.connection import get_engine

engine = get_engine()
with engine.connect() as conn:
    print("--- -18 Depo 2 Ölçüm Analizi ---")
    # Oda ID'sini bul
    oda = conn.execute(text("SELECT id, oda_adi, min_sicaklik, max_sicaklik FROM soguk_odalar WHERE oda_adi LIKE '%Depo 2%'")).fetchone()
    if not oda:
        print("Oda bulunamadı.")
    else:
        oda_id = oda[0]
        print(f"Oda: {oda[1]} (ID: {oda_id}) [Limit: {oda[2]} - {oda[3]}]")
        
        # Son ölçümleri getir
        res = conn.execute(text("""
            SELECT id, sicaklik_degeri, olcum_zamani, planlanan_zaman, sapma_var_mi, is_takip, sapma_aciklamasi 
            FROM sicaklik_olcumleri 
            WHERE oda_id = :oid 
            ORDER BY olcum_zamani DESC LIMIT 10
        """), {"oid": oda_id}).fetchall()
        
        df = pd.DataFrame([dict(r._mapping) for r in res])
        print(df)
        
        # Planlı görevleri kontrol et
        print("\n--- Planlı Görevler ---")
        res_p = conn.execute(text("""
            SELECT id, beklenen_zaman, durum, gerceklesen_olcum_id 
            FROM olcum_plani 
            WHERE oda_id = :oid AND beklenen_zaman >= CURRENT_DATE 
            ORDER BY beklenen_zaman ASC
        """), {"oid": oda_id}).fetchall()
        df_p = pd.DataFrame([dict(r._mapping) for r in res_p])
        print(df_p)
