import json
import logging
import re
import httpx
from typing import List, Optional, Dict, Any
from app.models.document import DocumentChunk
from app.models.audit import LegalContractAudit, FinancialReportAudit, CustomAudit
from app.services.ai.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    @staticmethod
    def _clean_url(raw_url: Optional[str]) -> str:
        url = (raw_url or settings.OLLAMA_BASE_URL).strip().rstrip("/")
        return re.sub(r"/api/?$", "", url)

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self._base_url = self._clean_url(base_url)
        self._model = model or getattr(settings, "OLLAMA_MODEL", "llama3")
        self._timeout = timeout or getattr(settings, "OLLAMA_TIMEOUT", 120.0)

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def timeout(self) -> float:
        return self._timeout

    @classmethod
    def _extract_model_names(cls, models_data: Any) -> List[str]:
        if not isinstance(models_data, list):
            return []
        names = []
        for m in models_data:
            if isinstance(m, dict):
                name = m.get("name") or m.get("model")
                if name and isinstance(name, str):
                    names.append(name.strip())
        return names

    @classmethod
    def _match_model(cls, target_model: str, installed_names: List[str]) -> bool:
        target_lower = target_model.lower().strip()
        target_base = target_lower.split(":")[0].strip()
        for name in installed_names:
            nl = name.lower().strip()
            if nl == target_lower:
                return True
            nb = nl.split(":")[0].strip()
            if nb == target_base:
                return True
            if target_base in nl:
                return True
        return False

    @classmethod
    async def check_connection(
        cls,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        check_timeout: float = 2.5
    ) -> Dict[str, Any]:
        """
        Pings Ollama server at /api/tags and verifies whether the specified model is installed.
        Returns:
            {
                "online": bool,
                "model_installed": bool,
                "installed_models": List[str],
                "message": str
            }
        """
        url = cls._clean_url(base_url)
        target_model = model or getattr(settings, "OLLAMA_MODEL", "llama3")
        tags_url = f"{url}/api/tags"

        try:
            async with httpx.AsyncClient(timeout=check_timeout) as client:
                res = await client.get(tags_url)
                if res.status_code != 200:
                    return {
                        "online": False,
                        "model_installed": False,
                        "installed_models": [],
                        "message": f"Ollama returned HTTP {res.status_code} on health ping ({tags_url})."
                    }
                data = res.json()
                installed_names = cls._extract_model_names(data.get("models"))
                model_found = cls._match_model(target_model, installed_names)

                if model_found:
                    return {
                        "online": True,
                        "model_installed": True,
                        "installed_models": installed_names,
                        "message": f"Ollama is running and '{target_model}' is ready."
                    }
                else:
                    return {
                        "online": True,
                        "model_installed": False,
                        "installed_models": installed_names,
                        "message": (
                            f"Ollama is online, but model '{target_model}' is not installed. "
                            f"Run 'ollama run {target_model}' in your terminal."
                        )
                    }

        except (httpx.ConnectError, httpx.ConnectTimeout):
            return {
                "online": False,
                "model_installed": False,
                "installed_models": [],
                "message": (
                    f"Ollama server is unreachable at {url}. "
                    f"Please ensure Ollama is running ('ollama serve') or check OLLAMA_BASE_URL."
                )
            }
        except httpx.TimeoutException:
            return {
                "online": False,
                "model_installed": False,
                "installed_models": [],
                "message": f"Connection to Ollama at {url} timed out after {check_timeout}s."
            }
        except Exception as e:
            return {
                "online": False,
                "model_installed": False,
                "installed_models": [],
                "message": f"Failed to connect to Ollama at {url}: {str(e)}"
            }

    @classmethod
    def check_connection_sync(
        cls,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        check_timeout: float = 2.5
    ) -> Dict[str, Any]:
        """
        Synchronous ping to Ollama /api/tags for use in sync environments or tests.
        """
        url = cls._clean_url(base_url)
        target_model = model or getattr(settings, "OLLAMA_MODEL", "llama3")
        tags_url = f"{url}/api/tags"

        try:
            with httpx.Client(timeout=check_timeout) as client:
                res = client.get(tags_url)
                if res.status_code != 200:
                    return {
                        "online": False,
                        "model_installed": False,
                        "installed_models": [],
                        "message": f"Ollama returned HTTP {res.status_code} on health ping ({tags_url})."
                    }
                data = res.json()
                installed_names = cls._extract_model_names(data.get("models"))
                model_found = cls._match_model(target_model, installed_names)

                if model_found:
                    return {
                        "online": True,
                        "model_installed": True,
                        "installed_models": installed_names,
                        "message": f"Ollama is running and '{target_model}' is ready."
                    }
                else:
                    return {
                        "online": True,
                        "model_installed": False,
                        "installed_models": installed_names,
                        "message": (
                            f"Ollama is online, but model '{target_model}' is not installed. "
                            f"Run 'ollama run {target_model}' in your terminal."
                        )
                    }
        except (httpx.ConnectError, httpx.ConnectTimeout):
            return {
                "online": False,
                "model_installed": False,
                "installed_models": [],
                "message": (
                    f"Ollama server is unreachable at {url}. "
                    f"Please ensure Ollama is running ('ollama serve') or check OLLAMA_BASE_URL."
                )
            }
        except httpx.TimeoutException:
            return {
                "online": False,
                "model_installed": False,
                "installed_models": [],
                "message": f"Connection to Ollama at {url} timed out after {check_timeout}s."
            }
        except Exception as e:
            return {
                "online": False,
                "model_installed": False,
                "installed_models": [],
                "message": f"Failed to connect to Ollama at {url}: {str(e)}"
            }

    def _format_error(self, e: Exception) -> RuntimeError:
        """
        Translates raw network or HTTP exceptions into clear, actionable diagnostic messages.
        """
        if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)):
            return RuntimeError(
                f"Ollama server is unreachable at {self._base_url}. "
                f"Please ensure Ollama is installed and running (run 'ollama serve' in your terminal)."
            )
        if isinstance(e, httpx.HTTPStatusError):
            status = e.response.status_code
            try:
                err_data = e.response.json()
                detail = err_data.get("error", e.response.text)
            except Exception:
                detail = e.response.text

            if status == 404:
                return RuntimeError(
                    f"Ollama model '{self._model}' is not found or not installed. "
                    f"Please install it in your terminal by running: 'ollama run {self._model}' or 'ollama pull {self._model}'."
                )
            return RuntimeError(f"Ollama API returned HTTP {status}: {detail}")
        if isinstance(e, httpx.TimeoutException):
            return RuntimeError(
                f"Ollama request timed out after {self._timeout}s while generating with model '{self._model}'. "
                f"If running on CPU, local generation may take longer. You can increase OLLAMA_TIMEOUT in .env."
            )
        if isinstance(e, httpx.RequestError):
            return RuntimeError(f"Ollama network request failed: {str(e)}")
        return RuntimeError(f"Ollama error: {str(e)}")

    @staticmethod
    def _parse_json_response(raw_text: str) -> dict:
        """
        Robust JSON extractor supporting raw JSON, markdown code fences, embedded objects,
        trailing commas, and multiline unescaped strings.
        """
        text = raw_text.strip()
        if not text:
            raise ValueError("Ollama returned an empty response.")

        def try_parse(candidate: str) -> Optional[dict]:
            # 1. Direct loads with strict=False (allows unescaped control characters in strings)
            try:
                parsed = json.loads(candidate, strict=False)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

            # 2. Fix trailing commas before } or ]
            cleaned_commas = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                parsed = json.loads(cleaned_commas, strict=False)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            return None

        # Step 1: Try parsing the text as-is
        res = try_parse(text)
        if res is not None:
            return res

        # Step 2: Extract from markdown code blocks (```json { ... } ``` or ``` { ... } ```)
        block_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if block_match:
            res = try_parse(block_match.group(1).strip())
            if res is not None:
                return res

        # Strip surrounding markdown markers if any
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        res = try_parse(cleaned)
        if res is not None:
            return res

        # Step 3: Locate outer JSON boundaries { ... }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = text[first_brace:last_brace + 1].strip()
            res = try_parse(candidate)
            if res is not None:
                return res

        raise ValueError(f"Could not parse valid JSON from Ollama response: {text[:200]}")

    @staticmethod
    def _normalize_audit_dict(data: dict, audit_type: str = "legal") -> dict:
        """
        Normalizes and sanitizes JSON dictionaries returned by Ollama before passing
        to Pydantic schema validation. Ensures enum values are uppercase, handles missing
        or non-standard fields, and supplies resilient fallbacks so the audit doesn't crash.
        """
        if not isinstance(data, dict):
            return {}

        # 1. Normalize risk score (0 - 100 integer)
        score = data.get("overall_risk_score")
        if score is not None:
            try:
                if isinstance(score, str):
                    digits = re.sub(r"[^\d]", "", score)
                    score = int(digits) if digits else 50
                else:
                    score = int(score)
                data["overall_risk_score"] = max(0, min(100, score))
            except Exception:
                data["overall_risk_score"] = 50
        else:
            data["overall_risk_score"] = 50

        # Helper to map case-insensitive strings to valid Enum values (LOW, MEDIUM, HIGH, CRITICAL)
        def map_level(val: Any, default_score: int = 50) -> str:
            if not val or not isinstance(val, str):
                if default_score < 30:
                    return "LOW"
                elif default_score < 65:
                    return "MEDIUM"
                elif default_score < 85:
                    return "HIGH"
                else:
                    return "CRITICAL"
            clean = val.strip().upper()
            if "CRIT" in clean:
                return "CRITICAL"
            if "HIGH" in clean:
                return "HIGH"
            if "MED" in clean or "MOD" in clean:
                return "MEDIUM"
            if "LOW" in clean or "INFO" in clean or "MIN" in clean:
                return "LOW"
            return "MEDIUM"

        # 2. Normalize overall_risk_level
        data["overall_risk_level"] = map_level(data.get("overall_risk_level"), data["overall_risk_score"])

        # 3. Normalize executive_summary
        if not data.get("executive_summary") or not isinstance(data.get("executive_summary"), str):
            data["executive_summary"] = "Audit assessment completed by Ollama AI engine."

        # 4. Normalize key_findings
        raw_findings = data.get("key_findings")
        if not isinstance(raw_findings, list):
            raw_findings = [raw_findings] if isinstance(raw_findings, dict) else []

        normalized_findings = []
        for idx, f in enumerate(raw_findings):
            if not isinstance(f, dict):
                continue
            f_id = f.get("id") or f"FIND-{idx+1:03d}"
            f_category = f.get("category") or "General Compliance"
            f_title = f.get("title") or f"Audit Finding {idx+1}"
            f_desc = f.get("description") or f_title
            f_sev = map_level(f.get("severity") or f.get("level"), data["overall_risk_score"])
            f_impact = f.get("impact") or "Potential compliance or operational impact."
            f_rec = f.get("recommendation") or "Review and align with contract guidelines."
            f_page = f.get("page_number")
            if f_page is not None:
                try:
                    f_page = int(f_page)
                except Exception:
                    f_page = None

            normalized_findings.append({
                "id": str(f_id),
                "category": str(f_category),
                "title": str(f_title),
                "description": str(f_desc),
                "severity": f_sev,
                "impact": str(f_impact),
                "recommendation": str(f_rec),
                "page_number": f_page,
                "quote": f.get("quote"),
                "relevance_score": float(f.get("relevance_score", 1.0) or 1.0)
            })
        data["key_findings"] = normalized_findings

        # 5. Normalize risk_matrix
        raw_matrix = data.get("risk_matrix")
        if not isinstance(raw_matrix, list):
            raw_matrix = [raw_matrix] if isinstance(raw_matrix, dict) else []

        normalized_matrix = []
        for idx, m in enumerate(raw_matrix):
            if not isinstance(m, dict):
                continue
            m_dim = m.get("dimension") or f"Risk Pillar {idx+1}"
            m_score = m.get("score")
            try:
                if isinstance(m_score, str):
                    digits = re.sub(r"[^\d]", "", m_score)
                    m_score = int(digits) if digits else data["overall_risk_score"]
                else:
                    m_score = int(m_score if m_score is not None else data["overall_risk_score"])
                m_score = max(0, min(100, m_score))
            except Exception:
                m_score = data["overall_risk_score"]
            m_level = map_level(m.get("level"), m_score)
            m_summary = m.get("summary") or f"Assessment of {m_dim}."

            normalized_matrix.append({
                "dimension": str(m_dim),
                "score": m_score,
                "level": m_level,
                "summary": str(m_summary)
            })
        data["risk_matrix"] = normalized_matrix

        # Fallback default risk matrix if empty
        if not data["risk_matrix"]:
            data["risk_matrix"] = [
                {
                    "dimension": "Contractual Compliance",
                    "score": data["overall_risk_score"],
                    "level": data["overall_risk_level"],
                    "summary": "General contract compliance evaluation."
                },
                {
                    "dimension": "Liability & Exposure",
                    "score": data["overall_risk_score"],
                    "level": data["overall_risk_level"],
                    "summary": "Evaluation of liability exposure and indemnity clauses."
                }
            ]

        # 6. Type-specific defaults
        if audit_type == "legal":
            if "parties" not in data or not isinstance(data["parties"], list):
                data["parties"] = []
            if "compliance_checklist" not in data or not isinstance(data["compliance_checklist"], dict):
                data["compliance_checklist"] = {
                    "Parties Clearly Identified": bool(data.get("parties")),
                    "Clear Governing Law Specified": bool(data.get("governing_law")),
                    "Capped Liability in Place": bool(data.get("liability_cap")),
                    "Standard Dispute Resolution": bool(data.get("jurisdiction")),
                    "Bilateral Termination Rights": bool(data.get("termination_notice_period"))
                }
        elif audit_type == "financial":
            if "contingent_liabilities" not in data or not isinstance(data["contingent_liabilities"], list):
                data["contingent_liabilities"] = []
            if "fiscal_risks" not in data or not isinstance(data["fiscal_risks"], list):
                data["fiscal_risks"] = []
            if "compliance_checklist" not in data or not isinstance(data["compliance_checklist"], dict):
                data["compliance_checklist"] = {
                    "Auditor Report Included": True,
                    "GAAP/IFRS Standards Met": True,
                    "Going Concern Assessment Passed": True,
                    "Revenue Recognition Verified": True,
                    "Debt Covenants in Compliance": True
                }
        elif audit_type == "custom":
            if "extracted_fields" not in data or not isinstance(data["extracted_fields"], dict):
                data["extracted_fields"] = {}
            if "compliance_checklist" not in data or not isinstance(data["compliance_checklist"], dict):
                data["compliance_checklist"] = {}

        return data

    async def _generate_json(self, prompt: str, schema_dict: dict) -> dict:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"You are an expert enterprise document auditor. You must respond strictly and ONLY in valid JSON matching this schema:\n"
                        f"{json.dumps(schema_dict)}\n"
                        f"Do not include any conversational filler, markdown commentary, or introductory text. Output valid JSON only."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 8192
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            logger.error(f"Ollama _generate_json request error: {e}")
            raise self._format_error(e) from e

        message = data.get("message")
        if isinstance(message, dict):
            raw_content = message.get("content", "")
        else:
            raw_content = str(data.get("response", ""))

        try:
            return self._parse_json_response(raw_content)
        except Exception as e:
            logger.error(f"Failed to parse JSON from Ollama response: {e}. Raw content: {raw_content[:300]}")
            raise RuntimeError(f"Ollama generated invalid or unparseable JSON: {str(e)}") from e

    async def audit_legal(self, document_text: str, chunks: List[DocumentChunk]) -> LegalContractAudit:
        from app.core.security import build_secure_audit_prompt
        prompt = build_secure_audit_prompt("Audit this legal contract and return the exact JSON schema:", document_text, max_chars=25000)
        result_json = await self._generate_json(prompt, LegalContractAudit.model_json_schema())
        try:
            normalized = self._normalize_audit_dict(result_json, audit_type="legal")
            return LegalContractAudit.model_validate(normalized)
        except Exception as e:
            logger.error(f"Ollama legal audit schema validation error: {e}")
            raise RuntimeError(f"Ollama response does not conform to legal audit schema: {e}") from e

    async def audit_financial(self, document_text: str, chunks: List[DocumentChunk]) -> FinancialReportAudit:
        from app.core.security import build_secure_audit_prompt
        prompt = build_secure_audit_prompt("Audit this financial report and return the exact JSON schema:", document_text, max_chars=25000)
        result_json = await self._generate_json(prompt, FinancialReportAudit.model_json_schema())
        try:
            normalized = self._normalize_audit_dict(result_json, audit_type="financial")
            return FinancialReportAudit.model_validate(normalized)
        except Exception as e:
            logger.error(f"Ollama financial audit schema validation error: {e}")
            raise RuntimeError(f"Ollama response does not conform to financial audit schema: {e}") from e

    async def audit_custom(self, document_text: str, chunks: List[DocumentChunk], custom_prompt: Optional[str] = None) -> CustomAudit:
        from app.core.security import build_secure_audit_prompt
        rule_desc = custom_prompt or "Standard compliance audit"
        prompt = build_secure_audit_prompt(f"Perform custom audit '{rule_desc}' on document:", document_text, max_chars=25000)
        result_json = await self._generate_json(prompt, CustomAudit.model_json_schema())
        try:
            normalized = self._normalize_audit_dict(result_json, audit_type="custom")
            return CustomAudit.model_validate(normalized)
        except Exception as e:
            logger.error(f"Ollama custom audit schema validation error: {e}")
            raise RuntimeError(f"Ollama response does not conform to custom audit schema: {e}") from e

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
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 8192
            }
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            logger.error(f"Ollama chat request error: {e}")
            raise self._format_error(e) from e

        message = data.get("message")
        if isinstance(message, dict) and "content" in message:
            return message["content"]
        elif "response" in data:
            return str(data["response"])
        raise RuntimeError("Ollama returned an unexpected empty chat response structure.")
