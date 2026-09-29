from abc import ABC, abstractmethod
from typing import List, Optional, Any
from app.models.document import DocumentChunk
from app.models.audit import LegalContractAudit, FinancialReportAudit, CustomAudit

class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    async def audit_legal(self, document_text: str, chunks: List[DocumentChunk]) -> LegalContractAudit:
        pass

    @abstractmethod
    async def audit_financial(self, document_text: str, chunks: List[DocumentChunk]) -> FinancialReportAudit:
        pass

    @abstractmethod
    async def audit_custom(self, document_text: str, chunks: List[DocumentChunk], custom_prompt: Optional[str] = None) -> CustomAudit:
        pass

    @abstractmethod
    async def chat(self, question: str, context_chunks: List[DocumentChunk]) -> str:
        pass

    @abstractmethod
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
        pass
