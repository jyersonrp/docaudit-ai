import logging
from typing import List
from fastapi import APIRouter, HTTPException
from app.models.chat import ChatQueryRequest, ChatResponse, Citation
from app.models.document import DocumentStatus
from app.workers.audit_worker import AuditWorker
from app.services.vector.store import vector_store
from app.services.ai.factory import LLMFactory
from app.core.security import sanitize_prompt_delimiters

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def query_document(request: ChatQueryRequest):
    """
    RAG Chat endpoint: performs hybrid vector retrieval on document chunks,
    extracts citations with exact page numbers, and prompts LLM to answer.
    """
    meta = AuditWorker.get_metadata(request.doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Document '{request.doc_id}' not found")

    sanitized_q = sanitize_prompt_delimiters(request.question.strip())
    if not sanitized_q:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Search top chunks
    scored_chunks = vector_store.search(
        query=sanitized_q,
        doc_id=request.doc_id,
        top_k=request.top_k
    )

    if not scored_chunks:
        return ChatResponse(
            doc_id=request.doc_id,
            question=sanitized_q,
            answer="No relevant text found in this document for your query.",
            citations=[],
            provider_used="none"
        )

    # Convert to Citations
    citations: List[Citation] = []
    context_chunks = []
    for chunk, score in scored_chunks:
        context_chunks.append(chunk)
        snippet = chunk.content[:300].replace("\n", " ").strip()
        citations.append(Citation(
            chunk_id=chunk.id,
            page_number=chunk.page_number,
            snippet=snippet,
            relevance=round(score, 3),
            section=chunk.section
        ))

    # Query LLM
    provider = LLMFactory.get_provider(request.provider)
    provider_used_name = provider.provider_name
    try:
        answer = await provider.chat(sanitized_q, context_chunks)
    except Exception as e:
        logger.warning(f"Provider '{provider.provider_name}' failed during chat query: {e}. Falling back to mock provider.")
        mock_p = LLMFactory.get_provider("mock")
        mock_answer = await mock_p.chat(sanitized_q, context_chunks)
        provider_used_name = f"{provider.provider_name} (fallback: mock)"
        answer = f"[⚠️ Note: {provider.provider_name.upper()} unavailable ({str(e)}). Response generated via Local Deterministic Engine]\n\n{mock_answer}"

    return ChatResponse(
        doc_id=request.doc_id,
        question=sanitized_q,
        answer=answer,
        citations=citations,
        provider_used=provider_used_name
    )
