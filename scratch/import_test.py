import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Testing logic.app_bootstrap import...")
    import logic.app_bootstrap
    print("SUCCESS: logic.app_bootstrap imported.")

    print("Testing logic.app_auth_flow import...")
    import logic.app_auth_flow
    print("SUCCESS: logic.app_auth_flow imported.")

    print("Testing database.connection import...")
    import database.connection
    print("SUCCESS: database.connection imported.")

    print("System Check PASSED: No top-level circular imports detected.")
except Exception as e:
    print(f"FAILED: Import error detected: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
