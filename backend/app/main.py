import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Suppress tokenizers warning

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.routes import router, initialize_services


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("\n" + "="*80)
    print("Starting Datamicron AI News Assistant")
    print("="*80 + "\n")

    try:
        initialize_services()
        print("\n✓ Application startup complete\n")
    except Exception as e:
        print(f"\n✗ Application startup failed: {e}\n")
        raise

    yield

    # Shutdown
    print("\nShutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Datamicron AI News Assistant",
    description="Advanced RAG-powered news retrieval system with hybrid search, reranking, and LLM-as-judge evaluation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        # Production
        "https://timely-tulumba-ac41cb.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Datamicron AI News Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
