"""Fail before freezing if this exact Python cannot run the application."""
import importlib
import os
import platform
import sys
from package_support import REQUIRED, ROOT, tools

def check(require_cuda=False):
    os.environ['KIVY_NO_ARGS'] = '1'
    (ROOT / 'Logs').mkdir(exist_ok=True)
    os.environ.setdefault('KIVY_HOME', str(ROOT / 'Logs' / 'kivy'))
    print('Build Python:', sys.executable, sys.version)
    failures = []
    if sys.platform != 'win32' or platform.architecture()[0] != '64bit':
        failures.append('A 64-bit Windows Python is required.')
    for name in REQUIRED + ('PyInstaller', 'kivy_deps.sdl2', 'kivy_deps.glew'):
        try:
            importlib.import_module(name)
        except Exception as error:
            failures.append(f'{name}: {type(error).__name__}: {error}')
    try:
        from sahi.model import Yolov5DetectionModel
        from sahi.utils.yolov5 import download_yolov5s6_model
    except Exception as error:
        failures.append(f'Legacy SAHI API required by Processing/predict.py: {error}')
    if require_cuda:
        try:
            import torch
            print('Torch:', torch.__version__, 'CUDA runtime:', torch.version.cuda,
                  'GPU available:', torch.cuda.is_available())
            if torch.version.cuda is None:
                failures.append('CUDA-enabled Torch is required for the GPU/CPU distribution. '
                                'Install Deployment/requirements-cuda.txt in the build environment.')
        except Exception as error:
            failures.append(f'CUDA build check: {error}')
    for relative in [entry[1] for entry in tools().values()] + [
            'ModelWeights/best.pt', 'SeeOtterUserGuide.docx', 'LICENSE',
            'Deployment/yolov5/hubconf.py']:
        if not (ROOT / relative).is_file():
            failures.append('Missing resource: ' + relative)
    if failures:
        print('\nBUILD BLOCKED:\n' + '\n'.join(failures))
        print('\nInstall dependencies with the Python printed above, then retry. '
              'The old requirements.txt contains local file URLs and is not portable.')
        return 1
    print('Dependency and resource checks passed.')
    return 0

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-cuda', action='store_true')
    raise SystemExit(check(require_cuda=parser.parse_args().require_cuda))
