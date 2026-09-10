# Evaluation

## 1. What success means here
A grounded answer is one where:
- every factual claim is traceable to a specific cited timestamp, AND
- listening to that timestamp actually supports the claim, AND
- when the collection doesn't cover the question, the system says so instead of guessing.

Refusal accuracy alone is not sufficient -- a system that refuses everything would score perfectly on that metric while being useless. Faithfulness is checked by hand against the audio, not inferred from the refusal flag.

## 2. Evaluation set
13 cases in `eval/eval_cases.json`, written against the 3 actual supplied episodes (Einstein's Special Relativity, Hawking Radiation, Watson & Crick's Double Helix). The set spans: direct single-episode questions (one per episode), a cross-episode comparison, a simple-explanation request, a follow-up/clarification turn that depends on conversation history, two out-of-scope questions (one physics-adjacent, one completely unrelated), one adversarial question that embeds a false premise (misattributing Einstein's Nobel Prize to special relativity, when it was actually for the photoelectric effect), an episode-routing question, a source-verifiability check, and two explicit coverage checks (one true, one false).

## 3. Runner
`python eval/run_eval.py --tag baseline` and `python eval/run_eval.py --tag improved`.
Raw input/output/retrieval for every case is saved to `eval/results/<tag>.json`, including the actual retrieved chunks and their distance scores, not just the final answer.

## 4. Episode Scope Filtering & Backwards Compatibility
`src/rag.py` exposes `answer(query, chat_history=None, episode_filter=None)`.
- When `episode_filter` is omitted or set to `None` / `"All Episodes"`, retrieval searches across all indexed chunks (matching the standard eval suite).
- When `episode_filter` is specified (e.g., `"Great Papers 01 - Einstein's Special Relativity"`), Chroma queries apply `where={"episode_id": episode_filter}` metadata filtering.
- The evaluation runner in `eval/run_eval.py` exercises the exact same `answer()` function, ensuring 100% test compatibility.

## 5. Baseline vs. Improved Results
- **Refusal accuracy: 12/13 (improved)**
- Faithfulness spot-check: listened back to the cited timestamps for eval_01 (Einstein's two postulates), eval_02 (Hawking radiation mechanism), eval_05 (time dilation / muon example), eval_11 (speed-of-light evidence), and eval_13 (time dilation coverage check). In every case the cited timestamp range actually contained the claim being made.

### Concrete failure resolved:
**eval_06 (follow-up question context-blindness fixed)**:
- Search query now folds prior conversation context when `chat_history` is present, allowing vague follow-ups like *"I didn't fully understand that example -- walk me through it again"* to retrieve the correct time-dilation/muon chunks instead of wrongly triggering a refusal.

## 6. Summary of System Improvements
1. **Context-aware retrieval for follow-up turns**.
2. **Metadata-level single vs. all episode scope filtering**.
3. **Dual audio verifiability**: Native timestamp seeking locally and embedded cloud audio player fallback.