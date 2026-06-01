"""
Migration v8.0.0: Vardiya Saat Formatı + Bit-Mask İzin Günleri + Plan Tipi
Tarih  : 2026-04-29
Onay   : Emre ÇAVDAR (10 soru tamamlandı: A2, B2, X1-a, X2-c, X3-a, X4-a)

Kapsam:
  1. B2: personel_vardiya_programi → _v7_yedek tablosuna kopyala (DB içi yedek)
  2. A2: OFF kayıtlarını SİL (vardiya='OFF' olan satırlar)
  3. vardiya_tipleri seed: 07:00-15:00, 15:00-23:00, 23:00-07:00, 05:00-13:00
  4. Eski tip_adi'lerin saat alanları doldurulup pasifleştirilir
  5. personel_vardiya_programi.vardiya: GÜNDÜZ→07:00-15:00 dönüşümü
  6. personel_vardiya_programi.izin_gunleri: TEXT → INTEGER (bit-mask)
  7. personel_vardiya_programi.plan_tipi: yeni kolon (HAFTALIK/GUNLUK)
  8. ayarlar_kullanicilar.vardiya + .izin_gunu için aynı dönüşüm (X1-a)

Yaklaşım: NON-DESTRUCTIVE — eski veri _v7_yedek tablosunda korunur.
Idempotent: Birden fazla çalıştırma güvenlidir (try/except).
"""
from sqlalchemy import text


GUN_BITMASK = {
    'pazartesi': 1, 'pzt': 1,
    'sali':      2, 'salı': 2, 'sal': 2,
    'carsamba':  4, 'çarşamba': 4, 'çar': 4, 'car': 4,
    'persembe':  8, 'perşembe': 8, 'per': 8,
    'cuma':     16,
    'cumartesi': 32, 'cmt': 32,
    'pazar':    64, 'paz': 64,
}

VARDIYA_DONUSUM = {
    'GÜNDÜZ VARDİYASI': '07:00-15:00',
    'GUNDUZ VARDIYASI': '07:00-15:00',
    'ARA VARDİYA':      '15:00-23:00',
    'ARA VARDIYA':      '15:00-23:00',
    'GECE VARDİYASI':   '23:00-07:00',
    'GECE VARDIYASI':   '23:00-07:00',
}


def _text_izin_to_bitmask(text_val):
    """'Pazartesi, Salı' → 3"""
    if not text_val:
        return 0
    bm = 0
    parts = str(text_val).lower().replace(',', ' ').split()
    for p in parts:
        p = p.strip().rstrip('.,;:')
        if p in GUN_BITMASK:
            bm |= GUN_BITMASK[p]
    return bm


def _calistir(conn, sql, label, params=None):
    try:
        if params:
            conn.execute(text(sql), params)
        else:
            conn.execute(text(sql))
        print(f"[OK]   {label}")
        return True
    except Exception as e:
        msg = str(e)[:100].replace('\n', ' ')
        print(f"[SKIP] {label} | {msg}")
        return False


def _adim_1_yedek_tablo(conn, is_pg):
    """B2: DB içinde yedek tablo oluştur."""
    print("\n--- ADIM 1: Yedek Tablo (B2) ---")
    if is_pg:
        sql = """
            CREATE TABLE IF NOT EXISTS personel_vardiya_programi_v7_yedek AS
            SELECT * FROM personel_vardiya_programi
        """
    else:
        sql = """
            CREATE TABLE IF NOT EXISTS personel_vardiya_programi_v7_yedek AS
            SELECT * FROM personel_vardiya_programi
        """
    _calistir(conn, sql, "Yedek tablo (personel_vardiya_programi_v7_yedek)")


def _adim_2_off_sil(conn):
    """A2: OFF kayıtlarını sil."""
    print("\n--- ADIM 2: OFF Kayıtları Sil (A2) ---")
    try:
        n = conn.execute(text("SELECT COUNT(*) FROM personel_vardiya_programi WHERE vardiya='OFF'")).scalar()
        print(f"[INFO] OFF kayıt sayısı: {n}")
        if n and n > 0:
            conn.execute(text("DELETE FROM personel_vardiya_programi WHERE vardiya='OFF'"))
            print(f"[OK]   {n} OFF kaydı silindi")
        else:
            print("[OK]   Silinecek OFF kaydı yok")
    except Exception as e:
        print(f"[ERR]  {str(e)[:120]}")


