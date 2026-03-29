# Session Handoff — 2026-03-29

## What was accomplished

### A1 Plans — ALL 55 reviewed and fixed
- All 8 phases (A1.1–A1.8) adversarial-reviewed by Gemini
- ~25 fixes: forward-references, English-centric framing, sequencing errors, activity distractors
- M01 plan rewritten v1.4 (removed false-friend categorization, focused on Ukrainian phonetics pedagogy)
- M05 plan: added personal pronouns section (was a curriculum gap)
- Global friction gf-012 added: memorized chunks allowed before grammar is formally taught

### Content built — 3 modules
| Module | Score | Audit | Status |
|--------|-------|-------|--------|
| M01 sounds-letters-and-hello | 9.9/10 | ✅ PASSED | Shipped |
| M02 reading-ukrainian | 9.7/10 | ✅ PASSED | Shipped |
| M03 special-signs | 8.5/10 | ✅ PASSED | Needs rebuild (prompt fixes applied after this build) |

### Pipeline fixes (15)
1. Pre-verify timeout 300→600s + retry on failure
2. Section rewrite: backup content before, restore on validation failure
3. Section rewrite timeout 300→600s
4. **Review fixes GUARANTEED** on every exit path (no more missed typos)
5. Score ≥9.0: apply fixes without re-review (prevents degradation)
6. Video embeds: removed from lesson tab entirely (workbook activities handle them)
7. Video embeds: stripped from reviewer's view
8. Motivational closers: stripped deterministically in post-process
9. Word ceiling: removed (targets are MINIMUMS, no upper limit)
10. RAG query.py: removed 500-char text truncation (was slicing textbook chunks)
11. Knowledge packet: 800-char sentence-boundary truncation, 20 excerpts max, 2+ per section guaranteed
12. МійКлас: lightpanda headless browser for JS-rendered content extraction
13. Skeleton template: respects plan's Підсумок format (self-check Q&A vs prose)
14. Write prompt: positive BAD/GOOD examples for dialogues and tone
15. Gemini review: strip markdown code fence wrapping from output

### Audit fixes (4)
1. A1 quiz min_len: 1 (single-word prompts valid for phonetics quizzes)
2. Phonetics phase M01-M03: exempt GLOSSARY_LIST, INLINE_ENGLISH, ROBOTIC_STRUCTURE, METALANGUAGE
3. VESUM: skip single letters and syllable fragments for M01-M03 only
4. Global friction gf-012 saved to `docs/rules/global-friction.yaml`

### Bug fixes
- `.gemini/settings.json` kept getting deleted by `deploy_prompts.sh` rsync --delete — fixed by adding to `gemini_extensions/` source directory
- Anthropic rate limits investigated — metering bug on Max 20x plan, GitHub issue #38335

## Next session priorities

### 1. Rebuild M03 (special-signs)
The write prompt now has positive dialogue/tone examples. The knowledge packet builder now guarantees 2+ excerpts per section (apostrophe content was missing). Rebuild should produce much better dialogues and tone.
```bash
.venv/bin/python scripts/build/v6_build.py a1 3 --writer gemini-tools --reviewer gemini-tools
```

### 2. Build M04–M07 (rest of A1.1 phase)
All plans reviewed and fixed. Pipeline is solid. These should build cleanly:
- M04 stress-and-melody
- M05 who-am-i
- M06 my-family
- M07 checkpoint-first-contact

### 3. Investigate M03 knowledge packet
Check if the rebuild produces apostrophe rule content from Захарійчук. If not, the RAG query for "Апостроф" needs debugging — the content IS in Qdrant but ColBERT reranking may be pushing it down.

### 4. Open issues
- #1093 EPIC Phase 4 (Ship A1) — in progress, M01-M02 shipped
- #1070 Gemini MCP tool usage — pre-verify works, needs successful build verification
- Rate limits — monitor Anthropic situation, work off-peak if needed

## Services
```bash
./services.sh status  # RAG on 8766, API on 8765, Starlight on 4321
```

## Build command
```bash
.venv/bin/python scripts/build/v6_build.py a1 {N} --writer gemini-tools --reviewer gemini-tools
```

## Key learnings for next session
- The write prompt's dialogue examples made the biggest quality difference — positive examples > negative rules
- Knowledge packet budget fairness (2+ per section) prevents sections from being starved
- The review fix guarantee catches every typo — no more "accepting as final" with known errors
- M01 took a month because it exposed every pipeline bug. M02 built in 20 minutes. The infrastructure investment is paying off.
