"""
Stage 4: The actual conversational answer function.

Import `answer()` from here in both app.py (the chat UI) and
eval/run_eval.py (the evaluation runner), so the eval always tests the
exact same code path a real user hits -- never a separate "eval-only"
shortcut.

This is also where the trustworthiness requirements from the brief are
enforced in one place:
  - answers are built ONLY from retrieved transcript chunks
  - every answer carries {episode_id, start, end} citations
  - if nothing relevant is retrieved, the model is instructed (and
    the code double-checks) to say the collection doesn't cover it
    instead of answering from general knowledge
"""
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

INDEX_DIR = Path("data/index")
COLLECTION_NAME = "fermi_podcast_chunks"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-120b"

TOP_K = 5
# Chroma returns L2 distance by default (lower = more similar). Anything
# worse than this is treated as "not actually relevant." Tune this
# during the eval improvement step -- don't just guess and leave it.
DISTANCE_REFUSAL_THRESHOLD = float(os.environ.get("RAG_DISTANCE_THRESHOLD", "1.1"))

SYSTEM_PROMPT = """You are a study companion for a physics podcast collection.
You must answer ONLY using the transcript excerpts provided below. Do not use
outside knowledge, even if you know the answer.

Rules:
- If the excerpts don't actually contain the answer, say clearly that the
  supplied episodes don't cover this, instead of guessing.
- Every claim you make must be traceable to one of the excerpts.
- After your answer, list the excerpts you relied on as [episode_id @ start-end].
- Keep the explanation clear and simple, as if explaining to a curious student.
"""


def _get_collection():
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return client.get_collection(COLLECTION_NAME, embedding_function=embed_fn)


def build_retrieval_query(query: str, chat_history: list[dict] | None) -> str:
    """
    A follow-up like "walk me through it again" has no topic words of its
    own -- searched alone, it matches nothing and wrongly triggers a
    refusal. Fold in the last exchange so the topic carries forward.
    """
    if not chat_history:
        return query
    recent_text = " ".join(turn["content"] for turn in chat_history[-2:])
    return f"{recent_text} {query}"


def retrieve(
    query: str,
    top_k: int = TOP_K,
    chat_history: list[dict] | None = None,
    episode_filter: str | None = None,
) -> list[dict]:
    collection = _get_collection()
    search_query = build_retrieval_query(query, chat_history)

    query_kwargs = {"query_texts": [search_query], "n_results": top_k}
    if episode_filter and episode_filter not in ("All Episodes", "All", ""):
        query_kwargs["where"] = {"episode_id": episode_filter}

    results = collection.query(**query_kwargs)

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        chunks.append({**meta, "text": doc, "distance": dist})
    return chunks


def answer(
    query: str,
    chat_history: list[dict] | None = None,
    episode_filter: str | None = None,
) -> dict:
    """
    Returns:
        {
          "answer": str,
          "citations": [{"episode_id":..., "start":..., "end":...}, ...],
          "refused": bool,
          "retrieved": [...],   # raw retrieval, kept for eval/debugging
        }
    """
    chunks = retrieve(query, chat_history=chat_history, episode_filter=episode_filter)
    relevant = [c for c in chunks if c["distance"] <= DISTANCE_REFUSAL_THRESHOLD]

    if not relevant:
        return {
            "answer": (
                "The supplied episodes don't seem to cover this topic, so I "
                "can't answer it from this collection."
            ),
            "citations": [],
            "refused": True,
            "retrieved": chunks,
        }

    context_block = "\n\n".join(
        f"[{c['episode_id']} @ {c['start']:.0f}-{c['end']:.0f}s]\n{c['text']}"
        for c in relevant
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chat_history:
        messages.extend(chat_history)
    messages.append(
        {
            "role": "user",
            "content": f"Transcript excerpts:\n\n{context_block}\n\nQuestion: {query}",
        }
    )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    completion = client.chat.completions.create(
        model=GROQ_MODEL, messages=messages, temperature=0.2
    )
    text = completion.choices[0].message.content

    return {
        "answer": text,
        "citations": [
            {"episode_id": c["episode_id"], "start": c["start"], "end": c["end"]}
            for c in relevant
        ],
        "refused": False,
        "retrieved": chunks,
    }