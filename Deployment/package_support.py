"""Shared packaging inventory; importing this never starts SeeOtter."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIRS = ('Calibration', 'Camera', 'Config', 'Controller', 'DataGenerators',
            'Inclinometer', 'Processing', 'SurveyEntities', 'Utilities', 'View')
TOOLS = {
    'app': ('SeeOtter survey manager', 'start_see_otter_no_survey.py'),
    'preprocess': ('Preprocess images and correct GPS', 'SeeOtter_prepro_GUI_non_Waldo_with_GPS_fix.py'),
    'gps': ('Extract image GPS metadata', 'Image_GPS_extract.py'),
    'copy-waldo': ('Copy Waldo images into camera folders', 'Copy_Waldo_Images_Into_1_0_folders.py'),
    'move-waldo': ('Move Waldo images into camera folders', 'Move_Waldo_Images_Into_1_0_folders.py'),
    'postprocess': ('Count otters and split odd/even images', 'SeeOtter_post_pro_count_and_split_odd_even.py'),
    'gis': ('Export camera polygons and points', 'SeeOtter_Project_Processed_Data.py'),
}
REQUIRED = ('exifread', 'exif', 'GPSPhoto.gpsphoto', 'PIL.Image', 'piexif',
            'numpy', 'pandas', 'scipy', 'geopandas', 'fiona', 'pyproj', 'pyogrio',
            'shapely', 'folium', 'geopy', 'pykml', 'simplekml', 'jsonpickle',
            'semantic_version', 'kivy', 'kivymd', 'tkinter', 'torch',
            'torchvision', 'sahi.model', 'sahi.predict', 'yolov5', 'tqdm')

def tools(root=ROOT):
    result = dict(TOOLS)
    for path in sorted((root / 'HelperScripts').rglob('*.py')):
        relative = path.relative_to(root).as_posix()
        result[relative] = ('Advanced: ' + relative, relative)
    return result

def sources(root=ROOT):
    paths = list(root.glob('*.py'))
    for directory in (*APP_DIRS, 'HelperScripts'):
        paths.extend((root / directory).rglob('*.py'))
    return sorted(paths)

def external_imports(root=ROOT):
    local = set(APP_DIRS) | {'HelperScripts'} | {p.stem for p in root.glob('*.py')}
    result = set(REQUIRED)
    for path in sources(root):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            result.update(name for name in names if name.split('.')[0] not in local)
    return sorted(result)
