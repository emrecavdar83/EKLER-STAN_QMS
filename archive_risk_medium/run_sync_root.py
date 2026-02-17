import sys
import os

# Ensure root is in path
sys.path.append(os.getcwd())

from scripts.sync_manager import SyncManager
import logging

logging.basicConfig(level=logging.INFO)

def sync_personnel():
    print("Starting sync...")
    with SyncManager() as manager:
        res = manager.sync_table("personel")
        print("Sync Result:", res)
        
if __name__ == "__main__":
    sync_personnel()
