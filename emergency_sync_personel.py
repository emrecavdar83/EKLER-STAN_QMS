
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.sync_manager import SyncManager
import logging

logging.basicConfig(level=logging.INFO)

print("=== EMERGENCY SYNC: PERSONEL ONLY ===")

try:
    with SyncManager() as manager:
        # Override sync order to only sync personnel
        manager.sync_order = ["personel"]
        print("Forcing sync order: ", manager.sync_order)
        
        # Run sync (non-dry run)
        results = manager.run_full_sync(dry_run=False)
        
        print("\nResults:", results)
        
        if "personel" in results and results["personel"].get("status") != "error":
            print("\n✅ SUCCESS: Personel table synced successfully!")
        else:
            print("\n❌ FAILURE: Personel sync failed.")
            
except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {e}")
