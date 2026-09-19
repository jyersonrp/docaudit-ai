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
        self._model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
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

    async def _generate_with_retry(self, contents, config=None, max_retries: int = 3):
        import asyncio
        models_to_try = [
            self._model,
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ]
        candidate_models = [m for m in dict.fromkeys(models_to_try) if m]
        last_error = None

        for model_name in candidate_models:
            for attempt in range(max_retries):
                try:
                    kwargs = {"model": model_name, "contents": contents}
                    if config:
                        kwargs["config"] = config
                    res = await self._client.aio.models.generate_content(**kwargs)
                    self._model = model_name
                    return res
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    if "404" in err_str or "not_found" in err_str or "no longer available" in err_str:
                        logger.warning(f"Gemini model {model_name} unavailable (404), switching to fallback: {e}")
                        break
                    elif "503" in err_str or "unavailable" in err_str or "high demand" in err_str or "429" in err_str:
                        wait_sec = 1.5 * (attempt + 1)
                        logger.warning(f"Gemini {model_name} busy ({err_str[:60]}), retrying in {wait_sec}s...")
                        await asyncio.sleep(wait_sec)
                    else:
                        break

        err_msg = str(last_error)
        if "503" in err_msg.lower() or "high demand" in err_msg.lower():
            raise RuntimeError(
                "Google Gemini free tier is currently experiencing peak traffic (503 High Demand). "
                "Please retry in a moment, or click 'Run Heuristic Engine (Offline)' for an instant audit."
            ) from last_error
        elif "429" in err_msg.lower():
            raise RuntimeError(
                "Google Gemini rate limit reached (429). "
                "Please wait 30 seconds and retry, or use the Heuristic Engine."
            ) from last_error

        raise RuntimeError(f"Gemini API error: {err_msg}") from last_error

    async def audit_legal(self, document_text: str, chunks: List[DocumentChunk]) -> LegalContractAudit:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        from google.genai import types
        from app.core.security import build_secure_audit_prompt

        system_instruction = (
            "You are a Senior Legal Tech Auditor and General Counsel. Analyze the following legal agreement thoroughly. "
            "Extract parties, dates, jurisdiction, termination clauses, liability caps, restrictive covenants, "
            "and identify key legal risks and exposure points. Provide an objective risk score (0-100) and actionable recommendations."
        )
        prompt = build_secure_audit_prompt(system_instruction, document_text, max_chars=35000)

        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=LegalContractAudit.model_json_schema()
            )
            response = await self._generate_with_retry(contents=prompt, config=config)
            return LegalContractAudit.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini legal audit failed: {e}")
            raise RuntimeError(f"Gemini API error during legal audit: {str(e)}") from e

    async def audit_financial(self, document_text: str, chunks: List[DocumentChunk]) -> FinancialReportAudit:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        from google.genai import types
        from app.core.security import build_secure_audit_prompt

        system_instruction = (
            "You are an Executive Financial Auditor and CPA. Audit the following financial report. "
            "Extract company name, reporting period, revenue, net income, margins, debt ratios, auditor opinions, "
            "and assess fiscal risks, off-balance sheet liabilities, and going concern indicators. "
            "Provide an overall risk score (0-100) and an executive risk breakdown."
        )
        prompt = build_secure_audit_prompt(system_instruction, document_text, max_chars=35000)

        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=FinancialReportAudit.model_json_schema()
            )
            response = await self._generate_with_retry(contents=prompt, config=config)
            return FinancialReportAudit.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini financial audit failed: {e}")
            raise RuntimeError(f"Gemini API error during financial audit: {str(e)}") from e

    async def audit_custom(self, document_text: str, chunks: List[DocumentChunk], custom_prompt: Optional[str] = None) -> CustomAudit:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        from google.genai import types
        from app.core.security import build_secure_audit_prompt

        rule_instruction = custom_prompt or "Audit the document for compliance and risk according to standard corporate standards."
        system_instruction = f"You are a specialized compliance auditor. Execute the following custom audit rules:\n{rule_instruction}"
        prompt = build_secure_audit_prompt(system_instruction, document_text, max_chars=35000)

        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=CustomAudit.model_json_schema()
            )
            response = await self._generate_with_retry(contents=prompt, config=config)
            return CustomAudit.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini custom audit failed: {e}")
            raise RuntimeError(f"Gemini API error during custom audit: {str(e)}") from e

    async def chat(self, question: str, context_chunks: List[DocumentChunk]) -> str:
        if not self._client:
            raise RuntimeError("Gemini Client is not initialized. Please configure GEMINI_API_KEY.")

        from app.core.security import build_secure_rag_prompt
        snippets = [
            f"[Page {c.page_number} | Section: {c.section or 'General'}]: {c.content}"
            for c in context_chunks
        ]
        prompt = build_secure_rag_prompt(question, snippets)

        try:
            response = await self._generate_with_retry(contents=prompt)
            return response.text or "No response generated."
        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            raise RuntimeError(f"Gemini API error during chat: {str(e)}") from e