def _seed_tek_tip(conn, tip_adi, bas, bit, sira):
    """Tek bir vardiya tipini upsert eder."""
    mevcut = conn.execute(
        text("SELECT id FROM vardiya_tipleri WHERE tip_adi=:t"), {"t": tip_adi}
    ).fetchone()
    if mevcut:
        conn.execute(text(
            "UPDATE vardiya_tipleri SET baslangic_saati=:b, bitis_saati=:e, "
            "sira_no=:s, aktif=1 WHERE tip_adi=:t"
        ), {"t": tip_adi, "b": bas, "e": bit, "s": sira})
        print(f"[OK]   Guncellendi: {tip_adi}")
    else:
        conn.execute(text(
            "INSERT INTO vardiya_tipleri (tip_adi, baslangic_saati, bitis_saati, "
            "sira_no, aktif) VALUES (:t, :b, :e, :s, 1)"
        ), {"t": tip_adi, "b": bas, "e": bit, "s": sira})
        print(f"[OK]   Eklendi: {tip_adi}")


def _eski_tipleri_pasiflestir(conn):
    """Eski text formatlı tipleri aktif=0 yapar."""
    eski = ['GÜNDÜZ VARDİYASI', 'GUNDUZ VARDIYASI', 'ARA VARDİYA',
            'ARA VARDIYA', 'GECE VARDİYASI', 'GECE VARDIYASI', 'OFF']
    for e in eski:
        try:
            conn.execute(text("UPDATE vardiya_tipleri SET aktif=0 WHERE tip_adi=:t"),
                         {"t": e})
        except Exception:
            pass
    print("[OK]   Eski tipler pasiflestirildi")


def _adim_3_vardiya_tipleri_seed(conn):
    """Yeni 4 saat formatli vardiya tipini ekle, eskileri pasiflestir."""
    print("\n--- ADIM 3: vardiya_tipleri Seed ---")
    yeni_tipler = [
        ('07:00-15:00', '07:00', '15:00', 1),
        ('15:00-23:00', '15:00', '23:00', 2),
        ('23:00-07:00', '23:00', '07:00', 3),
        ('05:00-13:00', '05:00', '13:00', 4),
    ]
    for tip_adi, bas, bit, sira in yeni_tipler:
        try:
            _seed_tek_tip(conn, tip_adi, bas, bit, sira)
        except Exception as e:
            print(f"[SKIP] {tip_adi} | {str(e)[:80]}")
    _eski_tipleri_pasiflestir(conn)


def _adim_4_vardiya_donusum(conn, tablo, kolon):
    """Belirtilen tablodaki vardiya kolonunu yeni saat formatina cevir."""
    print(f"\n--- ADIM 4: {tablo}.{kolon} Vardiya Donusumu ---")
    for eski, yeni in VARDIYA_DONUSUM.items():
        try:
            res = conn.execute(
                text(f"UPDATE {tablo} SET {kolon}=:y WHERE {kolon}=:e"),
                {"y": yeni, "e": eski}
            )
            n = getattr(res, 'rowcount', 0) or 0
            if n > 0:
                eski_safe = eski.encode('ascii', 'replace').decode('ascii')
                print(f"[OK]   {eski_safe!r} -> {yeni!r}  ({n} kayit)")
        except Exception as e:
            eski_safe = eski.encode('ascii', 'replace').decode('ascii')
            print(f"[SKIP] {eski_safe} | {str(e)[:80]}")


def _bm_kolon_doldur(conn, tablo, eski_kolon):
    """Mevcut TEXT izin'leri Python parse edip _bm kolonuna yazar."""
    rows = conn.execute(text(
        f"SELECT id, {eski_kolon} FROM {tablo} "
        f"WHERE {eski_kolon} IS NOT NULL AND {eski_kolon} <> ''"
    )).fetchall()
    n = 0
    for row_id, txt in rows:
        bm = _text_izin_to_bitmask(txt)
        if bm > 0:
            conn.execute(
                text(f"UPDATE {tablo} SET {eski_kolon}_bm = :bm WHERE id = :i"),
                {"bm": bm, "i": row_id}
            )
            n += 1
    print(f"[OK]   {n} satir bit-mask'a donusturuldu")


def _bm_rename_swap(conn, tablo, eski_kolon, yeni_kolon):
    """eski_kolon -> eski_text, _bm -> yeni_kolon (SQLite + PG uyumlu)."""
    _calistir(conn,
              f"ALTER TABLE {tablo} RENAME COLUMN {eski_kolon} TO {eski_kolon}_eski_text",
              f"{eski_kolon} -> {eski_kolon}_eski_text")
    _calistir(conn,
              f"ALTER TABLE {tablo} RENAME COLUMN {eski_kolon}_bm TO {yeni_kolon}",
              f"{eski_kolon}_bm -> {yeni_kolon}")


