param([string]$Python = 'python', [switch]$CpuOnly)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Deployment/build_application.ps1') -Python $Python -CpuOnly:$CpuOnly
