from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
import hashlib


class Source(BaseModel):
    """Source information for retrieved documents"""
    type: Literal["internal", "web"]
    title: str
    author: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    sentiment: Optional[str] = None


class JudgeScores(BaseModel):
    """LLM judge evaluation scores"""
    relevance: int = Field(ge=0, le=10, description="How relevant is the answer to the question")
    factuality: int = Field(ge=0, le=10, description="Is the answer factually accurate")
    completeness: int = Field(ge=0, le=10, description="Does the answer fully address the question")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str = Field(..., min_length=1, description="User's question")
    enable_web_search: bool = Field(default=True, description="Enable web search fallback")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response_id: str = Field(description="Unique identifier for this response")
    answer: str
    sources: List[Source]
    confidence: float = Field(ge=0.0, le=1.0)
    judge_scores: JudgeScores
    retrieval_method: str
    web_search_triggered: bool = False
    timestamp: str = Field(description="Response timestamp")


class AnalyticsRequest(BaseModel):
    """Request model for analytics endpoint"""
    query: str = Field(..., min_length=1, description="Natural language analytics query")


class AnalyticsResponse(BaseModel):
    """Response model for analytics endpoint"""
    answer: str
    data: Dict
    query_type: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    indexes_loaded: bool
    message: str


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback"""
    response_id: str = Field(description="ID of the response being rated")
    query: str = Field(description="Original user query")
    answer: str = Field(description="AI's answer")
    sources: List[Source] = Field(description="Sources used")
    feedback_type: Literal["positive", "negative"] = Field(description="Thumbs up or down")
    confidence: float = Field(ge=0.0, le=1.0)
    judge_scores: JudgeScores
    retrieval_method: str
    web_search_triggered: bool
    comment: Optional[str] = Field(None, description="Optional user comment")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    status: str
    feedback_id: str
    message: str


class FeedbackStatsResponse(BaseModel):
    """Response model for feedback statistics"""
    total_feedback: int
    positive: int
    negative: int
    positive_rate: float
    web_search_feedback: Dict
    confidence_correlation: Dict
