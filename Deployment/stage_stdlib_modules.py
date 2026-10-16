"""Keep source for standard-library modules used by runpy-based extra tools."""
import importlib.util
from pathlib import Path
import shutil
import sys

def stage(bundle):
    # The GIS tool imports ttk via `from tkinter import ttk`. Keep an explicit
    # filesystem fallback as well as the spec's hidden import.
    specification = importlib.util.find_spec('tkinter.ttk')
    if specification is None or not specification.origin:
        raise ImportError('tkinter.ttk is unavailable in the build Python')
    target = bundle / 'tkinter'
    target.mkdir(exist_ok=True)
    shutil.copy2(specification.origin, target / 'ttk.py')
    print('Staged tkinter.ttk source for the GIS tool')

if __name__ == '__main__':
    stage(Path(sys.argv[1]).resolve())
