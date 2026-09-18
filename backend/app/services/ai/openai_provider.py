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

        prompt = (
            "You are a Senior Legal Tech Auditor. Analyze this contract and output a JSON matching the requested schema.\n\n"
            f"DOCUMENT:\n{document_text[:30000]}"
        )

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

        prompt = (
            "You are an Executive Financial Auditor. Audit this report and output a JSON matching the requested schema.\n\n"
            f"DOCUMENT:\n{document_text[:30000]}"
        )

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

        rule_instruction = custom_prompt or "Audit the document for compliance and risk."
        prompt = (
            f"Custom audit instructions: {rule_instruction}\n\n"
            f"DOCUMENT:\n{document_text[:30000]}"
        )

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

        context_text = "\n\n".join([
            f"[Page {c.page_number} | Section: {c.section or 'General'}]: {c.content}"
            for c in context_chunks
        ])

        messages = [
            {"role": "system", "content": "You are DocAudit AI assistant. Answer using the provided context and cite page numbers."},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}
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
