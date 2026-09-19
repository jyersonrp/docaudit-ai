import json
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.document import DocumentChunk
from app.models.audit import LegalContractAudit
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.factory import LLMFactory

@pytest.mark.asyncio
async def test_ollama_check_connection_online_and_model_found():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama3:latest", "model": "llama3:latest"},
            {"name": "mistral:7b", "model": "mistral:7b"}
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        status = await OllamaProvider.check_connection(base_url="http://localhost:11434", model="llama3")

    assert status["online"] is True
    assert status["model_installed"] is True
    assert "llama3:latest" in status["installed_models"]
    assert "ready" in status["message"].lower()

@pytest.mark.asyncio
async def test_ollama_check_connection_model_missing():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "mistral:7b", "model": "mistral:7b"},
            {"name": "qwen2.5:latest", "model": "qwen2.5:latest"}
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        status = await OllamaProvider.check_connection(base_url="http://localhost:11434", model="llama3")

    assert status["online"] is True
    assert status["model_installed"] is False
    assert "ollama run llama3" in status["message"]

@pytest.mark.asyncio
async def test_ollama_check_connection_offline():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        status = await OllamaProvider.check_connection(base_url="http://localhost:11434", model="llama3")

    assert status["online"] is False
    assert status["model_installed"] is False
    assert "unreachable" in status["message"].lower()
    assert "ollama serve" in status["message"]

def test_ollama_check_connection_sync():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": "llama3:8b"}]
    }

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = mock_response
        status = OllamaProvider.check_connection_sync(base_url="http://localhost:11434", model="llama3")

    assert status["online"] is True
    assert status["model_installed"] is True

def test_parse_json_response_variations():
    # 1. Plain valid JSON
    res1 = OllamaProvider._parse_json_response('{"test": 123, "name": "docaudit"}')
    assert res1 == {"test": 123, "name": "docaudit"}

    # 2. Markdown fenced JSON ```json ... ```
    res2 = OllamaProvider._parse_json_response('```json\n{"score": 95, "status": "pass"}\n```')
    assert res2 == {"score": 95, "status": "pass"}

    # 3. Conversational intro and outro around markdown
    res3 = OllamaProvider._parse_json_response(
        'Here is the requested schema response:\n```json\n{"parties": ["Alpha", "Beta"]}\n```\nLet me know if you need more.'
    )
    assert res3 == {"parties": ["Alpha", "Beta"]}

    # 4. Embedded JSON without markdown fences
    res4 = OllamaProvider._parse_json_response('Some explanation before {"val": 42} and after.')
    assert res4 == {"val": 42}

    # 5. Invalid JSON raises ValueError
    with pytest.raises(ValueError, match="Could not parse valid JSON"):
        OllamaProvider._parse_json_response("This is completely plain text with no json.")

    # 6. Empty string raises ValueError
    with pytest.raises(ValueError, match="empty response"):
        OllamaProvider._parse_json_response("   ")

