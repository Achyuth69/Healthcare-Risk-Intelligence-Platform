"""
RAG Pipeline — LangChain + ChromaDB + Sentence Transformers
Handles document ingestion, retrieval, and LLM-augmented generation.
"""
import asyncio
import os
import tempfile
import time
import uuid
import structlog
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.rag import RAGQueryResponse, DocumentSource

logger = structlog.get_logger(__name__)

_CONTEXT_TEMPLATE = """\
You are a clinical AI assistant. Answer the question using ONLY the provided context.
If the context does not contain enough information, say so clearly.

Context from medical literature:
{context}
{patient_context}
Question: {question}

Provide a clear, evidence-based answer with specific references to the context where applicable.\
"""


class RAGPipeline:
    """
    Production RAG pipeline for clinical knowledge retrieval.

    Flow:
      Ingest  : PDF → chunk → embed → ChromaDB
      Query   : question → embed → similarity search → LLM → answer
    """

    _instance: Optional["RAGPipeline"] = None

    def __init__(self):
        self._chroma_client = None
        self._vectorstore = None
        self._embeddings = None
        self._text_splitter = None
        self._ready = False

    # ── Singleton lifecycle ───────────────────────────────────

    @classmethod
    async def initialize(cls) -> "RAGPipeline":
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._setup()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RAGPipeline":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Setup ─────────────────────────────────────────────────

    async def _setup(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._setup_sync)

    def _setup_sync(self):
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import Chroma
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""],
            )

            logger.info("Loading embedding model", model=settings.EMBEDDING_MODEL)
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            self._chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._chroma_client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

            self._vectorstore = Chroma(
                client=self._chroma_client,
                collection_name=settings.CHROMA_COLLECTION_NAME,
                embedding_function=self._embeddings,
            )

            self._ready = True
            logger.info("RAG pipeline ready")

        except Exception as e:
            logger.error("RAG setup failed — running in mock mode", error=str(e))
            self._ready = False

    # ── PDF Ingestion ─────────────────────────────────────────

    async def ingest_pdf(
        self,
        content: bytes,
        filename: str,
        title: str,
        document_type: str,
        tags: List[str] = None,
    ) -> Dict[str, Any]:
        document_id = str(uuid.uuid4())

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            loop = asyncio.get_event_loop()
            chunks_created = await loop.run_in_executor(
                None,
                self._ingest_pdf_sync,
                tmp_path, document_id, title, document_type, tags or [],
            )
        finally:
            os.unlink(tmp_path)

        return {
            "document_id": document_id,
            "title": title,
            "chunks_created": chunks_created,
            "status": "success",
            "message": f"Ingested {chunks_created} chunks from '{title}'",
        }

    def _ingest_pdf_sync(
        self,
        pdf_path: str,
        document_id: str,
        title: str,
        document_type: str,
        tags: List[str],
    ) -> int:
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        chunks = self._text_splitter.split_documents(pages)
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "document_id": document_id,
                "title": title,
                "document_type": document_type,
                "tags": ",".join(tags),
                "chunk_index": i,
                "total_chunks": len(chunks),
            })

        if self._ready and self._vectorstore:
            self._vectorstore.add_documents(chunks)

        logger.info("PDF ingested", document_id=document_id, chunks=len(chunks))
        return len(chunks)

    # ── Query ─────────────────────────────────────────────────

    async def query(
        self,
        question: str,
        patient_context: Optional[Dict] = None,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> RAGQueryResponse:
        start = time.perf_counter()
        sources: List[DocumentSource] = []
        context_text = ""

        if self._ready and self._vectorstore:
            loop = asyncio.get_event_loop()
            docs_with_scores = await loop.run_in_executor(
                None, self._retrieve_sync, question, top_k
            )
            parts = []
            for doc, score in docs_with_scores:
                parts.append(
                    f"[Source: {doc.metadata.get('title', 'Unknown')}]\n{doc.page_content}"
                )
                if include_sources:
                    sources.append(DocumentSource(
                        document_id=doc.metadata.get("document_id", ""),
                        title=doc.metadata.get("title", "Unknown"),
                        page=doc.metadata.get("page"),
                        relevance_score=float(score),
                        excerpt=doc.page_content[:200] + "...",
                    ))
            context_text = "\n\n---\n\n".join(parts)
        else:
            context_text = self._mock_context()

        patient_ctx_str = ""
        if patient_context:
            lines = "\n".join(f"  {k}: {v}" for k, v in patient_context.items() if v is not None)
            patient_ctx_str = f"\nPatient context:\n{lines}"

        prompt = _CONTEXT_TEMPLATE.format(
            context=context_text or "No relevant documents found.",
            patient_context=patient_ctx_str,
            question=question,
        )

        from app.ml.llm.inference import LLMInferenceEngine
        llm = LLMInferenceEngine.get_instance()
        answer = await llm.generate(prompt)

        elapsed_ms = (time.perf_counter() - start) * 1000
        return RAGQueryResponse(
            query=question,
            answer=answer,
            sources=sources if include_sources else None,
            confidence=0.85 if self._ready else 0.50,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def _retrieve_sync(self, question: str, top_k: int):
        return self._vectorstore.similarity_search_with_score(question, k=top_k)

    # ── Clinical narrative ────────────────────────────────────

    async def generate_clinical_narrative(
        self,
        disease_type: str,
        risk_score: float,
        risk_category: str,
        features: Dict[str, Any],
        shap_top_features: List[Dict],
    ) -> str:
        top_features_text = "\n".join(
            f"- {f['name']}: {f['direction'].replace('_', ' ')} "
            f"(impact: {abs(f['shap_value']):.3f})"
            for f in shap_top_features[:5]
        )

        prompt = (
            f"Generate a clinical risk explanation for a patient with the following assessment:\n\n"
            f"Disease: {disease_type.replace('_', ' ').title()}\n"
            f"Risk Score: {risk_score:.1%} ({risk_category.upper()} risk)\n\n"
            f"Top Contributing Factors:\n{top_features_text}\n\n"
            f"Patient Profile:\n"
            f"  Age: {features.get('age', 'N/A')} years\n"
            f"  BMI: {features.get('bmi', 'N/A')}\n"
            f"  Glucose: {features.get('glucose_level', 'N/A')} mg/dL\n"
            f"  BP: {features.get('blood_pressure_systolic', 'N/A')}/"
            f"{features.get('blood_pressure_diastolic', 'N/A')} mmHg\n\n"
            f"Provide:\n"
            f"1. A clear explanation of the risk level\n"
            f"2. The 3 most important contributing factors and why they matter\n"
            f"3. Specific, actionable recommendations\n"
            f"4. When to seek immediate medical attention\n\n"
            f"Keep the explanation clear for both clinicians and patients."
        )

        from app.ml.llm.inference import LLMInferenceEngine
        llm = LLMInferenceEngine.get_instance()
        return await llm.generate(prompt, max_tokens=600)

    # ── Mock helpers ──────────────────────────────────────────

    @staticmethod
    def _mock_context() -> str:
        return (
            "According to clinical guidelines, disease risk assessment should consider "
            "multiple factors including metabolic markers, lifestyle factors, and family history. "
            "Evidence-based interventions include lifestyle modification, pharmacotherapy when "
            "indicated, and regular monitoring. The ADA and ACC/AHA guidelines provide "
            "comprehensive frameworks for risk stratification and management."
        )
