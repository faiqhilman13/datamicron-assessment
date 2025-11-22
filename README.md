# Datamicron AI News Assistant

Advanced RAG-powered news retrieval system with **Hybrid Search**, **Reranking**, **LLM-as-Judge** evaluation, and **Web Search Fallback** for the Datamicron AI Engineer Assessment.

## 🎯 Features

### Core Functionality
- **Hybrid Search**: Combines semantic search (OpenAI embeddings + FAISS) with keyword search (BM25)
- **Reciprocal Rank Fusion (RRF)**: Intelligently merges results from both search methods
- **Cross-Encoder Reranking**: Reranks top-K results for improved relevance
- **LLM-as-Judge**: Evaluates retrieval adequacy and answer quality with confidence scores
- **Web Search Fallback**: Uses Exa MCP when internal knowledge base is insufficient
- **Dataset Analytics**: Natural language queries for dataset statistics using OpenAI function calling
- **Source Attribution**: Clear citation of sources with relevance scores and sentiment

### Technical Highlights
- **Backend**: FastAPI with async support
- **Frontend**: React + TypeScript + Tailwind CSS
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT-4 Turbo
- **Vector DB**: FAISS (efficient similarity search)
- **Reranker**: Cross-encoder model for document reranking
- **Bilingual**: Supports English and Malay

## 🏗️ Architecture

```
┌─────────────┐
│   User Query │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│   Hybrid Search              │
│  ┌────────────┬────────────┐ │
│  │  Semantic  │  Keyword   │ │
│  │  (FAISS)   │   (BM25)   │ │
│  └─────┬──────┴──────┬─────┘ │
│        └──────┬──────┘        │
│    Reciprocal Rank Fusion     │
└──────────────┬────────────────┘
               │
               ▼
    ┌──────────────────┐
    │   Reranking      │
    │  (Cross-Encoder) │
    └────────┬─────────┘
             │
             ▼
    ┌────────────────────┐
    │   LLM Judge        │
    │  (Adequacy Check)  │
    └────┬──────────┬────┘
         │          │
    Adequate   Insufficient
         │          │
         │          ▼
         │    ┌──────────────┐
         │    │ Web Search   │
         │    │  (Exa MCP)   │
         │    └──────┬───────┘
         │           │
         └───────┬───┘
                 │
                 ▼
        ┌────────────────┐
        │ Answer Gen     │
        │  (OpenAI GPT)  │
        └────────┬───────┘
                 │
                 ▼
        ┌────────────────┐
        │ Judge Answer   │
        │    Quality     │
        └────────┬───────┘
                 │
                 ▼
           ┌──────────┐
           │  Result  │
           └──────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key

### Backend Setup

1. **Clone and navigate to the project**:
   ```bash
   cd /Users/faiqhilman/projects/datamicron-assessment
   ```

2. **Set up Python virtual environment**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   EXA_API_KEY=your_exa_api_key_here  # Optional, for web search
   EMBEDDING_MODEL=text-embedding-3-small
   LLM_MODEL=gpt-4-turbo-preview
   RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
   JUDGE_THRESHOLD=6.0
   TOP_K_RETRIEVAL=20
   TOP_K_RERANK=5
   ```

5. **Build search indexes** (required before first run):
   ```bash
   python build_indexes.py
   ```

   This will:
   - Load news.csv
   - Create OpenAI embeddings (~90 API calls)
   - Build FAISS index for semantic search
   - Build BM25 index for keyword search
   - Save indexes to `backend/indexes/`

   **Note**: Building indexes takes ~2-3 minutes and costs ~$0.01 in OpenAI API usage.

6. **Run the backend server**:
   ```bash
   python run_server.py
   ```

   Server will start at: `http://localhost:8000`
   API docs available at: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```

   Frontend will start at: `http://localhost:5173`

## 🚀 Usage

### Web Interface

1. Open `http://localhost:5173` in your browser
2. Use the **News Q&A** tab to ask questions about Malaysian news
3. Use the **Analytics** tab to query dataset statistics

### Test Questions

Try these questions from the assessment:

**News Q&A:**
1. "What are some initiatives launched by MCMC?"
2. "Adakah SSM terbabit dengan kes-kes mahkamah?"
3. "What is the status of the Malaysian economy in 2025 and associated headwinds?"

**Analytics:**
1. "How many positive and negative news are there?"
2. "How many of the news are before June 2025?"
3. "Who are the top authors in the dataset?"

### API Endpoints

#### POST `/api/chat`
Query the news knowledge base:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are some initiatives launched by MCMC?",
    "enable_web_search": true
  }'
```

**Response:**
```json
{
  "answer": "MCMC has launched several initiatives...",
  "sources": [
    {
      "type": "internal",
      "title": "MCMC cadang bangun sistem amaran bencana...",
      "author": "Kosmo Digital",
      "relevance_score": 0.92,
      "sentiment": "Neutral"
    }
  ],
  "confidence": 0.87,
  "judge_scores": {
    "relevance": 9,
    "factuality": 8,
    "completeness": 9
  },
  "retrieval_method": "hybrid_search_with_reranking",
  "web_search_triggered": false
}
```

#### POST `/api/analytics`
Query dataset statistics:

```bash
curl -X POST http://localhost:8000/api/analytics \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many positive news are there?"
  }'
