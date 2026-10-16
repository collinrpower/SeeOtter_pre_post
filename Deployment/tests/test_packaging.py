import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_support as inventory
import distribution_launcher as launcher
import preflight
import release_bundle

class PackagingTests(unittest.TestCase):
    def test_every_helper_and_extra_tool_is_launchable(self):
        entries = inventory.tools()
        included = {value[1] for value in entries.values()}
        expected = {p.relative_to(inventory.ROOT).as_posix()
                    for p in (inventory.ROOT / 'HelperScripts').rglob('*.py')}
        self.assertTrue(expected <= included)
        self.assertEqual(len(inventory.TOOLS), 7)
        for _, relative in entries.values():
            self.assertTrue((inventory.ROOT / relative).is_file(), relative)

    def test_dependencies_of_all_extra_tools_are_collected(self):
        imports = inventory.external_imports()
        for name in ('exifread', 'piexif', 'geopandas', 'pandas', 'PIL.Image', 'tkinter'):
            self.assertIn(name, imports)
        self.assertNotIn('select_survey', imports)

    def test_frozen_child_uses_bundled_executable(self):
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', 'C:/SeeOtter/SeeOtter.exe'):
            self.assertEqual(launcher.command('preprocess'), ['C:/SeeOtter/SeeOtter.exe', '--tool', 'preprocess'])

    def test_missing_dependency_blocks_build(self):
        def missing(name):
            if name == 'exifread':
                raise ModuleNotFoundError('No module named exifread')
            return object()
        with patch.object(preflight.importlib, 'import_module', side_effect=missing):
            self.assertEqual(preflight.check(), 1)

    def test_incomplete_bundle_cannot_be_released(self):
        with self.assertRaisesRegex(FileNotFoundError, 'SeeOtter.exe'):
            release_bundle.verify(inventory.ROOT / 'nonexistent-test-bundle')

if __name__ == '__main__':
    unittest.main()
