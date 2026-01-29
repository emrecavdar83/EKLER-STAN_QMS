
import sqlalchemy
from sqlalchemy import create_engine, text

# Local database connection
db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

def delete_admin_user():
    target_name = "SİSTEM ADMİN"
    
    with engine.connect() as conn:
        # Check if user exists
        print(f"Checking for user: {target_name}...")
        result = conn.execute(text("SELECT id, ad_soyad, gorev FROM personel WHERE ad_soyad = :name"), {"name": target_name})
        users = result.fetchall()
        
        if not users:
            print(f"❌ User '{target_name}' not found in local database.")
            # Try fuzzy search just in case
            result = conn.execute(text("SELECT id, ad_soyad FROM personel WHERE ad_soyad LIKE :name"), {"name": '%ADMIN%'})
            similar = result.fetchall()
            if similar:
                print("Found similar users:", similar)
            return

        print(f"✅ Found {len(users)} user(s):")
        for u in users:
            print(f" - ID: {u.id}, Name: {u.ad_soyad}, Role: {u.gorev}")

        # Execute Deletion
        print(f"Deleting '{target_name}'...")
        conn.execute(text("DELETE FROM personel WHERE ad_soyad = :name"), {"name": target_name})
        conn.commit()
        print("✅ Deletion successful.")

if __name__ == "__main__":
    delete_admin_user()
