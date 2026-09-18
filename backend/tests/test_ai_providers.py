import pytest
from app.models.document import DocumentChunk
from app.services.ai.mock_provider import MockProvider
from app.services.ai.factory import LLMFactory

@pytest.mark.asyncio
async def test_mock_provider_legal():
    provider = MockProvider()
    doc_text = """
    AGREEMENT between Apex Global Inc and Beta Solutions LLC.
    Governed by the laws of Delaware.
    Either party may terminate upon 45 days prior written notice.
    Customer agrees to defend and indemnify Provider.
    Liability shall not exceed $500,000.
    """
    chunks = [DocumentChunk(id="c1", doc_id="d1", page_number=1, chunk_index=0, content=doc_text)]
    audit = await provider.audit_legal(doc_text, chunks)

    assert "Apex Global Inc" in audit.parties or len(audit.parties) >= 2
    assert audit.overall_risk_score > 0
    assert len(audit.key_findings) >= 2
    assert any("Indemnification" in f.category for f in audit.key_findings)
    assert len(audit.risk_matrix) >= 3

@pytest.mark.asyncio
async def test_mock_provider_financial():
    provider = MockProvider()
    doc_text = """
    CONSOLIDATED REPORT.
    Total Revenue: $250 Million.
    Net Income: $35 Million.
    Operating margin is 14%. Independent auditor opinion is Unqualified.
    """
    chunks = [DocumentChunk(id="c1", doc_id="d1", page_number=1, chunk_index=0, content=doc_text)]
    audit = await provider.audit_financial(doc_text, chunks)

    assert audit.total_revenue is not None
    assert audit.auditor_opinion is not None
    assert len(audit.key_findings) >= 1
    assert len(audit.risk_matrix) >= 1

@pytest.mark.asyncio
async def test_mock_provider_chat():
    provider = MockProvider()
    chunks = [
        DocumentChunk(
            id="c1",
            doc_id="d1",
            page_number=3,
            chunk_index=0,
            content="Section 7: In no event shall liability exceed $1,000,000.",
            section="Section 7"
        )
    ]
    answer = await provider.chat("What is the liability cap?", chunks)
    assert "Page 3" in answer
    assert "$1,000,000" in answer

def test_llm_factory_list():
    providers = LLMFactory.list_providers()
    assert len(providers) == 4
    provider_ids = [p["id"] for p in providers]
    assert "gemini" in provider_ids
    assert "openai" in provider_ids
    assert "ollama" in provider_ids
    assert "mock" in provider_ids

@pytest.mark.asyncio
async def test_mock_provider_custom():
    provider = MockProvider()
    doc_text = "Standard Operating Procedure. Must comply with ISO 27001 and NIST 800-53."
    chunks = [DocumentChunk(id="c1", doc_id="d1", page_number=1, chunk_index=0, content=doc_text)]
    custom_audit = await provider.audit_custom(doc_text, chunks, "Verify ISO 27001 certifications")
    assert "ISO 27001" in custom_audit.audit_name
    assert custom_audit.overall_risk_score == 25
    assert len(custom_audit.key_findings) >= 1
    assert "extracted_fields" in custom_audit.model_dump()

def test_provider_classes_configuration():
    from app.services.ai.gemini_provider import GeminiProvider
    from app.services.ai.openai_provider import OpenAIProvider
    from app.services.ai.ollama_provider import OllamaProvider

    gemini = GeminiProvider(api_key="mock_key")
    assert gemini.provider_name == "gemini"
    assert gemini.model_name == "gemini-2.5-flash"

    openai = OpenAIProvider(api_key="mock_key")
    assert openai.provider_name == "openai"
    assert openai.model_name == "gpt-4o-mini"

    ollama = OllamaProvider()
    assert ollama.provider_name == "ollama"
    assert ollama.model_name == "llama3"
