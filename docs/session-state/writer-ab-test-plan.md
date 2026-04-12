# Writer A/B Test Plan

## Goal

Determine which agent produces the best content when writing Ukrainian language modules. Test on B1 (grammar-heavy) and B2 (register/thematic).

## Test modules

| Level | Module | Slug | Wiki packet | Why this one |
|---|---|---|---|---|
| B1 | M25: Housing and Renting | housing-and-renting | ✅ 300+ lines | Communicative (not pure grammar), good B1 representative |
| B2 | Passive Voice System | passive-voice-system | ✅ 201 lines | The ONLY B2 module with a wiki packet — no choice |

## Writers to test

| Writer | Mode | Tool access | Model |
|---|---|---|---|
| **Gemini** | `--writer gemini-tools` | MCP (live VESUM, sources, textbooks) | gemini-3.1-pro-preview |
| **Codex** | `--writer codex-tools` | Shell-out (same tools, different protocol) | gpt-5.4 |
| **Claude** | `--writer claude-tools` | MCP (live VESUM, sources, textbooks) | claude-opus-4-6 |

Claude is backup — test it if budget allows, but Gemini vs Codex is the primary comparison.

## Reviewer

Cross-agent: whoever DIDN'T write reviews. For the A/B:
- Gemini's output → Codex reviews (or Claude as backup reviewer)
- Codex's output → Gemini reviews
- Claude's output → Gemini reviews

## Commands (USER runs these, not Claude)

```bash
# ── B1 test: housing-and-renting ──

# Writer A: Gemini
.venv/bin/python scripts/build/v6_build.py b1 25 --step write --writer gemini-tools

# Writer B: Codex  
.venv/bin/python scripts/build/v6_build.py b1 25 --step write --writer codex-tools

# Writer C (backup): Claude
.venv/bin/python scripts/build/v6_build.py b1 25 --step write --writer claude-tools

# ── B2 test: passive-voice-system ──

# Writer A: Gemini
.venv/bin/python scripts/build/v6_build.py b2 1 --step write --writer gemini-tools

# Writer B: Codex
.venv/bin/python scripts/build/v6_build.py b2 1 --step write --writer codex-tools
```

**Note**: Each write overwrites the previous output. Save/rename the output file between runs:
```bash
cp curriculum/l2-uk-en/b1/housing-and-renting.md curriculum/l2-uk-en/b1/housing-and-renting.gemini.md
# then run codex writer
cp curriculum/l2-uk-en/b1/housing-and-renting.md curriculum/l2-uk-en/b1/housing-and-renting.codex.md
```

## Evaluation criteria

| Criterion | Weight | How to measure |
|---|---|---|
| **Immersion** | 25% | `calculate_immersion()` — must be 90-100% for B1 |
| **Word count** | 15% | Must meet 4000 target |
| **Naturalness** | 20% | Human read + LLM review score |
| **Activity quality** | 15% | Activity density, type diversity, item count |
| **Vocabulary** | 10% | VESUM verification pass rate |
| **Tool usage** | 15% | Did the writer actually USE the tools (verify words, search textbooks)? |

## Expected timeline

- Each write step: ~5-10 min per module
- Review: ~5 min per module  
- Total: ~1 hour for full A/B on both modules
- Decision: same day
