<#
.SYNOPSIS
  Non-destructive verification of a local NTFS bulk-source mirror.

.DESCRIPTION
  Resolves the UkrainianData share's local NTFS path via Get-SmbShare, never
  via UNC. Verifies required marker directories and optionally an exact-file
  JSONL manifest (relative path, size, sha256). Writes a success receipt only
  when verification passes. Never deletes or modifies payload files.

.PARAMETER PayloadRoot
  Explicit local directory to verify. When omitted, uses
  <share local path>\raw-sources\learn-ukrainian-data.

.PARAMETER ShareName
  SMB share name (default: UkrainianData).

.PARAMETER DestinationRelative
  Relative path under the share when PayloadRoot is omitted.

.PARAMETER ManifestPath
  Optional JSONL manifest. Each line:
    {"path":"relative/posix/path","size":123,"sha256":"<64 hex>"}
  Extra fields are ignored. When omitted, only marker + non-reparse checks run.

.PARAMETER ReceiptPath
  Where to write the success receipt JSON. Default:
  <share>\staging\storage-topology\receipts\bulk-verify-<utc>.json

.PARAMETER RequiredMarkers
  Comma-separated top-level directory markers
  (default: literary_texts,textbook_chunks).

.NOTES
  Success stdout: BULK_SOURCES_VERIFIED
  Failure: non-zero exit; no success receipt.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$PayloadRoot = '',

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$ShareName = 'UkrainianData',

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$DestinationRelative = 'raw-sources\learn-ukrainian-data',

    [Parameter(Mandatory = $false)]
    [string]$ManifestPath = '',

    [Parameter(Mandatory = $false)]
    [string]$ReceiptPath = '',

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$RequiredMarkers = 'literary_texts,textbook_chunks'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ReceiptSchema = 'storage-topology.bulk-verify.v1'
$TimestampUtc = [DateTime]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'", [Globalization.CultureInfo]::InvariantCulture)
$MismatchCounts = [ordered]@{}
$MismatchDetails = New-Object -TypeName 'System.Collections.Generic.List[object]'
$MaxDetails = 50

function Add-Mismatch {
    param(
        [Parameter(Mandatory = $true)][string]$Kind,
        [string]$CanonicalPath = '',
        [string]$Message = ''
    )
    if (-not $script:MismatchCounts.Contains($Kind)) {
        $script:MismatchCounts[$Kind] = [Int64]0
    }
    $script:MismatchCounts[$Kind] = [Int64]$script:MismatchCounts[$Kind] + 1
    if ($script:MismatchDetails.Count -lt $script:MaxDetails) {
        [void]$script:MismatchDetails.Add([ordered]@{
            kind = $Kind
            path = $CanonicalPath
            message = $Message
        })
    }
}

function ConvertTo-LowerHex {
    param([byte[]]$Bytes)
    return ([BitConverter]::ToString($Bytes)).Replace('-', '').ToLowerInvariant()
}

function Get-FileSha256Lower {
    param([Parameter(Mandatory = $true)][string]$Path)
    $sha = $null
    $stream = $null
    try {
        $sha = [Security.Cryptography.SHA256]::Create()
        $stream = New-Object -TypeName IO.FileStream -ArgumentList @(
            $Path,
            [IO.FileMode]::Open,
            [IO.FileAccess]::Read,
            [IO.FileShare]::Read,
            1048576,
            [IO.FileOptions]::SequentialScan)
        $buffer = New-Object -TypeName byte[] -ArgumentList 1048576
        while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            [void]$sha.TransformBlock($buffer, 0, $read, $buffer, 0)
        }
        [void]$sha.TransformFinalBlock((New-Object -TypeName byte[] -ArgumentList 0), 0, 0)
        return ConvertTo-LowerHex $sha.Hash
    }
    finally {
        if ($null -ne $stream) { $stream.Dispose() }
        if ($null -ne $sha) { $sha.Dispose() }
    }
}

function Get-LocalShareRoot {
    param([Parameter(Mandatory = $true)][string]$Name)

    $share = Get-SmbShare -Name $Name -ErrorAction Stop
    $shareRoot = [IO.Path]::GetFullPath([string]$share.Path)
    if ($shareRoot.StartsWith('\\')) {
        throw "SMB share '$Name' Path is UNC; refuse network verification root"
    }
    $drive = New-Object -TypeName IO.DriveInfo -ArgumentList ([IO.Path]::GetPathRoot($shareRoot))
    if ($drive.DriveFormat -cne 'NTFS') {
        throw "Share '$Name' is not backed by local NTFS"
    }
    return $shareRoot
}

