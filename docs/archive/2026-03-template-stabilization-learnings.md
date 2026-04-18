---
name: template-stabilization-learnings
description: Lessons from a2/6 template stabilization session (2026-03-14) — what broke, what we fixed, what still needs work
type: project
---

## Template Stabilization Learnings (2026-03-14)

First real e2e test of build→review→consult→fix loop on a2/6 being-and-becoming.

### What We Fixed (in pipeline code)

1. **Stress marks (U+0301) break word counting** — regex `[\u0400-\u04ff]{2,}` splits `опи́суємо` into 2 words. Fixed: include `\u0301` in char class. Caused 42 false COMPLEXITY violations.
2. **Summary section missing from 35+ A2 plans** — `_build_exact_section_titles()` now auto-injects Підсумок if plan omits it.
3. **Plan points invisible to Gemini** — only H2 names and word counts were sent. Now includes `points:` bullet list under each section. KEY for plan adherence.
4. **Review opt-in → on by default** — `--skip-review` replaces old `--review` flag.
5. **Prompt preflight** (#858) — Gemini self-reviews prompt against audit gates before building.
6. **Model fallback on timeout/hang** — pro→flash when dispatch returns empty output.
7. **Research timeout 600→900s** — RAG tool calls need more time. Also fixed in assess_research.
8. **`run_verify()` content_only kwarg** — was passing unsupported kwarg, crashing escalation.
9. **`plan_adherence` "12+" string crash** — activity_hints items field is string not int.
10. **Always use beginner-full-rag.md** — removed rag toggle, non-RAG template was stale.
11. **Bidirectional model fallback** — pro↔flash on rate limit or timeout.

### What We Fixed (in templates)

1. **Table immersion contradiction** — "highest immersion density" vs "tables = ZERO". Fixed: WARNING label.
2. **Dialogue cap too low** — 2-3 max → 4-6 substantial dialogues.
3. **Example cap too low** — 4-6 → 10-15 per grammar point.
4. **"Paragraphs = English" blocks immersion** — added mandatory Reading Practice blocks (5-8 Ukrainian sentences after each section).
5. **Metalanguage policy** — blanket ban → level-appropriate (A2+ can use terms with first-use gloss).
6. **Word ceiling not enforced** — over ceiling now = FAIL.
7. **Beginner lesson arc** — WELCOME→PREVIEW→PRESENT→PRACTICE→CELEBRATE structure.
8. **Prioritize score-generating containers** — lists/dialogues over tables for immersion.
9. **Research template** — batched tool calls (2 rounds not 4 sequential), fewer mandatory searches.

### What Still Needs Work

1. **Activity separation** — user wants content and activities as separate phases. Content first, activities later. Not implemented.
2. **Core/seminar templates need same immersion fixes** — only beginner template was updated.
3. **`beginner-content.md` broken** — has unfilled placeholders, bypassed but should be deleted or fixed.
4. **Review→fix loop can undo validate's work** — review sometimes triggers content rebuild, resetting immersion from 45% back to 20%. Architecture issue.
5. **Preflight auto-fix** — preflight identifies issues but doesn't auto-fix HIGH issues in the prompt yet.
6. **VESUM false positives on names/abbreviations** — Микола, Олег, IT flagged as unknown. Non-blocking but noisy.
7. **Gemini hangs (Interactive Mode)** — some dispatches hang silently. Gemini says it's missing the ROLE trigger or context bloat. Timeout fallback helps but doesn't fix root cause.
8. **Dashboard v4→v5 cleanup** — #857 done for playgrounds, but API state_helpers still has v4 phase logic.

### Key Metric: a2/6 Progress

| Attempt | Immersion | Review Score | Blockers |
|---------|-----------|-------------|----------|
| Pre-consultation | 16.3% | N/A | Table contradiction, no review |
| Post-consultation #2 | 57.7% | N/A | 42 false COMPLEXITY (stress marks) |
| After stress fix | 20.8% | N/A | Wrong template (beginner-full.md) |
| After template fix | 21.1% → 45.1% (6 fix loops) | N/A | Validate pushed it over |
| After rebuild + review | 46.1% | 7.9/10 | Plan adherence (missing points) |
| Next attempt (pending) | ? | Target: 9/10 | Points injection + beginner arc |

**Why:** Understanding the immersion calculation and template contradictions was the key breakthrough. Gemini follows instructions literally — contradictory instructions = bad output.

**How to apply:** When touching ANY template, run it through prompt preflight first. Ask Gemini to review its own instructions.
