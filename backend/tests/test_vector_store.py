import pytest
from app.models.document import DocumentChunk
from app.services.vector.store import LocalVectorStore

def test_local_vector_store_operations(tmp_path):
    db_file = tmp_path / "test_vec.db"
    store = LocalVectorStore(db_path=db_file)

    chunks = [
        DocumentChunk(
            id="c1",
            doc_id="doc1",
            page_number=1,
            chunk_index=0,
            content="The indemnification clause requires Party A to defend against third-party patent suits.",
            token_count=13,
            section="Section 4: Indemnification"
        ),
        DocumentChunk(
            id="c2",
            doc_id="doc1",
            page_number=2,
            chunk_index=1,
            content="Either party may terminate upon thirty days prior written notice.",
            token_count=10,
            section="Section 5: Termination"
        ),
        DocumentChunk(
            id="c3",
            doc_id="doc2",
            page_number=1,
            chunk_index=0,
            content="Operating revenue reached 120 million USD in fiscal year 2024.",
            token_count=10,
            section="Financials"
        )
    ]

    store.add_chunks(chunks)

    # Search for indemnification
    results = store.search("indemnification defense patent", doc_id="doc1", top_k=2)
    assert len(results) >= 1
    assert results[0][0].id == "c1"
    assert results[0][1] > 0.3

    # Search with document filter
    results_doc2 = store.search("revenue million", doc_id="doc2")
    assert len(results_doc2) == 1
    assert results_doc2[0][0].id == "c3"

    # Delete doc
    store.delete_doc("doc1")
    remaining = store.get_chunks_by_doc("doc1")
    assert len(remaining) == 0
    assert len(store.get_chunks_by_doc("doc2")) == 1

def test_zero_match_returns_empty(tmp_path):
    db_file = tmp_path / "test_empty.db"
    store = LocalVectorStore(db_path=db_file)
    store.add_chunks([
        DocumentChunk(
            id="c1",
            doc_id="docA",
            page_number=1,
            chunk_index=0,
            content="Alpha beta gamma delta obligations.",
            token_count=5
        )
    ])
    # Unrelated query with zero matching tokens
    results = store.search("quantum celestial supernova", doc_id="docA")
    assert len(results) == 0
