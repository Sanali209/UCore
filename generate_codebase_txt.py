import os
import argparse
from tqdm import tqdm
from loguru import logger

class CodebaseCollector:
    def __init__(self, base_dir, output_file, split=False, chunk_size=50000):
        self.base_dir = os.path.abspath(base_dir)
        self.output_file = output_file
        self.split = split
        self.chunk_size = chunk_size
        self.py_files = []
        self.read_files = []

    def collect_py_files(self):
        logger.info(f"Collecting .py files from {self.base_dir}")
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.base_dir)
                    full_path = os.path.join(root, file)
                    if rel_path.startswith('venv') or rel_path.startswith('.venv'):
                        continue
                    self.py_files.append((rel_path, full_path))
        logger.info(f"Found {len(self.py_files)} Python files.")

    def merge_files(self):
        merged = ""
        self.read_files = []
        for rel_path, full_path in tqdm(self.py_files, desc="Merging files"):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                merged += f"\n--- FILE: {rel_path} ---\n"
                merged += content
                merged += f"\n--- END FILE: {rel_path} ---\n"
                self.read_files.append(rel_path)
            except Exception as e:
                logger.error(f"Failed to read {full_path}: {e}")
        return merged

    def write_output(self, merged_content):
        if not self.split:
            logger.info(f"Writing merged content to {self.output_file}")
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(self._file_list_header())
                f.write(merged_content)
            logger.success(f"Output written to {self.output_file}")
        else:
            logger.info("Splitting output into smaller files")
            base, ext = os.path.splitext(self.output_file)
            parts = [merged_content[i:i+self.chunk_size] for i in range(0, len(merged_content), self.chunk_size)]
            for idx, part in enumerate(parts):
                part_file = f"{base}_part{idx+1}{ext}"
                with open(part_file, "w", encoding="utf-8") as f:
                    f.write(self._file_list_header())
                    f.write(part)
                logger.success(f"Output part written to {part_file}")

    def _file_list_header(self):
        header = "# List of Python files included:\n"
        for rel_path in self.read_files:
            header += f"- {rel_path}\n"
        header += "\n"
        return header

    def run(self):
        self.collect_py_files()
        merged_content = self.merge_files()
        self.write_output(merged_content)

def parse_args():
    parser = argparse.ArgumentParser(description="Collect and merge Python files from a codebase.")
    parser.add_argument("--base-dir", type=str, default="", help="Base directory to scan for .py files.")
    parser.add_argument("--output", type=str, default="codebase.txt", help="Output file name.")
    parser.add_argument("--split", action="store_true", help="Enable splitting output into smaller files.")
    parser.add_argument("--chunk-size", type=int, default=150000, help="Chunk size for splitting (in characters).")
    return parser.parse_args()

def main():
    args = parse_args()
    logger.add("resource_manager.log", rotation="1 MB")

    # If run without parameters (all defaults), prompt interactively
    if (
        args.base_dir == ""
        and args.output == "codebase.txt"
        and not args.split == True
        and args.chunk_size == 50000
    ):
        print("No parameters provided. Please enter options:")
        base_dir = input("Base directory to scan for .py files [ucore_framework/core]: ").strip() or "ucore_framework/core"
        output = input("Output file name [codebase.txt]: ").strip() or "codebase.txt"
        split_input = input("Split output into smaller files? (y/N): ").strip().lower()
        split = split_input == "y"
        chunk_size = input("Chunk size for splitting (in characters) [50000]: ").strip()
        chunk_size = int(chunk_size) if chunk_size else 50000
    else:
        base_dir = ''
        output = args.output
        split = True
        chunk_size = 150000

    collector = CodebaseCollector(
        base_dir=base_dir,
        output_file=output,
        split=split,
        chunk_size=chunk_size
    )
    
    collector.run()

if __name__ == "__main__":
    main()
