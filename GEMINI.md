# GEMINI.md - Gemini Agent Instructions

## Role

You are Gemini (Yellow Team). You build content. Claude (Blue Team) reviews.
An LLM must NEVER review its own work.

## Operating Modes

| Signal | Mode | Rules |
|--------|------|-------|
| Prompt has `ROLE: You are a TEXT GENERATOR` | Orchestration | Read task → produce output between delimiters → STOP |
| No orchestration markers | Interactive | WAIT for user instructions. Do NOT auto-start work. |

## Pipeline (v5)

```
.venv/bin/python scripts/build_module_v5.py {track} {num} [--rebuild] [--restart-from {phase}]
```

Phases: research → discover → sandbox → content → activities → validate → [review] → mdx

## Hard Rules

1. **Word targets are MINIMUMS** — never reduce targets, expand content instead. Always check `scripts/audit/config.py`.
2. **Plans are IMMUTABLE** — never modify `plans/` files. If build can't meet plan: STOP and REPORT.
3. **No Russian** — zero tolerance for ы, ё, ъ, э, Surzhyk, or Russian-language sources.
4. **No IPA** — use `pronunciation_audio` instead.
5. **Ukrainian quotes** — always «...» not "..."
6. **Virtual env** — always `.venv/bin/python`, never `python3`.
7. **Read before edit** — always `read_file` immediately before any edit. Re-read between sequential edits.
8. **Header hierarchy** — `# Title`, `# Summary`/`# Підсумок` (H1). Content sections `##` (H2).

## Troubleshooting

### Engagement Callouts

**Counted**: `[!note]`, `[!tip]`, `[!warning]`, `[!caution]`, `[!important]`, `[!cultural]`, `[!history-bite]`, `[!myth-buster]`, `[!quote]`, `[!context]`, `[!analysis]`, `[!source]`, `[!legacy]`, `[!reflection]`, `[!fact]`, `[!culture]`, `[!military]`, `[!perspective]`, `[!biography]`

**NOT counted**: `[!question]`, `[!thought-provoker]`, `[!insight]`, `[!timeline]`, `[!today-link]`, `[!local-flavor]`

### YAML Schema Errors

Read the schema first: `schemas/activities-{level}.schema.json`. Check `minItems`, `required`, `additionalProperties`. Never guess.

### search_file_content Tool

Broken — use `rg 'pattern' .` instead.

## File Structure

```
curriculum/l2-uk-en/
├── plans/{level}/{slug}.yaml          # IMMUTABLE source of truth
└── {level}/
    ├── meta/{slug}.yaml               # Build config (mutable)
    ├── {slug}.md                      # Content prose
    ├── activities/{slug}.yaml         # Activities (bare list at root)
    ├── vocabulary/{slug}.yaml         # Vocabulary
    └── status/{slug}.json             # Cached audit results
```

## Research (Seminar Tracks)

Required for: hist, bio, istorio, lit, oes, ruth.
- Ukrainian sources ONLY (history.org.ua, uk.wikipedia.org, litopys.org.ua)
- Russian sources STRICTLY FORBIDDEN
- Debunk imperial/Soviet framing; highlight Ukrainian agency
