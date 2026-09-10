# Fermi Podcast Companion

A conversational study companion over 3 raw Fermi Podcast episodes:
- **Great Papers 01**: Einstein's Special Relativity (1905)
- **Great Papers 02**: How Black Holes Radiate, Hawking (1975)
- **Great Papers 03**: The Double Helix, Watson & Crick (1953)

Answers are grounded strictly in the supplied audio (via transcription + vector retrieval), every claim carries a timestamp citation you can jump to in the original audio, and the system explicitly declines to answer questions the supplied episodes don't cover.

## Features

- **Single vs. All Episode Search Scope**: Filter retrieval to a single specific episode or query across all episodes simultaneously.
- **Timestamp Citations & Source Audio Seeking**: Interactive citation buttons seek directly to the exact start timestamp in local `.mp3` files or via direct GitHub Release (`v1.0.0`) byte-range audio streaming for cloud deployment.
- **Context-Aware Follow-ups**: Retrieval folds prior conversation context into vector queries so follow-up questions like "walk me through it again" maintain topic continuity.
- **Clean Sample Prompts & Session Reset**: Built-in sample question prompts for fast testing and a dedicated `Clear Chat` feature in the sidebar.

## Setup

**Windows (PowerShell):**
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-transcribe.txt   # only needed to transcribe audio locally
```

**Mac/Linux:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-transcribe.txt   # only needed to transcribe audio locally
```

`requirements.txt` has only what the chat app itself needs (chromadb, groq, streamlit, etc.) -- this is also what's used for the deployed version. `requirements-transcribe.txt` adds `faster-whisper`, which is only needed once, locally, to turn the raw mp3s into transcripts.

Create a file named `.env` in the project root with your Groq key:
```
GROQ_API_KEY=your_key_here
```
(get a free key at console.groq.com; `src/rag.py` loads this automatically via `python-dotenv`)

Drop the 3 supplied mp3 files into `data/audio/`.

## Run the pipeline

On Mac/Linux with `make` available:
```bash
make ingest   # transcribe -> chunk -> index (only needs to be run once)
make run      # launches the Streamlit chat UI
```

On Windows (or anywhere without `make`), run the same steps directly:
```powershell
.venv\Scripts\python.exe src\transcribe.py
.venv\Scripts\python.exe src\chunk.py
.venv\Scripts\python.exe src\index.py
.venv\Scripts\python.exe -m streamlit run src\app.py
```

## Evaluation

```powershell
.venv\Scripts\python.exe eval\run_eval.py --tag baseline
# ... inspect eval/results/baseline.json, make improvements ...
.venv\Scripts\python.exe eval\run_eval.py --tag improved
```

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
src/app.py  (Streamlit chat; scope filter; interactive timestamp audio seeking)
```

`src/rag.py` is imported by both `src/app.py` and `eval/run_eval.py`, so the evaluation always exercises the exact same code path a real user hits.

Retrieval is history-aware and scope-aware:
- For follow-up questions, the last conversation turn is folded into the search query.
- When an episode filter is selected, Chroma queries filter metadata using `where={"episode_id": episode_filter}`.

## Known limitations
- Only 3 episodes / this specific collection -- not built for a growing catalogue.
- Transcription quality depends on the Whisper model size chosen (`WHISPER_MODEL_SIZE` env var).
- Refusal threshold (`RAG_DISTANCE_THRESHOLD` in `src/rag.py`) was tuned against the eval set in `EVAL.md`.
- Automated eval scorer measures hard refusals via distance thresholding; soft in-answer declines are verified via manual evaluation logs.
