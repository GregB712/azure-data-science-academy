"""Tests for the Module 8 local RAG core and retrieval metrics. Offline."""
from __future__ import annotations

import numpy as np
import pytest

from genai import evaluate as ev
from genai.rag import HashingEmbedder, RagIndex, VectorStore, build_prompt, chunk_text

DOCS = [
    {"id": "forecast", "text": "The demand forecast product gives weekly one-step-ahead predictions "
     "per product and store. Forecast units are non-negative and stock-outs are flagged not imputed."},
    {"id": "retraining", "text": "Retraining is triggered by schedule, feature drift measured with PSI, "
     "and accuracy decay. A challenger model must beat the naive baseline before promotion to champion."},
    {"id": "storage", "text": "ADLS Gen2 adds a hierarchical namespace to Blob Storage with POSIX ACLs "
     "and the dfs endpoint used by abfss. RBAC is evaluated before ACLs."},
]


def test_chunk_text_overlap_and_validation():
    words = " ".join(f"w{i}" for i in range(100))
    chunks = chunk_text(words, chunk_size=30, overlap=10)
    assert all(len(c.split()) <= 30 for c in chunks)
    # consecutive chunks overlap by `overlap` words
    first, second = chunks[0].split(), chunks[1].split()
    assert first[-10:] == second[:10]
    assert chunk_text("") == []
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=10, overlap=10)


def test_hashing_embedder_deterministic_and_normalised():
    a = HashingEmbedder().embed(["retrain the model when drift is high"])
    b = HashingEmbedder().embed(["retrain the model when drift is high"])
    assert np.array_equal(a, b)                       # stable across instances/processes
    assert np.isclose(np.linalg.norm(a[0]), 1.0)


def test_vector_store_returns_nearest():
    store = VectorStore()
    store.add(["a", "b"], np.array([[1.0, 0.0], [0.0, 1.0]], dtype="float32"),
              [{"text": "x"}, {"text": "y"}])
    hits = store.search(np.array([0.9, 0.1], dtype="float32"), k=1)
    assert hits[0]["id"] == "a"


def test_rag_retrieves_relevant_doc():
    index = RagIndex(HashingEmbedder(), chunk_size=40, overlap=10)
    assert index.index_documents(DOCS) >= 3
    hits = index.retrieve("when is the model retrained on drift?", k=1)
    assert hits[0]["doc_id"] == "retraining"


def test_build_prompt_grounds_and_cites():
    hits = [{"doc_id": "forecast", "text": "weekly one-step-ahead forecast"}]
    prompt = build_prompt("what is the forecast grain?", hits)
    assert "Context:" in prompt and "[1] (forecast)" in prompt
    assert "what is the forecast grain?" in prompt
    assert "don't know" in prompt          # the anti-hallucination instruction


def test_retrieval_metrics():
    assert ev.recall_at_k(["x", "retraining"], {"retraining"}, k=2) == 1.0
    assert ev.recall_at_k(["x", "y"], {"retraining"}, k=2) == 0.0
    assert ev.mrr(["x", "retraining"], {"retraining"}) == 0.5

    index = RagIndex(HashingEmbedder(), chunk_size=40, overlap=10)
    index.index_documents(DOCS)
    qrels = [
        {"query": "when is the model retrained", "relevant": {"retraining"}},
        {"query": "what endpoint does abfss use", "relevant": {"storage"}},
    ]
    report = ev.evaluate_retrieval(index, qrels, k=2)
    assert report["queries"] == 2
    assert 0.0 <= report["recall_at_k"] <= 1.0 and report["recall_at_k"] == 1.0
