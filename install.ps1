#Requires -Version 5.1
<#
.SYNOPSIS
  eMuleBB Suite installer — minimal bootstrap.

.DESCRIPTION
  This one-liner is a **minimal bootstrap** (decision 2026-06-16). It does NOT
  install the suite itself; it only:
    1. creates the install directory,
    2. downloads a self-contained `uv` binary into it (no system Python touched,
       no admin, no PATH change),
    3. fetches TrackMuleBB,
    4. hands off to TrackMuleBB's Python **setup CLI**, which does the real
       install + auto-wiring of the selectable bundle (emulebb-rust / eMuleBB MFC,
       qBittorrentBB, TrackMuleBB, Arr, SABnzbd, Bountarr; Docker also Plex).

  Design: emulebb-tooling `docs/active/SUITE-INSTALLER.md`. The setup CLI is the
  TrackMuleBB backlog item TMBB-FEAT-010.

  SCAFFOLD: the TrackMuleBB setup CLI is not built yet; the published install path
  stays on the tested RC bootstrap until this is validated.

.EXAMPLE
  irm https://emulebb.github.io/install.ps1 | iex

.EXAMPLE
  $s = irm https://emulebb.github.io/install.ps1
  & ([scriptblock]::Create($s)) -InstallRoot 'D:\eMuleBB-Suite' -Core rust
#>
[CmdletBinding()]
param(
    [string] $InstallRoot = "$env:LOCALAPPDATA\eMuleBB-Suite",
    [ValidateSet('mfc', 'rust')] [string] $Core = 'mfc',
    [string] $UvVersion = 'latest',
    [Parameter(ValueFromRemainingArguments = $true)] [string[]] $SetupArgs
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$UA = @{ 'User-Agent' = 'emulebb-suite-bootstrap' }

function Write-Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }

Write-Step "eMuleBB Suite bootstrap (root=$InstallRoot, core=$Core)"
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

# 1) self-contained uv (downloaded straight into the install dir; never the
#    system-modifying uv installer). uv then manages a standalone Python with
#    `--python-preference only-managed`, ignoring any system Python.
$uvDir = Join-Path $InstallRoot 'uv'
New-Item -ItemType Directory -Force -Path $uvDir | Out-Null
$tag = if ($UvVersion -eq 'latest') {
    (Invoke-RestMethod 'https://api.github.com/repos/astral-sh/uv/releases/latest' -Headers $UA).tag_name
}
else { $UvVersion }
$asset = "uv-x86_64-pc-windows-msvc.zip"
$uvUrl = "https://github.com/astral-sh/uv/releases/download/$tag/$asset"
$uvZip = Join-Path $env:TEMP $asset
Write-Step "Fetching uv $tag (self-contained)"
Invoke-WebRequest -Uri $uvUrl -OutFile $uvZip -Headers $UA -UseBasicParsing
Expand-Archive -Path $uvZip -DestinationPath $uvDir -Force
Remove-Item $uvZip -Force
$uv = Join-Path $uvDir 'uv.exe'

# Scope uv's data into the install dir so nothing leaks into the user profile.
$env:UV_PYTHON_INSTALL_DIR = Join-Path $InstallRoot 'python'
$env:UV_CACHE_DIR = Join-Path $InstallRoot '.uv-cache'

# 2) hand off to TrackMuleBB's setup CLI (TMBB-FEAT-010). Once TrackMuleBB
#    publishes a setup entry point this becomes, e.g.:
#       & $uv tool run --python-preference only-managed trackmulebb-setup --core $Core @SetupArgs
Write-Step "uv ready at $uv — handing off to the TrackMuleBB setup CLI"
Write-Host "  (scaffold) the TrackMuleBB Python setup CLI is not published yet; see"
Write-Host "  emulebb-tooling docs/active/SUITE-INSTALLER.md and TMBB-FEAT-010."
