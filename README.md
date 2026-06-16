---

# DocTalk — Private Document Q&A System
<img width="1507" height="793" alt="image" src="https://github.com/user-attachments/assets/b3b8c7c2-b4ea-466c-a57c-0d5735318492" />


A RAG-powered document intelligence system that lets you upload PDFs and ask questions in plain English. Hybrid search (semantic + keyword) under the hood, with source-attributed answers powered by Groq LLaMA 3.3 70B.

---

## Tech Stack

| Layer | Tool |
|---|---|
| PDF Parsing | PyMuPDF |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector Store + Hybrid Search | Qdrant (dense + sparse vectors) |
| Sparse Embeddings | fastembed (SPLADE) |
| LLM | Groq API (LLaMA 3.3 70B Versatile) |
| Backend | FastAPI |
| Frontend | Streamlit |

---

## Architecture

```
PDF Upload → PyMuPDF extract → overlapping chunks (512 tokens, 64 overlap)
                                        ↓
                  Dense embeddings (sentence-transformers)
                  Sparse embeddings (fastembed SPLADE)
                                        ↓
                         Qdrant (dense + sparse vectors)
                                        ↓
User Query → embed (dense + sparse) → Qdrant hybrid search → RRF fusion → top-5 chunks
                                        ↓
                     Groq LLaMA 3.3 70B → answer + page citations
```

---

## Project Structure

```
doctalk/
├── backend/
│   ├── main.py          # FastAPI app — upload, query, documents endpoints
│   ├── ingest.py        # PDF → chunks → embeddings → Qdrant
│   ├── retrieve.py      # Hybrid search with RRF fusion
│   └── llm.py           # Groq API call with retrieval-grounded prompt
├── frontend/
│   └── app.py           # Streamlit UI
├── qdrant_store/        # Persistent local Qdrant storage
├── .env                 # API keys and config
└── requirements.txt
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/NivethaSre/doctalk.git
cd doctalk
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment**

Create a `.env` file in the root folder:
```
GROQ_API_KEY=your_groq_api_key_here
QDRANT_PATH=./qdrant_store
COLLECTION_NAME=doctalk_docs
EMBED_MODEL=all-MiniLM-L6-v2
GROQ_MODEL=llama-3.3-70b-versatile
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K=5
```

Get your free Groq API key at [console.groq.com](https://console.groq.com)

**4. Run the backend**
```bash
python -m backend.main
```

**5. Run the frontend** (new terminal)
```bash
streamlit run frontend/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage

1. Upload a PDF using the sidebar
2. Wait for the "indexed" status badge
3. Type a question in the chat input
4. Get an answer with source citations showing page numbers

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload and index a PDF |
| POST | `/query` | Ask a question against an indexed document |
| GET | `/documents` | List all indexed documents |

---

## How Hybrid Search Works

Each chunk is stored in Qdrant with two vector types:
- **Dense vector** — semantic meaning via sentence-transformers
- **Sparse vector** — keyword signal via fastembed SPLADE

At query time both vectors are searched independently and results are merged using **Reciprocal Rank Fusion (RRF)**, combining semantic relevance and exact keyword matches for better retrieval accuracy than either alone.

---

## License

MIT License

Copyright (c) 2026 Nivetha Sre

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
