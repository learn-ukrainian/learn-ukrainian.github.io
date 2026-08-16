<#
.SYNOPSIS
  Non-destructive Google Drive → local NTFS bulk-source copy for UkrainianData.

.DESCRIPTION
  Runs `rclone copy` (never sync/purge/delete) from a configured Drive remote
  into the local NTFS path that backs the UkrainianData SMB share. Destination
  resolution uses Get-SmbShare so verification and copy never target a UNC path.

  Credentials stay in the operator's private rclone config. This script never
  prints secrets, account emails, hostnames, or absolute operator home paths.

.PARAMETER RcloneRemote
  rclone remote name that already points at Google Drive (default: gdrive).

.PARAMETER RemoteSubpath
  Path under the remote root for the project bulk folder
  (default: Projects/learn-ukrainian-data).

.PARAMETER ShareName
  Local SMB share name whose Path is the NTFS root (default: UkrainianData).

.PARAMETER DestinationRelative
  Destination under the share's local NTFS root
  (default: raw-sources\learn-ukrainian-data).

.PARAMETER Transfers
  rclone --transfers (default: 8).

.PARAMETER Checkers
  rclone --checkers (default: 16).

.PARAMETER DryRun
  Pass --dry-run to rclone; never write a success receipt.

.PARAMETER SkipRcloneInstall
  Do not attempt winget install when rclone is missing.

.NOTES
  Success message: BULK_COPY_COMPLETE
  A success receipt is intentionally NOT written here — run
  Verify-BulkSources.ps1 after copy; only verification may mint a receipt.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$RcloneRemote = 'gdrive',

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$RemoteSubpath = 'Projects/learn-ukrainian-data',

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$ShareName = 'UkrainianData',

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$DestinationRelative = 'raw-sources\learn-ukrainian-data',

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 64)]
    [int]$Transfers = 8,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 128)]
    [int]$Checkers = 16,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$SkipRcloneInstall
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-RclonePath {
    $cmd = Get-Command rclone.exe -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Source
    }
    $cmd = Get-Command rclone -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Source
    }
    if ($SkipRcloneInstall) {
        throw 'rclone was not found on PATH'
    }
    Write-Output 'rclone not found; attempting Windows Package Manager install (Rclone.Rclone)...'
    winget.exe install --id Rclone.Rclone -e `
        --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw 'rclone installation failed'
    }
    $cmd = Get-Command rclone.exe -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Source
    }
    $candidate = Get-ChildItem `
        -Path (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages') `
        -Filter rclone.exe -File -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $candidate) {
        throw 'rclone was installed but rclone.exe could not be located'
    }
    return $candidate.FullName
}

function Get-LocalShareRoot {
    param([Parameter(Mandatory = $true)][string]$Name)

    $share = Get-SmbShare -Name $Name -ErrorAction Stop
    $shareRoot = [IO.Path]::GetFullPath([string]$share.Path)
    if ([string]::IsNullOrWhiteSpace($shareRoot)) {
        throw "SMB share '$Name' has an empty local Path"
    }
    if ($shareRoot.StartsWith('\\')) {
        throw "SMB share '$Name' Path is UNC; refuse network destination"
    }
    $drive = New-Object -TypeName IO.DriveInfo -ArgumentList ([IO.Path]::GetPathRoot($shareRoot))
    if ($drive.DriveFormat -cne 'NTFS') {
        throw "Share '$Name' is not backed by local NTFS (format=$($drive.DriveFormat))"
    }
    if ($drive.DriveType -ne [IO.DriveType]::Fixed -and $drive.DriveType -ne [IO.DriveType]::Removable) {
        # Fixed is expected for the bulk disk; still allow removable for lab disks.
        throw "Share '$Name' is not on a local drive (DriveType=$($drive.DriveType))"
    }
    return $shareRoot
}

$rclonePath = Get-RclonePath
$remotePrefix = if ($RcloneRemote.EndsWith(':')) { $RcloneRemote } else { "$RcloneRemote`:" }
$remoteNames = @(& $rclonePath listremotes)
if ($LASTEXITCODE -ne 0) {
    throw 'rclone remote-list lookup failed'
}
if ($remoteNames -notcontains $remotePrefix) {
    throw "rclone remote '$remotePrefix' is not configured; create it interactively with a read-only Drive scope before running this script"
}

$shareRoot = Get-LocalShareRoot -Name $ShareName
$destination = [IO.Path]::GetFullPath((Join-Path $shareRoot $DestinationRelative))
if (-not $destination.StartsWith($shareRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) -and
    $destination -cne $shareRoot) {
    throw 'DestinationRelative escapes the local share root'
}
[void](New-Item -ItemType Directory -Path $destination -Force)

$remoteSpec = "$remotePrefix$RemoteSubpath"
$rcloneArgs = @(
    'copy',
    $remoteSpec,
    $destination,
    '--fast-list',
    '--checksum',
    '--transfers', "$Transfers",
    '--checkers', "$Checkers",
    '--create-empty-src-dirs',
    '--retries', '10',
    '--low-level-retries', '20',
    '--progress'
)
# Explicit safety: never pass sync, delete, or purge.
if ($DryRun) {
    $rcloneArgs += '--dry-run'
}

Write-Output "Starting non-destructive rclone copy to local NTFS destination under share '$ShareName'..."
& $rclonePath @rcloneArgs
if ($LASTEXITCODE -ne 0) {
    throw "rclone copy failed with exit code $LASTEXITCODE"
}

if ($DryRun) {
    Write-Output 'BULK_COPY_DRY_RUN_COMPLETE'
    exit 0
}

Write-Output 'BULK_COPY_COMPLETE'
Write-Output 'Next: run Verify-BulkSources.ps1 against the destination; a receipt is written only after successful verification.'
exit 0
