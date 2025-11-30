import json
import os
import sys

import faiss
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()


class LaborRAG:
    def __init__(self, chunks_file, index_file):
        self.chunks_file = chunks_file
        self.index_file = index_file
        self.api_key = os.environ.get("MEGANOVA_API_KEY")
        self.index_result_count = 50
        self.rerank_result_count = 5
        self.embedding_dim = 4096
        self.index = None
        self.chunks = None
        self.load_files()

    def load_files(self):
        try:
            self.index = faiss.read_index(self.index_file)
            with open(self.chunks_file, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
            print(
                f"Loaded {self.index.ntotal} vectors and {len(self.chunks)} text chunks."
            )
        except FileNotFoundError:
            print("Error: index.faiss or chunks.json not found. Run ingest first.")
            sys.exit(1)

    def make_request(self, data_dict, url):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.post(url, headers=headers, json=data_dict)
        return response

    def embed_query(self, query):
        embedding_data = {"model": "Qwen/Qwen3-Embedding-8B", "input": [query]}
        url = "https://inference.meganova.ai/v1/embeddings"

        response = self.make_request(embedding_data, url)
        if response.status_code == 200:
            embeddings = response.json()["data"]
            return embeddings[0]["embedding"]
        else:
            raise Exception(
                f"Embedding API failed: {response.status_code} - {response.text}"
            )

    def search_index(self, query_embedding):
        q_np = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(q_np)
        _, indices = self.index.search(q_np, self.index_result_count)
        results = []
        for _, idx in enumerate(indices[0]):
            results.append(self.chunks[idx]["content"])
        print(f"Retrieved {len(results)} results from index.")
        return results

    def rerank_results(self, query, documents):
        url = "https://inference.meganova.ai/v1/rerank"
        rerank_data = {
            "model": "BAAI/bge-reranker-v2-m3",
            "query": query,
            "documents": documents,
            "top_n": self.rerank_result_count,
        }
        response = self.make_request(rerank_data, url)
        print(f"Rerank API response status: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Rerank API failed: {response.status_code} - {response.text}"
            )

    def run_query(self, query):
        query_embedding = self.embed_query(query)
        results = self.search_index(query_embedding)
        reranked_results = self.rerank_results(query, results)
        return reranked_results


if __name__ == "__main__":
    rag_system = LaborRAG(
        chunks_file="data/files/chunks.json", index_file="data/files/index.faiss"
    )
    user_query = "كم عدد أيام الإجازة السنوية للعامل؟"
    results = rag_system.run_query(user_query)
    with open("search_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
