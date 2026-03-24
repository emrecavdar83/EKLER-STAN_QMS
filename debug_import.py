import sys
import traceback

print("Starting import diagnostic...")

try:
    print("Attempting to import logic.data_fetcher...")
    import logic.data_fetcher
    print("SUCCESS: logic.data_fetcher imported.")
except ImportError:
    print("FAILED: ImportError in logic.data_fetcher")
    traceback.print_exc()
except Exception:
    print("FAILED: Other exception in logic.data_fetcher")
    traceback.print_exc()

try:
    print("\nAttempting to import app.py line-by-line equivalent...")
    import streamlit as st
    from logic.branding import set_branding
    import pandas as pd
    from sqlalchemy import create_engine, text
    print("Base imports OK.")
    
    from logic.data_fetcher import (
        run_query, get_user_roles, get_department_tree,
        get_department_options_hierarchical,
        get_all_sub_department_ids, get_personnel_hierarchy,
        cached_veri_getir, veri_getir,
        get_personnel_shift, is_personnel_off
    )
    print("SUCCESS: Full data_fetcher import OK.")
except ImportError:
    print("FAILED: ImportError during app.py steps")
    traceback.print_exc()
except Exception:
    print("FAILED: Exception during app.py steps")
    traceback.print_exc()
