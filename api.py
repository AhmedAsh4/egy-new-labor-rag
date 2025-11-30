import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from rag import LaborRAG

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Egyptian Labor Law RAG API")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag_system = LaborRAG(
    chunks_file="data/files/chunks.json", index_file="data/files/index.faiss"
)


@app.post("/ask")
async def ask_question(request: dict):
    """
    Handle user queries about Egyptian Labor Law.

    Args:
        request: Dictionary containing the user's query

    Returns:
        Text response with the answer including citations
    """
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        logger.info(f"Received query: {query}")

        # Run the complete RAG pipeline
        answer = rag_system.run_query(query)

        if not answer:
            raise HTTPException(status_code=404, detail="No answer generated")

        logger.info("Successfully processed query")

        return {"answer": answer}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Egyptian Labor Law RAG API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
