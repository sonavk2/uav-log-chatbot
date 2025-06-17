import os
import pickle
import faiss
import numpy as np

VECTOR_DIR = "backend/vector_store_data"
os.makedirs(VECTOR_DIR, exist_ok=True)

def save_vector_index(session_id: str, chunks: list[str], embeddings: np.ndarray):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, f"{VECTOR_DIR}/{session_id}.index")
    with open(f"{VECTOR_DIR}/{session_id}_chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

def load_vector_index(session_id: str):
    index = faiss.read_index(f"{VECTOR_DIR}/{session_id}.index")
    with open(f"{VECTOR_DIR}/{session_id}_chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

def search_chunks(session_id: str, query: str, model, top_k=3):
    index, chunks = load_vector_index(session_id)
    query_vec = model.encode([query])
    D, I = index.search(np.array(query_vec), top_k)
    return [chunks[i] for i in I[0]]