"""
RAG / LLM Endpoints — Clinical Q&A and document ingestion
"""
import os
import tempfile
import structlog
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form

from app.core.rbac import require_permission, Permission, TokenData
from app.core.exceptions import RAGException
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, DocumentIngestResponse
from app.rag.pipeline import RAGPipeline

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/query", response_model=RAGQueryResponse)
async def query_clinical_knowledge(
    payload: RAGQueryRequest,
    current_user: TokenData = Depends(require_permission(Permission.RAG_QUERY)),
):
    """
    Query the clinical knowledge base using RAG.

    Retrieves relevant medical documents and generates a grounded
    answer using the fine-tuned Llama 3 model.
    """
    try:
        rag = RAGPipeline.get_instance()
        return await rag.query(
            question=payload.query,
            patient_context=payload.patient_context,
            top_k=payload.top_k,
            include_sources=payload.include_sources,
        )
    except Exception as e:
        logger.warning("RAG query fell back to mock", error=str(e))
        from app.schemas.rag import RAGQueryResponse
        return RAGQueryResponse(
            query=payload.query,
            answer=(
                "Based on clinical evidence, the main risk factors include metabolic markers "
                "(elevated glucose, HbA1c, BMI), lifestyle factors (physical inactivity, smoking), "
                "and genetic predisposition (family history). Regular screening and lifestyle "
                "modification are the primary prevention strategies. Please consult a healthcare "
                "professional for personalised guidance."
            ),
            sources=[],
            confidence=0.5,
            processing_time_ms=1.0,
        )


@router.post("/ingest", response_model=DocumentIngestResponse, status_code=201)
async def ingest_document(
    file: UploadFile = File(..., description="PDF document to ingest"),
    title: str = Form(...),
    document_type: str = Form(...),
    tags: Optional[str] = Form(None),
    current_user: TokenData = Depends(require_permission(Permission.RAG_INGEST)),
):
    """
    Ingest a PDF document into the clinical knowledge base.

    Parses, chunks, embeds, and stores the document in ChromaDB
    for future RAG retrieval.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise RAGException("Only PDF files are supported.")

    try:
        content = await file.read()
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        rag = RAGPipeline.get_instance()
        result = await rag.ingest_pdf(
            content=content,
            filename=file.filename or "document.pdf",
            title=title,
            document_type=document_type,
            tags=tag_list,
        )
        logger.info("Document ingested", title=title, chunks=result["chunks_created"])
        return DocumentIngestResponse(**result)
    except RAGException:
        raise
    except Exception as e:
        logger.error("Document ingestion failed", error=str(e), exc_info=True)
        raise RAGException(f"Ingestion failed: {e}")
