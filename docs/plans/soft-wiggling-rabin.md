# Plan: Textbook Processing Pipeline — Clean Start

## Context

We have 175 curriculum modules planned (A1-B2) but can't build them properly because the textbook content isn't searchable. The 4 abetka YAML files have `image_url: null` everywhere — they're skeletons, not real modules.

**What exists but isn't connected:**
- 85 PDFs in `data/textbooks/grade-{01..11}/`
- 12,298 extracted images in `data/textbook_images/` (cleaned, all grades)
- Text chunks for grades 1-3 only (1,205 chunks in 9 JSONL files)
- Grades 4-11 text: NOT extracted
- Qdrant: EMPTY (Docker via `docker-compose.qdrant.yaml`, never populated)
- All RAG scripts exist and are functional — just never run end-to-end
- **Playground app** (`playgrounds/images.html` + `scripts/api/`) — FastAPI web UI for browsing/searching

**What we need:** Populate Qdrant so the playground app and MCP RAG tools can search textbook content. SigLIP handles cross-modal text→image search natively (no Gemini Vision annotation needed).

## Pipeline (3 steps)

### Step 1: Start Qdrant + verify clean state

```bash
docker-compose -f docker-compose.qdrant.yaml up -d
curl http://localhost:6333/collections
# Should return {"collections":[]} (clean start)
```

### Step 2: Extract text from ALL grades

Currently only grades 1-3 have text chunks. Run for all 85 PDFs:

```bash
.venv/bin/python scripts/rag/extract_text.py --all
```

- Digital PDFs (grades 3+): PyMuPDF fast mode (~2s per PDF)
- Scanned PDFs (G1 Bolshakova, Kravcova): Marker OCR (slower)
- Output: `data/textbook_chunks/grade-{01..11}/*.jsonl`

### Step 3: Ingest into Qdrant

**Text chunks** (BGE-M3 embeddings — hybrid dense+sparse):
```bash
.venv/bin/python scripts/rag/ingest.py --text --all
```

**Images** (SigLIP 2 embeddings — cross-modal text→image):
```bash
./scripts/rag/ingest_overnight.sh
# Or specific grades: ./scripts/rag/ingest_overnight.sh --grade 1 2
```

**Literary texts** (BGE-M3 — 78K+ chunks ready):
```bash
.venv/bin/python scripts/rag/ingest.py --literary --all
```

### Step 4: Verify

```bash
# Collection stats
.venv/bin/python scripts/rag/query.py stats

# Text search
.venv/bin/python scripts/rag/query.py text "яблуко" --grade 1

# Image search (SigLIP cross-modal)
.venv/bin/python scripts/rag/query.py images "яблуко" --grade 1

# Playground web UI
.venv/bin/python -m uvicorn scripts.api.main:app --port 8790
# Open http://localhost:8790/images.html

# MCP tools (from Claude Code session)
# mcp__rag__search_text query="яблуко" grade=1
# mcp__rag__search_images query="яблуко" grade=1
```

## What Already Works (no code changes needed)

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/rag/extract_images.py` | Extract PNGs from PDFs | ✅ Done for all grades (12,298 images) |
| `scripts/rag/extract_text.py` | Extract text chunks (PyMuPDF + Marker OCR) | ✅ Code works (only run for G1-3) |
| `scripts/rag/embed.py` | BGE-M3 (text) + SigLIP 2 (images) | ✅ Complete |
| `scripts/rag/ingest.py` | Batch upload to Qdrant | ✅ Complete |
| `scripts/rag/query.py` | CLI search interface | ✅ Complete |
| `scripts/rag/ingest_overnight.sh` | Batch image ingestion wrapper | ✅ Complete |
| `scripts/cleanup_images.py` | Remove junk images | ✅ Already run (removed 2,890 junk) |
| `.mcp/servers/rag/server.py` | MCP RAG tools (6 tools) | ✅ Complete |
| `scripts/api/rag_router.py` | FastAPI search endpoints | ✅ Complete |
| `playgrounds/images.html` | Web UI for image browsing/search | ✅ Complete |

## After Qdrant Is Populated

Build `scripts/source_images_direct.py` (#664):
- Takes a module YAML (e.g., `abetka-1.yaml`)
- For each item with `image_url: null`, searches Qdrant for matching images
- Suggests best matches with SigLIP similarity scores
- User confirms → populates `image_ref` field

This unblocks #662 (A1 Module Build).

## Resource Notes

- Qdrant Docker: ~200MB RAM
- SigLIP model loading: ~1.5GB RAM (one-time during ingestion)
- BGE-M3 model loading: ~1.2GB RAM (one-time during ingestion)
- Text extraction: CPU-only, lightweight
- Image ingestion: GPU-accelerated if available, CPU fallback
- **Run steps sequentially** — don't overlap model loading with other heavy processes
