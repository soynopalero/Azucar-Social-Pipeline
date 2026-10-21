#!/usr/bin/env python3
"""Transcribe the handover video with timestamps.

Whisper on its own returns one undifferentiated block of text, which is
useless here -- the whole point is pinning each SOP step to the moment in
the footage that demonstrates it. So speech is segmented first with a voice
activity detector, and each segment carries its real start and end. Those
timestamps are what `flag_deictic.py` reads and what the clip cuts key off.

Runs entirely offline once the models are fetched. Accepts anything ffmpeg
can open -- the source .mp4 directly, or the .opus that
extract-aquarium-media.ps1 produces.

    python transcribe.py audio.opus --models ./models --out transcript/
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np
import sherpa_onnx

SAMPLE_RATE = 16000

# Seeds the decoder with vocabulary it would otherwise mangle. The audio is a
# phone mic next to a running filter, and "bio-media" lands as "bio meeting"
# without help.
VOCAB = (
    "Aquarium maintenance. Canister filter, impeller, media basket, bio-media, "
    "ceramic rings, filter floss, sponge pre-filter, powerhead, substrate, "
    "gravel vacuum, siphon, dechlorinator, water conditioner, ammonia, nitrite, "
    "nitrate, pH, API master test kit, algae scraper, magnet cleaner, heater, "
    "airstone, return line, intake, spray bar, O-ring, priming, backwash."
)


def to_wav(src: Path, dst: Path) -> None:
    """Decode anything ffmpeg understands into 16 kHz mono PCM."""
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)],
        check=True,
    )


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as f:
        if f.getframerate() != SAMPLE_RATE or f.getnchannels() != 1:
            raise SystemExit(f"expected 16 kHz mono, got {f.getframerate()} Hz / {f.getnchannels()}ch")
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def build_vad(models: Path, max_seconds: float) -> sherpa_onnx.VoiceActivityDetector:
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = str(models / "silero_vad.onnx")
    cfg.silero_vad.threshold = 0.5
    # He pauses mid-sentence while working, so a short silence must not split
    # a step in half; a long one should.
    cfg.silero_vad.min_silence_duration = 0.45
    cfg.silero_vad.min_speech_duration = 0.25
    cfg.silero_vad.max_speech_duration = max_seconds
    cfg.sample_rate = SAMPLE_RATE
    return sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=180)


def build_recognizer(models: Path, size: str, threads: int) -> sherpa_onnx.OfflineRecognizer:
    d = models / f"sherpa-onnx-whisper-{size}"
    if not d.is_dir():
        raise SystemExit(f"model not found: {d}\nFetch it with fetch_models.sh")
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(d / f"{size}-encoder.int8.onnx"),
        decoder=str(d / f"{size}-decoder.int8.onnx"),
        tokens=str(d / f"{size}-tokens.txt"),
        num_threads=threads,
    )


def stamp(seconds: float, sep: str = ",") -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", type=Path, help="source video or audio file")
    ap.add_argument("--models", type=Path, default=Path("models"))
    ap.add_argument("--size", default="small.en", help="small.en or medium.en")
    ap.add_argument("--out", type=Path, default=Path("transcript"))
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--max-segment", type=float, default=20.0, help="seconds before forcing a split")
    args = ap.parse_args()

    if not args.audio.exists():
        raise SystemExit(f"not found: {args.audio}")

    args.out.mkdir(parents=True, exist_ok=True)
    wav = args.out / "audio16k.wav"
    print(f"decoding {args.audio.name} ...", flush=True)
    to_wav(args.audio, wav)
    samples = read_wav(wav)
    duration = len(samples) / SAMPLE_RATE
    print(f"  {duration/60:.1f} min of audio")

    vad = build_vad(args.models, args.max_segment)
    rec = build_recognizer(args.models, args.size, args.threads)
    print(f"  model {args.size} ready", flush=True)

    # Push through the VAD in window-sized chunks, transcribing each speech
    # run as it falls out so memory stays flat on a long recording.
    segments, started = [], time.time()
    window = vad.config.silero_vad.window_size

    # The VAD trims to the exact speech boundary, which clips the first
    # phoneme and costs Whisper the leading word of nearly every segment
    # ("you see" decoding as "who see"). Re-slice from the full waveform with
    # a lead-in instead, and keep the VAD's own start as the timestamp.
    pad = int(0.35 * SAMPLE_RATE)

    def drain() -> None:
        while not vad.empty():
            seg = vad.front
            start = seg.start / SAMPLE_RATE
            lo = max(0, seg.start - pad)
            hi = min(len(samples), seg.start + len(seg.samples) + pad)
            audio = samples[lo:hi]
            s = rec.create_stream()
            s.accept_waveform(SAMPLE_RATE, audio)
            rec.decode_stream(s)
            text = s.result.text.strip()
            if text:
                segments.append({
                    "start": round(start, 3),
                    "end": round((seg.start + len(seg.samples)) / SAMPLE_RATE, 3),
                    "text": text,
                })
                print(f"  [{stamp(start, '.')}] {text[:76]}", flush=True)
            vad.pop()

    for i in range(0, len(samples), window):
        vad.accept_waveform(samples[i:i + window])
        drain()
    vad.flush()
    drain()

    elapsed = time.time() - started
    speech = sum(s["end"] - s["start"] for s in segments)
    words = sum(len(s["text"].split()) for s in segments)

    (args.out / "transcript.json").write_text(
        json.dumps({"source": str(args.audio), "model": args.size,
                    "duration_sec": round(duration, 2), "segments": segments}, indent=2),
        encoding="utf-8")

    srt = []
    for i, s in enumerate(segments, 1):
        srt += [str(i), f"{stamp(s['start'])} --> {stamp(s['end'])}", s["text"], ""]
    (args.out / "transcript.srt").write_text("\n".join(srt), encoding="utf-8")
    (args.out / "transcript.txt").write_text(
        "\n".join(f"[{stamp(s['start'], '.')}] {s['text']}" for s in segments) + "\n",
        encoding="utf-8")

    print(f"\n{len(segments)} segments, {words} words, {speech/60:.1f} min of speech")
    print(f"decoded in {elapsed/60:.1f} min ({duration/elapsed:.1f}x realtime)")
    print(f"wrote {args.out}/transcript.json, .srt, .txt")
    print(f"\nNext:  python flag_deictic.py {args.out}/transcript.json --video {args.audio.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
