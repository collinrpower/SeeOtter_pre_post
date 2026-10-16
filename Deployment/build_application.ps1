param([string]$Python = 'python', [string]$ArchivePython = '')
$ErrorActionPreference = 'Stop'
if (-not $ArchivePython) { $ArchivePython = $Python }
Push-Location $PSScriptRoot
try {
    & $Python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'The Python environment has conflicting dependencies.' }
    & $Python "$PSScriptRoot/preflight.py"
    if ($LASTEXITCODE -ne 0) { throw 'Preflight failed; no release was built.' }
    & $Python -m PyInstaller --noconfirm --clean --distpath "$PSScriptRoot/dist" --workpath "$PSScriptRoot/build" "$PSScriptRoot/SeeOtter.spec"
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
    $Bundle = Join-Path $PSScriptRoot 'dist/SeeOtter'
    & $Python "$PSScriptRoot/stage_native_libraries.py" $Bundle
    if ($LASTEXITCODE -ne 0) { throw 'Native wheel library collection failed.' }
    & $Python "$PSScriptRoot/stage_stdlib_modules.py" $Bundle
    if ($LASTEXITCODE -ne 0) { throw 'Dynamic standard-library collection failed.' }
    & $Python "$PSScriptRoot/collect_notices.py" $Bundle
    if ($LASTEXITCODE -ne 0) { throw 'Dependency notice collection failed.' }
    & "$Bundle/SeeOtter.exe" --self-test
    if ($LASTEXITCODE -ne 0) { throw 'Frozen self-test failed. Do not distribute this build.' }
    & "$Bundle/SeeOtter.exe" --gui-smoke-test
    if ($LASTEXITCODE -ne 0) { throw 'Application GUI startup failed.' }
    foreach ($Tool in @('preprocess', 'gps', 'copy-waldo', 'move-waldo', 'postprocess', 'gis')) {
        & "$Bundle/SeeOtter.exe" --tool $Tool --tool-smoke-test
        if ($LASTEXITCODE -ne 0) { throw "Tool startup failed: $Tool" }
    }
    & $ArchivePython "$PSScriptRoot/release_bundle.py" $Bundle
    if ($LASTEXITCODE -ne 0) { throw 'Release verification failed.' }
    Write-Output "Release archives and SHA256 files are in $PSScriptRoot/dist"
} finally {
    Pop-Location
}
