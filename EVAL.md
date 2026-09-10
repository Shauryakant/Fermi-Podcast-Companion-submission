# Evaluation

## 1. What success means here
A grounded answer is one where:
- every factual claim is traceable to a specific cited timestamp, AND
- listening to that timestamp actually supports the claim, AND
- when the collection doesn't cover the question, the system says so instead of guessing.

Refusal accuracy alone is not sufficient -- a system that refuses everything
would score perfectly on that metric while being useless. Faithfulness is
checked by hand against the audio, not inferred from the refusal flag.

## 2. Evaluation set
13 cases in `eval/eval_cases.json`, written against the 3 actual supplied
episodes (Einstein's Special Relativity, Hawking Radiation, Watson & Crick's
Double Helix). The set spans: direct single-episode questions (one per
episode), a cross-episode comparison, a simple-explanation request, a
follow-up/clarification turn that depends on conversation history, two
out-of-scope questions (one physics-adjacent, one completely unrelated), one
adversarial question that embeds a false premise (misattributing Einstein's
Nobel Prize to special relativity, when it was actually for the photoelectric
effect), an episode-routing question, a source-verifiability check, and two
explicit coverage checks (one true, one false).

## 3. Runner
`python eval/run_eval.py --tag baseline` and `python eval/run_eval.py --tag improved`.
Raw input/output/retrieval for every case is saved to `eval/results/<tag>.json`,
including the actual retrieved chunks and their distance scores, not just the
final answer.

## 4. Baseline results
- **Refusal accuracy: 11/13**
- Faithfulness spot-check: listened back to the cited timestamps for eval_01
  (Einstein's two postulates), eval_02 (Hawking radiation mechanism), eval_05
  (time dilation / muon example), eval_11 (speed-of-light evidence), and
  eval_13 (time dilation coverage check). In every case the cited timestamp
  range actually contained the claim being made -- no fabricated citations
  observed in this sample.

### Concrete failures observed

**eval_06 (real bug) -- follow-up question wrongly refused.**
Query: *"I didn't fully understand that example -- walk me through it again,
step by step."* (asked right after the time-dilation explanation in eval_05)

Actual baseline output:
> "The supplied episodes don't seem to cover this topic, so I can't answer it
> from this collection."

Root cause: the query on its own contains no topic words at all (no "time,"
"clock," "muon"). Retrieval searched using only this sentence, found nothing
similar enough to clear the distance threshold, and refused -- even though a
human reading the conversation would immediately know "it" refers to the
muon/time-dilation example from the previous turn. The bug is that retrieval
was context-blind: it never looked at chat history, only the latest message.

**eval_09 (scoring-metric limitation, not a real product bug) -- adversarial
Nobel Prize question flagged as "should have refused."**
Query: *"The episode says Einstein won his Nobel Prize for the theory of
special relativity -- can you confirm that and explain why?"*

Actual output (both baseline and improved):
> "The excerpts you provided don't contain any mention of Einstein's Nobel
> Prize or the committee's reasons for awarding it. None of the quoted
> sections discuss the prize, so I can't confirm or explain that claim from
> the material you've shared."

This is actually the *correct* behavior -- it declined to confirm a false
premise instead of hallucinating an answer. It just didn't trip the
automatic `refused=True` flag, because relevant chunks about Einstein were
retrieved (the topic is present), even though the specific Nobel claim
wasn't. This exposes a real limitation of the automated scorer: it only
detects hard refusals (zero relevant chunks retrieved), not soft in-answer
refusals where the model saw related material but still declined to confirm
an unsupported claim. Manual inspection is what catches this -- the
refusal-accuracy number alone would have under-reported how well the system
actually performed.

## 5. Improvement made
Retrieval was topic-blind for follow-up questions -- it searched using only
the latest message, ignoring prior conversation turns entirely. Added
`build_retrieval_query()` in `src/rag.py`, which folds the last exchange
(prior user question + prior answer) into the text used for the vector
search whenever `chat_history` is present. This gives context-dependent
follow-ups like "walk me through it again" the topic words they're missing
on their own, while leaving standalone first-turn questions completely
unaffected (`chat_history` is empty on turn one, so the function just
returns the original query unchanged).

## 6. Re-run results (after improvement)
`python eval/run_eval.py --tag improved`

- **Refusal accuracy: 12/13 (was 11/13)**
- **What improved:** eval_06 now retrieves the correct time-dilation/muon
  chunks (top result distance dropped from >1.1, i.e. refused, to 0.47, a
  strong match) and produces a full, accurate step-by-step walkthrough of the
  muon example, correctly explaining both the ground-frame (time dilation)
  and muon-frame (length contraction) perspectives with citations.
- **What regressed:** none. All 11 previously-correct cases stayed correct;
  the history-folding change only affects follow-up turns, so standalone
  questions were untouched.
- **What remains unresolved:** eval_09's soft-refusal still isn't caught by
  the automatic `refused` flag, since the flag only measures retrieval
  outcome, not whether the generated text itself hedges or declines to
  confirm a claim. A stricter version of this eval would need a second
  automatic check -- e.g. an LLM-judge pass over the answer text itself
  looking for confirmation language -- rather than relying on the retrieval
  threshold alone. Left as a known limitation rather than "fixed" for this
  trial, since the current behavior (declining to confirm) is already
  correct in substance; only the scoring instrumentation is incomplete.
  - The "jump to source audio" buttons show every retrieved chunk that passed
  the relevance threshold, not only the chunks the model actually cited in
  its written answer -- so occasionally one extra, unused-but-related
  timestamp button appears alongside the ones the answer text references.
  Not incorrect, just imprecise UI; a tighter version would filter buttons
  to only the citations explicitly named in the generated text.