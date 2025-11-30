import json
import logging
import os
import sys

import faiss
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
            logger.info(
                f"Loaded {self.index.ntotal} vectors and {len(self.chunks)} text chunks."
            )
        except FileNotFoundError:
            logger.error("Error: index.faiss or chunks.json not found. Run ingest first.")
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
            results.append(
                {"id": self.chunks[idx]["id"], "content": self.chunks[idx]["content"]}
            )
        logger.info(f"Retrieved {len(results)} results from index.")
        return results

    def rerank_results(self, query, documents):
        url = "https://inference.meganova.ai/v1/rerank"
        # Extract content for reranking API
        doc_contents = [doc["content"] for doc in documents]
        rerank_data = {
            "model": "BAAI/bge-reranker-v2-m3",
            "query": query,
            "documents": doc_contents,
            "top_n": self.rerank_result_count,
        }
        response = self.make_request(rerank_data, url)
        logger.info(f"Rerank API response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            # Add article IDs back to reranked results
            reranked_with_ids = []
            for item in result["results"]:
                original_index = item["index"]
                reranked_with_ids.append(
                    {
                        "document": item["document"],
                        "relevance_score": item.get("relevance_score", 0),
                        "article_id": documents[original_index]["id"],
                    }
                )
            return reranked_with_ids
        else:
            raise Exception(
                f"Rerank API failed: {response.status_code} - {response.text}"
            )

    def build_prompt(self, user_query, reranked_results, reference_chunk):
        context_str = ""
        for i, result in enumerate(reranked_results):
            article_id = result["article_id"]
            context_str += f"[Article {article_id}]:\n{result['document']['text']}\n\n"
        prompt = f"""
            ### ROLE
            You are an expert legal assistant specializing in Egyptian Labor Law. 
            Your task is to answer the user's query strictly using the provided context.

            ### REFERENCE DEFINITIONS (Global Context)
            The following text contains the official definitions of legal terms used in this law. 
            Consult this section to understand the precise meaning of words like "Worker", "Employer", "Wage", etc.
            --------------------------------------------------
            {reference_chunk}
            --------------------------------------------------

            ### RELEVANT ARTICLES (Specific Context)
            The following text contains the specific legal articles retrieved for this query.
            --------------------------------------------------
            {context_str}
            --------------------------------------------------

            ### USER QUERY
            {user_query}

            ### INSTRUCTIONS
            1. **Analyze**: First, look up any key terms in the "Reference Definitions" to ensure you interpret them correctly.
            2. **Synthesize**: Answer the query using *only* the information found in the "Relevant Articles" section.
            3. **Format**: Structure your response with clear sections and bullet points where appropriate for better readability.
            4. **Cite**: At the end of every claim or statement, cite the article ID in brackets, e.g., [Article 12] or [Article 48].
            5. **Language**: Answer in the same language as the query (Arabic).
            6. **Tone**: Professional, precise, and legal.
            7. **Unknowns**: If the answer is not in the provided text, state: "The provided documents do not contain this information." Do not hallucinate.

            ### ANSWER
            """
        return prompt

    def call_llm(self, prompt):
        llm_data = {
            "model": "deepseek-ai/DeepSeek-V3-0324-Free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.002,
        }
        url = "https://inference.meganova.ai/v1/chat/completions"
        response = self.make_request(llm_data, url)
        if response.status_code == 200:
            logger.info("LLM API call successful.")
            completion = response.json()["choices"][0]["message"]["content"]
            return completion
        else:
            raise Exception(f"LLM API failed: {response.status_code} - {response.text}")

    def run_query(self, query):
        query_embedding = self.embed_query(query)
        results = self.search_index(query_embedding)
        reranked_results = self.rerank_results(query, results)
        prompt = self.build_prompt(query, reranked_results, self.chunks[0]["content"])
        answer = self.call_llm(prompt)
        return answer


if __name__ == "__main__":
    rag_system = LaborRAG(
        chunks_file="data/files/chunks.json", index_file="data/files/index.faiss"
    )
    user_query = "كم عدد أيام الإجازة السنوية للعامل؟"
    results = rag_system.run_query(user_query)
    print(results)
