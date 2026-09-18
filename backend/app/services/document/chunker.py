import re
import uuid
from typing import List, Dict, Any, Optional
from app.models.document import DocumentChunk
from app.core.config import settings

class DocumentChunker:
    @staticmethod
    def _detect_section(text: str) -> Optional[str]:
        # Detect common contract or report headers like "SECTION 1", "ARTICLE IV", "CLAUSE 3", "BALANCE SHEET", etc.
        patterns = [
            r"^(?:ARTICLE|SECTION|CLAUSE)\s+([0-9IVXLCDM\.]+[\s\:\-\w]{2,50})",
            r"^([0-9]+\.[0-9]*\s+[A-Z][\w\s]{2,50})",
            r"^([A-Z\s]{4,40}:)",
            r"^(BALANCE SHEET|INCOME STATEMENT|CASH FLOW|NOTES TO FINANCIAL STATEMENTS|RISK FACTORS)"
        ]
        lines = text.splitlines()
        for line in lines[:3]:
            line = line.strip()
            for pat in patterns:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    return line[:60]
        return None

    @classmethod
    def chunk_document(
        cls, 
        doc_id: str, 
        pages: List[Dict[str, Any]], 
        chunk_size: int = settings.CHUNK_SIZE, 
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        global_index = 0

        for page in pages:
            page_num = page["page_number"]
            text = page["text"]
            
            # Split by double newlines (paragraphs) first
            paragraphs = re.split(r"\n\s*\n", text)
            current_chunk_text = ""
            current_section = None

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Check if paragraph begins with a section title
                detected_sec = cls._detect_section(para)
                if detected_sec:
                    current_section = detected_sec

                if len(current_chunk_text) + len(para) <= chunk_size:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + para
                    else:
                        current_chunk_text = para
                else:
                    # Current chunk is full, emit it if not empty
                    if current_chunk_text:
                        chunk_id = f"{doc_id}_p{page_num}_c{global_index}"
                        chunks.append(DocumentChunk(
                            id=chunk_id,
                            doc_id=doc_id,
                            page_number=page_num,
                            chunk_index=global_index,
                            content=current_chunk_text,
                            token_count=len(current_chunk_text.split()),
                            section=current_section
                        ))
                        global_index += 1

                    # Handle paragraphs that exceed chunk_size on their own
                    if len(para) > chunk_size:
                        # Slice large paragraph with overlap
                        start = 0
                        while start < len(para):
                            end = min(start + chunk_size, len(para))
                            sub_text = para[start:end]
                            chunk_id = f"{doc_id}_p{page_num}_c{global_index}"
                            chunks.append(DocumentChunk(
                                id=chunk_id,
                                doc_id=doc_id,
                                page_number=page_num,
                                chunk_index=global_index,
                                content=sub_text,
                                token_count=len(sub_text.split()),
                                section=current_section
                            ))
                            global_index += 1
                            if end == len(para):
                                break
                            start += chunk_size - chunk_overlap
                        current_chunk_text = ""
                    else:
                        current_chunk_text = para

            # Emit any remaining text for the page
            if current_chunk_text:
                chunk_id = f"{doc_id}_p{page_num}_c{global_index}"
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    doc_id=doc_id,
                    page_number=page_num,
                    chunk_index=global_index,
                    content=current_chunk_text,
                    token_count=len(current_chunk_text.split()),
                    section=current_section
                ))
                global_index += 1

        return chunks
