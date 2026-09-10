"""
Minimal chat UI. Deliberately not fancy -- the brief lists a polished
frontend as a non-goal. The one feature worth the extra effort is the
"jump to the source audio" button, since it's called out explicitly
as an example learner interaction and it's what makes citations
actually verifiable instead of just text.

Run with:
    streamlit run src/app.py
"""

import streamlit as st

from rag import answer

st.set_page_config(page_title="Fermi Podcast Companion", layout="centered")
st.title("Fermi Podcast Companion")
st.caption("Ask questions across the supplied episodes. Answers are grounded in the transcripts only.")

if "history" not in st.session_state:
    st.session_state.history = []  # list of {"role", "content"}
if "jump_to" not in st.session_state:
    st.session_state.jump_to = None  # (episode_id, start_seconds)

query = st.chat_input("Ask something about the episodes...")

if query:
    result = answer(query, chat_history=st.session_state.history)
    st.session_state.history.append({"role": "user", "content": query})
    st.session_state.history.append({"role": "assistant", "content": result["answer"]})
    st.session_state.last_result = result

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.write(turn["content"])

if "last_result" in st.session_state and st.session_state.last_result["citations"]:
    st.subheader("Jump to source audio")
    for i, c in enumerate(st.session_state.last_result["citations"]):
        label = f"{c['episode_id']} @ {c['start']:.0f}s"
        if st.button(label, key=f"cite_{i}_{c['episode_id']}_{c['start']}"):
            st.session_state.jump_to = (c["episode_id"], c["start"])

if st.session_state.jump_to:
    episode_id, start = st.session_state.jump_to
    audio_path = f"data/audio/{episode_id}.mp3"
    st.audio(audio_path, start_time=int(start))
