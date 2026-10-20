"""Retrieval-augmented generation core: chunk, embed, store, retrieve, ground.

Deliberately dependency-light and offline so retrieval logic is testable without
Azure. The ``Embedder`` protocol lets you swap the deterministic ``HashingEmbedder``
(for local dev/tests) for a Microsoft Foundry embedding deployment, and the
``VectorStore`` for Azure AI Search, without touching the retrieval/prompt code.

Run (WSL / Python), from code/:
    python -m genai.rag        # indexes a couple of sample docs and runs a query
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")


def _stable_hash(token: str) -> int:
    """Process-independent hash (builtin hash() is randomised per run)."""
    return int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big")


def chunk_text(text: str, chunk_size: int = 60, overlap: int = 15) -> list[str]:
    """Split text into overlapping word-windows (sizes in words).

    Overlap keeps context across chunk boundaries so a sentence split in two is
    still retrievable. ``chunk_size`` and ``overlap`` are in words for clarity;
    production pipelines often size by tokens.
    """
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("require chunk_size > 0 and 0 <= overlap < chunk_size")
    words = text.split()
    if not words:
        return []
    step = chunk_size - overlap
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), step)]
    # drop a trailing chunk fully contained in the previous one
    if len(chunks) > 1 and len(words) - (len(chunks) - 1) * step <= overlap:
        chunks.pop()
    return chunks


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray: ...


@dataclass
class HashingEmbedder:
    """Deterministic bag-of-hashed-tokens embedding (offline; for dev/tests).

    Not semantic like a real model, but stable and dependency-free, so retrieval
    of lexically related chunks works and tests are reproducible. Swap for a
    Foundry embedding deployment (text-embedding-3-*) in production.
    """

    dim: int = 256

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype="float32")
        for i, text in enumerate(texts):
            for tok in _TOKEN.findall(text.lower()):
                out[i, _stable_hash(tok) % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.clip(norms, 1e-9, None)


@dataclass
class VectorStore:
    """In-memory cosine-similarity store (vectors are L2-normalised on add)."""

    _vectors: np.ndarray | None = None
    _ids: list[str] = field(default_factory=list)
    _meta: list[dict] = field(default_factory=list)

    def add(self, ids: list[str], vectors: np.ndarray, metas: list[dict]) -> None:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.clip(norms, 1e-9, None)
        self._vectors = vectors if self._vectors is None else np.vstack([self._vectors, vectors])
        self._ids.extend(ids)
        self._meta.extend(metas)

    def search(self, query_vector: np.ndarray, k: int = 4) -> list[dict]:
        if self._vectors is None:
            return []
        q = query_vector / np.clip(np.linalg.norm(query_vector), 1e-9, None)
        scores = self._vectors @ q
        top = np.argsort(scores)[::-1][:k]
        return [{"id": self._ids[i], "score": float(scores[i]), **self._meta[i]} for i in top]


@dataclass
class RagIndex:
    """Chunk documents, embed and store them, then retrieve for a query."""

    embedder: Embedder
    chunk_size: int = 60
    overlap: int = 15
    store: VectorStore = field(default_factory=VectorStore)

    def index_documents(self, docs: list[dict]) -> int:
        """docs: [{"id": ..., "text": ..., **metadata}]. Returns chunks indexed."""
        ids, texts, metas = [], [], []
        for doc in docs:
            for j, chunk in enumerate(chunk_text(doc["text"], self.chunk_size, self.overlap)):
                ids.append(f"{doc['id']}#{j}")
                texts.append(chunk)
                metas.append({"doc_id": doc["id"], "chunk": j, "text": chunk,
                              **{k: v for k, v in doc.items() if k not in ("id", "text")}})
        if texts:
            self.store.add(ids, self.embedder.embed(texts), metas)
        return len(texts)

    def retrieve(self, query: str, k: int = 4) -> list[dict]:
        return self.store.search(self.embedder.embed([query])[0], k)


def build_prompt(query: str, retrieved: list[dict], instruction: str | None = None) -> str:
    """Assemble a grounded prompt: numbered context passages + the question.

    The instruction tells the model to answer only from the context and to say so
    when the context is insufficient - the core defence against RAG hallucination.
    """
    instruction = instruction or (
        "Answer the question using ONLY the context below. "
        "If the context does not contain the answer, say you don't know. Cite passages by [n].")
    context = "\n\n".join(f"[{i + 1}] ({r['doc_id']}) {r['text']}" for i, r in enumerate(retrieved))
    return f"{instruction}\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"


def main() -> None:
    docs = [
        {"id": "forecast-contract", "text": "The demand forecast product is weekly one-step-ahead "
         "per product and store. Forecast units are non-negative. Stock-outs are flagged not imputed."},
        {"id": "retraining", "text": "Retraining triggers are schedule, feature drift and accuracy "
         "decay. A challenger must beat the naive baseline MASE below one before promotion."},
    ]
    index = RagIndex(HashingEmbedder())
    print("chunks indexed:", index.index_documents(docs))
    hits = index.retrieve("when do we retrain the model", k=2)
    print("top doc:", hits[0]["doc_id"], round(hits[0]["score"], 3))
    print(build_prompt("when do we retrain the model", hits))


if __name__ == "__main__":
    main()
