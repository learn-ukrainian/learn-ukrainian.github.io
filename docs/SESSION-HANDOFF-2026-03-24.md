# Session Handoff — 2026-03-24

## What was accomplished

### Pipeline (V6)
- Reviewer-as-fixer: Gemini outputs `<fixes>` find/replace, pipeline applies deterministically
- Writer-driven словнік with contextual translations
- Dialogue formatting (blockquote → `<div class="dialogue">`)
- VESUM whitelist for false positives (#1017 closed)
- Stress annotation idempotency fix + 48 tests (#988 closed)
- Heteronym stress report (#1019 closed)
- Review now strips enrichment and injects deterministic word count
- Writer prompt: natural dialogues from textbooks, no archaic words, speaker names
- Seminar prompt (`v6-write-seminar.md`) + auto-detection in pipeline
- 8 GH issues closed total

### A1.1 Modules (7/7 rebuilt)
- Average 9.8/10, all PASS
- Natural dialogues with speaker names + translations

### A2 Test Build
- genitive-intro: 10.0/10 PASS
- Natural dialogues (searching for phone/keys, ordering at restaurant)

### Dictionaries (663K+ points in RAG)
- Downloaded + converted: СУМ-11 (127K), Балла EN→UK (79K), Фразеологічний (25K),
  Вікісловник (50K), dmklinger UK→EN (30K), Ukrajinet WordNet (122K synsets!)
- All ingested to RAG
- PULS CEFR vocabulary scraped (5,939 words, A1-C1)
- UberText frequency in SQLite (12.4M rows)
- СУМ-11 register labels extracted (25,565 words)
- Грушевський тт. 4-10 + Конституція Орлика scraped
- Wiktionary dump extracted (50K entries)
- Literary catalog documented (125K chunks, 3,257 works)
- Content gaps tracked in `docs/RAG-CONTENT-GAPS.md`
- Anna Ohoiko books as reference (500+ Verbs, 1000 Words, Motion Verbs)

### Plans
- A2: 7/60 done (A2.1 phase — excellent quality)
- 53 A2 plans deleted (structurally broken from batch generation)
- B1: 91 plans exist (from previous sessions)
- Seminar tracks: 1,135 plans V6-compatible

## What needs doing next session

### PRIORITY 1: Rewrite 53 A2 plans (A2.2-A2.8)
- Must use same quality as A2.1 (genitive-intro is the gold standard)
- Send to Gemini one phase at a time via `dispatch_gemini`
- Include a GOOD plan as example in every prompt
- Strict format requirements: pedagogy, focus, word budgets, proper vocab format,
  valid activity types (quiz/fill-in/match-up/group-sort/true-false only)
- Every plan must have references
- Design doc: `docs/l2-uk-en/A2-CURRICULUM-V3.md`

### PRIORITY 2: Test builds on different module types
- B1 module (4000 words, skeleton→flesh)
- HIST seminar (5000 words, full Ukrainian, `v6-write-seminar.md`)
- B1 writer should be Gemini (better at long Ukrainian content)

### PRIORITY 3: Literary text ingestion
- Run: `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest.py --all-literary --batch-size 16`
- Adds Грушевський тт. 4-10 + Конституція Орлика to RAG

### Open V6 issues
- #985: Preflight auto-fixes for plans
- #984: Automated plan review
- #998: Skeleton→flesh (implemented, needs B1 test)
- #1014: Dynamic golden examples
- #1016: RAG-backed exercise generation for B1+
- #1018: VERIFY flag handling
- #1020: Seminar plan conversion (mostly done, script bug on FOLK/OES/RUTH)

### Behavioral reminders
- CLAUDE.md and MEMORY.md both have behavioral rules — READ THEM
- No tech debt, finish everything in same commit
- Use tracking docs (`DICTIONARY-PIPELINE-STATUS.md`)
- Natural dialogues from textbooks, not invented
- Plans must have references
- Gemini at 0.2% usage — push more work through him
