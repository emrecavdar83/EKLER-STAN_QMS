import os

search_terms = ["lokan", "canlı", "lokasyon", "durum", "gözden geçir", "yetki", "izin"]
search_dir = "."

print(f"Searching for: {search_terms}")

for root, dirs, files in os.walk(search_dir):
    if ".git" in root or "__pycache__" in root or ".streamlit" in root:
        continue
        
    for file in files:
        if file.endswith(".py") or file.endswith(".md"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.readlines()
                    for i, line in enumerate(content):
                        for term in search_terms:
                            if term.lower() in line.lower():
                                print(f"MATCH: {file}:{i+1} -> {line.strip()}")
            except Exception as e:
                print(f"Error reading {file}: {e}")
