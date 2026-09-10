"""
Fermi Podcast Companion - Conversational Study Assistant over Podcast Episodes.
"""

import os
import sys
from pathlib import Path

# Ensure src/ directory is in sys.path for Streamlit Cloud deployment
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import streamlit.components.v1 as components

try:
    from rag import answer
except ImportError:
    from src.rag import answer

st.set_page_config(page_title="Fermi Podcast Companion", layout="wide", page_icon="🎙️")

# Ingested episodes list
EPISODE_OPTIONS = {
    "All episodes (no filter)": "All Episodes",
    "Great Papers 01 - Einstein's Special Relativity": "Great Papers 01 - Einstein's Special Relativity",
    "Great Papers 02 - How Black Holes Radiate, Hawking 1975": "Great Papers 02 - How Black Holes Radiate, Hawking 1975",
    "Great Papers 03 - The Double Helix, Watson and Crick 1953": "Great Papers 03 - The Double Helix, Watson and Crick 1953",
}

SAMPLE_QUESTIONS = [
    "According to the Special Relativity episode, what are Einstein's two postulates that the theory is built on?",
    "According to the Hawking episode, what does Hawking radiation suggest happens at the edge of a black hole?",
    "According to the Double Helix episode, what shape did Watson and Crick propose for the structure of DNA?",
    "What does time dilation mean? Explain it simply, the way the Special Relativity episode describes it.",
]

# Build index check
if not Path("data/index").exists() or not any(Path("data/index").iterdir()):
    with st.spinner("First-time setup: building search index from transcripts..."):
        import index as index_stage
        index_stage.main()

# Initialize session states
if "history" not in st.session_state:
    st.session_state.history = []
if "jump_to" not in st.session_state:
    st.session_state.jump_to = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Sidebar - Episode Selection & Clear Chat
st.sidebar.markdown("### EPISODES")
selected_option = st.sidebar.radio(
    "Select episode scope:",
    options=list(EPISODE_OPTIONS.keys()),
    index=0,
    label_visibility="collapsed"
)
episode_filter = EPISODE_OPTIONS[selected_option]
if episode_filter == "All Episodes":
    episode_filter = None

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat / New Question", use_container_width=True):
    st.session_state.history = []
    st.session_state.jump_to = None
    st.session_state.last_result = None
    st.rerun()

# Main Title & Subtitle
st.title("Fermi Podcast Companion")
st.caption("Answers come only from the supplied episodes — click any source to hear it.")

# Handle input submission FIRST before rendering sample questions or history
query = None
if st.session_state.get("pending_query"):
    query = st.session_state.pending_query
    st.session_state.pending_query = None
else:
    user_input = st.chat_input("Ask about these episodes...")
    if user_input:
        query = user_input

if query:
    result = answer(query, chat_history=st.session_state.history, episode_filter=episode_filter)
    st.session_state.history.append({"role": "user", "content": query})
    st.session_state.history.append({
        "role": "assistant",
        "content": result["answer"],
        "citations": result.get("citations", [])
    })
    st.session_state.last_result = result
    st.session_state.jump_to = None  # Reset audio jump state for new queries

# Render Sample Questions ONLY if history is completely empty
if not st.session_state.history:
    st.markdown("**Ask about the ingested episodes. Try:**")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, key=f"sample_{hash(q)}"):
            st.session_state.pending_query = q
            st.rerun()

# Render Conversation History
for idx, turn in enumerate(st.session_state.history):
    with st.chat_message(turn["role"]):
        st.write(turn["content"])
        
        # Attach Citations & Audio Player directly under the assistant's answer
        if turn["role"] == "assistant" and turn.get("citations") and idx == len(st.session_state.history) - 1:
            st.markdown("---")
            st.markdown("**Click a citation to listen to the source audio:**")
            cols = st.columns(min(len(turn["citations"]), 4))
            for i, c in enumerate(turn["citations"]):
                mins = int(c['start'] // 60)
                secs = int(c['start'] % 60)
                label = f"📍 {c['episode_id']} ({mins:02d}:{secs:02d})"
                with cols[i % len(cols)]:
                    if st.button(label, key=f"cite_{i}_{c['episode_id']}_{c['start']}"):
                        st.session_state.jump_to = (c["episode_id"], c["start"])

            # Display audio player anchored directly under the citations of this answer
            if st.session_state.jump_to:
                episode_id, start = st.session_state.jump_to
                audio_path = f"data/audio/{episode_id}.mp3"
                mins = int(start // 60)
                secs = int(start % 60)
                
                st.markdown(f"**Audio Source:** *{episode_id}* @ `{mins:02d}:{secs:02d}`")
                if os.path.exists(audio_path):
                    st.audio(audio_path, start_time=int(start))
                else:
                    drive_folder_id = "1dCXk1c93aRVEvNBx-4_6QxeBDqw-ZoDU"
                    embed_code = f"""
                    <iframe src="https://drive.google.com/embeddedfolderview?id={drive_folder_id}#list" width="100%" height="180" style="border:1px solid #333; border-radius:8px;"></iframe>
                    """
                    components.html(embed_code, height=200)
