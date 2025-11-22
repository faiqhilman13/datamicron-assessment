from fastapi import APIRouter, HTTPException, status
from pathlib import Path
from datetime import datetime
import hashlib
import os

from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    AnalyticsRequest,
    AnalyticsResponse,
    HealthResponse,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackStatsResponse,
    Source,
    JudgeScores
)
from ..services.rag import RAGService
from ..services.analytics import AnalyticsService
from ..services.feedback import FeedbackService

# Initialize router
router = APIRouter()

# Get paths
BASE_DIR = Path(__file__).parent.parent.parent
INDEX_DIR = BASE_DIR / "indexes"
DATA_PATH = BASE_DIR / "data" / "news.csv"

# Initialize services (will be done at startup)
rag_service = None
analytics_service = None
feedback_service = None


def initialize_services():
    """Initialize services at startup"""
    global rag_service, analytics_service, feedback_service

    try:
        print("Initializing services...")

        # Check if indexes exist
        if not (INDEX_DIR / "faiss.index").exists():
            raise FileNotFoundError(
                f"Indexes not found at {INDEX_DIR}. "
                "Please run 'python -m app.services.data_processor' to build indexes first."
            )

        rag_service = RAGService(str(INDEX_DIR))
        analytics_service = AnalyticsService(str(DATA_PATH))
        feedback_service = FeedbackService(str(BASE_DIR / "data" / "feedback.json"))

        print("✓ All services initialized successfully")

    except Exception as e:
        print(f"Error initializing services: {e}")
        raise


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    indexes_loaded = rag_service is not None and analytics_service is not None

    return HealthResponse(
        status="healthy" if indexes_loaded else "unhealthy",
        indexes_loaded=indexes_loaded,
        message="All services running" if indexes_loaded else "Services not initialized"
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main Q&A endpoint using RAG

    Process user query through:
    1. Hybrid search (semantic + keyword)
    2. Reranking
    3. LLM judge evaluation
    4. Web search fallback (if needed)
    5. Answer generation
    """
    if rag_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service not initialized"
        )

    try:
        # Process query through RAG pipeline
        result = rag_service.process_query(
            query=request.query,
            enable_web_search=request.enable_web_search
        )

        # Generate unique response ID
        timestamp = datetime.now().isoformat()
        response_id = hashlib.md5(f"{request.query}{timestamp}".encode()).hexdigest()[:16]

        # Convert to response model
        sources = [Source(**src) for src in result['sources']]
        judge_scores = JudgeScores(**result['judge_scores'])

        response = ChatResponse(
            response_id=response_id,
            answer=result['answer'],
            sources=sources,
            confidence=result['confidence'],
            judge_scores=judge_scores,
            retrieval_method=result['retrieval_method'],
            web_search_triggered=result['web_search_triggered'],
            timestamp=timestamp
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/analytics", response_model=AnalyticsResponse)
async def analytics(request: AnalyticsRequest):
    """
    Dataset analytics endpoint

    Process natural language queries about dataset statistics using
    OpenAI function calling
    """
    if analytics_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service not initialized"
        )

    try:
        result = analytics_service.process_query(request.query)

        response = AnalyticsResponse(
            answer=result['answer'],
            data=result['data'],
            query_type=result['query_type']
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing analytics query: {str(e)}"
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback (thumbs up/down) for a response

    This endpoint collects user feedback to enable reinforcement learning
    and continuous improvement of the AI system.
    """
    if feedback_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback service not initialized"
        )

    try:
        # Convert sources to dict for storage
        sources_dict = [src.model_dump() for src in request.sources]
        judge_scores_dict = request.judge_scores.model_dump()

        result = feedback_service.submit_feedback(
            response_id=request.response_id,
            query=request.query,
            answer=request.answer,
            sources=sources_dict,
            feedback_type=request.feedback_type,
            confidence=request.confidence,
            judge_scores=judge_scores_dict,
            retrieval_method=request.retrieval_method,
            web_search_triggered=request.web_search_triggered,
            comment=request.comment
        )

        return FeedbackResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats():
    """
    Get aggregate feedback statistics

    Returns overall feedback metrics including positive rate,
    web search performance, and confidence correlation.
    """
    if feedback_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback service not initialized"
        )

    try:
        stats = feedback_service.get_feedback_stats()
        return FeedbackStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving feedback stats: {str(e)}"
        )


@router.get("/feedback/recommendations")
async def get_recommendations():
    """
    Get AI system adjustment recommendations based on feedback

    Returns actionable recommendations for improving retrieval
    and response quality based on user feedback patterns.
    """
    if feedback_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback service not initialized"
        )

    try:
        recommendations = feedback_service.get_adjustment_recommendations()
        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}"
        )


@router.get("/rl/config")
async def get_rl_config():
    """
    Get current RL configuration

    Shows the current learned parameters including thresholds,
    weights, and performance history.
    """
    if feedback_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback service not initialized"
        )

    try:
        config = feedback_service.rl_optimizer.get_config()
        trend = feedback_service.rl_optimizer.get_performance_trend()

        return {
            "config": config,
            "performance_trend": trend
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting RL config: {str(e)}"
        )
