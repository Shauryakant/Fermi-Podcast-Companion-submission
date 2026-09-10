# Product Note

## Who this is for
A physics student (self-learner or coursework-adjacent) who has already
listened to a Fermi Podcast episode once, or is partway through one, and
wants to revisit and re-understand specific concepts without re-listening to
the full episode end to end -- similar to how someone re-reads a highlighted
paragraph in a textbook instead of rereading the whole chapter.

## The problem I chose to solve
Finding and re-explaining a specific concept or example from a specific
point in a specific episode, with the ability to jump straight to that exact
audio to verify it. Concretely: a learner can ask about a concept ("what
does time dilation mean?"), get a grounded explanation tied to a timestamp,
ask a natural follow-up ("walk me through that example again"), and click
through to listen to the exact moment in the original audio that the answer
is based on.

## Why this problem
Among the example interactions in the brief, concept lookup + re-explanation
+ source verification is the one a learner would realistically use *during*
active studying, not just once out of curiosity -- and it's the interaction
that most directly tests trustworthiness (can the system's claim actually be
checked against the source audio in one click?). Given a 2-day scope, this
is narrow enough to build and evaluate properly end to end, rather than
spreading effort thin across many shallow features (e.g. full episode
summarization, multi-episode syllabus generation) that are harder to
evaluate for faithfulness.

## What I explicitly did not build (and why)
- No support for a growing/arbitrary podcast catalogue -- scoped to exactly
  the 3 supplied episodes, per the brief's non-goals.
- No polished frontend -- a plain Streamlit chat interface, since the brief
  explicitly lists a highly polished frontend as a non-goal and the 2-day
  budget is better spent on retrieval quality and evaluation.
- No production deployment, auth, or multi-user support -- runs locally via
  one-command setup, matching the brief's non-goals section.
- No voice interface or audio editing/generation -- out of scope per the
  brief, and unrelated to the core learner problem being solved here.
