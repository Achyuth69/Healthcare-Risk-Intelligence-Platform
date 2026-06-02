"""
RAG / LLM Schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000, description="Clinical question")
    patient_context: Optional[dict] = Field(None, description="Optional patient features for context")
    top_k: int = Field(5, ge=1, le=20, description="Number of retrieved documents")
    include_sources: bool = Field(True, description="Include source document references")


class DocumentSource(BaseModel):
    document_id: str
    title: str
    page: Optional[int] = None
    relevance_score: float
    excerpt: str


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: Optional[List[DocumentSource]] = None
    confidence: float
    processing_time_ms: float


class DocumentIngestRequest(BaseModel):
    title: str = Field(..., description="Document title")
    document_type: str = Field(..., description="guideline/research/protocol/reference")
    tags: Optional[List[str]] = None


class DocumentIngestResponse(BaseModel):
    document_id: str
    title: str
    chunks_created: int
    status: str
    message: str
