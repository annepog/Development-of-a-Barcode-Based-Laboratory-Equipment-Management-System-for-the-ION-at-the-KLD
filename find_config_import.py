import os
import re

def find_config_imports():
    """Find all files that import 'config' module"""
    print("=" * 70)
    print("SEARCHING FOR 'config' IMPORTS")
    print("=" * 70)
    
    python_files = []
    
    # Get all Python files in current directory
    for file in os.listdir('.'):
        if file.endswith('.py'):
            python_files.append(file)
    
    found_imports = []
    
    for file in python_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for various import patterns
                    if re.search(r'\bimport\s+config\b', line) or \
                       re.search(r'\bfrom\s+config\b', line):
                        found_imports.append({
                            'file': file,
                            'line': i,
                            'content': line.strip()
                        })
        except Exception as e:
            print(f"  Error reading {file}: {e}")
    
    if found_imports:
        print(f"\nFOUND {len(found_imports)} 'config' IMPORT(S):\n")
        for item in found_imports:
            try:
                print(f"File: {item['file']}")
                print(f"   Line {item['line']}: {item['content']}")
                print("-" * 70)
            except UnicodeEncodeError:
                print(f"File: {item['file']}")
                print(f"   Line {item['line']}: [Contains special characters]")
                print("-" * 70)
    else:
        print("\n NO 'config' imports found in Python files")
        print("\nThis means the import might be in a subdirectory or")
        print("the error is coming from a different source.")
    
    print("\n" + "=" * 70)
    print("SEARCH COMPLETE")
    print("=" * 70)
    
    # Also check which files are imported by home.py
    if 'home.py' in python_files:
        print("\n FILES IMPORTED BY home.py:")
        print("-" * 70)
        try:
            with open('home.py', 'r', encoding='utf-8') as f:
                content = f.read()
                imports = re.findall(r'(?:from|import)\s+([\w\.]+)', content)
                for imp in set(imports):
                    print(f"   - {imp}")
        except Exception as e:
            print(f"  Error reading home.py: {e}")

if __name__ == "__main__":
    find_config_imports()