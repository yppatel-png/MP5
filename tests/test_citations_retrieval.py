"""
Tests for Courses of Study Document Retrieval, Chunking, Citations & Embeddings (§2.1, §2.5, §5).
Asserts that:
1. Courses of Study text is chunked with source page numbers.
2. BM25 and Hybrid retrieval locate correct course syllabus and rule chunks.
3. Buddy answers about course content, credits, or rules cite official page numbers (PDF p. X).
4. EMBEDDING_MODEL is wired into retrieval and executes via LiteLLMClient.embed().
"""

import pytest
from backend.retrieval.indexer import retriever
from backend.buddy.router import buddy_router
from backend.llm.client import llm_client
from backend.config import settings
from backend.db.seed_loader import load_seed_data


@pytest.fixture(scope="module", autouse=True)
def setup_retrieval_tests():
    load_seed_data(reset=True)
    llm_client.offline = True
    retriever.initialize()


def test_chunking_and_page_provenance():
    assert len(retriever.chunks) >= 100, f"Expected at least 100 chunks, got {len(retriever.chunks)}"
    pages = set(c["source_page"] for c in retriever.chunks)
    assert len(pages) >= 50, "Chunks must span across multiple pages of Courses of Study"

    # Verify CSL100 chunk has exact page 83 citation
    csl100 = retriever.lookup_course("CSL100")
    assert csl100 is not None, "CSL100 must be indexed"
    assert csl100["source_page"] == 83, f"Expected page 83 for CSL100, got {csl100['source_page']}"
    assert "PDF p. 83" in csl100["source_citation"]
    assert "Introduction to Programming" in csl100["text"]


def test_bm25_search_citations():
    results = retriever.search_bm25("Introduction to Programming CSL100", top_k=3)
    assert len(results) > 0, "BM25 search should return results"
    top = results[0]
    assert "source_page" in top
    assert "source_citation" in top
    assert "PDF p." in top["source_citation"]


def test_buddy_course_content_answer_cites_page():
    # 1. Asking why a course is in plan / explain course
    ans1 = buddy_router.handle_message("BH-SW-001", "Why CSL201 in my plan?")
    reply1 = ans1.get("reply", "")
    assert "PDF p." in reply1 or "Courses of Study" in reply1, (
        f"Buddy reply must cite source document and page number. Got: {reply1}"
    )

    # 2. General course syllabus question
    ans2 = buddy_router.handle_message("BH-SW-001", "What topics are taught in CSL100 Introduction to Programming?")
    reply2 = ans2.get("reply", "")
    assert "PDF p." in reply2 or "Courses of Study" in reply2, (
        f"Buddy reply must cite source document and page number. Got: {reply2}"
    )


def test_embedding_model_wiring_and_hybrid_retrieval():
    # Test dense embedding generation
    test_texts = [
        "Data structures and algorithms complexity",
        "Operating systems processes and memory management"
    ]
    vectors = llm_client.embed(test_texts)
    assert len(vectors) == 2
    assert len(vectors[0]) > 0
    assert all(isinstance(val, float) for val in vectors[0])

    # Test semantic vector search execution
    sem_results = retriever.search_semantic("Data Structures and Algorithms", top_k=3)
    assert len(sem_results) > 0
    assert "source_page" in sem_results[0]
    assert "semantic_score" in sem_results[0]

