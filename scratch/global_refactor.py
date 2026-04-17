import os
import re

def global_refactor_table_name():
    target_table = "ayarlar_kullanicilar"
    old_table = "personel"
    
    # Excluded directories
    exclude_dirs = {'.git', '.claude', '__pycache__', 'venv', 'logs', 'node_modules', '.antigravity'}
    
    # Files using the table name (from git grep) - adding some logic to be thorough
    extensions = {'.py', '.sql', '.yaml', '.yml', '.md'}
    
    count = 0
    errors = 0
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Pattern intended for SQL and Python sqlalchemy/text usage
                    # Matches "personel" in quotes or as word
                    # We have to be careful not to replace "personel_vardiya" accidentally if it exists
                    # but usually it's better to preserve prefixes if they match.
                    
                    # Regex logic: Match 'personel' as a whole word 
                    # but NOT if it's already prefixed by ayarlar_
                    pattern = r'(?<!ayarlar_)\bpersonel\b'
                    
                    if re.search(pattern, content):
                        print(f"Refactoring: {filepath}")
                        new_content = re.sub(pattern, target_table, content)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        count += 1
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                    errors += 1
                    
    print(f"\n--- REFACTOR COMPLETE ---")
    print(f"Files updated: {count}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    global_refactor_table_name()
