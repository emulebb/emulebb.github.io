#Requires -Version 5.1
<#
.SYNOPSIS
  eMuleBB Suite public install wrapper.

.DESCRIPTION
  This Pages-hosted script resolves the GitHub Release
  Bootstrap-eMuleBBSuite.ps1 asset, verifies its SHA-256 sidecar when present,
  and invokes it with the supplied arguments.

  For stable 0.7.3 and the 0.7.x support line this is intentionally a PowerShell wrapper,
  not the future TrackMuleBB/uv/Python installer.

.EXAMPLE
  irm https://emulebb.github.io/install.ps1 | iex

.EXAMPLE
  $s = irm https://emulebb.github.io/install.ps1
  & ([scriptblock]::Create($s)) -InstallRoot 'D:\eMuleBBSuite' -Bundle Full
#>
[CmdletBinding()]
param(
    [ValidateSet('Core', 'Controller', 'Full')]
    [string]$Bundle = 'Full',

    [string[]]$Apps,

    [ValidateSet('English', 'Spanish', 'Italian', 'Portuguese')]
    [string]$Language = 'English',

    [ValidateSet('', 'English', 'Spanish', 'Italian', 'Portuguese')]
    [string]$UiLanguage = '',

    [ValidateRange(0, 65535)]
    [int]$PortBlockStart = 0,

    [string]$InstallRoot = 'C:\eMuleBBSuite',

    [string]$Version,

    [ValidateSet('', 'x64', 'ARM64')]
    [string]$Platform = '',

    [string]$EmulebbPackageZip,
    [string]$EmulebbPackageManifest,
    [string]$AmutorrentPackageZip,
    [string]$AmutorrentPackageManifest,
    [string]$DependencyManifest,
    [string]$SuiteScriptsZip,
    [string]$SuiteScriptsManifest,
    [string]$AutomationExamplesZip,
    [string]$AutomationExamplesManifest,

    [string]$P2PBindInterface,
    [string]$ControlBindAddress,
    [string]$EmulebbBindAddress,
    [string]$AmutorrentBindAddress,
    [string]$ProwlarrBindAddress,
    [string]$RadarrBindAddress,
    [string]$SonarrBindAddress,
    [string]$LidarrBindAddress,
    [string]$WhisparrBindAddress,

    [ValidateRange(0, 65535)]
    [int]$EmulebbPort = 0,
    [ValidateRange(0, 65535)]
    [int]$AmutorrentPort = 0,
    [ValidateRange(0, 65535)]
    [int]$ProwlarrPort = 0,
    [ValidateRange(0, 65535)]
    [int]$RadarrPort = 0,
    [ValidateRange(0, 65535)]
    [int]$SonarrPort = 0,
    [ValidateRange(0, 65535)]
    [int]$LidarrPort = 0,
    [ValidateRange(0, 65535)]
    [int]$WhisparrPort = 0,

    [switch]$IncludeNightly,
    [switch]$IncludePrerelease,
    [switch]$AllowRemoteServiceBind,
    [switch]$NonInteractive,
    [switch]$NoStart,
    [switch]$InstallMediaTools,
    [switch]$NoMediaTools,
    [switch]$NoSuiteScriptsBundle,
    [switch]$AllowSuiteScriptsVersionMismatch,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$KeepDownloads,

    [string]$BootstrapReleaseTag,
    [string]$BootstrapUrl,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BootstrapArgs
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$Repository = 'emulebb/emulebb'
$ApiBase = 'https://api.github.com'
$UserAgent = 'emulebb-pages-install-wrapper'
$BootstrapAssetName = 'Bootstrap-eMuleBBSuite.ps1'
$BootstrapHashAssetName = 'Bootstrap-eMuleBBSuite.ps1.sha256'

function Enable-Tls12 {
    try {
        $tls12 = [Net.SecurityProtocolType]::Tls12
        if (([Net.ServicePointManager]::SecurityProtocol -band $tls12) -ne $tls12) {
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor $tls12
        }
    } catch {
        Write-Warning "Could not enable TLS 1.2. If GitHub downloads fail, run the release bootstrapper directly. $($_.Exception.Message)"
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host "[eMuleBB pages install] $Message"
}

function Get-HttpErrorDetail {
    param($Exception)
    if ($null -eq $Exception -or $null -eq $Exception.Response) {
        return ''
    }
    $response = $Exception.Response
    $status = 0
    try { $status = [int]$response.StatusCode } catch { $status = 0 }
    $statusText = if ($status -gt 0) { "HTTP $status" } else { 'HTTP request failed' }
    try {
        if (-not [string]::IsNullOrWhiteSpace([string]$response.StatusDescription)) {
            $statusText = "$statusText $($response.StatusDescription)"
        }
    } catch {
    }
    $detail = ''
    try {
        $stream = $response.GetResponseStream()
        if ($null -ne $stream) {
            $reader = New-Object IO.StreamReader($stream)
            try {
                $detail = $reader.ReadToEnd()
            } finally {
                $reader.Dispose()
            }
        }
    } catch {
    }
    $detail = ([string]$detail -replace '\s+', ' ').Trim()
    if ($detail.Length -gt 800) {
        $detail = $detail.Substring(0, 800) + '...'
    }
    if ([string]::IsNullOrWhiteSpace($detail)) {
        return $statusText
    }
    return "$statusText`: $detail"
}

function Get-HttpStatusCode {
    param($Exception)
    try {
        if ($null -ne $Exception -and $null -ne $Exception.Response) {
            return [int]$Exception.Response.StatusCode
        }
    } catch {
    }
    return 0
}

function Invoke-GitHubWebRequest {
    param([hashtable]$RequestArgs, [string]$ErrorPrefix, [int]$MaxAttempts = 4)
    $attempt = 0
    while ($true) {
        $attempt++
        try {
            return Invoke-WebRequest @RequestArgs -Headers @{ 'User-Agent' = $UserAgent } -UseBasicParsing -ErrorAction Stop
        } catch {
            $status = Get-HttpStatusCode -Exception $_.Exception
            # Retry transient gateway / throttle / network failures (e.g. GitHub HTTP
            # 502/503/504, 429, or a dropped connection); fail fast on everything else.
            $transient = ($status -ge 500) -or ($status -eq 408) -or ($status -eq 429) -or ($status -eq 0)
            if ((-not $transient) -or ($attempt -ge $MaxAttempts)) {
                $detail = Get-HttpErrorDetail -Exception $_.Exception
                if ([string]::IsNullOrWhiteSpace($detail)) {
                    $detail = $_.Exception.Message
                }
                throw "${ErrorPrefix}: $detail"
            }
            $reason = if ($status -gt 0) { "HTTP $status" } else { 'network error' }
            $delay = [int][Math]::Min(20, [Math]::Pow(2, $attempt))
            Write-Warning "$ErrorPrefix - transient $reason; retrying in $delay s (attempt $attempt of $($MaxAttempts - 1))..."
            Start-Sleep -Seconds $delay
        }
    }
}

function Invoke-GitHubApi {
    param([string]$Uri, [string]$Description)
    # Use Invoke-WebRequest + ConvertFrom-Json instead of Invoke-RestMethod: in some
    # environments Invoke-RestMethod collapses the GitHub releases JSON array into a
    # single merged object (tag_name becomes all tags joined), which breaks release
    # resolution. Parsing the raw content ourselves is deterministic across hosts.
    $response = Invoke-GitHubWebRequest -RequestArgs @{ Uri = $Uri } -ErrorPrefix "Could not read $Description from GitHub"
    return ($response.Content | ConvertFrom-Json)
}

function Invoke-DownloadFile {
    param([string]$Url, [string]$OutFile, [string]$Description)
    [void](Invoke-GitHubWebRequest -RequestArgs @{ Uri = $Url; OutFile = $OutFile } -ErrorPrefix "Could not download $Description from $Url")
}

function Resolve-Release {
    # The /releases list already carries each release's assets, so resolve everything
    # from it and never call /releases/tags/<tag> (that endpoint can 504 while the
    # list stays healthy, and it would be a redundant second request anyway).
    $releases = @(Invoke-GitHubApi -Uri "$ApiBase/repos/$Repository/releases?per_page=100" -Description 'eMuleBB releases')

    $explicitTag = ''
    if (-not [string]::IsNullOrWhiteSpace($BootstrapReleaseTag)) {
        $explicitTag = $BootstrapReleaseTag
    } elseif (-not [string]::IsNullOrWhiteSpace($Version)) {
        $explicitTag = if ($Version -like 'emulebb-v*') { $Version } else { "emulebb-v$Version" }
    }
    if (-not [string]::IsNullOrWhiteSpace($explicitTag)) {
        foreach ($release in $releases) {
            if ([string]$release.tag_name -eq $explicitTag) {
                return $release
            }
        }
        throw "Release $explicitTag was not found among the latest eMuleBB releases."
    }

    # GitHub returns releases newest-first, so the first match of each kind is the latest.
    $latestRelease = $null
    $latestNightly = $null
    foreach ($release in $releases) {
        if ($release.draft) {
            continue
        }
        $tag = [string]$release.tag_name
        if ($tag -match '^emulebb-v.+') {
            if ($null -eq $latestRelease) { $latestRelease = $release }
        } elseif ($tag -match '^emulebb-nightly-') {
            if ($null -eq $latestNightly) { $latestNightly = $release }
        }
    }

    if ($null -eq $latestRelease) {
        if ($null -ne $latestNightly) {
            Write-Step "No tagged release found; using the latest nightly $([string]$latestNightly.tag_name)."
            return $latestNightly
        }
        throw 'No usable eMuleBB release with a suite bootstrapper was found.'
    }

    if ($null -eq $latestNightly) {
        return $latestRelease
    }

    # Default to the latest RC/stable release; only consider a nightly when it is newer.
    $releaseTag = [string]$latestRelease.tag_name
    $nightlyTag = [string]$latestNightly.tag_name
    $nightlyIsNewer = $false
    try {
        $nightlyIsNewer = ([datetime]$latestNightly.created_at) -gt ([datetime]$latestRelease.created_at)
    } catch {
        $nightlyIsNewer = $false
    }
    if (-not $nightlyIsNewer) {
        return $latestRelease
    }

    # A nightly is more recent than the latest release. -IncludeNightly opts in
    # non-interactively; otherwise offer the choice and default to the release.
    if ($IncludeNightly) {
        Write-Step "Newer nightly $nightlyTag selected over $releaseTag (-IncludeNightly)."
        return $latestNightly
    }
    if ($NonInteractive) {
        Write-Step "A newer nightly ($nightlyTag) is available; keeping $releaseTag. Pass -IncludeNightly to use the nightly."
        return $latestRelease
    }

    # Offer the newer nightly. Keep the `irm | iex` one-liner unbreakable: if the
    # prompt cannot read (non-interactive/redirected host), fall back to the release
    # instead of hanging or erroring.
    Write-Host ""
    Write-Host "Latest release : $releaseTag (created $([string]$latestRelease.created_at))"
    Write-Host "Newer nightly  : $nightlyTag (created $([string]$latestNightly.created_at))"
    $answer = ''
    try {
        $answer = Read-Host "Install the newer nightly instead of the latest release? [y/N]"
    } catch {
        Write-Step "No interactive prompt available; keeping $releaseTag. Pass -IncludeNightly to use the nightly."
        return $latestRelease
    }
    if ($answer -match '^\s*(y|yes)\s*$') {
        Write-Step "Selected nightly $nightlyTag."
        return $latestNightly
    }
    Write-Step "Keeping latest release $releaseTag."
    return $latestRelease
}

function Resolve-ReleaseAsset {
    param($Release, [string]$Name, [switch]$Required)
    foreach ($asset in @($Release.assets)) {
        if ([string]$asset.name -eq $Name) {
            return $asset
        }
    }
    if ($Required) {
        throw "Release $($Release.tag_name) does not contain $Name."
    }
    return $null
}

function Assert-BootstrapHash {
    param([string]$BootstrapPath, [string]$HashPath)
    $hashText = Get-Content -Raw -LiteralPath $HashPath
    $match = [regex]::Match($hashText, '(?i)\b[a-f0-9]{64}\b')
    if (-not $match.Success) {
        throw "Hash sidecar did not contain a SHA-256 value: $HashPath"
    }
    $expected = $match.Value.ToLowerInvariant()
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $BootstrapPath).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        throw "Bootstrapper hash mismatch. Expected $expected, got $actual."
    }
}

