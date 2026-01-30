import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from scripts.sync_manager import SyncManager

print("--- VERIFICATION START ---")
try:
    manager = SyncManager()
    print("[OK] SyncManager initialized successfully.")
    
    # Dry Run Test
    print("--- Running Dry Run ---")
    results = manager.run_full_sync(dry_run=True)
    
    print("\n[RESULTS]")
    for table, stats in results.items():
        print(f"{table}: {stats}")
        
    print("\n--- VERIFICATION SUCCESS ---")
    
except Exception as e:
    print(f"\n[ERROR] Verification failed: {e}")
    # Print traceback for detail
    import traceback
    traceback.print_exc()

