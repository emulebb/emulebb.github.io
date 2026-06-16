#Requires -Version 5.1
<#
.SYNOPSIS
  eMuleBB Suite installer — generic, version-independent Windows bootstrap.

.DESCRIPTION
  Resolves and installs the LATEST release of each suite product straight from
  GitHub Releases. Generic by design: it pins no version, so it is never coupled
  to a single product's release train and always installs the latest. The product
  set is described by suite-manifest.json, fetched from the same origin as this
  script.

  eD2K core selection:
    -Core mfc    eMuleBB (Windows MFC desktop client)                  [default]
    -Core rust   emulebb-rust (multiplatform eD2K/Kad core) instead of the MFC client

  qBittorrentBB (BitTorrent companion) is always installed. aMuTorrent (the
  0.7.3-line controller) is optional via -IncludeController.

  SCAFFOLD: validate end-to-end before this becomes the primary published install
  path. Products without a published release yet are skipped with a warning.

.EXAMPLE
  irm https://emulebb.github.io/install.ps1 | iex

.EXAMPLE
  # with options:
  $s = irm https://emulebb.github.io/install.ps1
  & ([scriptblock]::Create($s)) -Core rust -IncludeController
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('mfc', 'rust')] [string] $Core = 'mfc',
    [string] $InstallRoot = "$env:LOCALAPPDATA\eMuleBB-Suite",
    [switch] $IncludeController,
    [switch] $DryRun,
    [string] $BaseUrl = 'https://emulebb.github.io'
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$UA = @{ 'User-Agent' = 'emulebb-suite-installer' }

function Write-Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Note($m) { Write-Host "  ! $m" -ForegroundColor Yellow }

function Get-Json($url) { Invoke-RestMethod -Uri $url -Headers $UA }
function Get-Text($url) { (Invoke-WebRequest -Uri $url -Headers $UA -UseBasicParsing).Content }

function Resolve-LatestRelease($repo) {
    try { Get-Json "https://api.github.com/repos/$repo/releases/latest" } catch { $null }
}

function Select-Asset($release, $pattern) {
    if (-not $release) { return $null }
    $release.assets | Where-Object { $_.name -like $pattern } | Select-Object -First 1
}

function Test-AssetHash($file, $release, $assetName) {
    # Integrity source: a '<asset>.sha256' sibling asset in the same release.
    $shaAsset = $release.assets | Where-Object { $_.name -eq "$assetName.sha256" } | Select-Object -First 1
    if (-not $shaAsset) { Write-Note "no .sha256 published for $assetName — skipping hash check"; return }
    $expected = ((Get-Text $shaAsset.browser_download_url) -split '\s+')[0].Trim().ToLower()
    $actual = (Get-FileHash -Algorithm SHA256 -Path $file).Hash.ToLower()
    if ($expected -ne $actual) { throw "SHA-256 mismatch for $assetName (expected $expected, got $actual)" }
    Write-Host "    sha256 ok"
}

function Install-Product($name, $repo, $pattern) {
    Write-Step "Resolving $name ($repo)"
    $rel = Resolve-LatestRelease $repo
    if (-not $rel) { Write-Note "$name has no published release yet — skipping"; return }
    $asset = Select-Asset $rel $pattern
    if (-not $asset) { Write-Note "$name $($rel.tag_name): no asset matching '$pattern' — skipping"; return }
    $dir = Join-Path $InstallRoot $name
    if ($DryRun) { Write-Host "    [dry-run] would install $($asset.name) ($($rel.tag_name)) -> $dir"; return }
    if ($PSCmdlet.ShouldProcess($name, "install $($rel.tag_name)")) {
        $tmp = Join-Path $env:TEMP $asset.name
        Write-Host "    downloading $($asset.name)"
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $tmp -Headers $UA -UseBasicParsing
        Test-AssetHash $tmp $rel $asset.name
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Expand-Archive -Path $tmp -DestinationPath $dir -Force
        Remove-Item $tmp -Force
        Write-Host "    installed $name $($rel.tag_name) -> $dir" -ForegroundColor Green
    }
}

# --- main ---
Write-Step "eMuleBB Suite installer (core=$Core, root=$InstallRoot)"
$manifest = Get-Json "$BaseUrl/suite-manifest.json"

# 1) eD2K core (MFC eMuleBB or emulebb-rust)
$coreProduct = $manifest.cores.$Core.product
$cp = $manifest.products.$coreProduct
Install-Product $coreProduct $cp.repo $cp.assetPattern

# 2) always-installed products (qBittorrentBB)
foreach ($p in $manifest.alwaysInstall) {
    $mp = $manifest.products.$p
    Install-Product $p $mp.repo $mp.assetPattern
}

# 3) optional controller (aMuTorrent)
if ($IncludeController) {
    $mp = $manifest.products.amutorrent
    Install-Product 'amutorrent' $mp.repo $mp.assetPattern
}

Write-Step "Done. Installed under $InstallRoot"
Write-Host "Suite roadmap: https://github.com/orgs/emulebb/projects/3"
