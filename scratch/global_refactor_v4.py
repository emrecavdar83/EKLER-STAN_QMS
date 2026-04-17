import os
import re

# v4.0: Aggressive Refactor (SQL and String contexts)
# Focuses on catching "personel" in various SQL and code patterns that were missed.

target_dirs = [
    "logic",
    "ui",
    "modules",
    "database",
    "scripts",  # Added scripts
    "app.py",
    "constants.py",
    "data_fetcher.py"
]

patterns = [
    # 1. SQL patterns: FROM personel, JOIN personel, UPDATE personel, DELETE FROM personel
    (re.compile(r"FROM\s+personel([\s\"';]|$)", re.IGNORECASE), r"FROM ayarlar_kullanicilar\1"),
    (re.compile(r"JOIN\s+personel([\s\"';]|$)", re.IGNORECASE), r"JOIN ayarlar_kullanicilar\1"),
    (re.compile(r"UPDATE\s+personel([\s\"';]|$)", re.IGNORECASE), r"UPDATE ayarlar_kullanicilar\1"),
    (re.compile(r"INTO\s+personel([\s\"';]|$)", re.IGNORECASE), r"INTO ayarlar_kullanicilar\1"),
    
    # 2. String/Variable patterns used as table names
    (re.compile(r'(["\'])personel(["\'])'), r"\1ayarlar_kullanicilar\2"),
]

def refactor_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return # Skip non-text files

    original_content = content
    for pattern, replacement in patterns:
        content = pattern.sub(replacement, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Refactored: {filepath}")
        return True
    return False

def main():
    count = 0
    for target in target_dirs:
        if os.path.isfile(target):
            if refactor_file(target):
                count += 1
        elif os.path.isdir(target):
            for root, dirs, files in os.walk(target):
                for file in files:
                    if file.endswith(".py") or file.endswith(".sql"):
                        if refactor_file(os.path.join(root, file)):
                            count += 1
    print(f"Total files updated: {count}")

if __name__ == "__main__":
    main()