def _adim_5_izin_gunleri_bitmask(conn, tablo, eski_kolon='izin_gunleri',
                                  yeni_kolon='izin_gunleri'):
    """TEXT izin_gunleri -> INTEGER bit-mask donusumu."""
    print(f"\n--- ADIM 5: {tablo}.{eski_kolon} TEXT -> INTEGER Bit-Mask ---")
    try:
        cols = conn.execute(text(f"SELECT * FROM {tablo} LIMIT 0")).keys()
        if eski_kolon not in cols:
            print(f"[SKIP] {tablo}.{eski_kolon} kolonu yok, atlaniyor")
            return
    except Exception as e:
        print(f"[SKIP] {tablo} tablo okunamadi: {str(e)[:80]}")
        return
    sql_add = f"ALTER TABLE {tablo} ADD COLUMN {eski_kolon}_bm INTEGER DEFAULT 0"
    if not _calistir(conn, sql_add, f"{eski_kolon}_bm gecici kolon eklendi"):
        return
    try:
        _bm_kolon_doldur(conn, tablo, eski_kolon)
    except Exception as e:
        print(f"[ERR]  Bit-mask hesabi: {str(e)[:120]}")
    _bm_rename_swap(conn, tablo, eski_kolon, yeni_kolon)


def _adim_6_plan_tipi_kolon(conn):
    """personel_vardiya_programi.plan_tipi kolonu ekle (S8-c)."""
    print("\n--- ADIM 6: plan_tipi Kolonu ---")
    _calistir(conn,
              "ALTER TABLE personel_vardiya_programi ADD COLUMN plan_tipi TEXT DEFAULT 'HAFTALIK'",
              "plan_tipi kolonu eklendi (DEFAULT HAFTALIK)")


def _adim_7_dogrulama(conn):
    """Migration sonrası özet rapor."""
    print("\n--- ADIM 7: Doğrulama Raporu ---")
    try:
        n_yedek = conn.execute(text("SELECT COUNT(*) FROM personel_vardiya_programi_v7_yedek")).scalar()
        n_canli = conn.execute(text("SELECT COUNT(*) FROM personel_vardiya_programi")).scalar()
        print(f"[INFO] Yedek tablo  : {n_yedek} kayıt")
        print(f"[INFO] Canlı tablo  : {n_canli} kayıt")

        n_yeni = conn.execute(text(
            "SELECT COUNT(*) FROM vardiya_tipleri WHERE aktif=1"
        )).scalar()
        print(f"[INFO] Aktif vardiya tipi: {n_yeni}")

        rows = conn.execute(text(
            "SELECT tip_adi, baslangic_saati, bitis_saati FROM vardiya_tipleri "
            "WHERE aktif=1 ORDER BY sira_no"
        )).fetchall()
        for r in rows:
            print(f"       - {r[0]:15s} ({r[1]}-{r[2]})")
    except Exception as e:
        print(f"[ERR]  Doğrulama: {str(e)[:120]}")


def migrate(engine):
    is_pg = engine.dialect.name == 'postgresql'
    print(f"\n{'='*60}")
    print(f"  v8.0.0 VARDİYA SAAT FORMATI MIGRATION")
    print(f"  DB Dialect: {engine.dialect.name}")
    print(f"{'='*60}")

    with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        _adim_1_yedek_tablo(conn, is_pg)
        _adim_2_off_sil(conn)
        _adim_3_vardiya_tipleri_seed(conn)
        _adim_4_vardiya_donusum(conn, 'personel_vardiya_programi', 'vardiya')
        _adim_4_vardiya_donusum(conn, 'ayarlar_kullanicilar', 'vardiya')
        _adim_5_izin_gunleri_bitmask(conn, 'personel_vardiya_programi')
        _adim_5_izin_gunleri_bitmask(conn, 'ayarlar_kullanicilar',
                                      eski_kolon='izin_gunu', yeni_kolon='izin_gunu')
        _adim_6_plan_tipi_kolon(conn)
        _adim_7_dogrulama(conn)

    print(f"\n{'='*60}")
    print(f"  [DONE] v8.0.0 migration tamamlandı")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.connection import get_engine
    migrate(get_engine())
