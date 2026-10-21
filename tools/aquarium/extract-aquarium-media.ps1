<#
.SYNOPSIS
  Windows-side prep for the aquarium cleaning SOP.

.DESCRIPTION
  Runs where the video actually lives (gokic-00101) and produces three small
  artifacts that are safe to hand off or commit:

    inventory.json   duration / resolution / rotation / audio per source file
    audio/*.opus     16 kHz mono, ~32 kbps -- roughly 5 MB for 18 minutes
    contact/*.jpg    tiled thumbnails, one frame every 15 s

  The raw video never has to move. Clips get cut later from a cut list, on
  this same machine, once the SOP steps are written.

.EXAMPLE
  .\extract-aquarium-media.ps1 -Source "C:\Users\Pedro.AzureAD\Videos\Aquarium Cleaning"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Source,

    [string] $Out = ".\aquarium-out",

    # Seconds between contact-sheet thumbnails.
    [int] $FrameInterval = 15
)

$ErrorActionPreference = 'Stop'
# PowerShell 7.4+ turns a non-zero native exit code into a terminating error.
# This script inspects $LASTEXITCODE itself (to fall back when libopus is
# missing), so opt back out of that behaviour where the setting exists.
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

foreach ($bin in 'ffmpeg', 'ffprobe') {
    if (-not (Get-Command $bin -ErrorAction SilentlyContinue)) {
        throw "$bin is not on PATH. Install with:  winget install Gyan.FFmpeg  (then open a new terminal)"
    }
}

if (-not (Test-Path -LiteralPath $Source)) { throw "Source folder not found: $Source" }

$audioDir   = Join-Path $Out 'audio'
$contactDir = Join-Path $Out 'contact'
New-Item -ItemType Directory -Force -Path $audioDir, $contactDir | Out-Null

$files = Get-ChildItem -LiteralPath $Source -File |
    Where-Object { $_.Extension -match '^\.(mp4|mov|m4v|avi|mkv|3gp)$' } |
    Sort-Object LastWriteTime, Name

if ($files.Count -eq 0) { throw "No video files found in $Source" }

Write-Host "Found $($files.Count) video file(s).`n"

$inventory = @()
$offset    = 0.0

foreach ($f in $files) {
    Write-Host "--- $($f.Name)"

    # -show_streams rather than -show_entries: the display-matrix rotation a
    # phone writes only appears under the stream's side_data_list, and asking
    # for it via -show_entries side_data makes ffprobe dump every packet.
    $probeJson = & ffprobe -v error -print_format json -show_format -show_streams `
        -- "$($f.FullName)" | Out-String
    $probe = $probeJson | ConvertFrom-Json

    $video = $probe.streams | Where-Object { $_.codec_type -eq 'video' } | Select-Object -First 1
    $audio = $probe.streams | Where-Object { $_.codec_type -eq 'audio' } | Select-Object -First 1

    # Phone video carries rotation either as a stream tag or as display-matrix
    # side data. Ignoring it yields sideways clips, so record whatever is there.
    $rotation = 0
    $displayMatrix = $video.side_data_list | Where-Object { $null -ne $_.rotation } | Select-Object -First 1
    if ($displayMatrix)      { $rotation = [int] $displayMatrix.rotation }
    elseif ($video.tags.rotate) { $rotation = [int] $video.tags.rotate }

    $duration = [double] $probe.format.duration
    $stem     = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
    # Keep derived filenames safe for a URL and for a git path.
    $slug     = ($stem -replace '[^A-Za-z0-9]+', '-').Trim('-').ToLower()

    if (-not $audio) {
        Write-Warning "  no audio track -- skipping audio extraction"
    } else {
        $audioPath = Join-Path $audioDir "$slug.opus"
        Write-Host "  audio -> $audioPath"
        & ffmpeg -v error -y -i "$($f.FullName)" -vn -ac 1 -ar 16000 `
            -c:a libopus -b:a 32k -- "$audioPath"
        if ($LASTEXITCODE -ne 0) {
            # Not every Windows build ships libopus; AAC is always present.
            $audioPath = Join-Path $audioDir "$slug.m4a"
            Write-Warning "  libopus unavailable, falling back to AAC"
            & ffmpeg -v error -y -i "$($f.FullName)" -vn -ac 1 -ar 16000 `
                -c:a aac -b:a 48k -- "$audioPath"
        }
    }

    # Tiled thumbnails. These are what lets a reader who cannot watch the video
    # identify the equipment behind "this one here" and "the blue one".
    $contactPath = Join-Path $contactDir "$slug-%02d.jpg"
    Write-Host "  contact sheet -> $contactDir\$slug-*.jpg"
    & ffmpeg -v error -y -i "$($f.FullName)" `
        -vf "fps=1/$FrameInterval,scale=320:-2,tile=5x5" -q:v 4 -- "$contactPath"

    $inventory += [ordered]@{
        file            = $f.Name
        slug            = $slug
        bytes           = $f.Length
        modified        = $f.LastWriteTime.ToString('o')
        duration_sec    = [math]::Round($duration, 3)
        timeline_offset = [math]::Round($offset, 3)
        width           = $video.width
        height          = $video.height
        rotation        = $rotation
        video_codec     = $video.codec_name
        frame_rate      = $video.r_frame_rate
        has_audio       = [bool] $audio
        audio_codec     = $audio.codec_name
        audio_channels  = $audio.channels
        frame_interval  = $FrameInterval
    }

    $offset += $duration
}

$report = [ordered]@{
    source          = $Source
    generated       = (Get-Date).ToString('o')
    file_count      = $files.Count
    total_duration_sec = [math]::Round($offset, 3)
    files           = $inventory
}

$invPath = Join-Path $Out 'inventory.json'
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $invPath -Encoding UTF8

$audioMB = [math]::Round((Get-ChildItem $audioDir -File | Measure-Object Length -Sum).Sum / 1MB, 1)
$sheets  = (Get-ChildItem $contactDir -File).Count

Write-Host ""
Write-Host "Done."
Write-Host "  total runtime   $([timespan]::FromSeconds($offset).ToString('hh\:mm\:ss'))"
Write-Host "  audio           $audioMB MB in $audioDir"
Write-Host "  contact sheets  $sheets in $contactDir"
Write-Host "  inventory       $invPath"
Write-Host ""
Write-Host "Order used (check this is the order he actually recorded in):"
$inventory | ForEach-Object { Write-Host ("  {0,8:N1}s  {1}" -f $_.duration_sec, $_.file) }
Write-Host ""
Write-Host "Hand off inventory.json, audio\, and contact\ -- leave the raw video here."
