"""
Güvenli Lokal-Canlı Veritabanı Eşitleme
========================================
Bu script, lokal değişiklikleri canlı ortama güvenli bir şekilde aktarır.

Özellikler:
-----------
1. Önce DRY RUN (test) modu
2. Kritik tabloları sırayla sync eder
3. İki aşamalı personel sync'i (Foreign Key güvenliği)
4. Detaylı log kaydı

Kullanım:
---------
python safe_sync.py           # Dry run (test)
python safe_sync.py --execute # Gerçek sync
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.sync_manager import SyncManager
import logging
from datetime import datetime

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'sync_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_sync_summary(results):
    """Sync sonuçlarını özetler."""
    print("\n" + "="*60)
    print("SYNC SONUÇLARI")
    print("="*60)
    
    total_inserted = 0
    total_updated = 0
    total_skipped = 0
    
    for table, stats in results.items():
        if isinstance(stats, dict):
            if stats.get("status") == "error":
                print(f"❌ {table}: HATA - {stats.get('message', 'Bilinmeyen')}")
            elif stats.get("status") == "skipped":
                print(f"⏭️ {table}: Atlandı - {stats.get('reason', 'Boş tablo')}")
            else:
                inserted = stats.get("inserted", 0)
                updated = stats.get("updated", 0)
                skipped = stats.get("skipped", 0)
                
                total_inserted += inserted
                total_updated += updated
                total_skipped += skipped
                
                print(f"✅ {table}: +{inserted} | ↻{updated} | ={skipped}")
        else:
            print(f"⚠️ {table}: Beklenmeyen sonuç formatı")
    
    print("\n" + "="*60)
    print(f"TOPLAM: {total_inserted} yeni, {total_updated} güncelleme, {total_skipped} değişiklik yok")
    print("="*60 + "\n")

def main():
    # Check command line args
    is_dry_run = True
    if "--execute" in sys.argv or "-e" in sys.argv:
        is_dry_run = False
        print("⚠️ GERÇEK SYNC MODU AKTIF!")
        print("Canlı veritabanına yazılacak. 5 saniye içinde iptal edebilirsiniz...")
        import time
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        print("Başlatılıyor...\n")
    else:
        print("🧪 DRY RUN MODU (Test)")
        print("Hiçbir değişiklik kaydedilmeyecek.\n")
    
    try:
        print("SyncManager başlatılıyor...")
        with SyncManager() as manager:
            print(f"Senkronize edilecek tablolar: {len(manager.sync_order)}")
            print(f"Sıralama: {', '.join(manager.sync_order)}\n")
            
            results = manager.run_full_sync(dry_run=is_dry_run)
            print_sync_summary(results)
            
            if is_dry_run:
                print("✅ DRY RUN tamamlandı. Gerçek sync için: python safe_sync.py --execute")
            else:
                print("✅ SYNC BAŞARIYLA TAMAMLANDI!")
                
    except Exception as e:
        logger.error(f"Sync başarısız: {e}")
        print(f"\n❌ HATA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
