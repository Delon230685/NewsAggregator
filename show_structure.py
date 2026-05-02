import os
from pathlib import Path

def show_structure(startpath=".", exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', '.idea', '.vscode', 'logs'}
    
    print("\n" + "="*60)
    print("📁 СТРУКТУРА ПРОЕКТА")
    print("="*60 + "\n")
    
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * level
        folder_name = os.path.basename(root)
        
        if level == 0:
            print(f"📦 {folder_name}/")
        else:
            print(f'{indent}├── 📁 {folder_name}/')
        
        subindent = '│   ' * (level + 1)
        for i, file in enumerate(sorted(files)):
            if file.endswith(('.pyc', '.db', '.sqlite', '.log')):
                continue
            
            icon = "🐍" if file.endswith('.py') else "📝" if file.endswith('.md') else "📄"
            
            if i == len(files) - 1:
                print(f'{subindent}└── {icon} {file}')
            else:
                print(f'{subindent}├── {icon} {file}')

if __name__ == "__main__":
    show_structure()
