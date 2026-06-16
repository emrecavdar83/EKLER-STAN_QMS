"""
Migration: temizlik_kayitlari tablosuna 'vardiya' sütunu ekleme.
Hata Ref: #E-20260616-3UVD
Sebep: temizlik_ui.py INSERT sırasında 'vardiya' sütununa yazıyor ancak
       tabloda bu sütun mevcut değildi.
"""
from sqlalchemy import text


def run(conn):
    """temizlik_kayitlari tablosuna eksik 'vardiya' sütununu ekler."""
    # Sütun zaten varsa hata vermesin — idempotent migration
    try:
        conn.execute(text(
            "ALTER TABLE temizlik_kayitlari ADD COLUMN IF NOT EXISTS "
            "vardiya VARCHAR(20)"
        ))
        print("[MIGRATION] temizlik_kayitlari.vardiya sütunu eklendi.")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
            print("[MIGRATION] temizlik_kayitlari.vardiya zaten mevcut, atlanıyor.")
        else:
            raise
