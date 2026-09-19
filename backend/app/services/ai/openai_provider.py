import json
import logging
from typing import List, Optional
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