@pytest.mark.asyncio
async def test_ollama_generate_json_connection_error():
    provider = OllamaProvider(base_url="http://localhost:11434")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("[WinError 10061] No connection")
        with pytest.raises(RuntimeError) as exc_info:
            await provider._generate_json("test prompt", {"type": "object"})

    assert "unreachable at http://localhost:11434" in str(exc_info.value)
    assert "ollama serve" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ollama_generate_json_model_not_found_404():
    provider = OllamaProvider(base_url="http://localhost:11434")

    req = httpx.Request("POST", "http://localhost:11434/api/chat")
    res = httpx.Response(404, request=req, text='{"error":"model \'llama3\' not found, try pulling it first"}')

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = res
        with pytest.raises(RuntimeError) as exc_info:
            await provider._generate_json("test prompt", {"type": "object"})

    assert "model 'llama3' is not found or not installed" in str(exc_info.value)
    assert "ollama run llama3" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ollama_generate_json_timeout():
    provider = OllamaProvider(base_url="http://localhost:11434", timeout=30.0)

    req = httpx.Request("POST", "http://localhost:11434/api/chat")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ReadTimeout("Read timed out", request=req)
        with pytest.raises(RuntimeError) as exc_info:
            await provider._generate_json("test prompt", {"type": "object"})

    assert "timed out after 30.0s" in str(exc_info.value)
    assert "OLLAMA_TIMEOUT" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ollama_audit_legal_success():
    provider = OllamaProvider(base_url="http://localhost:11434")

    valid_payload_return = {
        "parties": ["Apex Global", "Beta Solutions"],
        "effective_date": "2024-01-01",
        "governing_law": "Delaware",
        "overall_risk_score": 35,
        "overall_risk_level": "MEDIUM",
        "executive_summary": "Comprehensive legal audit summary.",
        "key_findings": [
            {
                "id": "FIND-001",
                "category": "Indemnification",
                "title": "Mutual Indemnification",
                "description": "Mutual indemnification clause detected.",
                "severity": "MEDIUM",
                "impact": "Shared liability for claims.",
                "recommendation": "Review caps on indemnity.",
                "page_number": 1
            }
        ],
        "risk_matrix": [
            {
                "dimension": "Legal Liability",
                "score": 40,
                "level": "MEDIUM",
                "summary": "Standard liability cap applies."
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "role": "assistant",
            "content": f"```json\n{json.dumps(valid_payload_return)}\n```"
        }
    }

    chunks = [DocumentChunk(id="c1", doc_id="d1", page_number=1, chunk_index=0, content="Test contract content")]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        audit = await provider.audit_legal("Test contract text", chunks)

        # Inspect payload passed to post
        call_kwargs = mock_post.call_args.kwargs
        assert "json" in call_kwargs
        sent_payload = call_kwargs["json"]
        assert sent_payload["model"] == "llama3"
        assert sent_payload["format"] == "json"
        assert sent_payload["stream"] is False
        assert sent_payload["options"]["num_ctx"] == 8192
        assert sent_payload["options"]["temperature"] == 0.1

    assert isinstance(audit, LegalContractAudit)
    assert "Apex Global" in audit.parties
    assert audit.overall_risk_score == 35

@pytest.mark.asyncio
async def test_ollama_chat_success():
    provider = OllamaProvider(base_url="http://localhost:11434")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "role": "assistant",
            "content": "The liability cap under Section 7 is $500,000 as stated on Page 1."
        }
    }

    chunks = [DocumentChunk(id="c1", doc_id="d1", page_number=1, chunk_index=0, content="Liability cap $500k")]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        ans = await provider.chat("What is the liability cap?", chunks)

    assert "$500,000" in ans
    assert "Page 1" in ans

@pytest.mark.asyncio
async def test_factory_list_providers_dynamic():
    # Test when Ollama is offline
    with patch.object(LLMFactory, "check_ollama_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "online": False,
            "model_installed": False,
            "installed_models": [],
            "message": "Ollama server is unreachable at http://localhost:11434."
        }
        providers = await LLMFactory.list_providers_async()
        ollama_p = next(p for p in providers if p["id"] == "ollama")
        assert ollama_p["available"] is False
        assert ollama_p["online"] is False
        assert "unreachable" in ollama_p["status_message"].lower()

    # Test when Ollama is online with llama3
    with patch.object(LLMFactory, "check_ollama_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {
            "online": True,
            "model_installed": True,
            "installed_models": ["llama3:latest"],
            "message": "Ollama is running and 'llama3' is ready."
        }
        providers = await LLMFactory.list_providers_async()
        ollama_p = next(p for p in providers if p["id"] == "ollama")
        assert ollama_p["available"] is True
        assert ollama_p["online"] is True
        assert ollama_p["model_installed"] is True
        assert "ready" in ollama_p["status_message"].lower()

