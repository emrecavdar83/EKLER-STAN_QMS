from scripts.sync_manager import SyncManager
import logging

logging.basicConfig(level=logging.INFO)

def sync_personnel():
    print("Starting sync...")
    with SyncManager() as manager:
        # Sync only personnel table
        res = manager.sync_table("personel")
        print("Sync Result:", res)
        
if __name__ == "__main__":
    sync_personnel()
