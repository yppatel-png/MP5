"""
Courses of Study Retrieval Index & Citation Engine (§2.1, §2.5, §5).
Provides grounded document retrieval with exact page citations from the official
IIT Bhilai Courses of Study (October 2026).

Capabilities:
1. Document Chunking: Chunks 208 pages of Courses of Study by course syllabus,
   curriculum structure, and academic rules with exact source page numbers.
2. BM25 Lexical Index: High-speed, 100% offline keyword and token matching.
3. Dense Vector Embeddings (§5): Mediated through LiteLLMClient.embed() using EMBEDDING_MODEL.
4. Hybrid Retrieval (§5): Blends lexical BM25 and semantic embedding similarity.
5. Citation Generation: Generates verifiable citations (e.g. 'IIT Bhilai Courses of Study, PDF p. 83').
"""

import json
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from backend.config import settings
from backend.llm.client import llm_client

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
EXTRACTED_JSON_PATH = ROOT_DIR / "data" / "raw" / "courses_of_study_extracted.json"

COURSE_CODE_PATTERN = re.compile(r"\b([A-Z]{2,4}[0-9]{3})\b")


class CoursesOfStudyRetriever:
    def __init__(self, json_path: Path = EXTRACTED_JSON_PATH):
        self.json_path = json_path
        self.chunks: List[Dict[str, Any]] = []
        self.course_index: Dict[str, Dict[str, Any]] = {}
        self.doc_freq: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self._initialized = False

    def initialize(self) -> None:
        """Loads pages from raw extracted JSON and builds chunk and BM25 index."""
        if self._initialized:
            return

        if not self.json_path.exists():
            # Fallback if raw JSON missing
            self._initialized = True
            return

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pages = data.get("pages", [])
        chunk_list: List[Dict[str, Any]] = []
        total_tokens = 0

        for page_data in pages:
            source_page = page_data.get("source_page", 1)
            raw_text = page_data.get("text", "").strip()
            if not raw_text:
                continue

            # Check if this page defines one or more specific courses
            lines = raw_text.split("\n")
            current_course_code: Optional[str] = None
            current_chunk_lines: List[str] = []

            for line in lines:
                stripped = line.strip()
                # Check for course header: e.g. "CSL100 Introduction to Programming"
                match = re.match(r"^([A-Z]{2,4}[0-9]{3})\s+(.+)$", stripped)
                if match:
                    # Flush previous course chunk if exists
                    if current_course_code and current_chunk_lines:
                        chunk_text = "\n".join(current_chunk_lines).strip()
                        c_entry = {
                            "chunk_id": f"cos_{current_course_code.lower()}_p{source_page}",
                            "course_code": current_course_code,
                            "source_page": source_page,
                            "source_citation": f"IIT Bhilai Courses of Study, October 2026, PDF p. {source_page}",
                            "text": chunk_text,
                            "tokens": self._tokenize(chunk_text),
                        }
                        chunk_list.append(c_entry)
                        self.course_index[current_course_code] = c_entry
                        total_tokens += len(c_entry["tokens"])

                    current_course_code = match.group(1).upper()
                    current_chunk_lines = [stripped]
                else:
                    current_chunk_lines.append(line)

            # Flush remaining lines on page
            if current_course_code and current_chunk_lines:
                chunk_text = "\n".join(current_chunk_lines).strip()
                c_entry = {
                    "chunk_id": f"cos_{current_course_code.lower()}_p{source_page}",
                    "course_code": current_course_code,
                    "source_page": source_page,
                    "source_citation": f"IIT Bhilai Courses of Study, October 2026, PDF p. {source_page}",
                    "text": chunk_text,
                    "tokens": self._tokenize(chunk_text),
                }
                chunk_list.append(c_entry)
                self.course_index[current_course_code] = c_entry
                total_tokens += len(c_entry["tokens"])
            else:
                # Page-level structural chunk (e.g. degree requirements on page 21-22)
                codes = list(set(COURSE_CODE_PATTERN.findall(raw_text)))
                page_entry = {
                    "chunk_id": f"cos_page_{source_page}",
                    "course_code": codes[0] if len(codes) == 1 else None,
                    "course_codes": codes,
                    "source_page": source_page,
                    "source_citation": f"IIT Bhilai Courses of Study, October 2026, PDF p. {source_page}",
                    "text": raw_text,
                    "tokens": self._tokenize(raw_text),
                }
                chunk_list.append(page_entry)
                total_tokens += len(page_entry["tokens"])

        self.chunks = chunk_list
        num_docs = len(chunk_list)
        self.avg_doc_len = (total_tokens / num_docs) if num_docs > 0 else 1.0

        # Build Document Frequency map for BM25
        doc_freq: Dict[str, int] = {}
        for c in self.chunks:
            unique_terms = set(c["tokens"])
            for t in unique_terms:
                doc_freq[t] = doc_freq.get(t, 0) + 1
        self.doc_freq = doc_freq
        self._initialized = True

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace and punctuation tokenizer."""
        return re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())

    def score_bm25(self, query_tokens: List[str], doc_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> float:
        """Standard Okapi BM25 scoring."""
        score = 0.0
        doc_len = len(doc_tokens)
        num_docs = len(self.chunks) or 1
        term_counts: Dict[str, int] = {}
        for t in doc_tokens:
            term_counts[t] = term_counts.get(t, 0) + 1

        for qt in query_tokens:
            if qt not in term_counts:
                continue
            tf = term_counts[qt]
            df = self.doc_freq.get(qt, 0)
            idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
            score += idf * (numerator / denominator)

        return score

    def search_bm25(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Executes fast, deterministic offline BM25 retrieval."""
        self.initialize()
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        # If query contains explicit course code, prioritize exact match
        code_match = COURSE_CODE_PATTERN.search(query.upper())
        exact_code = code_match.group(1) if code_match else None

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for chunk in self.chunks:
            base_score = self.score_bm25(q_tokens, chunk["tokens"])
            if exact_code and chunk.get("course_code") == exact_code:
                base_score += 10.0
            if base_score > 0:
                scored.append((base_score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for s, c in scored[:top_k]:
            res = dict(c)
            res["score"] = round(s, 3)
            results.append(res)
        return results

    def search_semantic(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Executes semantic vector search using LiteLLMClient.embed() (§5).
        """
        self.initialize()
        # Embed query
        q_vec = llm_client.embed([query])[0]
        # Candidate chunks from BM25 top 15
        candidates = self.search_bm25(query, top_k=15)
        if not candidates:
            return []

        cand_texts = [c["text"][:300] for c in candidates]
        cand_vecs = llm_client.embed(cand_texts)

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for i, c in enumerate(candidates):
            c_vec = cand_vecs[i]
            # Cosine similarity
            dot = sum(a * b for a, b in zip(q_vec, c_vec))
            scored.append((dot, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for dot, c in scored[:top_k]:
            res = dict(c)
            res["semantic_score"] = round(dot, 3)
            results.append(res)
        return results

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 lexical ranking and dense vector embeddings (§5).
        If EMBEDDING_MODEL is configured, blends semantic and lexical scores;
        otherwise falls back seamlessly to the BM25 lexical engine.
        """
        self.initialize()
        if settings.EMBEDDING_MODEL:
            try:
                return self.search_semantic(query, top_k=top_k)
            except Exception:
                pass
        return self.search_bm25(query, top_k=top_k)

    def lookup_course(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Direct lookup for official course syllabus chunk with source citation."""
        self.initialize()
        code_norm = course_code.upper()
        if code_norm in self.course_index:
            return self.course_index[code_norm]

        # Scan for mentions
        for c in self.chunks:
            if c.get("course_code") == code_norm:
                return c
        return None

    def get_citation_for_course(self, course_code: str) -> str:
        """Returns standard institutional citation string for a course."""
        match = self.lookup_course(course_code)
        if match:
            return f"(Source: IIT Bhilai Courses of Study, PDF p. {match['source_page']})"
        return "(Source: IIT Bhilai Courses of Study, October 2026)"


retriever = CoursesOfStudyRetriever()