def test_chat_endpoint_ollama_fallback_with_diagnostic():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.workers.audit_worker import AuditWorker
    from app.models.document import DocumentMetadata, DocumentStatus, DocumentType
    from datetime import datetime, timezone
    from app.services.vector.store import vector_store

    meta = DocumentMetadata(
        id="test_chat_doc",
        filename="contract.pdf",
        file_type="pdf",
        file_size=1024,
        total_pages=1,
        total_chunks=1,
        status=DocumentStatus.COMPLETED,
        status_message="Audit complete",
        progress=100,
        audit_type=DocumentType.LEGAL,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        error=None
    )
    AuditWorker.save_metadata(meta)

    chunk = DocumentChunk(id="c_test_1", doc_id="test_chat_doc", page_number=1, chunk_index=0, content="Indemnity cap is $250,000.")
    vector_store.add_chunks([chunk])

    client = TestClient(app)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        res = client.post("/api/v1/chat/query", json={
            "doc_id": "test_chat_doc",
            "question": "What is the indemnity cap?",
            "top_k": 3,
            "provider": "ollama"
        })

    assert res.status_code == 200
    data = res.json()
    assert "fallback: mock" in data["provider_used"]
    assert "⚠️ Note: OLLAMA unavailable" in data["answer"]
    assert "ollama serve" in data["answer"]

@pytest.mark.asyncio
async def test_audit_worker_ollama_failure_diagnostic(tmp_path):
    from app.workers.audit_worker import AuditWorker
    from app.models.document import DocumentMetadata, DocumentStatus, DocumentType
    from datetime import datetime, timezone

    doc_id = "test_audit_worker_ollama"
    meta = DocumentMetadata(
        id=doc_id,
        filename="test.txt",
        file_type="txt",
        file_size=100,
        total_pages=0,
        total_chunks=0,
        status=DocumentStatus.PENDING,
        status_message="Queued",
        progress=0,
        audit_type=DocumentType.LEGAL,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        error=None
    )
    AuditWorker.save_metadata(meta)

    test_file = tmp_path / "test.txt"
    test_file.write_text("This is an agreement between Company A and Company B.", encoding="utf-8")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("[WinError 10061] No connection")
        await AuditWorker.process_document_pipeline(
            doc_id=doc_id,
            file_path=test_file,
            audit_type=DocumentType.LEGAL,
            provider_name="ollama"
        )

    updated_meta = AuditWorker.get_metadata(doc_id)
    assert updated_meta is not None
    assert updated_meta.status == DocumentStatus.FAILED
    assert "unreachable at http://localhost:11434" in updated_meta.error
    assert "ollama serve" in updated_meta.error

def test_ollama_clean_url():
    assert OllamaProvider._clean_url("http://localhost:11434") == "http://localhost:11434"
    assert OllamaProvider._clean_url("http://localhost:11434/") == "http://localhost:11434"
    assert OllamaProvider._clean_url("http://localhost:11434/api") == "http://localhost:11434"
    assert OllamaProvider._clean_url("http://localhost:11434/api/") == "http://localhost:11434"
    assert OllamaProvider._clean_url("http://remote.host:11434/api") == "http://remote.host:11434"

def test_parse_json_response_trailing_commas_and_newlines():
    # Trailing comma in object and array
    raw_trailing = '{"title": "Contract", "parties": ["Apex", "Beta",], "score": 80,}'
    res = OllamaProvider._parse_json_response(raw_trailing)
    assert res["title"] == "Contract"
    assert res["parties"] == ["Apex", "Beta"]
    assert res["score"] == 80

    # Unescaped newline inside string literal (strict=False)
    raw_newline = '{"summary": "Line 1\nLine 2 with unescaped newline"}'
    res2 = OllamaProvider._parse_json_response(raw_newline)
    assert "Line 1\nLine 2" in res2["summary"]

