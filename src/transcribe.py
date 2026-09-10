"""
Stage 1: Transcribe raw podcast audio into timestamped segments.

Usage:
    python src/transcribe.py

Reads every .mp3 in data/audio/ and writes a matching JSON transcript
to data/transcripts/<episode_id>.json with the shape:

    {
      "episode_id": "condensed_matter_01",
      "source_file": "data/audio/condensed_matter_01.mp3",
      "segments": [
        {"start": 0.0, "end": 4.2, "text": "..."},
        ...
      ]
    }

This is the ONLY place raw audio is touched. Everything downstream
(chunking, indexing, RAG) works off these JSON files, so re-running
later stages never re-costs transcription time/money.
"""

import json
import os
from pathlib import Path

from faster_whisper import WhisperModel

AUDIO_DIR = Path("data/audio")
TRANSCRIPT_DIR = Path("data/transcripts")

# "small" or "medium" is usually enough for a 2-day trial and is much
# faster than "large-v3" on CPU. Bump up only if quality looks poor
# when you spot-check a transcript against the audio.
MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")


def transcribe_file(model: WhisperModel, audio_path: Path) -> dict:
    segments, info = model.transcribe(str(audio_path), beam_size=5, vad_filter=True)

    seg_list = [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in segments
    ]

    return {
        "episode_id": audio_path.stem,
        "source_file": str(audio_path),
        "language": info.language,
        "duration": info.duration,
        "segments": seg_list,
    }


def main() -> None:
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    audio_files = sorted(AUDIO_DIR.glob("*.mp3"))

    if not audio_files:
        print(f"No .mp3 files found in {AUDIO_DIR}. Drop the 3 episodes there first.")
        return

    # CPU is fine for 3 files; switch device="cuda" if you have a GPU handy.
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    for audio_path in audio_files:
        out_path = TRANSCRIPT_DIR / f"{audio_path.stem}.json"
        if out_path.exists():
            print(f"Skipping {audio_path.name} (transcript already exists)")
            continue

        print(f"Transcribing {audio_path.name} ...")
        transcript = transcribe_file(model, audio_path)
        out_path.write_text(json.dumps(transcript, indent=2))
        print(f"  -> wrote {out_path} ({len(transcript['segments'])} segments)")


if __name__ == "__main__":
    main()
