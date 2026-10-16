param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Deployment/build_application.ps1') -Python $Python
