import json
import logging
from typing import List, Optional, Any
from app.models.document import DocumentChunk
from app.models.audit import LegalContractAudit, FinancialReportAudit, CustomAudit
from app.services.ai.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._model = "gpt-4o-mini"
        self._client = None
        if self._api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI Client: {e}")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    async def audit_legal(self, document_text: str, chunks: List[DocumentChunk]) -> LegalContractAudit:
        if not self._client:
            raise RuntimeError("OpenAI Client is not initialized. Please configure OPENAI_API_KEY.")

        from app.core.security import build_secure_audit_prompt
        system_instruction = "You are a Senior Legal Tech Auditor. Analyze this contract and output a JSON matching the requested schema."
        prompt = build_secure_audit_prompt(system_instruction, document_text, max_chars=30000)

        try:
            response = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format=LegalContractAudit
            )
            parsed = response.choices[0].message.parsed
            if not parsed:
                raise RuntimeError("OpenAI returned an empty or unparseable legal audit response.")
            return parsed
        except Exception as e:
            logger.error(f"OpenAI legal audit error: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

    async def audit_financial(self, document_text: str, chunks: List[DocumentChunk]) -> FinancialReportAudit:
        if not self._client:
            raise RuntimeError("OpenAI Client is not initialized. Please configure OPENAI_API_KEY.")

        from app.core.security import build_secure_audit_prompt
        system_instruction = "You are an Executive Financial Auditor. Audit this report and output a JSON matching the requested schema."
        prompt = build_secure_audit_prompt(system_instruction, document_text, max_chars=30000)

        try:
            response = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format=FinancialReportAudit
            )
            parsed = response.choices[0].message.parsed
            if not parsed:
                raise RuntimeError("OpenAI returned an empty or unparseable financial audit response.")
            return parsed
        except Exception as e:
            logger.error(f"OpenAI financial audit error: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

    async def audit_custom(self, document_text: str, chunks: List[DocumentChunk], custom_prompt: Optional[str] = None) -> CustomAudit:
        if not self._client:
            raise RuntimeError("OpenAI Client is not initialized. Please configure OPENAI_API_KEY.")

        from app.core.security import build_secure_audit_prompt
        rule_instruction = custom_prompt or "Audit the document for compliance and risk."
        system_instruction = f"Custom audit instructions: {rule_instruction}"
        prompt = build_secure_audit_prompt(system_instruction, document_text, max_chars=30000)

        try:
            response = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                response_format=CustomAudit
            )
            parsed = response.choices[0].message.parsed
            if not parsed:
                raise RuntimeError("OpenAI returned an empty or unparseable custom audit response.")
            return parsed
        except Exception as e:
            logger.error(f"OpenAI custom audit error: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

    async def chat(self, question: str, context_chunks: List[DocumentChunk]) -> str:
        if not self._client:
            raise RuntimeError("OpenAI Client is not initialized. Please configure OPENAI_API_KEY.")

        from app.core.security import build_secure_rag_prompt
        snippets = [
            f"[Page {c.page_number} | Section: {c.section or 'General'}]: {c.content}"
            for c in context_chunks
        ]
        prompt = build_secure_rag_prompt(question, snippets)

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages
            )
            return response.choices[0].message.content or "No response generated."
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise RuntimeError(f"OpenAI API error during chat: {str(e)}") from e

    async def compare_documents(
        self,
        doc1_id: str,
        doc1_name: str,
        doc1_text: str,
        doc1_audit: Optional[Any],
        doc2_id: str,
        doc2_name: str,
        doc2_text: str,
        doc2_audit: Optional[Any],
        doc_type: Any
    ) -> Any:
        from app.models.comparison import ComparativeAuditResult
        from app.services.ai.mock_provider import MockProvider

        if not self._client:
            return await MockProvider().compare_documents(
                doc1_id, doc1_name, doc1_text, doc1_audit,
                doc2_id, doc2_name, doc2_text, doc2_audit, doc_type
            )

        comparison_prompt = (
            f"You are a Senior Legal Counsel and Enterprise Auditor. Compare the following two documents in detail.\n"
            f"DOCUMENT 1 (Baseline: {doc1_name}):\n{doc1_text[:20000]}\n\n"
            f"DOCUMENT 2 (Revision: {doc2_name}):\n{doc2_text[:20000]}\n\n"
            f"Perform a comprehensive redline comparison: identify added, modified, or removed clauses, "
            f"calculate the risk delta, evaluate commercial impact, and provide renegotiation strategies."
        )

        try:
            completion = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": "You are an expert contract auditor and corporate risk analyst."},
                    {"role": "user", "content": comparison_prompt}
                ],
                response_format=ComparativeAuditResult
            )
            result = completion.choices[0].message.parsed
            result.doc1_id = doc1_id
            result.doc1_name = doc1_name
            result.doc2_id = doc2_id
            result.doc2_name = doc2_name
            result.provider_used = self.provider_name
            result.model_used = self.model_name
            return result
        except Exception as e:
            logger.warning(f"OpenAI comparative audit error ({e}), falling back to deterministic comparison.")
            return await MockProvider().compare_documents(
                doc1_id, doc1_name, doc1_text, doc1_audit,
                doc2_id, doc2_name, doc2_text, doc2_audit, doc_type
            )
