# Build with PyInstaller 6. See WINDOWS_DISTRIBUTION.md.
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_all
from kivy_deps import sdl2, glew

deployment = Path(SPECPATH)
sys.path.insert(0, str(deployment))
from package_support import ROOT, sources, external_imports

datas = [(str(p), str(p.relative_to(ROOT).parent)) for p in sources()]
for directory in ('View/Images', 'View/Icons', 'ModelWeights'):
    for path in (ROOT / directory).glob('*'):
        if path.is_file():
            datas.append((str(path), directory))
for filename in ('LICENSE', 'README.md', 'SeeOtterUserGuide.docx', 'see_otter_config.json'):
    datas.append((str(ROOT / filename), '.'))
datas.append((str(deployment / 'WINDOWS_DISTRIBUTION.md'), '.'))
binaries = []
hidden = external_imports() + ['tkinter.ttk']
for package in ('kivymd', 'sahi', 'yolov5', 'geopandas', 'fiona', 'pyproj'):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hidden += package_hidden

# The vendored directory is partial (no utils/). Keep installed YOLOv5 resources
# and overlay the repository's deployment files, with one entry per destination.
for path in (deployment / 'yolov5').rglob('*'):
    if path.is_file():
        datas.append((str(path), str(Path('yolov5') / path.relative_to(deployment / 'yolov5').parent)))
datas = list({str(Path(destination) / Path(source).name): (source, destination)
              for source, destination in datas}.values())

a = Analysis([str(deployment / 'distribution_launcher.py')],
             pathex=[str(ROOT), str(deployment)], binaries=binaries, datas=datas,
             hiddenimports=sorted(set(hidden)), hookspath=[],
             runtime_hooks=[str(deployment / 'runtime_hook.py')],
             excludes=['tensorflow', 'tensorflowjs', 'tensorboard', 'keras',
                       'mmdet', 'mmcv', 'onnx', 'onnxruntime', 'tensorrt',
                       'openvino', 'paddle', 'coremltools',
                       'PyQt5', 'PyQt6', 'PySide2', 'PySide6'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='SeeOtter',
          console=True, debug=False, strip=False, upx=False, contents_directory='.')
coll = COLLECT(exe, a.binaries, a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False, upx=False, name='SeeOtter')
