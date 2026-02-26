# Plan: RAG Infrastructure — Qdrant + BGE-M3 + SigLIP 2

**Issue**: #666
**Scope**: Prototype phase — get 2 textbooks indexed and queryable via MCP

## Context

42 Ukrainian school textbooks (48 PDFs, ~740 MB) are downloaded and ready for indexing. The l2-uk-direct track needs textbook content as a reference source during module development — without RAG, content work means writing from memory (anti-pattern per MEMORY.md). This plan covers the prototype: 2 textbooks indexed, hybrid search working, MCP server queryable from Claude Code.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector DB | **Qdrant** (Docker) | Hybrid search (dense+sparse), named vectors for multi-modal, payload indexing |
| Text embeddings | **BGE-M3** (568M, MIT) | Native hybrid output (dense+sparse+colbert in one pass), ~1 GB on MacBook |
| Image embeddings | **SigLIP 2 So400m** (Apache 2.0) | Best multilingual image search, 109 languages, sigmoid loss |
| PDF extraction | **marker** (text structure) + **pymupdf** (images) | marker for section-aware chunking; pymupdf for image extraction |
| MCP server | Python stdio | Same pattern as `.mcp/servers/message-broker/server.py` |

**Rejected**: Qwen3-8B (dense-only, 16 GB, needs separate BM25), OpenAI embeddings (API-only, vendor lock-in), ChromaDB (no hybrid/multi-vector), CLIP (English-centric).

## Risks & Mitigations (from Gemini adversarial review)

| Risk | Mitigation |
|------|-----------|
| PDF text quality (garbled OCR, merged columns) | **Text quality gate** before embedding — flag chunks with >20% non-Ukrainian chars |
| Image-text association (images float far from context) | **Don't over-engineer** v1 — visual embedding + page metadata only, no auto-tagging |
| Pedagogical quality variance across editions | **`trust_tier` metadata** — tier 1: NUS 2022+, tier 2: 2017-2021 |
| Chunk boundary detection | **Prototype on 2 books**, manually verify before full ingestion |

---

## Step 1: Qdrant Docker Setup

**Create** `docker-compose.qdrant.yaml`:
- Qdrant service with REST (6333) + gRPC (6334) ports
- Persistent storage at `data/qdrant/`
- Add `data/qdrant/` to `.gitignore`

---

## Step 2: Install Dependencies

```
qdrant-client FlagEmbedding marker-pdf pymupdf torch open_clip_torch Pillow
```

---

## Step 3: PDF Text Extraction

**Create** `scripts/rag/extract_text.py`

1. `marker` converts PDF → structured markdown with section headings
2. Split at section boundaries (H1/H2 = hard break, paragraphs = soft break)
3. Chunk size: 256-512 tokens, 64-token overlap
4. **Quality gate**: check Ukrainian character ratio per chunk, flag garbled ones
5. Metadata per chunk: `grade, subject, author, year, page_start, page_end, section_title, trust_tier`

---

## Step 4: Image Extraction

**Create** `scripts/rag/extract_images.py`

1. `pymupdf` extracts images > 100x100px (skip tiny icons)
2. Save to `data/textbook_images/grade-{N}/{filename}-p{page}-{idx}.png`
3. Metadata: `grade, subject, author, page, image_index`
4. No automatic `concept_type` in v1

---

## Step 5: Embedding + Ingestion

**Create** `scripts/rag/ingest.py`

### Qdrant collections:

**`textbook_chunks`** (text):
- Named vector `dense`: BGE-M3 dense (1024d, Cosine)
- Named vector `sparse`: BGE-M3 sparse (BM25-like weights)
- Payload: `grade`, `subject`, `author`, `year`, `page_start`, `section_title`, `trust_tier`, `text`
- Indexes on: `grade`, `subject`, `trust_tier`

**`textbook_images`** (images):
- Vector: SigLIP 2 So400m (1152d, Cosine)
- Payload: `grade`, `subject`, `author`, `page`, `image_path`
- Indexes on: `grade`, `subject`

### Trust tier assignment:
- Tier 1: NUS 2022+ editions (grades 5-8 newest)
- Tier 2: 2017-2021 editions (grades 9-11, older grades 3-4)

---

## Step 6: MCP Server

**Create** `.mcp/servers/rag/server.py`

Pattern: same as `.mcp/servers/message-broker/server.py` (mcp.server.Server + stdio)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `search_text` | query, grade?, subject?, trust_tier?, limit=5 | Hybrid text search |
| `search_images` | query, grade?, limit=5 | Image search via Ukrainian text |
| `get_chunk_context` | chunk_id, window=2 | Surrounding chunks |
| `collection_stats` | — | Index stats |

**Update** `.mcp.json` — add `rag` entry.

---

## Step 7: Prototype Validation

### Test books:
1. Grade 1 Большакова (Буквар Part 1) — richest illustrations
2. Grade 3 Вашуленко Part 1 — grammar + riddles

### Manual checks:
- [ ] Chunks respect section/paragraph boundaries
- [ ] Ukrainian text is clean (no garbled OCR)
- [ ] Metadata correct (grade, author, pages)
- [ ] Images > 100x100, reasonable quality

### Test queries:
1. `search_text("як утворюється минулий час")` → past tense from grade 3
2. `search_text("загадка про тварин", grade=3)` → animal riddles
3. `search_text("буква Ї", trust_tier=1)` → letter Ї from NUS books
4. `search_images("яблуко")` → apple illustrations from grade 1
5. `search_images("ілюстрація до букви А")` → letter A from Буквар
6. `collection_stats()` → chunk/image counts

### Pass criteria:
- Qdrant starts via docker-compose
- 2 books fully ingested (text + images)
- All 6 test queries return relevant results
- MCP server responds from Claude Code
- Query latency < 500ms

---

## Files

| File | Action |
|------|--------|
| `docker-compose.qdrant.yaml` | CREATE |
| `scripts/rag/__init__.py` | CREATE |
| `scripts/rag/config.py` | CREATE — model paths, collection names, trust tiers |
| `scripts/rag/extract_text.py` | CREATE — PDF → structured chunks |
| `scripts/rag/extract_images.py` | CREATE — PDF → images |
| `scripts/rag/embed.py` | CREATE — BGE-M3 + SigLIP encoding |
| `scripts/rag/ingest.py` | CREATE — chunks + images → Qdrant |
| `scripts/rag/query.py` | CREATE — CLI query tool |
| `.mcp/servers/rag/server.py` | CREATE — MCP server |
| `.mcp.json` | EDIT — add `rag` entry |
| `.gitignore` | EDIT — add `data/qdrant/`, `data/textbook_images/` |

## Out of Scope

- Full 48-PDF ingestion (after prototype validates)
- Chunk deduplication across editions
- Qwen3 vs BGE-M3 head-to-head eval (after prototype)
- Image `concept_type` auto-tagging via VLM
- Evaluation harness with gold-standard answers
