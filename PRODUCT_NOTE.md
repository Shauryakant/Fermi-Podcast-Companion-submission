# Product Note

## Who this is for
A physics student (self-learner or coursework-adjacent) who has already listened to a Fermi Podcast episode once, or is partway through one, and wants to revisit and re-understand specific concepts without re-listening to the full episode end to end -- similar to how someone re-reads a highlighted paragraph in a textbook instead of rereading the whole chapter.

## The problem I chose to solve
Finding and re-explaining a specific concept or example from a specific point in a specific episode, with the ability to jump straight to that exact audio to verify it. Concretely: a learner can select a specific episode (or query across all episodes), ask about a concept ("what does time dilation mean?"), get a grounded explanation tied to a timestamp citation, ask a natural follow-up ("walk me through that example again"), and click through to listen to the exact moment in the original audio that the answer is based on.

## Why this problem
Among the example interactions in the brief, concept lookup + re-explanation + source verification is the one a learner would realistically use *during* active studying, not just once out of curiosity -- and it's the interaction that most directly tests trustworthiness (can the system's claim actually be checked against the source audio in one click?).

## Extended Features Implemented
1. **Single vs. All Episode Scope Filtering**:
   - Learners can isolate retrieval to a single episode (*Einstein's Special Relativity*, *Hawking Black Holes*, or *Watson & Crick Double Helix*) or search across the full collection.
   - Enforced cleanly via Chroma vector query metadata filtering (`where={"episode_id": episode_filter}`) in `src/rag.py`.
2. **Dual Audio Playback & Cloud Embedding**:
   - Native audio player seeking via `st.audio(..., start_time=...)` for local `.mp3` setups.
   - Integrated embedded audio iframe previews for cloud/deployed environments where local `.mp3` files are not hosted on disk.
3. **Clean UX & Session Management**:
   - Clean, standard Streamlit sidebar navigation and sample question prompts.
   - Instant session reset via the `Clear Chat / New Question` sidebar action.

## What I explicitly did not build (and why)
- No support for a growing/arbitrary podcast catalogue -- scoped to exactly the 3 supplied episodes, per the brief's non-goals.
- No heavy custom CSS hacks or cloned competitor UIs -- standard Streamlit layout prioritizing clean UX, retrieval quality, and audio verifiability.
- No voice interface or audio editing/generation -- out of scope per the brief, and unrelated to the core learner problem being solved here.
