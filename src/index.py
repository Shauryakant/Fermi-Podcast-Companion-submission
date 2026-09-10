"""
Stage 3: Embed chunks and build a local Chroma vector index.

Usage:
    python src/index.py

Reads data/chunks/*.json, writes a persistent Chroma collection to
data/index/. Re-run any time chunk.py output changes -- this script
wipes and rebuilds the collection so it's always consistent with the
current chunks on disk.
"""

import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

CHUNK_DIR = Path("data/chunks")
INDEX_DIR = Path("data/index")
COLLECTION_NAME = "fermi_podcast_chunks"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # small, local, no API cost


def main() -> None:
    chunk_files = sorted(CHUNK_DIR.glob("*.json"))
    if not chunk_files:
        print(f"No chunk files found in {CHUNK_DIR}. Run chunk.py first.")
        return

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(INDEX_DIR))

    # Fresh build every time -- keeps the index honest with what's on disk.
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    collection = client.create_collection(COLLECTION_NAME, embedding_function=embed_fn)

    ids, docs, metadatas = [], [], []
    for c_path in chunk_files:
        for chunk in json.loads(c_path.read_text()):
            ids.append(chunk["chunk_id"])
            docs.append(chunk["text"])
            metadatas.append(
                {
                    "episode_id": chunk["episode_id"],
                    "start": chunk["start"],
                    "end": chunk["end"],
                }
            )

    collection.add(ids=ids, documents=docs, metadatas=metadatas)
    print(f"Indexed {len(ids)} chunks from {len(chunk_files)} episodes into {INDEX_DIR}")


if __name__ == "__main__":
    main()
