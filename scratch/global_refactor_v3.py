import os
import re

def global_refactor():
    target_dirs = [
        "logic",
        "ui",
        "modules",
        "database",
        "app.py",
        "constants.py"
    ]
    
    # Exact table search patterns
    patterns = [
        (re.compile(r"(['\"])personel(['\"])"), r"\1ayarlar_kullanicilar\2"),
        (re.compile(r"(\s)personel(\s)"), r"\1ayarlar_kullanicilar\2"),
        (re.compile(r"JOIN personel(\s)"), r"JOIN ayarlar_kullanicilar\1"),
        (re.compile(r"FROM personel(\s)"), r"FROM ayarlar_kullanicilar\1"),
        (re.compile(r"UPDATE personel(\s)"), r"UPDATE ayarlar_kullanicilar\1"),
        (re.compile(r"INSERT INTO personel"), r"INSERT INTO ayarlar_kullanicilar"),
    ]
    
    refactor_count = 0
    file_count = 0
    
    for root_dir in target_dirs:
        if os.path.isfile(root_dir):
            paths = [root_dir]
        else:
            paths = []
            for root, dirs, files in os.walk(root_dir):
                if any(x in root for x in ["__pycache__", ".git", "scratch", "tmp", "migrations"]):
                    continue
                for file in files:
                    if file.endswith(".py"):
                        paths.append(os.path.join(root, file))
        
        for path in paths:
            file_changed = False
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = content
            for pattern, replacement in patterns:
                new_content, count = pattern.subn(replacement, new_content)
                if count > 0:
                    file_changed = True
                    refactor_count += count
            
            if file_changed:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Refactored: {path}")
                file_count += 1
                
    print(f"\nFINISHED: {refactor_count} occurrences in {file_count} files.")

if __name__ == "__main__":
    global_refactor()
