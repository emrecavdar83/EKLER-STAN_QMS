
import unittest
import pandas as pd
from sqlalchemy import create_engine, text
import sys
import os

# Add scripts folder to path to import SyncManager
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
try:
    from sync_manager import SyncManager
except ImportError:
    # If running from root
    from scripts.sync_manager import SyncManager

class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.manager = SyncManager() # connects to actual DBs based on implementation
        # Checks if we can connect
        self.assertTrue(self.manager.local_engine)
        self.assertTrue(self.manager.live_engine)

    def tearDown(self):
        """Clean up connections after test."""
        if hasattr(self, 'manager'):
            self.manager.dispose()

    def test_01_dry_run_no_errors(self):
        """Run a full dry run and ensure no exceptions are raised."""
        print("\n[TEST] Executing Dry Run...")
        try:
            results = self.manager.run_full_sync(dry_run=True)
            print(f"[RESULT] Dry Run Stats: {results}")
        except Exception as e:
            self.fail(f"Dry run failed with error: {e}")

    def test_02_department_consistency(self):
        """Verify department counts and names match between Local and Live."""
        print("\n[TEST] Verifying Departments...")
        local_df = self.manager.get_local_data("ayarlar_bolumler")
        live_df = self.manager.get_live_data("ayarlar_bolumler")
        
        # Check counts
        self.assertEqual(len(local_df), len(live_df), f"Department count mismatch! Local: {len(local_df)}, Live: {len(live_df)}")
        
        # Check specific critical department
        local_pandispanya = local_df[local_df['bolum_adi'].str.contains('PANDİSPANYA')]
        live_pandispanya = live_df[live_df['bolum_adi'].str.contains('PANDİSPANYA')]
        
        self.assertFalse(local_pandispanya.empty, "PANDİSPANYA missing in Local")
        self.assertFalse(live_pandispanya.empty, "PANDİSPANYA missing in Live")
        
        # Check IDs match
        self.assertEqual(local_pandispanya.iloc[0]['id'], live_pandispanya.iloc[0]['id'], "PANDİSPANYA ID mismatch")

    def test_03_location_hierarchy(self):
        """Verify OKUL PROJESİ hierarchy in Locations."""
        print("\n[TEST] Verifying Location Hierarchy...")
        live_df = self.manager.get_live_data("lokasyonlar")
        
        # Check for paths containing OKUL PROJESİ > BOMBA
        bomba_locs = live_df[live_df['sorumlu_departman'].str.contains('OKUL PROJESİ > BOMBA', na=False)]
        
        if bomba_locs.empty:
            # Maybe it's just 'BOMBA' and user already verified manual update, 
            # but if sync ran, it should match local.
            # If local hasn't been updated with the new hierarchy yet (since we did it on Live directly!), this sync might REVERT it if we are not careful!
            # CRITICAL CHECK: Did we update Local DB with "OKUL PROJESİ" hierarchy changes?
            # We applied hierarchy changes to LIVE DB directly in previous steps (Step 152).
            # We did NOT apply them to Local DB yet?
            pass
        
        self.assertFalse(bomba_locs.empty, "BOMBA locations under OKUL PROJESİ not found in Live DB. Sync might have reverted them or they weren't there?")

    def test_04_data_integrity(self):
        """Check for orphaned records."""
        print("\n[TEST] Checking Integrity...")
        with self.manager.live_engine.connect() as conn:
            # Check for orphans in lokasyonlar
            orphans = conn.execute(text("SELECT count(*) FROM lokasyonlar WHERE parent_id IS NOT NULL AND parent_id NOT IN (SELECT id FROM lokasyonlar)")).scalar()
            self.assertEqual(orphans, 0, f"Found {orphans} orphaned locations in Live DB")

if __name__ == '__main__':
    unittest.main()
