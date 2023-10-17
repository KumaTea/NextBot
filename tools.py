import os


def sort_imports():
    python_files = [i for i in os.listdir() if i.endswith('.py')]
    for file in python_files:
        sort_import(file)


def sort_import(file):
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    original_lines = lines.copy()
    imports = []
    for line in lines:
        if line.startswith('import ') or line.startswith('from '):
            imports.append(line)
    imports.sort(key=lambda x: len(x.split('  #')[0]))
    for i in range(len(imports)):
        imports[i] = imports[i].rstrip() + '\n'
    for i in range(len(lines)):
        if lines[i].startswith('import ') or lines[i].startswith('from '):
            lines[i] = imports.pop(0)
    if lines != original_lines:
        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f'{file} sorted')


if __name__ == '__main__':
    sort_imports()
