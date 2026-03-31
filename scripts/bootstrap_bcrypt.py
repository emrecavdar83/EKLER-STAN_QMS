#!/usr/bin/env python3
"""
VAKA-026: Toplu Bcrypt Migrasyonu
Plaintext şifreleri bcrypt hash'e dönüştürür.

Kullanım:
  python scripts/bootstrap_bcrypt.py           # Dry run (sadece listeler)
  python scripts/bootstrap_bcrypt.py --uygula  # Gerçek migrasyon
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows terminal encoding fix
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def _engine_olustur():
    """Streamlit bağlamı olmadan doğrudan engine oluşturur."""
    try:
        import toml
        secrets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '.streamlit', 'secrets.toml'
        )
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            db_url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
            if db_url:
                from sqlalchemy import create_engine
                print(f"Bağlantı: Supabase (PostgreSQL)")
                return create_engine(db_url)
    except ImportError:
        pass

    from sqlalchemy import create_engine
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'ekleristan_local.db'
    )
    print(f"Bağlantı: SQLite (Yerel) → {db_path}")
    return create_engine(f"sqlite:///{db_path}")


def _plaintext_mi(sifre):
    """Bcrypt hash değilse plaintext kabul eder."""
    if not sifre:
        return False
    return not str(sifre).strip().startswith('$2')


def _sifre_hashle(sifre_str):
    """bcrypt ile hash üretir — auth_logic.py ile aynı [:64] truncation.
    passlib atlanır: bcrypt>=4.x ile sürüm uyumsuzluğu var."""
    import bcrypt as _bcrypt
    safe_bytes = str(sifre_str).encode('utf-8')[:64]
    return _bcrypt.hashpw(safe_bytes, _bcrypt.gensalt()).decode('utf-8')


def bcrypt_migrasyonu_yap(dry_run=True):
    from sqlalchemy import text

    engine = _engine_olustur()

    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, kullanici_adi, sifre FROM personel "
            "WHERE kullanici_adi IS NOT NULL AND sifre IS NOT NULL"
        )).fetchall()

    plaintext_liste = [(r[0], r[1], r[2]) for r in rows if _plaintext_mi(r[2])]
    hashli_sayisi = len(rows) - len(plaintext_liste)

    print(f"\n{'=' * 50}")
    print(f"VAKA-026: Bcrypt Toplu Migrasyon")
    print(f"{'=' * 50}")
    print(f"Toplam kullanıcı   : {len(rows)}")
    print(f"Zaten hashli       : {hashli_sayisi}")
    print(f"Plaintext şifre    : {len(plaintext_liste)}")

    if not plaintext_liste:
        print("\n✅ Tüm şifreler zaten hashli. İşlem gerekmiyor.")
        return

    if dry_run:
        print(f"\n--- DRY RUN (değişiklik yapılmadı) ---")
        for p_id, kullanici_adi, _ in plaintext_liste:
            print(f"  [BEKLIYOR] ID:{p_id:>4} | {kullanici_adi}")
        print(f"\nGerçek migrasyon için:")
        print(f"  python scripts/bootstrap_bcrypt.py --uygula")
        return

    print(f"\n⚠️  GERÇEK MİGRASYON BAŞLIYOR ({len(plaintext_liste)} kullanıcı)...")
    basarili = 0
    hatali = 0

    with engine.begin() as conn:
        for p_id, kullanici_adi, sifre in plaintext_liste:
            try:
                yeni_hash = _sifre_hashle(str(sifre))
                conn.execute(
                    text("UPDATE personel SET sifre=:s WHERE id=:id"),
                    {"s": yeni_hash, "id": p_id}
                )
                conn.execute(
                    text("INSERT INTO sistem_loglari (islem_tipi, detay) VALUES ('BCRYPT_MIGRASYON', :d)"),
                    {"d": f"ID:{p_id} bcrypt ile hashlendi."}
                )
                print(f"  [OK] ID:{p_id:>4} | {kullanici_adi}")
                basarili += 1
            except Exception as e:
                print(f"  [HATA] ID:{p_id:>4} | {kullanici_adi} - {e}")
                hatali += 1

    print(f"\n{'=' * 50}")
    print(f"Tamamlandı: {basarili} başarılı, {hatali} hatalı")
    if hatali == 0:
        print("✅ VAKA-026 KAPATILDI")
    else:
        print("⚠️  Hatalı kayıtları manuel kontrol edin.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    dry_run = "--uygula" not in sys.argv
    bcrypt_migrasyonu_yap(dry_run=dry_run)
