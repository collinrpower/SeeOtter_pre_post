"""Split oversized release ZIPs for GitHub and provide native Windows extraction."""
import hashlib
from pathlib import Path
import re
import sys

GITHUB_ASSET_LIMIT = 2 * 1024 ** 3
PART_SIZE = 1536 * 1024 ** 2


def prepare(archive, part_size=PART_SIZE):
    archive = Path(archive)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+\.zip', archive.name):
        raise ValueError('Archive must have a simple ZIP filename')
    if not 0 < part_size < GITHUB_ASSET_LIMIT:
        raise ValueError('Each part must be smaller than GitHub\'s 2 GiB limit')
    if archive.stat().st_size < GITHUB_ASSET_LIMIT:
        return [archive]
    complete_hash = hashlib.sha256()
    parts = []
    with archive.open('rb') as source:
        remaining = archive.stat().st_size
        while remaining:
            part = archive.with_name(archive.name + f'.{len(parts) + 1:03}')
            digest = hashlib.sha256()
            count = min(part_size, remaining)
            with part.open('wb') as output:
                while count:
                    block = source.read(min(count, 1024 * 1024))
                    if not block:
                        raise EOFError('Archive changed during splitting')
                    output.write(block)
                    digest.update(block)
                    complete_hash.update(block)
                    count -= len(block)
                    remaining -= len(block)
            parts.append((part, digest.hexdigest()))
            part.with_name(part.name + '.sha256').write_text(
                digest.hexdigest() + '  ' + part.name + '\n', encoding='utf-8')
    expected = complete_hash.hexdigest()
    records = ','.join("@{Name='%s';Hash='%s'}" % (p.name, h) for p, h in parts)
    # Paths come from an environment variable, never interpolated into shell code.
    # CreateNew and the destination check preserve any existing application/data.
    script = """$ErrorActionPreference='Stop';
function FileHash($path){
  $sha=[Security.Cryptography.SHA256]::Create();
  $stream=[IO.File]::OpenRead($path);
  try{return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}finally{$stream.Dispose();$sha.Dispose()};
};
$root=$env:SEEOTTER_PACKAGE_DIR;
$archive=[IO.Path]::Combine($root,'@@ARCHIVE@@');
$target=[IO.Path]::Combine($root,'@@FOLDER@@');
if([IO.Directory]::Exists($target) -or [IO.File]::Exists($target)){throw 'Application folder already exists. Put these downloads in a fresh folder and retry.'};
if(![IO.File]::Exists($archive)){
  $parts=@(@@PARTS@@);
  foreach($part in $parts){
    $path=[IO.Path]::Combine($root,$part.Name);
    if(![IO.File]::Exists($path)){throw ('Missing download: '+$part.Name)};
    [Console]::WriteLine('Checking '+$part.Name);
    if((FileHash $path) -ne $part.Hash){throw ('Checksum mismatch: '+$part.Name)};
  };
  [Console]::WriteLine('Reconstructing SeeOtter ZIP...');
  $output=[IO.File]::Open($archive,[IO.FileMode]::CreateNew);
  try{foreach($part in $parts){
    $inputStream=[IO.File]::OpenRead([IO.Path]::Combine($root,$part.Name));
    try{$inputStream.CopyTo($output)}finally{$inputStream.Dispose()};
  }}finally{$output.Dispose()};
};
if((FileHash $archive) -ne '@@HASH@@'){throw 'ZIP checksum mismatch. Move the damaged ZIP aside and retry.'};
[Console]::WriteLine('Extracting SeeOtter. This can take several minutes...');
$null=[Reflection.Assembly]::LoadWithPartialName('System.IO.Compression.FileSystem');
[IO.Compression.ZipFile]::ExtractToDirectory($archive,$root);
[Console]::WriteLine('Ready. Open '+[IO.Path]::Combine($target,'SeeOtter.exe'));
"""
    script = script.replace('@@ARCHIVE@@', archive.name).replace(
        '@@FOLDER@@', archive.stem).replace('@@PARTS@@', records).replace('@@HASH@@', expected)
    helper = archive.with_name('Extract-SeeOtter.cmd')
    helper.write_bytes(('@echo off\r\nsetlocal\r\n'
        'set "SEEOTTER_PACKAGE_DIR=%~dp0"\r\n'
        'powershell.exe -NoProfile -Command "' + ' '.join(script.splitlines()) + '"\r\n'
        'if errorlevel 1 (\r\n  echo Extraction failed. See the message above.\r\n'
        '  pause\r\n  exit /b 1\r\n)\r\npause\r\n').encode('ascii'))
    print('GitHub download parts:', ', '.join(p.name for p, _ in parts), flush=True)
    return [p for p, _ in parts] + [helper]


if __name__ == '__main__':
    prepare(Path(sys.argv[1]))
