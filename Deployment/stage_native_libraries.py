"""Preserve sibling .libs folders and load-order files used by Windows wheels.

Conda Python 3.9 wheels can preload these DLLs via their load-order files rather
than normal PE imports. PyInstaller's normal dependency scan can miss them.
"""
from pathlib import Path
import shutil
import sys

def stage(bundle):
    copied = []
    seen = set()
    for entry in sys.path:
        location = Path(entry)
        if not location.is_dir():
            continue
        for libraries in location.glob('*.libs'):
            package = libraries.name[:-5]
            if not libraries.is_dir() or not (bundle / package).is_dir():
                continue
            key = libraries.name.lower()
            if key in seen:
                continue
            seen.add(key)
            shutil.copytree(libraries, bundle / libraries.name, dirs_exist_ok=True)
            copied.append(libraries.name)
    print('Staged native wheel libraries:', ', '.join(copied))
    return copied

if __name__ == '__main__':
    stage(Path(sys.argv[1]).resolve())
