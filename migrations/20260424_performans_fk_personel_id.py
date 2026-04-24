"""
Migration: performans_degerledirme — personel_id FK kısıtı + backfill
Tarih: 2026-04-24
Yaklaşım: NON-DESTRUCTIVE — TEXT sütunlar (calisan_adi_soyadi, bolum, gorevi)
          korunur; personel_id INTEGER FK olarak güçlendirilir ve doldurulur.
"""
from sqlalchemy import text


def migrate(engine):
    is_pg = engine.dialect.name == 'postgresql'
    stmts = []

    # 1. FK kısıtı ekle (varsa atlanır — try/except pattern)
    if is_pg:
        stmts.append("""
            ALTER TABLE performans_degerledirme
            ADD CONSTRAINT fk_perf_personel_id
            FOREIGN KEY (personel_id)
            REFERENCES ayarlar_kullanicilar(id) ON DELETE SET NULL
        """)

    # 2. Backfill: calisan_adi_soyadi TEXT → ayarlar_kullanicilar.ad_soyad eşleştir
    stmts.append("""
        UPDATE performans_degerledirme pd
        SET personel_id = u.id
        FROM ayarlar_kullanicilar u
        WHERE TRIM(pd.calisan_adi_soyadi) = TRIM(u.ad_soyad)
          AND pd.personel_id IS NULL
    """)

    # 3. Composite index (personel+donem sorgularını hızlandırır — varsa atlanır)
    stmts.append(
        "CREATE INDEX IF NOT EXISTS idx_perf_personel_donem "
        "ON performans_degerledirme(personel_id, donem)"
    )

    with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        for stmt in stmts:
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                    print(f"[OK] {stmt[:90].replace(chr(10), ' ')}...")
                except Exception as e:
                    print(f"[SKIP] {str(e)[:120]}")

    # Doldurulan kayıt sayısını raporla
    try:
        with engine.connect() as conn:
            total  = conn.execute(text("SELECT COUNT(*) FROM performans_degerledirme")).scalar()
            dolu   = conn.execute(text("SELECT COUNT(*) FROM performans_degerledirme WHERE personel_id IS NOT NULL")).scalar()
            bos    = total - dolu
        print(f"[INFO] Toplam: {total} | personel_id dolu: {dolu} | boş (eşleşmedi): {bos}")
    except Exception:
        pass

    print("[DONE] 20260424_performans_fk_personel_id migration tamamlandı.")


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.connection import get_engine
    migrate(get_engine())
