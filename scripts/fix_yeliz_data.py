from sqlalchemy import create_engine, text

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- FIXING DATA FOR YELİZ ÇAKIR & GENERAL CLEANUP ---")
        
        # 1. Fix specific user YELİZ ÇAKIR (ID 49 based on debug output)
        print("1. Updating Yeliz Çakır...")
        sql_fix_yeliz = text("""
            UPDATE personel 
            SET rol = 'Personel', 
                kullanici_adi = 'yeliz.cakir',
                durum = 'AKTİF'
            WHERE ad_soyad LIKE '%YELİZ ÇAKIR%'
        """)
        result = conn.execute(sql_fix_yeliz)
        print(f"   -> Rows affected: {result.rowcount}")

        # 2. General Safety Net: Fix ALL users with NULL or Empty Role
        print("\n2. Fixing all users with missing roles...")
        sql_fix_roles = text("""
            UPDATE personel 
            SET rol = 'Personel'
            WHERE (rol IS NULL OR rol = '') AND ad_soyad IS NOT NULL
        """)
        result_roles = conn.execute(sql_fix_roles)
        print(f"   -> Rows affected (General Fix): {result_roles.rowcount}")
        
        conn.commit()
        print("\n✅ SUCCESS: Database updated successfully.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
