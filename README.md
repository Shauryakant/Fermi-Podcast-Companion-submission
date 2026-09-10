# Fermi Podcast Companion

A conversational study companion over 3 raw Fermi Podcast episodes.
Answers are grounded strictly in the supplied audio (via transcription
+ retrieval), every claim carries a timestamp citation you can jump to
in the original audio, and the system explicitly declines to answer
questions the supplied episodes don't cover.

## Setup

**Windows (PowerShell):**
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a file named `.env` in the project root with your Groq key:
```
GROQ_API_KEY=your_key_here
```
(get a free key at console.groq.com; `src/rag.py` loads this automatically
via `python-dotenv`, so no manual environment-variable step is needed)

Drop the 3 supplied mp3 files into `data/audio/`.

## Run the pipeline

On Mac/Linux with `make` available:
```bash
make ingest   # transcribe -> chunk -> index (only needs to be run once)
make run      # launches the Streamlit chat UI
```

On Windows (or anywhere without `make`), run the same steps directly:
```powershell
python src\transcribe.py
python src\chunk.py
python src\index.py
streamlit run src\app.py
```

Note: transcription is the slow step -- roughly as long as the audio itself
on a normal CPU, so for ~3 hours of combined audio, expect it to take a
while the first time. It only needs to be re-run if the audio changes.

## Evaluation

```powershell
python eval\run_eval.py --tag baseline
# ... inspect eval/results/baseline.json, make the improvement described in EVAL.md ...
python eval\run_eval.py --tag improved
```

(`make eval-baseline` / `make eval-improved` do the same thing on systems with `make`.)

See `EVAL.md` for success criteria, results, and failure analysis.
See `PRODUCT_NOTE.md` for the intended user and the problem this was scoped to solve.

## How it works

```
data/audio/*.mp3
      |  src/transcribe.py  (faster-whisper, local, timestamped)
      v
data/transcripts/*.json
      |  src/chunk.py  (merge into ~45s overlapping windows)
      v
data/chunks/*.json
      |  src/index.py  (sentence-transformers embeddings -> Chroma)
      v
data/index/  (persistent local vector store)
      |  src/rag.py  (retrieve -> Groq -> cited, grounded answer)
      v
src/app.py  (Streamlit chat; citations are clickable and seek the audio player)
```

`src/rag.py` is imported by both `src/app.py` and `eval/run_eval.py`, so
the evaluation always exercises the exact same code path a real user hits.

Retrieval is history-aware: for follow-up questions, the last conversation
turn is folded into the search query, so vague follow-ups like "walk me
through it again" still retrieve the right topic instead of matching
nothing and being wrongly refused. See `EVAL.md` section 5 for the concrete
failure this fixed.

## Known limitations
- Only 3 episodes / this specific collection -- not built for a growing catalogue.
- Transcription quality depends on the Whisper model size chosen (`WHISPER_MODEL_SIZE` env var).
- Refusal threshold (`RAG_DISTANCE_THRESHOLD` in `src/rag.py`) was tuned against the eval set in `EVAL.md`, not derived analytically.
- The automatic eval scorer only detects hard refusals, not soft in-answer
  declines -- see `EVAL.md` section 4 for a case this affects.