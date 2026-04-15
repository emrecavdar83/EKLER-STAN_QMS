import ast
import os

def count_function_lines(filepath):
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
            lines = content.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = node.lineno
                    # Approximate end line
                    end = start
                    for child in ast.walk(node):
                        if hasattr(child, 'lineno'):
                            end = max(end, child.lineno)
                    func_size = end - start + 1
                    if func_size > 30:
                        results.append((filepath, node.name, func_size))
    except Exception:
        pass
    return results

all_results = []
for root, dirs, files in os.walk('.'):
    if '.antigravity' in root or 'venv' in root or '.git' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            all_results.extend(count_function_lines(os.path.join(root, file)))

all_results.sort(key=lambda x: x[2], reverse=True)
print(f"Toplam 30+ satır fonksiyon: {len(all_results)}")
for r in all_results[:15]:
    print(f"{r[0]} | {r[1]} | {r[2]} satır")
