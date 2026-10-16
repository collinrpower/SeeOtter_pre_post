"""Verify payload, record hashes, and archive binary + matching source."""
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile
from package_support import ROOT, sources, tools
from release_downloads import prepare

def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def verify(bundle):
    required = ['SeeOtter.exe', 'LICENSE', 'SeeOtterUserGuide.docx',
                'ModelWeights/best.pt', 'yolov5/hubconf.py', 'WINDOWS_DISTRIBUTION.md']
    required += [p.relative_to(ROOT).as_posix() for p in sources()]
    missing = [p for p in required if not (bundle / p).is_file()]
    if missing:
        raise FileNotFoundError('Incomplete distribution: ' + ', '.join(missing))

def release(bundle, reuse_verified_manifest=False):
    print('Verifying payload...', flush=True)
    verify(bundle)
    version = re.search(r"Version\('([^']+)'\)", (ROOT / 'version.py').read_text()).group(1)
    name = f'SeeOtter-{version}-windows-x64'
    manifest_path = bundle / 'SHA256SUMS.json'
    previous, previous_time = {}, -1
    if reuse_verified_manifest and manifest_path.is_file():
        previous = json.loads(manifest_path.read_text(encoding='utf-8'))
        previous_time = manifest_path.stat().st_mtime_ns
    manifest = {}
    for p in sorted(bundle.rglob('*')):
        if not p.is_file() or p.name in {'SHA256SUMS.json', 'otter_checker_config.json', 'see_otter_config.json'} or set(p.relative_to(bundle).parts) & {'Logs', 'Surveys', '__pycache__'}:
            continue
        relative = p.relative_to(bundle).as_posix()
        manifest[relative] = previous[relative] if relative in previous and p.stat().st_mtime_ns <= previous_time else sha256(p)
        if len(manifest) % 1000 == 0:
            print('Hashed files:', len(manifest), flush=True)
    (bundle / 'SHA256SUMS.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    archive = bundle.parent / (name + '.zip')
    print('Creating Windows archive...', flush=True)
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as output:
        for path in sorted(bundle.rglob('*')):
            if path.is_file() and path.name not in {'otter_checker_config.json', 'see_otter_config.json'} and not set(path.relative_to(bundle).parts) & {'Logs', 'Surveys', '__pycache__'}:
                output.write(path, Path(name) / path.relative_to(bundle))
    # Matching source includes build scripts, vendored code, model files and license.
    source = bundle.parent / (name + '-source.zip')
    print('Creating source archive...', flush=True)
    with zipfile.ZipFile(source, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as output:
        for path in sorted(ROOT.rglob('*')):
            relative = path.relative_to(ROOT)
            if path.is_file() and path.name != 'otter_checker_config.json' and not set(relative.parts) & {'.git', 'dist', 'build', 'build-refresh', 'refresh-output', 'BuildEnvironment', 'Backups', '__pycache__', 'Logs', 'Surveys'}:
                output.write(path, Path(name + '-source') / relative)
    for path in (archive, source):
        path.with_suffix(path.suffix + '.sha256').write_text(sha256(path) + '  ' + path.name + '\n', encoding='utf-8')
    prepare(archive)
    print(archive)
    print(source)

if __name__ == '__main__':
    release(Path(sys.argv[1]).resolve())
