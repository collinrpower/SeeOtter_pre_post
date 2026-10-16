"""One frozen runtime for SeeOtter and every processing tool."""
import argparse
import importlib
import multiprocessing
import os
from pathlib import Path
import runpy
import subprocess
import sys
import traceback
from package_support import REQUIRED, tools

def distribution_root():
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]

def configure(root):
    os.chdir(root)
    sys.path.insert(0, str(root))
    for directory in ('Logs', 'Surveys'):
        (root / directory).mkdir(exist_ok=True)
    os.environ.setdefault('KIVY_HOME', str(root / 'Logs' / 'kivy'))
    os.environ['KIVY_NO_ARGS'] = '1'

def self_test(root, require_gpu=False):
    for name in REQUIRED:
        importlib.import_module(name)
        print('OK:', name)
    for _, relative in tools(root).values():
        if not (root / relative).is_file():
            raise FileNotFoundError(relative)
    for relative in ('ModelWeights/best.pt', 'SeeOtterUserGuide.docx'):
        if not (root / relative).is_file():
            raise FileNotFoundError(relative)
    if not any((root / relative).is_file() for relative in ('yolov5/hubconf.py', 'Deployment/yolov5/hubconf.py')):
        raise FileNotFoundError('yolov5/hubconf.py')
    import tempfile
    import geopandas as gpd
    from shapely.geometry import Point
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / 'test.shp'
        gpd.GeoDataFrame({'id': [1]}, geometry=[Point(0, 0)], crs='EPSG:4326').to_file(path)
        assert len(gpd.read_file(path)) == 1
    # Exercise import of plain raster files, not just dependency imports.
    from PIL import Image
    from Config.see_otter_config import SeeOtterConfig
    from SurveyEntities.survey import Survey
    from SurveyEntities.waldo_survey import WaldoSurvey
    config = SeeOtterConfig.instance()
    previous_policy = config.REQUIRE_GPS, config.FAIL_ON_MISSING_EXIF_FIELD
    try:
        config.REQUIRE_GPS = config.FAIL_ON_MISSING_EXIF_FIELD = False
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            images = folder / 'images'
            images.mkdir()
            for extension in ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'):
                Image.new('RGB', (48, 32)).save(images / ('frame' + extension))
            survey = WaldoSurvey.new('metadata-smoke-test', survey_path=str(folder / 'project'),
                                     images_dir=str(images))
            assert survey.num_images == 6, survey.num_images
            assert all(image.resolution == (48, 32) for image in survey.images)
            assert all(image.datetime is None for image in survey.images)
            assert Survey.load(str(folder / 'project')).num_images == 6
            print('PASS: EXIF-free JPG/JPEG/PNG/TIFF/BMP survey import, dimensions, save and reload')
    finally:
        config.REQUIRE_GPS, config.FAIL_ON_MISSING_EXIF_FIELD = previous_policy
    import Processing.predict
    import numpy as np
    import torch
    model = Processing.predict.detection_model
    expected_device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    assert str(model.device) == expected_device, (model.device, expected_device)
    assert next(model.model.parameters()).device.type == expected_device.split(':')[0]
    if require_gpu and expected_device == 'cpu':
        raise RuntimeError('GPU self-test requested but CUDA is unavailable.')
    from torchvision.ops import nms
    boxes = torch.tensor([[0., 0., 10., 10.], [1., 1., 9., 9.],
                          [20., 20., 30., 30.]], device=expected_device)
    scores = torch.tensor([0.9, 0.8, 0.7], device=expected_device)
    assert nms(boxes, scores, 0.5).tolist() == [0, 2]
    Processing.predict.detection_model.perform_inference(np.zeros((64, 64, 3), dtype=np.uint8))
    if expected_device.startswith('cuda'):
        torch.cuda.synchronize()
    from View.Windows.see_otter_window import SeeOtterWindow
    print('PASS: dependencies, resources, GIS round trip, model load, inference and app imports')

