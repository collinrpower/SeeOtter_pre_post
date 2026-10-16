"""Import real raster files with no EXIF, rather than only testing startup."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from kivy.event import EventDispatcher
from kivy.properties import StringProperty

from Config.see_otter_config import SeeOtterConfig
from SurveyEntities.image_metadata import ImageMetadata
from SurveyEntities.survey import Survey
from SurveyEntities.survey_image import SurveyImage
from SurveyEntities.waldo_survey import WaldoSurvey
from View.Widgets.image_info_card import ImageInfoCard


class TextValue(EventDispatcher):
    value = StringProperty("")


class ImageMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = SeeOtterConfig()
        self.config_patch = patch.object(SeeOtterConfig, '_instance', self.config)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def image(self, name='000880.jpg'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (48, 32), (40, 80, 120)).save(path)
        return path

    def test_all_supported_extensions_without_exif_have_real_dimensions(self):
        for extension in ('.jpg', '.JPEG', '.png', '.tif', '.TIFF', '.bmp'):
            with self.subTest(extension=extension):
                image = SurveyImage(str(self.image('frame' + extension)))
                self.assertEqual(image.resolution, (48.0, 32.0))
                self.assertIsNone(image.datetime)
                self.assertIsNone(image.datetime_obj)
                self.assertIsNone(image.metadata.camera_make)

    def test_strict_metadata_setting_still_rejects_missing_fields(self):
        self.config.FAIL_ON_MISSING_EXIF_FIELD = True
        with self.assertRaisesRegex(KeyError, 'Image Make'):
            ImageMetadata(str(self.image()))

    def test_strict_gps_setting_still_rejects_missing_gps(self):
        self.config.REQUIRE_GPS = True
        with self.assertRaises(KeyError):
            SurveyImage(str(self.image()))

    def test_valid_exif_values_are_preserved(self):
        tags = {key: SimpleNamespace(printable=value) for key, value in {
            'Image Make': 'Camera maker', 'Image Model': 'Camera model',
            'Image Orientation': 'Horizontal (normal)',
            'EXIF DateTimeOriginal': '2026:01:02 03:04:05',
            'EXIF ExifImageWidth': '48', 'EXIF ExifImageLength': '32',
            'EXIF ISOSpeedRatings': '200', 'EXIF FNumber': '4',
            'EXIF ExposureTime': '1/500', 'EXIF FocalLength': '35'}.items()}
        self.config.FAIL_ON_MISSING_EXIF_FIELD = True
        with patch('SurveyEntities.image_metadata.ImageProcessing.load_exif_tags', return_value=tags):
            metadata = ImageMetadata(str(self.image()))
        self.assertEqual(metadata.datetime, '2026:01:02 03:04:05')
        self.assertEqual(metadata.iso, '200')
        self.assertEqual(metadata.fstop, '4')
        self.assertEqual(metadata.resolution_x, 48)

    def test_new_survey_with_undated_frames_saves_and_reloads(self):
        paths = [self.image('images/' + name) for name in ('000890.jpg', '000880.jpg')]
        survey = WaldoSurvey.new('Frames', survey_path=str(self.root / 'survey'),
                                 images_dir=str(paths[0].parent))
        self.assertEqual([image.file_name for image in survey.images], ['000880.jpg', '000890.jpg'])
        self.assertEqual(len(survey.camera_system.cameras), 1)
        loaded = Survey.load(str(self.root / 'survey'))
        self.assertEqual([image.file_path for image in loaded.images], [str(paths[1]), str(paths[0])])
        self.assertTrue(all(image.datetime is None for image in loaded.images))

    def test_mixed_capture_times_sort_without_comparing_none_to_string(self):
        images = [SurveyImage(str(self.image(name))) for name in ('000890.jpg', '000880.jpg')]
        images[0].metadata.datetime = '2026:01:02 03:04:05'
        survey = SimpleNamespace(images=images, camera_system=None)
        Survey.order_images_by_type_and_datetime(survey)
        self.assertEqual([image.file_name for image in survey.images], ['000890.jpg', '000880.jpg'])

    def test_image_info_accepts_unknown_values_in_kivy_string_properties(self):
        image = SurveyImage(str(self.image()))
        card = SimpleNamespace(**{name: TextValue() for name in (
            'image_name', 'created_dttm', 'lattitude', 'longitude', 'altitude',
            'iso', 'fstop', 'exposure')})
        ImageInfoCard.set_fields(card, image)
        for field in ('created_dttm', 'iso', 'fstop', 'exposure'):
            self.assertEqual(getattr(card, field).value, 'Unknown')

    def test_undated_images_are_not_matched_to_inclinometer_records(self):
        image = SurveyImage(str(self.image()))
        survey = SimpleNamespace(images=[image], load_inclinometer_data=lambda force: [
            SimpleNamespace(datetime='2026:01:02 03:04:05')])
        Survey.load_and_apply_inclinometer_data(survey)
        self.assertIsNone(image.inclinometer_data)


if __name__ == '__main__':
    unittest.main()
