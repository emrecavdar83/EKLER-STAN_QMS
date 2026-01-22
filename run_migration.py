from sqlalchemy import create_engine, text
import re

# Veritabanı bağlantısı
engine = create_engine('sqlite:///ekleristan_local.db')

# SQL dosyasını oku
with open('sql/sqlite_personel_org_fix.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# SQL ifadelerini ayır (yorum satırlarını ve boşlukları temizle)
statements = []
for stmt in sql_content.split(';'):
    stmt = stmt.strip()
    # Yorum satırlarını temizle
    lines = [line for line in stmt.split('\n') if not line.strip().startswith('--')]
    clean_stmt = '\n'.join(lines).strip()
    if clean_stmt:
        statements.append(clean_stmt)

# Her ifadeyi çalıştır
with engine.connect() as conn:
    for i, stmt in enumerate(statements):
        try:
            print(f"Çalıştırılıyor ({i+1}/{len(statements)}): {stmt[:50]}...")
            result = conn.execute(text(stmt))
            
            # SELECT sorguları için sonuçları göster
            if stmt.upper().strip().startswith('SELECT'):
                rows = result.fetchall()
                if rows:
                    print("\nSonuçlar:")
                    for row in rows:
                        print(row)
                    print()
            
            conn.commit()
            print("[OK] Basarili\n")
        except Exception as e:
            print(f"[UYARI] Hata: {e}\n")
            # Bazı hatalar (örn: kolon zaten var) görmezden gelinebilir
            if "duplicate column name" not in str(e).lower():
                raise

print("\n[BASARILI] Tum islemler tamamlandi!")
