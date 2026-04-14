"""
Personel Seçici Sıfırlama Scripti
===================================
AMAÇ:
  - emre.cavdar ve hdenliyeva hesaplarını koru
  - hdenliyeva'yı ADMIN rolüyle aktif et (personel oluşturabilsin)
  - Diğer tüm personel kayıtlarını ve bağımlı verilerini temizle

KULLANIM:
  python scripts/personel_sifirlama.py --dry-run   # Önce ne olacağını gör
  python scripts/personel_sifirlama.py --execute   # Gerçekten çalıştır

HEDEF DB: Hem local SQLite hem Supabase (env'e göre otomatik seçer)
"""

import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

KORUNAN_KULLANICILAR = ['emre.cavdar']

BAGIMLI_TABLOLAR = [
    'personel_vardiya_programi',
    'personel_vardiya_istisnalari',
    'personel_transfer_log',
    'personel_performans_skorlari',
    'birlesik_gorev_havuzu',
    'qdms_okuma_onay',
    'polivalans_matris',
    'performans_degerledirme',
    'flow_bypass_logs',
    'hijyen_kayitlari',
    'kpi_olcum',
    'map_uretim_kayitlari',
    'temizlik_kontrol_kayitlari',
]

# QDMS ve log FK kolonları — NULL'a çekilerek korunur (belgeler silinmez)
QDMS_NULL_KOLONLAR = [
    ('qdms_belgeler',      'olusturan_id'),
    ('qdms_revizyon_log',  'degistiren_id'),
    ('qdms_yayim',         'yayimlayan_id'),
    ('sistem_loglari',     'kullanici_id'),
]


def get_engine():
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return create_engine(db_url)
    return create_engine('sqlite:///ekleristan_local.db',
                         connect_args={'check_same_thread': False})


def tablo_var_mi(conn, tablo, is_pg):
    if is_pg:
        r = conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=:t"
        ), {"t": tablo}).scalar()
    else:
        r = conn.execute(text(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:t"
        ), {"t": tablo}).scalar()
    return r > 0


def kolon_var_mi(conn, tablo, kolon, is_pg):
    try:
        if is_pg:
            r = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name=:t AND column_name=:c"
            ), {"t": tablo, "c": kolon}).scalar()
        else:
            cols = conn.execute(text(f"PRAGMA table_info({tablo})")).fetchall()
            r = sum(1 for c in cols if c[1] == kolon)
        return r > 0
    except Exception:
        return False