```

**Response:**
```json
{
  "answer": "There are 45 positive news articles in the dataset.",
  "data": {
    "positive": 45,
    "negative": 30,
    "neutral": 15,
    "total": 90
  },
  "query_type": "sentiment_count"
}
```

#### GET `/api/health`
Check system health:

```bash
curl http://localhost:8000/api/health
```

## 🔬 Evaluation & Improvement

### A) Evaluation Methods

The system implements multiple evaluation metrics:

1. **Retrieval Quality**
   - Precision@K, Recall@K for search accuracy
   - MRR (Mean Reciprocal Rank) for ranking quality
   - NDCG@K for reranking evaluation

2. **LLM-as-Judge Scores**
   - **Relevance** (0-10): Does answer address the question?
   - **Factuality** (0-10): Is answer supported by sources?
   - **Completeness** (0-10): Does answer fully address the question?
   - **Overall Confidence** (0-1): Combined score

3. **Source Attribution**
   - Relevance scores for each source
   - Verification of citation accuracy

4. **System Metrics**
   - Response latency per component
   - Web search trigger rate
   - API usage tracking

### B) Improvement Strategies

**Already Implemented:**
- ✅ Hybrid search (semantic + keyword)
- ✅ Cross-encoder reranking
- ✅ LLM-as-judge evaluation
- ✅ Source attribution with confidence scores

**Future Enhancements:**

1. **Retrieval Improvements**
   - Fine-tune embeddings on Malaysian news domain
   - Implement query expansion with LLM
   - Add multi-vector retrieval (title, summary, content separately)
   - Experiment with different fusion algorithms (CombSUM, CombMNZ)

2. **Reranking Enhancements**
   - Fine-tune cross-encoder on news domain
   - Ensemble multiple rerankers
   - Add metadata-based boosting (recency, sentiment)

3. **Answer Generation**
   - Implement streaming responses for better UX
   - Add multi-hop reasoning for complex questions
   - Generate follow-up questions

4. **Caching & Performance**
   - Cache embeddings and common queries
   - Implement Redis for distributed caching
   - Add query result caching with TTL

5. **Monitoring & Analytics**
   - User feedback collection (thumbs up/down)
   - A/B testing framework
   - Query intent classification
   - Response quality tracking dashboard

6. **Web Search Integration**
   - Fully integrate Exa MCP
   - Implement smart query reformulation for web search
   - Add source credibility scoring

## 📊 Dataset

The system uses `news.csv` containing 90 Malaysian news articles with:
- **Title**: News article title
- **Article Content**: Full article text
- **Summary**: Article summary
- **Author**: News source/author
- **Sentiment**: Positive/Negative/Neutral
- **Timestamp**: Publication date

## 🛠️ Project Structure

```
datamicron-assessment/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py           # FastAPI endpoints
│   │   ├── services/
│   │   │   ├── data_processor.py   # Data loading & indexing
│   │   │   ├── hybrid_search.py    # Hybrid search (FAISS + BM25)
│   │   │   ├── reranker.py         # Cross-encoder reranking
│   │   │   ├── llm_judge.py        # LLM-as-judge evaluation
│   │   │   ├── rag.py              # Main RAG pipeline
│   │   │   ├── web_search.py       # Exa MCP integration
│   │   │   └── analytics.py        # Dataset analytics
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic models
│   │   └── main.py                 # FastAPI app
│   ├── data/
│   │   └── news.csv
│   ├── indexes/                    # Generated indexes
│   ├── build_indexes.py            # Index building script
│   ├── run_server.py               # Server runner
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── AnalyticsPanel.tsx
│   │   │   ├── SourceDisplay.tsx
│   │   │   └── ConfidenceScore.tsx
│   │   ├── api/
│   │   │   └── client.ts           # API client
│   │   ├── App.tsx
│   │   └── index.css
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

## 🎓 Key Components

### 1. Hybrid Search
Combines semantic and keyword search using Reciprocal Rank Fusion:
- **Semantic**: OpenAI embeddings + FAISS for similarity search
- **Keyword**: BM25 for exact term matching
- **Fusion**: RRF algorithm merges results

### 2. Reranking
Cross-encoder model rescores top-K results for improved relevance:
- Uses `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Computes query-document pair scores
- Significantly improves top-5 precision

### 3. LLM-as-Judge
OpenAI evaluates both retrieval and answer quality:
- **Retrieval adequacy**: Determines if internal KB is sufficient
- **Answer quality**: Scores relevance, factuality, completeness
- **Confidence**: Combined score for user transparency

### 4. Web Search Fallback
Triggers when internal knowledge is insufficient:
- Uses Exa MCP for web search
- Clearly labels web sources
- Combines internal + web results

### 5. Analytics
Natural language queries using OpenAI function calling:
- Sentiment analysis
- Temporal filtering
- Author statistics
- Custom aggregations

## 📝 License

This project is created for the Datamicron AI Engineer Assessment.

## 👤 Author

Faiq Hilman

## 🙏 Acknowledgments

- OpenAI for GPT-4 and embeddings
- FAISS for efficient vector search
- Sentence Transformers for reranking models
- Exa for web search capabilities
