import json
import logging
from typing import List, Optional
from app.models.document import DocumentChunk
from app.models.audit import LegalContractAudit, FinancialReportAudit, CustomAudit
from app.services.ai.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = "gemini-2.5-flash"
        self._client = None
        if self._api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    async def audit_legal(self, document_text: str, chunks: List[DocumentChunk]) -> LegalContractAudit:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        from google.genai import types

        prompt = (
            "You are a Senior Legal Tech Auditor and General Counsel. Analyze the following legal agreement thoroughly. "
            "Extract parties, dates, jurisdiction, termination clauses, liability caps, restrictive covenants, "
            "and identify key legal risks and exposure points. Provide an objective risk score (0-100) and actionable recommendations.\n\n"
            f"DOCUMENT CONTENT:\n{document_text[:35000]}"
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=LegalContractAudit.model_json_schema()
                )
            )
            return LegalContractAudit.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini legal audit failed: {e}")
            raise RuntimeError(f"Gemini API error during legal audit: {str(e)}") from e

    async def audit_financial(self, document_text: str, chunks: List[DocumentChunk]) -> FinancialReportAudit:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        from google.genai import types

        prompt = (
            "You are an Executive Financial Auditor and CPA. Audit the following financial report. "
            "Extract company name, reporting period, revenue, net income, margins, debt ratios, auditor opinions, "
            "and assess fiscal risks, off-balance sheet liabilities, and going concern indicators. "
            "Provide an overall risk score (0-100) and an executive risk breakdown.\n\n"
            f"DOCUMENT CONTENT:\n{document_text[:35000]}"
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=FinancialReportAudit.model_json_schema()
                )
            )
            return FinancialReportAudit.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini financial audit failed: {e}")
            raise RuntimeError(f"Gemini API error during financial audit: {str(e)}") from e

    async def audit_custom(self, document_text: str, chunks: List[DocumentChunk], custom_prompt: Optional[str] = None) -> CustomAudit:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        from google.genai import types

        rule_instruction = custom_prompt or "Audit the document for compliance and risk according to standard corporate standards."
        prompt = (
            f"You are a specialized compliance auditor. Execute the following custom audit rules:\n{rule_instruction}\n\n"
            f"DOCUMENT CONTENT:\n{document_text[:35000]}"
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=CustomAudit.model_json_schema()
                )
            )
            return CustomAudit.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini custom audit failed: {e}")
            raise RuntimeError(f"Gemini API error during custom audit: {str(e)}") from e

    async def chat(self, question: str, context_chunks: List[DocumentChunk]) -> str:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        context_text = "\n\n".join([
            f"[Page {c.page_number} | Section: {c.section or 'General'}]: {c.content}"
            for c in context_chunks
        ])

        prompt = (
            "You are DocAudit AI assistant. Answer the user's question strictly using the provided context passages. "
            "Cite page numbers where relevant. If the answer is not in the context, explicitly indicate that.\n\n"
            f"CONTEXT:\n{context_text}\n\n"
            f"QUESTION: {question}\n\n"
            "ANSWER:"
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt
            )
            return response.text or "No response generated."
        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            raise RuntimeError(f"Gemini API error during chat: {str(e)}") from e
