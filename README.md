# Egyptian Labor Law RAG System ⚖️

A Retrieval-Augmented Generation (RAG) system for answering questions about the New Egyptian Labor Law No. 14 of 2025.

## 🌟 Features

- **Semantic Search**: Uses FAISS vector database with Qwen3-Embedding-8B for efficient document retrieval
- **Advanced Reranking**: Implements BGE-Reranker-v2-m3 for improved result relevance
- **Smart Answer Generation**: Powered by DeepSeek-V3 for accurate, citation-backed responses
- **Bilingual Support**: Handles both Arabic and English queries seamlessly
- **Related Questions**: Automatically generates contextual follow-up questions
- **Modern UI**: Beautiful Streamlit interface with RTL support for Arabic
- **RESTful API**: FastAPI backend for easy integration

## 📁 Project Structure

```
egy-new-labor-rag/
├── src/
│   ├── app.py              # Streamlit frontend
│   ├── api.py              # FastAPI backend
│   └── rag.py              # Core RAG implementation
├── data/
│   ├── chunk_data.py       # Text chunking utilities
│   ├── creating_indexes.py # FAISS index creation
│   ├── extract_text_from_pdf.py
│   └── files/
│       ├── chunks.json     # Preprocessed text chunks
│       ├── index.faiss     # Vector database
│       └── labor law.txt   # Source legal text
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── .env                    # API keys (not in git)
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- MEGANOVA API key (for embeddings, reranking, and LLM)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AhmedAsh4/egy-new-labor-rag.git
   cd egy-new-labor-rag
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   MEGANOVA_API_KEY=your_api_key_here
   ```

5. **Prepare data (if needed)**
   ```bash
   # Extract text from PDF
   python data/extract_text_from_pdf.py
   
   # Create chunks
   python data/chunk_data.py
   
   # Build FAISS index
   python data/creating_indexes.py
   ```

### Running the Application

#### Option 1: Streamlit App (Recommended)
```bash
streamlit run src/app.py
```
Visit `http://localhost:8501`

#### Option 2: FastAPI Backend Only
```bash
python src/api.py
```
API available at `http://localhost:8000`

#### Option 3: Docker
```bash
cd docker
docker-compose up --build
```

## 🔧 API Usage

### Query Endpoint

```bash
POST http://localhost:8000/ask
Content-Type: application/json

{
  "query": "كم عدد أيام الإجازة السنوية للعامل؟"
}
```

**Response:**
```json
{
  "answer": "عدد أيام الإجازة السنوية للعامل هو 21 يوماً في السنة [Article 48]",
  "related_questions": [
    "ما هي شروط استحقاق الإجازة السنوية؟",
    "هل يمكن تجميع الإجازات السنوية؟",
    "ما هو تعويض الإجازة السنوية؟"
  ]
}
```

### Health Check
```bash
GET http://localhost:8000/health
```

## 🛠️ Tech Stack

- **Embedding Model**: Qwen/Qwen3-Embedding-8B (4096 dimensions)
- **Reranking Model**: BAAI/bge-reranker-v2-m3
- **LLM**: DeepSeek-V3-0324-Free
- **Vector DB**: FAISS (Facebook AI Similarity Search)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **API Provider**: MegaNova Inference API

## 📊 RAG Pipeline

1. **Query Embedding**: User query → Qwen3-Embedding-8B → 4096-dim vector
2. **Vector Search**: FAISS retrieves top 50 similar chunks
3. **Reranking**: BGE-Reranker refines to top 5 most relevant
4. **Context Building**: Combines retrieved articles with legal definitions
5. **Answer Generation**: DeepSeek-V3 generates response with citations
6. **Related Questions**: LLM generates 3 contextual follow-ups

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Legal Disclaimer

This system provides legal information only, not legal advice. Consult a qualified lawyer for specific legal counsel regarding Egyptian Labor Law matters.

## 📝 License

MIT License - see LICENSE file for details

## 👨‍💻 Author

**Ahmed Ashraf**
- LinkedIn: [ahmedashraaff](https://www.linkedin.com/in/ahmedashraaff/)
- GitHub: [AhmedAsh4](https://github.com/AhmedAsh4)

## 🙏 Acknowledgments

- Egyptian Government for publishing Labor Law No. 14 of 2025
- MegaNova for providing inference API access
- Open source community for the amazing tools
