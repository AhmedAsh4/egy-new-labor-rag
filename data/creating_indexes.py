import json
import os

import faiss
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_DIM = 4096

with open("data/files/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

vectors = []
chunks_content = [c["content"] for c in chunks]

embedding_url = "https://inference.meganova.ai/v1/embeddings"

embedding_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ.get('MEGANOVA_API_KEY')}",
}

embedding_data = {"model": "Qwen/Qwen3-Embedding-8B", "input": chunks_content}

response = requests.post(embedding_url, headers=embedding_headers, json=embedding_data)
if response.status_code == 200:
    embeddings = response.json()["data"]
    for item in embeddings:
        vectors.append(item["embedding"])
    print("Embeddings generated successfully.")
else:
    raise Exception(f"Embedding API failed: {response.status_code} - {response.text}")

vectors_np = np.array(vectors).astype("float32")
faiss.normalize_L2(vectors_np)  # Normalize for Cosine Similarity

index = faiss.IndexFlatIP(EMBEDDING_DIM)
index.add(vectors_np)

faiss.write_index(index, os.path.join("data", "files", "index.faiss"))