Enable-Tls12

$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ("emulebb-pages-install-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

try {
    $bootstrapPath = Join-Path $tempRoot $BootstrapAssetName

    if (-not [string]::IsNullOrWhiteSpace($BootstrapUrl)) {
        Write-Step "Downloading bootstrapper from explicit URL"
        Invoke-DownloadFile -Url $BootstrapUrl -OutFile $bootstrapPath -Description $BootstrapAssetName
    } else {
        $release = Resolve-Release
        $tag = [string]$release.tag_name
        $bootstrapAsset = Resolve-ReleaseAsset -Release $release -Name $BootstrapAssetName -Required
        $hashAsset = Resolve-ReleaseAsset -Release $release -Name $BootstrapHashAssetName

        Write-Step "Downloading $BootstrapAssetName from $tag"
        Invoke-DownloadFile -Url ([string]$bootstrapAsset.browser_download_url) -OutFile $bootstrapPath -Description $BootstrapAssetName

        if ($null -ne $hashAsset) {
            $hashPath = Join-Path $tempRoot $BootstrapHashAssetName
            Invoke-DownloadFile -Url ([string]$hashAsset.browser_download_url) -OutFile $hashPath -Description $BootstrapHashAssetName
            Assert-BootstrapHash -BootstrapPath $bootstrapPath -HashPath $hashPath
            Write-Step "Verified bootstrapper SHA-256 sidecar"
        } else {
            Write-Warning "Release $tag does not include $BootstrapHashAssetName; continuing without wrapper-side hash verification."
        }
    }

    $wrapperOnly = @('BootstrapReleaseTag', 'BootstrapUrl', 'BootstrapArgs')
    $forward = @{}
    foreach ($entry in $PSBoundParameters.GetEnumerator()) {
        if ($wrapperOnly -contains $entry.Key) {
            continue
        }
        $forward[$entry.Key] = $entry.Value
    }

    # ValueFromRemainingArguments yields a single empty string when no extra args
    # are supplied; splatting that would bind '' to the bootstrapper's first
    # positional parameter (Bundle) and fail its ValidateSet. Drop empty entries.
    $passthru = @(@($BootstrapArgs) | Where-Object { -not [string]::IsNullOrEmpty($_) })
    & $bootstrapPath @forward @passthru
} finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
