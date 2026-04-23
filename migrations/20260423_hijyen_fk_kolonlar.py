"""
Migration: hijyen_kontrol_kayitlari — kullanici_id ve bolum_id FK kolonları ekleme
Tarih: 2026-04-23
Yaklaşım: NON-DESTRUCTIVE — eski TEXT sütunlar korunur, yeni FK sütunlar eklenir.
          Mevcut TEXT değerlerinden en iyi çabayla doldurulur.
"""
from sqlalchemy import text


def migrate(engine):
    stmts = []

    # 1. Yeni FK sütunlar ekle (nullable — mevcut INSERT'leri kırmaz)
    stmts += [
        """ALTER TABLE hijyen_kontrol_kayitlari
           ADD COLUMN IF NOT EXISTS kullanici_id INTEGER
               REFERENCES ayarlar_kullanicilar(id) ON DELETE SET NULL""",

        """ALTER TABLE hijyen_kontrol_kayitlari
           ADD COLUMN IF NOT EXISTS bolum_id INTEGER
               REFERENCES qms_departmanlar(id) ON DELETE SET NULL""",
    ]

    # 2. Mevcut TEXT değerlerinden doldur (en iyi çaba — eşleşmeyenler NULL kalır)
    stmts += [
        # kullanici: h.kullanici TEXT → ayarlar_kullanicilar.ad_soyad eşleştir
        """UPDATE hijyen_kontrol_kayitlari h
           SET kullanici_id = u.id
           FROM ayarlar_kullanicilar u
           WHERE TRIM(h.kullanici) = TRIM(u.ad_soyad)
             AND h.kullanici_id IS NULL""",

        # bolum: h.bolum TEXT → qms_departmanlar.ad eşleştir
        """UPDATE hijyen_kontrol_kayitlari h
           SET bolum_id = d.id
           FROM qms_departmanlar d
           WHERE TRIM(h.bolum) = TRIM(d.ad)
             AND h.bolum_id IS NULL""",
    ]

    # 3. Yeni FK sütunlara index ekle
    stmts += [
        "CREATE INDEX IF NOT EXISTS idx_hijyen_kullanici_id ON hijyen_kontrol_kayitlari(kullanici_id)",
        "CREATE INDEX IF NOT EXISTS idx_hijyen_bolum_id     ON hijyen_kontrol_kayitlari(bolum_id)",
        "CREATE INDEX IF NOT EXISTS idx_hijyen_tarih        ON hijyen_kontrol_kayitlari(tarih DESC)",
    ]

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
            total   = conn.execute(text("SELECT COUNT(*) FROM hijyen_kontrol_kayitlari")).scalar()
            k_dolu  = conn.execute(text("SELECT COUNT(*) FROM hijyen_kontrol_kayitlari WHERE kullanici_id IS NOT NULL")).scalar()
            b_dolu  = conn.execute(text("SELECT COUNT(*) FROM hijyen_kontrol_kayitlari WHERE bolum_id IS NOT NULL")).scalar()
        print(f"[INFO] Toplam kayıt: {total} | kullanici_id dolu: {k_dolu} | bolum_id dolu: {b_dolu}")
    except Exception:
        pass

    print("[DONE] 20260423_hijyen_fk_kolonlar migration tamamlandı.")


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.connection import get_engine
    migrate(get_engine())
