"""Local RAG building blocks for Module 8 (Azure AI / Generative AI).

Chunking, embedding, an in-memory vector store, retrieval and grounded-prompt
assembly - all runnable offline with a deterministic local embedder, so you can
develop and test retrieval logic with no Azure. The lessons show how to swap the
local embedder for Microsoft Foundry embedding deployments and the in-memory
store for Azure AI Search, keeping these interfaces.
"""

from .rag import (
    HashingEmbedder,
    RagIndex,
    VectorStore,
    build_prompt,
    chunk_text,
)
from .evaluate import mrr, recall_at_k, evaluate_retrieval

__all__ = [
    "HashingEmbedder",
    "RagIndex",
    "VectorStore",
    "build_prompt",
    "chunk_text",
    "mrr",
    "recall_at_k",
    "evaluate_retrieval",
]
