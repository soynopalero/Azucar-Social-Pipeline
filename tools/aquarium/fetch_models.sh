#!/bin/sh
# Fetch the speech models transcribe.py needs.
#
# Hugging Face and openaipublic are blocked from the cloud container, which
# rules out faster-whisper and openai-whisper there. These are the same
# Whisper weights exported to ONNX and published as GitHub release assets,
# which is a route that does work. On a machine with open network access,
# faster-whisper is the easier option -- see HANDOFF.md.
#
#   ./fetch_models.sh [small.en|medium.en] [dest]

set -e
SIZE="${1:-small.en}"
DEST="${2:-models}"
BASE="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"

mkdir -p "$DEST"
cd "$DEST"

if [ ! -f silero_vad.onnx ]; then
  echo "fetching voice activity detector ..."
  curl -fsSL -o silero_vad.onnx "$BASE/silero_vad.onnx"
fi

if [ ! -d "sherpa-onnx-whisper-$SIZE" ]; then
  echo "fetching whisper $SIZE ..."
  curl -fL --progress-bar -o "m.tar.bz2" "$BASE/sherpa-onnx-whisper-$SIZE.tar.bz2"
  tar xf m.tar.bz2
  rm m.tar.bz2
fi

echo "ready in $DEST:"
ls -d sherpa-onnx-whisper-* silero_vad.onnx
echo
echo "pip install sherpa-onnx numpy"
echo "python transcribe.py AUDIO --models $DEST --size $SIZE"
