"""Retrieval evaluation metrics for the RAG core (Module 8).

Retrieval quality is the foundation of RAG answer quality: if the right passage
is not retrieved, no model can ground on it. These are the offline, testable
retrieval metrics; the lessons cover Foundry's answer-quality evaluators
(groundedness, relevance) via azure-ai-evaluation.

- recall@k: did a relevant document appear in the top k?
- MRR: how high did the first relevant document rank (reciprocal rank)?
"""

from __future__ import annotations


def recall_at_k(retrieved_doc_ids: list[str], relevant_doc_ids: set[str], k: int) -> float:
    """1.0 if any relevant doc is in the top-k retrieved, else 0.0 (per query)."""
    return 1.0 if set(retrieved_doc_ids[:k]) & relevant_doc_ids else 0.0


def mrr(retrieved_doc_ids: list[str], relevant_doc_ids: set[str]) -> float:
    """Reciprocal rank of the first relevant doc (0.0 if none retrieved)."""
    for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
        if doc_id in relevant_doc_ids:
            return 1.0 / rank
    return 0.0


def evaluate_retrieval(index, qrels: list[dict], k: int = 4) -> dict:
    """Aggregate recall@k and MRR over a labelled set.

    ``index`` has ``.retrieve(query, k)`` returning dicts with ``doc_id``.
    ``qrels``: [{"query": str, "relevant": set[str]}].
    """
    recalls, rrs = [], []
    for q in qrels:
        hits = index.retrieve(q["query"], k)
        doc_ids = [h["doc_id"] for h in hits]
        recalls.append(recall_at_k(doc_ids, set(q["relevant"]), k))
        rrs.append(mrr(doc_ids, set(q["relevant"])))
    n = len(qrels) or 1
    return {"queries": len(qrels), "k": k,
            "recall_at_k": round(sum(recalls) / n, 4),
            "mrr": round(sum(rrs) / n, 4)}