def command(key):
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--tool', key]
    return [sys.executable, str(Path(__file__).resolve()), '--tool', key]

def menu(root):
    import tkinter as tk
    from tkinter import messagebox
    window = tk.Tk()
    window.title('SeeOtter tools')
    tk.Label(window, text='SeeOtter — survey and processing tools', font=('', 14)).pack(padx=20, pady=16)
    inventory = tools(root)
    def launch(key):
        if key.startswith('HelperScripts/'):
            if not messagebox.askokcancel('Advanced helper script',
                    'These scripts use settings in select_survey.py and in the script itself. '
                    'Some overwrite survey data. Review those files and use a copy of your survey. '
                    'Continue with ' + key + '?'):
                return
        subprocess.Popen(command(key), cwd=root)
    for key, (label, _) in inventory.items():
        if not key.startswith('HelperScripts/'):
            tk.Button(window, text=label, width=48, command=lambda key=key: launch(key)).pack(padx=20, pady=4)
    advanced = tk.StringVar(value=next(key for key in inventory if key.startswith('HelperScripts/')))
    tk.Label(window, text='Advanced helpers (configure source files first)').pack(pady=(16, 4))
    tk.OptionMenu(window, advanced, *[key for key in inventory if key.startswith('HelperScripts/')]).pack(padx=20)
    tk.Button(window, text='Run selected helper', command=lambda: launch(advanced.get())).pack(pady=10)
    window.mainloop()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tool')
    parser.add_argument('--list-tools', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--require-gpu', action='store_true',
                        help='Require actual CUDA inference with --self-test')
    parser.add_argument('--gui-smoke-test', action='store_true')
    parser.add_argument('--tool-smoke-test', action='store_true')
    args = parser.parse_args()
    if args.require_gpu and not args.self_test:
        parser.error('--require-gpu requires --self-test')
    if args.self_test or args.gui_smoke_test or args.tool_smoke_test:
        os.environ['SEEOTTER_AUTOMATED_TEST'] = '1'
    root = distribution_root()
    configure(root)
    if args.list_tools:
        for key, (label, _) in tools(root).items():
            print(key + ': ' + label)
    elif args.self_test:
        self_test(root, require_gpu=args.require_gpu)
    elif args.gui_smoke_test:
        from kivy.clock import Clock
        from View.Windows.see_otter_window import SeeOtterWindow
        app = SeeOtterWindow()
        Clock.schedule_once(lambda dt: app.stop(), 5)
        app.run()
        print('PASS: application constructed and event loop ran')
    elif args.tool:
        inventory = tools(root)
        if args.tool not in inventory:
            parser.error('Unknown tool: ' + args.tool)
        script = root / inventory[args.tool][1]
        sys.argv = [str(script)]
        if args.tool_smoke_test:
            import tkinter as tk
            from tkinter import filedialog
            original_loop = tk.Misc.mainloop
            def smoke_loop(window, *loop_args, **loop_kwargs):
                window.after(1000, window.destroy)
                return original_loop(window, *loop_args, **loop_kwargs)
            tk.Misc.mainloop = smoke_loop
            filedialog.askdirectory = lambda *a, **kw: ''
        runpy.run_path(str(script), run_name='__main__')
        if args.tool_smoke_test:
            print('PASS: tool startup:', args.tool)
    else:
        menu(root)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except Exception:
        detail = traceback.format_exc()
        print(detail, file=sys.stderr)
        log = distribution_root() / 'Logs' / 'launcher-error.log'
        log.parent.mkdir(exist_ok=True)
        log.write_text(detail, encoding='utf-8')
        try:
            if os.environ.get('SEEOTTER_AUTOMATED_TEST') == '1':
                raise RuntimeError('Automated test failed; see traceback above')
            import tkinter.messagebox
            tkinter.messagebox.showerror('SeeOtter error', f'{detail}\nDetails saved to {log}')
        except Exception:
            pass
        raise SystemExit(1)
