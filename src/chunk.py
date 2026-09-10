"""
Stage 2: Group raw Whisper segments into retrieval-sized chunks.

Whisper segments are too short/granular for good retrieval (often a
single sentence). We merge consecutive segments into ~45s windows with
a small overlap, so a concept that spans a sentence boundary doesn't
get split away from its context.

Usage:
    python src/chunk.py

Reads data/transcripts/*.json, writes data/chunks/<episode_id>.json:

    [
      {
        "chunk_id": "condensed_matter_01_0003",
        "episode_id": "condensed_matter_01",
        "start": 120.0,
        "end": 168.4,
        "text": "..."
      },
      ...
    ]
"""

import json
from pathlib import Path

TRANSCRIPT_DIR = Path("data/transcripts")
CHUNK_DIR = Path("data/chunks")

TARGET_WINDOW_SECONDS = 45
OVERLAP_SECONDS = 10  # re-include the tail of the previous chunk


def chunk_episode(transcript: dict) -> list[dict]:
    segments = transcript["segments"]
    episode_id = transcript["episode_id"]

    chunks = []
    window_start_idx = 0
    idx = 0

    while window_start_idx < len(segments):
        window_start_time = segments[window_start_idx]["start"]
        window_segments = []

        idx = window_start_idx
        while idx < len(segments) and (
            segments[idx]["start"] - window_start_time < TARGET_WINDOW_SECONDS
        ):
            window_segments.append(segments[idx])
            idx += 1

        if not window_segments:
            break

        chunk_text = " ".join(s["text"] for s in window_segments)
        chunks.append(
            {
                "chunk_id": f"{episode_id}_{len(chunks):04d}",
                "episode_id": episode_id,
                "start": window_segments[0]["start"],
                "end": window_segments[-1]["end"],
                "text": chunk_text,
            }
        )

        # Move the window forward, but step back by OVERLAP_SECONDS worth
        # of segments so consecutive chunks share a little context.
        next_start_time = window_segments[-1]["end"] - OVERLAP_SECONDS
        new_start_idx = idx
        for j in range(idx - 1, window_start_idx - 1, -1):
            if segments[j]["start"] <= next_start_time:
                new_start_idx = j
                break
        window_start_idx = max(new_start_idx, window_start_idx + 1)

    return chunks


def main() -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    transcript_files = sorted(TRANSCRIPT_DIR.glob("*.json"))

    if not transcript_files:
        print(f"No transcripts found in {TRANSCRIPT_DIR}. Run transcribe.py first.")
        return

    for t_path in transcript_files:
        transcript = json.loads(t_path.read_text())
        chunks = chunk_episode(transcript)
        out_path = CHUNK_DIR / f"{transcript['episode_id']}.json"
        out_path.write_text(json.dumps(chunks, indent=2))
        print(f"{transcript['episode_id']}: {len(chunks)} chunks -> {out_path}")


if __name__ == "__main__":
    main()
