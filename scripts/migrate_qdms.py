import os
import shutil

# 1. Create ui/qdms_ui.py from pages/qdms_ana_sayfa.py
source = "pages/qdms_ana_sayfa.py"
target = "ui/qdms_ui.py"

if os.path.exists(source):
    print(f"Moving {source} to {target}...")
    shutil.copy2(source, target)
    print("Copy complete.")
else:
    print(f"Error: Source {source} not found!")

# Note: Deletion of pages/qdms_ana_sayfa.py and app.py update handled via replace_file_content
