import json
import logging
import httpx
from typing import List, Optional
from app.models.document import DocumentChunk
from app.models.audit import LegalContractAudit, FinancialReportAudit, CustomAudit
from app.services.ai.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: Optional[str] = None):
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = "llama3"

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    async def _generate_json(self, prompt: str, schema_dict: dict) -> dict:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": f"You must reply ONLY in valid JSON matching this schema: {json.dumps(schema_dict)}"},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_content = data["message"]["content"].strip()
            if raw_content.startswith("```"):
                import re
                raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.IGNORECASE)
                raw_content = re.sub(r"\s*```$", "", raw_content)
            return json.loads(raw_content.strip())

    async def audit_legal(self, document_text: str, chunks: List[DocumentChunk]) -> LegalContractAudit:
        from app.core.security import build_secure_audit_prompt
        prompt = build_secure_audit_prompt("Audit this legal contract and return the exact JSON schema:", document_text, max_chars=25000)
        result_json = await self._generate_json(prompt, LegalContractAudit.model_json_schema())
        return LegalContractAudit.model_validate(result_json)

    async def audit_financial(self, document_text: str, chunks: List[DocumentChunk]) -> FinancialReportAudit:
        from app.core.security import build_secure_audit_prompt
        prompt = build_secure_audit_prompt("Audit this financial report and return the exact JSON schema:", document_text, max_chars=25000)
        result_json = await self._generate_json(prompt, FinancialReportAudit.model_json_schema())
        return FinancialReportAudit.model_validate(result_json)

    async def audit_custom(self, document_text: str, chunks: List[DocumentChunk], custom_prompt: Optional[str] = None) -> CustomAudit:
        from app.core.security import build_secure_audit_prompt
        rule_desc = custom_prompt or "Standard compliance audit"
        prompt = build_secure_audit_prompt(f"Perform custom audit '{rule_desc}' on document:", document_text, max_chars=25000)
        result_json = await self._generate_json(prompt, CustomAudit.model_json_schema())
        return CustomAudit.model_validate(result_json)

    async def chat(self, question: str, context_chunks: List[DocumentChunk]) -> str:
        url = f"{self._base_url}/api/chat"
        from app.core.security import build_secure_rag_prompt
        snippets = [f"[Page {c.page_number}]: {c.content}" for c in context_chunks]
        prompt = build_secure_rag_prompt(question, snippets)
        payload = {
            "model": self._model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["message"]["content"]
