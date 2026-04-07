#!/usr/bin/env python3
"""
EKLERİSTAN QMS — Hata Sync Daemon (v5.9.0)
===========================================
Supabase'deki hata_loglari tablosunu belirli aralıklarla yerel
logs/hata_loglari/ dizinine indirir ve analiz özetini ekrana basar.

Kullanım:
  python scripts/hata_sync_daemon.py                   # 5 dakikada bir
  python scripts/hata_sync_daemon.py --interval 60     # 1 dakikada bir
  python scripts/hata_sync_daemon.py --once            # Tek seferlik çalıştır

Windows arka plan:
  pythonw scripts/hata_sync_daemon.py  (konsol penceresi açmadan)
"""
import sys
import time
import argparse
import signal
from datetime import datetime
from pathlib import Path

# Proje kökünü Python yoluna ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

_devam = True


def _cikis_sinyali(sig, frame):
    global _devam
    print("\n[DAEMON] Durdurma sinyali alındı. Kapatılıyor...")
    _devam = False


def _zaman_damgasi() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sync_calistir(engine) -> tuple[int, str]:
    from logic.hata_sync import bulut_hatalari_indir
    return bulut_hatalari_indir(engine)


def _ozet_yazdir(df):
    """İstatistik özetini terminale basar."""
    if df is None or df.empty:
        return
    from logic.hata_sync import hata_istatistikleri
    stats = hata_istatistikleri(df)
    print(f"   Toplam : {stats.get('toplam', 0)} | "
          f"Çözüldü: {stats.get('cozuldu', 0)} | "
          f"Kritik : {stats.get('kritik', 0)}")
    if stats.get("modul_dagilimi"):
        top3 = list(stats["modul_dagilimi"].items())[:3]
        ozet = ", ".join([f"{m}({s})" for m, s in top3])
        print(f"   Top modüller: {ozet}")


def main():
    global _devam
    parser = argparse.ArgumentParser(
        description="EKLERİSTAN QMS — Hata Sync Daemon"
    )
    parser.add_argument(
        "--interval", type=int, default=300,
        help="Sync aralığı saniye cinsinden (varsayılan: 300)"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Tek seferlik çalıştırıp çık"
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _cikis_sinyali)
    signal.signal(signal.SIGTERM, _cikis_sinyali)

    print("=" * 55)
    print("  EKLERİSTAN QMS — Hata Sync Daemon")
    print(f"  Sync aralığı : {args.interval} saniye")
    print(f"  Hedef dizin  : logs/hata_loglari/")
    print("=" * 55)

    # Engine'i lazy yükle (Streamlit context olmadan)
    try:
        import streamlit as st
    except Exception:
        pass

    try:
        from database.connection import get_engine
        engine = get_engine()
    except Exception as e:
        print(f"[HATA] Engine başlatılamadı: {e}")
        sys.exit(1)

    dongu = 0
    while _devam:
        dongu += 1
        print(f"\n[{_zaman_damgasi()}] Sync #{dongu} başlıyor...")
        try:
            sayi, mesaj = _sync_calistir(engine)
            print(f"[SYNC] {mesaj}")
            if sayi > 0:
                from logic.hata_sync import yerel_hatalari_oku
                df = yerel_hatalari_oku()
                _ozet_yazdir(df)
        except Exception as e:
            print(f"[HATA] {e}")

        if args.once:
            print("[DAEMON] --once modu: tamamlandı.")
            break

        print(f"[DAEMON] Sonraki sync: {args.interval} saniye sonra (Ctrl+C ile durdur)")
        for _ in range(args.interval):
            if not _devam:
                break
            time.sleep(1)

    print(f"[{_zaman_damgasi()}] Daemon kapatıldı.")


if __name__ == "__main__":
    main()
