import os
import shutil
import json
import argparse
from datetime import datetime, timedelta

# --- YAPILANDIRMA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_FILE = os.path.join(BASE_DIR, "cleanup_manifest.json")
RETENTION_DAYS = 7

ARCHIVE_DIRS = {
    "low": os.path.join(BASE_DIR, "archive_risk_low"),
    "medium": os.path.join(BASE_DIR, "archive_risk_medium"),
    "high": os.path.join(BASE_DIR, "archive_risk_high"),
}

# Kritik dosyalar (ASLA SİLİNMEYECEK)
PROTECTED_FILES = [
    "app.py", "constants.py", "baslat.bat", "requirements.txt", 
    "DURUM_RAPORU.md", "cleanup_automation.py", "cleanup_manifest.json",
    "ekleristan_local.db"
]

PROTECTED_DIRS = [
    ".agent", ".streamlit", ".git", "archive_risk_low", 
    "archive_risk_medium", "archive_risk_high", "scripts", "sql", "data_sync"
]

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(manifest):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)

def categorize_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    
    # Kategori 1 (Düşük Risk)
    if ext in [".txt", ".log", ".json", ".txt"] or filename == "__pycache__":
        return "low"
    
    # Kategori 2 (Orta Risk)
    if any(filename.startswith(prefix) for prefix in ["check_", "debug_", "inspect_", "verify_", "analyze_"]):
        return "medium"
    
    # Kategori 3 (Yüksek Risk)
    if ext in [".db", ".sql", ".csv"]:
        return "high"
    
    return "medium"  # Varsayılan orta risk

def archive_files():
    manifest = load_manifest()
    now_full = datetime.now()
    now_iso = now_full.isoformat()
    
    # Tüm projeyi tara (Recursive)
    for root, dirs, files in os.walk(BASE_DIR):
        # Sistem klasörlerini ve arşiv klasörlerini tamamen atla
        dirs[:] = [d for d in dirs if d not in [".git", ".agent", ".streamlit", "archive_risk_low", "archive_risk_medium", "archive_risk_high"]]
        
        for item in files:
            if item in PROTECTED_FILES:
                continue
                
            full_path = os.path.join(root, item)
            
            # Son değişiklik zamanını kontrol et (Sadece 7 günden eskileri arşivle)
            mtime = os.path.getmtime(full_path)
            last_modified = datetime.fromtimestamp(mtime)
            
            if last_modified > (now_full - timedelta(days=RETENTION_DAYS)):
                # Son 7 günde değişmiş, koru
                continue

            category = categorize_file(item)
            target_dir = ARCHIVE_DIRS[category]
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Çakışmayı önlemek için hedef yolu benzersiz yap
            rel_path = os.path.relpath(full_path, BASE_DIR).replace(os.sep, "_")
            target_path = os.path.join(target_dir, rel_path)
            
            print(f"Archiving (Old File): {rel_path} -> {category}")
            try:
                shutil.move(full_path, target_path)
                manifest[rel_path] = {
                    "original_path": full_path,
                    "category": category,
                    "archived_at": now_iso
                }
            except Exception as e:
                print(f"Error ({item}): {e}")

    save_manifest(manifest)
    print("\nRecursive archiving completed. Manifest updated.")

def purge_expired():
    manifest = load_manifest()
    new_manifest = {}
    now = datetime.now()
    deleted_count = 0
    
    for item, info in manifest.items():
        archived_at = datetime.fromisoformat(info["archived_at"])
        if now - archived_at > timedelta(days=RETENTION_DAYS):
            # Süresi dolmuş
            category = info["category"]
            target_path = os.path.join(ARCHIVE_DIRS[category], item)
            
            if os.path.exists(target_path):
                print(f"PURGING (7 Days Expired): {item}")
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)
                deleted_count += 1
            else:
                print(f"Warning: File already missing: {item}")
        else:
            new_manifest[item] = info
            
    save_manifest(new_manifest)
    print(f"\nPurge completed. {deleted_count} files permanently deleted.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kademeli Temizlik Sistemi")
    parser.add_argument("--archive", action="store_true", help="Kullanılmayan dosyaları arşivle")
    parser.add_argument("--purge", action="store_true", help="Süresi dolmuş (7 gün) arşivleri sil")
    
    args = parser.parse_args()
    
    if args.archive:
        archive_files()
    elif args.purge:
        purge_expired()
    else:
        print("Lütfen bir parametre seçin: --archive veya --purge")
