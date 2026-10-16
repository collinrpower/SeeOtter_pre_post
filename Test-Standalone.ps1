param([switch]$RequireGpu)
$ErrorActionPreference = 'Stop'
$StandaloneExe = Join-Path $PSScriptRoot 'Deployment\dist\SeeOtter\SeeOtter.exe'
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
$env:PYTHONHOME = ''
$env:PYTHONPATH = ''
$env:CONDA_PREFIX = ''
$env:VIRTUAL_ENV = ''
$env:QT_PLUGIN_PATH = ''
$env:TCL_LIBRARY = ''
$env:TK_LIBRARY = ''
$SelfTestArguments = @('--self-test')
if ($RequireGpu) { $SelfTestArguments += '--require-gpu' }
& $StandaloneExe @SelfTestArguments
if ($LASTEXITCODE -ne 0) { throw 'Standalone dependency/inference/GIS test failed.' }
$PreviousCudaDevices = $env:CUDA_VISIBLE_DEVICES
try {
    $env:CUDA_VISIBLE_DEVICES = '-1'
    & $StandaloneExe --self-test
    if ($LASTEXITCODE -ne 0) { throw 'Standalone CPU fallback test failed.' }
} finally {
    $env:CUDA_VISIBLE_DEVICES = $PreviousCudaDevices
}
& $StandaloneExe --gui-smoke-test
if ($LASTEXITCODE -ne 0) { throw 'Standalone app startup failed.' }
foreach ($StandaloneTool in @('preprocess','gps','copy-waldo','move-waldo','postprocess','gis')) {
    & $StandaloneExe --tool $StandaloneTool --tool-smoke-test
    if ($LASTEXITCODE -ne 0) { throw "Standalone tool failed: $StandaloneTool" }
}
Write-Output 'PASS: all standalone tests with system-only PATH and no Python/Conda environment variables.'
