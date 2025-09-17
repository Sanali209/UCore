import sys

def test_print_sys_path():
    with open("sys_path_debug.txt", "w", encoding="utf-8") as f:
        f.write("PYTHON sys.path:\\n")
        for p in sys.path:
            f.write(p + "\\n")