function Test-ReparsePoint {
    param([Parameter(Mandatory = $true)][IO.FileSystemInfo]$Item)
    return (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}

$shareRoot = Get-LocalShareRoot -Name $ShareName

if ([string]::IsNullOrWhiteSpace($PayloadRoot)) {
    $payloadFull = [IO.Path]::GetFullPath((Join-Path $shareRoot $DestinationRelative))
}
else {
    $payloadFull = [IO.Path]::GetFullPath($PayloadRoot)
}

if ($payloadFull.StartsWith('\\')) {
    throw 'PayloadRoot must be a local path, not UNC/SMB'
}
$payloadItem = Get-Item -LiteralPath $payloadFull -Force -ErrorAction Stop
if (-not $payloadItem.PSIsContainer) {
    throw 'PayloadRoot must be a directory'
}
if (Test-ReparsePoint $payloadItem) {
    throw 'PayloadRoot must not be a reparse point'
}
$payloadDrive = New-Object -TypeName IO.DriveInfo -ArgumentList ([IO.Path]::GetPathRoot($payloadFull))
if ($payloadDrive.DriveType -eq [IO.DriveType]::Network) {
    throw 'PayloadRoot is on a network drive; verify only via local NTFS'
}

$markerList = @($RequiredMarkers.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
foreach ($marker in $markerList) {
    $markerPath = Join-Path $payloadFull $marker
    if (-not (Test-Path -LiteralPath $markerPath -PathType Container)) {
        Add-Mismatch -Kind 'missing_marker' -CanonicalPath $marker -Message 'required marker directory absent'
    }
}

$manifestRows = [Int64]0
$manifestChecked = [Int64]0
if (-not [string]::IsNullOrWhiteSpace($ManifestPath)) {
    $manifestFull = [IO.Path]::GetFullPath($ManifestPath)
    if (-not (Test-Path -LiteralPath $manifestFull -PathType Leaf)) {
        throw "ManifestPath not found: $manifestFull"
    }
    $lineNumber = 0
    Get-Content -LiteralPath $manifestFull | ForEach-Object {
        $lineNumber++
        $line = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($line)) { return }
        $manifestRows++
        try {
            $row = $line | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            Add-Mismatch -Kind 'manifest_parse_error' -Message "line $lineNumber"
            return
        }
        $rel = [string]$row.path
        if ([string]::IsNullOrWhiteSpace($rel) -or $rel.Contains('\') -or $rel.StartsWith('/') -or $rel.Contains('..')) {
            Add-Mismatch -Kind 'manifest_path_error' -CanonicalPath $rel -Message "line $lineNumber"
            return
        }
        $expectedSize = [Int64]$row.size
        $expectedSha = ([string]$row.sha256).ToLowerInvariant()
        $target = [IO.Path]::GetFullPath((Join-Path $payloadFull ($rel.Replace('/', '\'))))
        $rootPrefix = $payloadFull.TrimEnd('\') + '\'
        if (-not $target.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            Add-Mismatch -Kind 'manifest_path_error' -CanonicalPath $rel -Message 'escapes payload root'
            return
        }
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            Add-Mismatch -Kind 'missing' -CanonicalPath $rel -Message 'file absent'
            return
        }
        $item = Get-Item -LiteralPath $target -Force
        if (Test-ReparsePoint $item) {
            Add-Mismatch -Kind 'payload_reparse_point' -CanonicalPath $rel -Message 'reparse point'
            return
        }
        if ([Int64]$item.Length -ne $expectedSize) {
            Add-Mismatch -Kind 'size_mismatch' -CanonicalPath $rel -Message "expected=$expectedSize actual=$($item.Length)"
            return
        }
        $actualSha = Get-FileSha256Lower -Path $target
        if ($actualSha -cne $expectedSha) {
            Add-Mismatch -Kind 'sha256_mismatch' -CanonicalPath $rel -Message 'digest mismatch'
            return
        }
        $manifestChecked++
    }
}

$totalMismatches = [Int64]0
foreach ($key in @($MismatchCounts.Keys)) {
    $totalMismatches += [Int64]$MismatchCounts[$key]
}

$passed = ($totalMismatches -eq 0)
$receiptObject = [ordered]@{
    schema = $ReceiptSchema
    timestamp_utc = $TimestampUtc
    share_name = $ShareName
    payload_root = $payloadFull
    destination_is_local_ntfs = $true
    required_markers = $markerList
    manifest_path = if ([string]::IsNullOrWhiteSpace($ManifestPath)) { $null } else { [IO.Path]::GetFullPath($ManifestPath) }
    manifest_rows = $manifestRows
    manifest_checked = $manifestChecked
    mismatch_counts = $MismatchCounts
    mismatch_details = @($MismatchDetails)
    state = if ($passed) { 'BULK_SOURCES_VERIFIED' } else { 'BULK_SOURCES_VERIFY_FAILED' }
    non_destructive = $true
    copy_tool_constraint = 'rclone copy only; never sync/purge/delete'
}

if (-not $passed) {
    $failJson = ($receiptObject | ConvertTo-Json -Depth 6)
    Write-Output 'BULK_SOURCES_VERIFY_FAILED'
    Write-Output $failJson
    exit 1
}

# Success-only receipt on disk.
if ([string]::IsNullOrWhiteSpace($ReceiptPath)) {
    $receiptDir = Join-Path $shareRoot 'staging\storage-topology\receipts'
    [void](New-Item -ItemType Directory -Path $receiptDir -Force)
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ', [Globalization.CultureInfo]::InvariantCulture)
    $ReceiptPath = Join-Path $receiptDir "bulk-verify-$stamp.json"
}
else {
    $ReceiptPath = [IO.Path]::GetFullPath($ReceiptPath)
    $parent = Split-Path -Parent $ReceiptPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
        [void](New-Item -ItemType Directory -Path $parent -Force)
    }
}

($receiptObject | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $ReceiptPath -Encoding utf8
Write-Output 'BULK_SOURCES_VERIFIED'
Write-Output "receipt=$ReceiptPath"
exit 0
