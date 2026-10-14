---
id: arch-rag
title: Generative AI and RAG on Azure
type: architecture
order: 7
status: planned
services: [Microsoft Foundry, Azure AI Search, Azure Container Apps, Azure Data Lake Storage Gen2, Managed identities, Azure Monitor and Application Insights]
lessons: [m8-genai-roadmap]
summary: Retrieval-augmented generation and agent tooling with Microsoft Foundry and Azure AI Search (design for Module 8).
---

# Generative AI and RAG on Azure (design, Module 8)

```mermaid
flowchart LR
  subgraph Ingest["Ingestion (offline)"]
    docs[("Docs in ADLS / Blob")] --> chunk["Chunk + metadata"] --> emb["Embed<br/>(Foundry embedding deployment)"] --> idx[("AI Search index")]
  end
  subgraph Online["Query (online)"]
    q["User question"] --> api["FastAPI on Container Apps"]
    api -->|"hybrid search + filters"| idx
    api -->|"grounded prompt"| llm["Foundry chat deployment"]
    api -->|"tool call"| tool["Forecast API / Gold data"]
    llm --> ans["Answer + citations"]
  end
  api -.-> obs["Tracing · evaluation · App Insights"]
```

Status: **planned**. See the [Module 8 roadmap](../docs/generative-ai/README.md). Product names: Microsoft Foundry was formerly Azure AI Foundry.
