.PHONY: ingest run eval-baseline eval-improved

# Full pipeline from raw audio to a queryable index. Run this once
# (or whenever data/audio/ changes).
ingest:
	python src/transcribe.py
	python src/chunk.py
	python src/index.py

run:
	streamlit run src/app.py

eval-baseline:
	python eval/run_eval.py --tag baseline

eval-improved:
	python eval/run_eval.py --tag improved