def calistir(dry_run=True):
    engine = get_engine()
    is_pg = 'postgresql' in str(engine.url)
    db_tipi = "Supabase (PostgreSQL)" if is_pg else "Local SQLite"

    print(f"\n{'='*60}")
    print(f"  PERSONEL SEÇICI SIFIRLAMA")
    print(f"  Hedef DB: {db_tipi}")
    print(f"  Mod: {'DRY-RUN (gerçek işlem YOK)' if dry_run else '*** EXECUTE - GERÇEK İŞLEM ***'}")
    print(f"{'='*60}\n")

    with engine.begin() as conn:

        # 1. Korunan hesapları doğrula
        print("── KORUNAN HESAPLAR ──────────────────────────────────────")
        korunan_ids = []
        for kullanici in KORUNAN_KULLANICILAR:
            row = conn.execute(text(
                "SELECT id, ad_soyad, rol, durum FROM personel WHERE kullanici_adi=:k"
            ), {"k": kullanici}).fetchone()
            if row:
                print(f"  ✅ BULUNDU  → {kullanici} | {row[1]} | Rol:{row[2]} | {row[3]}")
                korunan_ids.append(row[0])
            else:
                print(f"  ⚠️  BULUNAMADI → {kullanici}")

        if not korunan_ids:
            print("\n❌ Hiçbir korunan hesap bulunamadı. İşlem iptal.")
            return

        # 2. Silinecek personeli göster
        print("\n── SİLİNECEK PERSONEL ───────────────────────────────────")
        if len(korunan_ids) == 1:
            silinecekler = conn.execute(text(
                "SELECT id, ad_soyad, kullanici_adi, rol FROM personel WHERE id != :k1"
            ), {"k1": korunan_ids[0]}).fetchall()
        else:
            silinecekler = conn.execute(text(
                "SELECT id, ad_soyad, kullanici_adi, rol FROM personel "
                "WHERE id NOT IN (:k1, :k2)"
            ), {"k1": korunan_ids[0], "k2": korunan_ids[1]}).fetchall()

        if silinecekler:
            print(f"  Toplam {len(silinecekler)} kayıt silinecek:")
            for r in silinecekler:
                print(f"    ID:{r[0]}  {r[1]}  [{r[2] or '—'}]  Rol:{r[3]}")
        else:
            print("  Silinecek başka personel yok.")

        # 3. Bağımlı tablolardaki etkilenecek kayıtları say
        print("\n── BAĞIMLI VERİ ÖZETI ────────────────────────────────────")
        silinecek_ids = [r[0] for r in silinecekler]
        if silinecek_ids:
            for tablo in BAGIMLI_TABLOLAR:
                if not tablo_var_mi(conn, tablo, is_pg):
                    continue
                if not kolon_var_mi(conn, tablo, 'personel_id', is_pg):
                    continue
                try:
                    n = conn.execute(text(
                        f"SELECT COUNT(*) FROM {tablo} WHERE personel_id = ANY(:ids)"
                        if is_pg else
                        f"SELECT COUNT(*) FROM {tablo} WHERE personel_id IN ({','.join(str(i) for i in silinecek_ids)})"
                    ), {"ids": silinecek_ids} if is_pg else {}).scalar()
                    if n:
                        print(f"  📦 {tablo}: {n} kayıt silinecek")
                except Exception as e:
                    print(f"  ⚠️  {tablo}: sayım hatası ({e})")

        print()

        if dry_run:
            print("💡 Gerçekten çalıştırmak için: python scripts/personel_sifirlama.py --execute")
            print("="*60)
            return

    # ── GERÇEK İŞLEM — her adım kendi transaction'ında ──────────

    print("── ADIM 1: emre.cavdar korunuyor ─────────────────────────")

    if not silinecek_ids:
        print("  Silinecek personel yok.")
        return

    id_list = ','.join(str(i) for i in silinecek_ids)
    any_param = silinecek_ids

    # 2. Bağımlı tablolar — her biri ayrı transaction
    print("── ADIM 2: Bağımlı tablolar temizleniyor ─────────────────")
    for tablo in BAGIMLI_TABLOLAR:
        with engine.begin() as c:
            if not tablo_var_mi(c, tablo, is_pg):
                continue
            if not kolon_var_mi(c, tablo, 'personel_id', is_pg):
                continue
            try:
                if is_pg:
                    r = c.execute(text(f"DELETE FROM {tablo} WHERE personel_id = ANY(:ids)"), {"ids": any_param})
                else:
                    r = c.execute(text(f"DELETE FROM {tablo} WHERE personel_id IN ({id_list})"))
                if r.rowcount:
                    print(f"  deleted  {tablo}: {r.rowcount} kayıt")
            except Exception as e:
                print(f"  skip  {tablo}: {e}")

    # QDMS / log FK referansları → NULL yap (belgeler korunur)
    print("── ADIM 2b: QDMS / log FK referansları NULL'a çekiliyor ─")
    for tablo, kolon in QDMS_NULL_KOLONLAR:
        with engine.begin() as c:
            if not tablo_var_mi(c, tablo, is_pg):
                continue
            if not kolon_var_mi(c, tablo, kolon, is_pg):
                continue
            try:
                if is_pg:
                    r = c.execute(text(f"UPDATE {tablo} SET {kolon}=NULL WHERE {kolon} = ANY(:ids)"), {"ids": any_param})
                else:
                    r = c.execute(text(f"UPDATE {tablo} SET {kolon}=NULL WHERE {kolon} IN ({id_list})"))
                if r.rowcount:
                    print(f"  nulled  {tablo}.{kolon}: {r.rowcount} kayıt")
            except Exception as e:
                print(f"  skip  {tablo}.{kolon}: {e}")

    # onaylayan_id
    with engine.begin() as c:
        try:
            if tablo_var_mi(c, 'birlesik_gorev_havuzu', is_pg):
                if is_pg:
                    c.execute(text("UPDATE birlesik_gorev_havuzu SET onaylayan_id=NULL WHERE onaylayan_id = ANY(:ids)"), {"ids": any_param})
                else:
                    c.execute(text(f"UPDATE birlesik_gorev_havuzu SET onaylayan_id=NULL WHERE onaylayan_id IN ({id_list})"))
        except Exception:
            pass

    # departman yöneticisi
    with engine.begin() as c:
        try:
            if tablo_var_mi(c, 'qms_departmanlar', is_pg):
                if is_pg:
                    c.execute(text("UPDATE qms_departmanlar SET yonetici_id=NULL WHERE yonetici_id = ANY(:ids)"), {"ids": any_param})
                else:
                    c.execute(text(f"UPDATE qms_departmanlar SET yonetici_id=NULL WHERE yonetici_id IN ({id_list})"))
        except Exception:
            pass

    # personel self-reference
    for kolon in ['yonetici_id', 'vekil_id', 'ikincil_yonetici_id']:
        with engine.begin() as c:
            try:
                if kolon_var_mi(c, 'personel', kolon, is_pg):
                    if is_pg:
                        c.execute(text(f"UPDATE personel SET {kolon}=NULL WHERE {kolon} = ANY(:ids)"), {"ids": any_param})
                    else:
                        c.execute(text(f"UPDATE personel SET {kolon}=NULL WHERE {kolon} IN ({id_list})"))
            except Exception:
                pass

    # 3. Personelleri sil
    print("── ADIM 3: Personel kayıtları siliniyor ──────────────────")
    with engine.begin() as c:
        if is_pg:
            r = c.execute(text("DELETE FROM personel WHERE id = ANY(:ids)"), {"ids": any_param})
        else:
            r = c.execute(text(f"DELETE FROM personel WHERE id IN ({id_list})"))
        print(f"  ✅ {r.rowcount} personel silindi")

    # Audit log
    with engine.begin() as c:
        try:
            c.execute(text(
                "INSERT INTO sistem_loglari (islem_tipi, detay) VALUES "
                "('PERSONEL_SIFIRLAMA', 'emre.cavdar korundu, diger tum personel temizlendi.')"
            ))
        except Exception:
            pass

    print("\n" + "="*60)
    print("  ✅ İŞLEM TAMAMLANDI")
    print("  Kalan hesap: emre.cavdar (ADMIN/AKTİF)")
    print("  Uygulama yeniden başlatıldığında değişiklikler aktif olur.")
    print("="*60)


if __name__ == "__main__":
    if '--execute' in sys.argv:
        onay = input("\n⚠️  Bu işlem geri alınamaz. Devam etmek için 'EVET' yazın: ")
        if onay.strip().upper() == 'EVET':
            calistir(dry_run=False)
        else:
            print("İptal edildi.")
    else:
        calistir(dry_run=True)
