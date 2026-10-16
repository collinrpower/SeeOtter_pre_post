import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_downloads


class ReleaseDownloadTests(unittest.TestCase):
    def test_parts_reconstruct_exact_archive_and_record_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'SeeOtter-test.zip'
            payload = bytes(range(256))
            archive.write_bytes(payload)
            with patch.object(release_downloads, 'GITHUB_ASSET_LIMIT', 100):
                downloads = release_downloads.prepare(archive, part_size=80)
            parts = downloads[:-1]
            self.assertEqual(b''.join(p.read_bytes() for p in parts), payload)
            self.assertTrue(all(p.stat().st_size < 100 for p in parts))
            for part in parts:
                checksum = part.with_name(part.name + '.sha256').read_text().split()[0]
                self.assertEqual(checksum, hashlib.sha256(part.read_bytes()).hexdigest())
            helper = downloads[-1].read_text()
            self.assertIn(hashlib.sha256(payload).hexdigest(), helper)
            self.assertIn('FileMode]::CreateNew', helper)
            self.assertIn('Application folder already exists', helper)

    def test_small_archive_does_not_need_parts(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'small.zip'
            archive.write_bytes(b'example')
            self.assertEqual(release_downloads.prepare(archive), [archive])

    def test_shell_characters_in_archive_name_are_rejected(self):
        with self.assertRaises(ValueError):
            release_downloads.prepare(Path('unsafe&name.zip'))


if __name__ == '__main__':
    unittest.main()
