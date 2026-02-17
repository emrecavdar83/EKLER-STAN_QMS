import sys
filename = 'app.py'
search_term = "Bazı personellerin departman bilgisi eşleştirilemedi"

try:
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    found = False
    for i, line in enumerate(lines):
        if search_term in line:
            print(f"Found on line {i+1}")
            # print(line.strip().encode('utf-8', 'replace')) # Avoid printing problematic chars to console directly
            found = True
            
    if not found:
        print("Search term not found in app.py")

except Exception as e:
    print(f"Error: {e}")
