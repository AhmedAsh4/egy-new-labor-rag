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
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LaborRAG:
    """Retrieval-Augmented Generation system for Egyptian Labor Law queries.

    This class implements a complete RAG pipeline that uses FAISS for vector search,
    embedding models for query encoding, reranking for result refinement, and an LLM
    for generating answers based on retrieved legal articles.
    """

    # API endpoints
    EMBEDDING_URL = "https://inference.meganova.ai/v1/embeddings"
    RERANK_URL = "https://inference.meganova.ai/v1/rerank"
    LLM_URL = "https://inference.meganova.ai/v1/chat/completions"

    # Model names
    EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"
    RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
    LLM_MODEL = "deepseek-ai/DeepSeek-V3-0324-Free"

    def __init__(self, chunks_file, index_file):
        """Initialize the LaborRAG system.

        Args:
            chunks_file: Path to JSON file containing text chunks with article IDs.
            index_file: Path to FAISS index file containing vector embeddings.
        """
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
        """Load FAISS index and text chunks from disk.

        Raises:
            FileNotFoundError: If index or chunks file is not found.
            SystemExit: Exits the program if files are missing.
        """
        try:
            self.index = faiss.read_index(self.index_file)
            with open(self.chunks_file, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
            logger.info(
                f"Loaded {self.index.ntotal} vectors and {len(self.chunks)} text chunks."
            )
        except FileNotFoundError:
            logger.error(
                "Error: index.faiss or chunks.json not found. Run ingest first."
            )
            sys.exit(1)

    def make_request(self, data_dict, url):
        """Make an authenticated POST request to the API.

        Args:
            data_dict: Dictionary containing request payload.
            url: API endpoint URL.

        Returns:
            Response object from the API call.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.post(url, headers=headers, json=data_dict)
        return response

    def embed_query(self, query):
        """Convert query text into a vector embedding.

        Args:
            query: Text query to embed.

        Returns:
            List of floats representing the query embedding.

        Raises:
            Exception: If the embedding API call fails.
        """
        embedding_data = {"model": self.EMBEDDING_MODEL, "input": [query]}

        response = self.make_request(embedding_data, self.EMBEDDING_URL)
        if response.status_code == 200:
            embeddings = response.json()["data"]
            return embeddings[0]["embedding"]
        else:
            raise Exception(
                f"Embedding API failed: {response.status_code} - {response.text}"
            )

    def search_index(self, query_embedding):
        """Search FAISS index for similar document chunks.

        Args:
            query_embedding: Vector embedding of the query.

        Returns:
            List of dictionaries containing article IDs and content.
            Returns empty list if no valid results found or indices are out of bounds.
        """
        q_np = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(q_np)
        _, indices = self.index.search(q_np, self.index_result_count)
        results = []
        for idx in indices[0]:
            if idx < 0 or idx >= len(self.chunks):
                logger.error(
                    f"Index {idx} is out of bounds for chunks list (length: {len(self.chunks)}). "
                    "FAISS index and chunks are out of sync."
                )
                continue
            try:
                results.append(
                    {
                        "id": self.chunks[idx]["id"],
                        "content": self.chunks[idx]["content"],
                    }
                )
            except (KeyError, IndexError) as e:
                logger.error(f"Error accessing chunk at index {idx}: {e}")
                continue

        if not results:
            logger.error("No valid results retrieved from index. Returning empty list.")
            return []

        logger.info(f"Retrieved {len(results)} results from index.")
        return results

    def rerank_results(self, query, documents):
        """Rerank search results using a dedicated reranking model.

        Args:
            query: Original user query text.
            documents: List of document dictionaries from search_index.

        Returns:
            List of reranked documents with relevance scores and article IDs.
            Returns empty list if no documents provided or reranking fails.

        Raises:
            Exception: If the reranking API call fails.
        """
        if not documents:
            logger.warning("No documents provided for reranking. Returning empty list.")
            return []

        # Extract content for reranking API
        doc_contents = [doc["content"] for doc in documents]
        rerank_data = {
            "model": self.RERANK_MODEL,
            "query": query,
            "documents": doc_contents,
            "top_n": self.rerank_result_count,
        }
        response = self.make_request(rerank_data, self.RERANK_URL)
        logger.info(f"Rerank API response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            # Add article IDs back to reranked results
            reranked_with_ids = []
            for item in result["results"]:
                original_index = item["index"]
                if original_index < 0 or original_index >= len(documents):
                    logger.error(
                        f"Rerank result index {original_index} is out of bounds for documents list "
                        f"(length: {len(documents)}). Skipping this result."
                    )
                    continue
                try:
                    reranked_with_ids.append(
                        {
                            "document": item["document"],
                            "relevance_score": item.get("relevance_score", 0),
                            "article_id": documents[original_index]["id"],
                        }
                    )
                except (KeyError, IndexError) as e:
                    logger.error(
                        f"Error accessing document at index {original_index}: {e}"
                    )
                    continue

            if not reranked_with_ids:
                logger.warning(
                    "No valid reranked results after processing. Returning empty list."
                )

            return reranked_with_ids
        else:
            raise Exception(
                f"Rerank API failed: {response.status_code} - {response.text}"
            )

    def build_prompt(self, user_query, reranked_results, reference_chunk):
        """Construct the LLM prompt with context and instructions.

        Args:
            user_query: The user's question.
            reranked_results: List of reranked document results.
            reference_chunk: Text containing legal term definitions.

        Returns:
            Formatted prompt string for the LLM.
        """
        context_str = ""
        for result in reranked_results:
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
            4. **Cite**: At the end of every claim or statement, cite the article ID in brackets, e.g., [Article 12] or [Article 48] for english query.
            5. **Language**: Always answer in the same language as the query. for both the body and the citations, for example, if the query is in Arabic, respond in Arabic.
            6. **Tone**: Professional, precise, and legal.
            7. **Unknowns**: If the answer is not in the provided text, state: "The provided documents do not contain this information." in the same language as the query. Do not hallucinate. If the query is unrelated to Egyptian Labor Law, politely decline to answer.
            8. **Out of Scope**: Do not provide legal advice or opinions beyond the scope of the Egyptian Labor Law. If asked for interpretations, refer only to the text.

            ### ANSWER
            """
        return prompt

    def call_llm(self, prompt):
        """Generate an answer using the language model.

        Args:
            prompt: Formatted prompt containing context and query.

        Returns:
            Generated answer text from the LLM.

        Raises:
            Exception: If the LLM API call fails.
        """
        llm_data = {
            "model": self.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.002,
        }
        response = self.make_request(llm_data, self.LLM_URL)
        if response.status_code == 200:
            logger.info("LLM API call successful.")
            completion = response.json()["choices"][0]["message"]["content"]
            return completion
        else:
            raise Exception(f"LLM API failed: {response.status_code} - {response.text}")

    def generate_related_questions(self, original_query, answer):
        """Generate related follow-up questions based on the query and answer.

        Args:
            original_query: The original user query.
            answer: The generated answer to the query.

        Returns:
            List of 3 related questions in the same language as the original query.
        """
        # Detect language of the query
        arabic_chars = sum(1 for c in original_query if "\u0600" <= c <= "\u06ff")
        total_chars = sum(1 for c in original_query if c.isalpha())
        is_arabic = total_chars > 0 and arabic_chars / total_chars > 0.5

        language = "Arabic" if is_arabic else "English"

        prompt = f"""Based on this Egyptian Labor Law query and answer, generate exactly 3 related follow-up questions that a user might want to ask next.

Original Query: {original_query}
Answer Summary: {answer[:400]}...

Generate questions in {language} that:
1. Explore related aspects of the same topic (e.g., exceptions, special cases)
2. Ask about related rights or obligations mentioned but not fully covered
3. Inquire about practical applications or procedures

Requirements:
- Generate EXACTLY 3 questions
- Each question on a new line
- Do NOT number the questions
- Keep questions concise (under 15 words)
- Make them specific to Egyptian Labor Law
- Use {language} language only

Questions:"""

        llm_data = {
            "model": self.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 200,
        }

        try:
            response = self.make_request(llm_data, self.LLM_URL)
            if response.status_code == 200:
                questions_text = response.json()["choices"][0]["message"]["content"]
                # Parse questions - split by newlines and clean
                questions = [
                    q.strip().lstrip("0123456789.-) ")
                    for q in questions_text.strip().split("\n")
                    if q.strip()
                ]
                # Return only first 3, filter out empty ones
                questions = [q for q in questions if len(q) > 10][:3]
                logger.info(f"Generated {len(questions)} related questions")
                return questions
            else:
                logger.warning(
                    f"Related questions generation failed: {response.status_code}"
                )
                return []
        except Exception as e:
            logger.error(f"Error generating related questions: {e}")
            return []

    def run_query(self, query):
        """Execute the complete RAG pipeline for a user query.

        This method orchestrates the full workflow: embedding the query, searching
        the index, reranking results, building the prompt, and generating an answer.

        Args:
            query: User's question about Egyptian Labor Law.

        Returns:
            Generated answer from the LLM or an error message if processing fails.
        """
        query_embedding = self.embed_query(query)
        results = self.search_index(query_embedding)

        if not results:
            logger.error("No search results found. Cannot proceed with query.")
            return ""

        reranked_results = self.rerank_results(query, results)

        if not reranked_results:
            logger.error("No reranked results available. Cannot proceed with query.")
            return ""

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
