import pytest
from app.services.document.chunker import DocumentChunker

def test_chunk_document_basic():
    pages = [
        {"page_number": 1, "text": "SECTION 1: DEFINITIONS\n\nConfidential information means all technical data.\n\nParty A and Party B agree."},
        {"page_number": 2, "text": "ARTICLE IV: TERMINATION\n\nNotice of thirty days shall be mandatory for termination."}
    ]
    chunks = DocumentChunker.chunk_document("doc-123", pages, chunk_size=150, chunk_overlap=30)
    assert len(chunks) >= 2
    assert all(c.doc_id == "doc-123" for c in chunks)
    assert chunks[0].page_number == 1
    assert "SECTION 1" in (chunks[0].section or "")
    assert any("TERMINATION" in (c.section or "") for c in chunks)

def test_chunk_large_paragraph():
    long_para = "Word " * 200 # 1000 characters
    pages = [{"page_number": 1, "text": long_para}]
    chunks = DocumentChunker.chunk_document("doc-big", pages, chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    assert all(len(c.content) <= 350 for c in chunks)
