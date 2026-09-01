# Aquarium cleaning SOP — media prep

Source video lives on `gokic-00101` at
`C:\Users\Pedro.AzureAD\Videos\Aquarium Cleaning`.

## Why the work is split

A Claude Code web session runs in a cloud container that cannot see that
folder, and its network policy only allows package registries, GitHub, and
the Anthropic API — Google Drive is refused at the proxy, and speech-model
weights (Hugging Face, openaipublic) are unreachable. Moving ~18 minutes of
phone video into that container is neither possible nor useful.

So the video never moves. `extract-aquarium-media.ps1` runs on the Windows
machine and reduces the footage to three small artifacts:

| Output | Size | Purpose |
|---|---|---|
| `inventory.json` | a few KB | duration, resolution, **rotation**, audio track per file |
| `audio/*.opus` | ~5 MB total | 16 kHz mono, what gets transcribed |
| `contact/*.jpg` | ~1 MB | tiled thumbnails, one frame per 15 s |

The contact sheets matter more than they look. The SOP has to resolve
"this one here" and "the blue one" into named equipment, and thumbnails are
what makes that possible without watching the video.

Clips are cut later, on this same machine, from a cut list keyed to
transcript timestamps — only the final 720p clips need to reach the web.

## Usage

```powershell
winget install Gyan.FFmpeg   # once; then open a new terminal
.\extract-aquarium-media.ps1 -Source "C:\Users\Pedro.AzureAD\Videos\Aquarium Cleaning"
```

Check the ordering it prints at the end. It sorts by last-modified time,
which is usually the recording order but is not guaranteed — files copied
off a phone in one batch can all share a timestamp.

## Status

The `ffmpeg`/`ffprobe` invocations were verified against test footage,
including display-matrix rotation detection. The PowerShell itself has not
been run — there is no `pwsh` in the container to lint it.
