import os

def collect_py_files(base_dir):
    """
    Recursively collect all .py files in the project directory.
    Returns a list of (relative_path, absolute_path).
    """
    py_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(root, file), base_dir)
                full_path = os.path.join(root, file)
                py_files.append((rel_path, full_path))
    return py_files

def merge_files_to_string(py_files):
    """
    Merge all .py files into one string, marking the name and path of each file before its content.
    """
    merged = ""
    for rel_path, full_path in py_files:
        merged += f"\n--- FILE: {rel_path} ---\n"
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            merged += f.read()
        merged += f"\n--- END FILE: {rel_path} ---\n"
    return merged

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    py_files = collect_py_files(base_dir)
    merged_content = merge_files_to_string(py_files)
    with open(os.path.join(base_dir, "codebase.txt"), "w", encoding="utf-8") as f:
        f.write(merged_content)
    print(f"Collected {len(py_files)} .py files. Merged content saved to codebase.txt.")

if __name__ == "__main__":
    main()