def test_normalize_audit_dict_legal():
    raw = {
        "parties": "Solo Corporation", # string instead of list
        "overall_risk_score": "75%",   # string with percent
        "overall_risk_level": "high",   # lowercase enum
        "key_findings": [
            {
                "category": "Liability",
                "title": "Uncapped Liability",
                "description": "Risk detected",
                "severity": "medium",   # lowercase enum
                "impact": "High exposure",
                "recommendation": "Cap it"
                # id missing
            }
        ],
        "risk_matrix": [
            {
                "dimension": "Legal",
                "score": "80",
                "level": "high",       # lowercase enum
                "summary": "Legal liability"
            }
        ]
    }
    normalized = OllamaProvider._normalize_audit_dict(raw, audit_type="legal")
    assert normalized["overall_risk_score"] == 75
    assert normalized["overall_risk_level"] == "HIGH"
    assert normalized["key_findings"][0]["id"] == "FIND-001"
    assert normalized["key_findings"][0]["severity"] == "MEDIUM"
    assert normalized["risk_matrix"][0]["level"] == "HIGH"
    assert "compliance_checklist" in normalized

    # Pydantic validation must succeed with normalized data
    audit = LegalContractAudit.model_validate(normalized)
    assert audit.overall_risk_score == 75
    assert audit.overall_risk_level.value == "HIGH"
    assert audit.key_findings[0].id == "FIND-001"

@pytest.mark.asyncio
async def test_ollama_audit_legal_with_lowercase_enums():
    """Verify that llama3 output with lowercase/mixed-case enums validates seamlessly."""
    provider = OllamaProvider(base_url="http://localhost:11434")

    llama3_output = {
        "parties": ["Apex Global", "Beta Solutions"],
        "overall_risk_score": 40,
        "overall_risk_level": "medium",  # lowercase
        "executive_summary": "Summary text",
        "key_findings": [
            {
                "id": "FIND-001",
                "category": "Indemnification",
                "title": "Mutual Indemnity",
                "description": "Mutual indemnification clause detected.",
                "severity": "medium",     # lowercase
                "impact": "Shared liability",
                "recommendation": "Review caps",
                "page_number": 1
            }
        ],
        "risk_matrix": [
            {
                "dimension": "Legal Liability",
                "score": 40,
                "level": "medium",        # lowercase
                "summary": "Standard liability cap applies."
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "role": "assistant",
            "content": json.dumps(llama3_output)
        }
    }

    chunks = [DocumentChunk(id="c1", doc_id="d1", page_number=1, chunk_index=0, content="Test")]
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        audit = await provider.audit_legal("Contract text", chunks)

    assert audit.overall_risk_level.value == "MEDIUM"
    assert audit.key_findings[0].severity.value == "MEDIUM"
    assert audit.risk_matrix[0].level.value == "MEDIUM"

def test_factory_auto_selects_ollama_when_ready():
    from app.core.config import settings
    orig_gemini = settings.GEMINI_API_KEY
    orig_openai = settings.OPENAI_API_KEY
    orig_default = settings.DEFAULT_LLM_PROVIDER
    try:
        settings.GEMINI_API_KEY = None
        settings.OPENAI_API_KEY = None
        settings.DEFAULT_LLM_PROVIDER = "auto"
        LLMFactory._cached_providers.clear()

        with patch.object(LLMFactory, "check_ollama_status_sync") as mock_status:
            mock_status.return_value = {"online": True, "model_installed": True}
            provider = LLMFactory.get_provider(None)
            assert provider.provider_name == "ollama"
    finally:
        settings.GEMINI_API_KEY = orig_gemini
        settings.OPENAI_API_KEY = orig_openai
        settings.DEFAULT_LLM_PROVIDER = orig_default
        LLMFactory._cached_providers.clear()

def test_factory_default_ollama_falls_back_to_mock_when_offline():
    from app.core.config import settings
    orig_default = settings.DEFAULT_LLM_PROVIDER
    try:
        settings.DEFAULT_LLM_PROVIDER = "ollama"
        LLMFactory._cached_providers.clear()

        with patch.object(LLMFactory, "check_ollama_status_sync") as mock_status:
            mock_status.return_value = {"online": False, "model_installed": False}
            provider = LLMFactory.get_provider(None)
            assert provider.provider_name == "mock"
    finally:
        settings.DEFAULT_LLM_PROVIDER = orig_default
        LLMFactory._cached_providers.clear()


