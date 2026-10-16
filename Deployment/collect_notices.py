"""Keep installed dependency license/notice files with the distribution."""
import importlib.metadata as metadata
from pathlib import Path
import re
import shutil
import sys

def collect(bundle):
    target = bundle / 'ThirdPartyNotices'
    count = 0
    for distribution in metadata.distributions():
        label = re.sub(r'[^A-Za-z0-9_.-]', '_',
                       distribution.metadata.get('Name', 'unknown') + '-' + distribution.version)
        for entry in distribution.files or []:
            if not entry.name.lower().startswith(('license', 'copying', 'notice')):
                continue
            source = Path(distribution.locate_file(entry))
            if not source.is_file() or source.stat().st_size > 2_000_000:
                continue
            directory = target / label
            directory.mkdir(parents=True, exist_ok=True)
            filename = re.sub(r'[^A-Za-z0-9_.-]', '_', str(entry))
            shutil.copy2(source, directory / filename)
            count += 1
    (target / 'README.txt').write_text(
        'License and notice files preserved from the build environment. '
        'This inventory may also include optional packages not used by SeeOtter.\n', encoding='utf-8')
    print('Preserved dependency notice files:', count)

if __name__ == '__main__':
    collect(Path(sys.argv[1]).resolve())
