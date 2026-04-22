# A.8 — Narrow Canary Protocol: enriched-corpus vs baseline

> **Status:** DRAFT — written 2026-04-22 night while wire-up dispatch (#1410) is in flight. Adopt + refine when ready to execute. Per EPIC #1365.

## Purpose

A.8 is the **measurement that justifies (or invalidates) the entire wiki bootstrap**. Build 1 A1 module two ways:

1. **Baseline** — current pipeline retrieval surface (textbooks + literary + Wikipedia + external; no `ukrainian_wiki`)
2. **Enriched** — current pipeline retrieval surface PLUS `ukrainian_wiki` corpus via the new MCP `search_sources` tool (#1410)

If enriched ≥ baseline on quality + faithfulness metrics, scale to A.9 (batch A1 rebuilds). If not, the bootstrap doesn't earn its keep — re-think before scaling.

## Slug selection

**Pick:** `at-the-cafe` — **L2-UK-EN A1/M18** (English-speaker immersion module)

Build target output path: `curriculum/l2-uk-en/a1/at-the-cafe.md`
L1-UK source artifact (retrieved from): `wiki/pedagogy/a1/at-the-cafe.md`

Reasoning:
- Has a strong scenario-specific Ukrainian wiki article on the L1-UK side (`wiki/pedagogy/a1/at-the-cafe.md`) — meaningful enriched-side delta is plausible
- Plan exists and is locked at `curriculum/l2-uk-en/plans/a1/at-the-cafe.yaml`
- Concrete user-facing scenario (ordering at a café) — quality differences are inspectable by a non-expert
- Dialogue-heavy, which is where naturalness regressions are easiest to spot
- NOT `sounds-letters-and-hello` — that one's been beaten on for weeks; we want a fresh delta-detection signal, not a recovery story
- NOT a checkpoint module — checkpoints aggregate across slugs; the wiki bootstrap signal would be diluted

**Why this distinction matters:** the canary is measuring whether the L1-UK Ukrainian wiki corpus, surfaced via the new `search_sources` MCP tool (#1410), changes the quality of L2-UK-EN module output. The destination is always the English-speaker module — the L1-UK wikis are corpus input, never the build target.

## Pipeline parameters (held constant across both arms)

- Writer: Gemini opus default (`gemini-3.1-pro-preview`)
- Reviewer: Codex (current canonical reviewer per the 2026-04-18 PM switch)
- Effort: writer + reviewer both at default
- Plan version: lock the current `at-the-cafe.yaml` version. Bump it ONLY if the plan itself has a fixable bug surfaced during the canary
- Hard timeout per phase: default
- All other v6 settings: default

## The single variable

Whether the writer can call the new `mcp__sources__search_sources` MCP tool (which includes ukrainian_wiki).

**Baseline arm:** patch the writer prompt to remove the `search_sources` tool reference. Or equivalently: temporarily revert the prompt change from #1410. Use a PROMPT-LEVEL toggle rather than disabling the MCP tool itself, so the toggle is reversible per-build.

**Enriched arm:** writer prompt as shipped after #1410 merges (search_sources is preferred default).

Both arms use the SAME plan, SAME reviewer, SAME models, SAME parameters. Only the retrieval surface differs.

## Measurements

### Quantitative (deterministic — runs immediately after each build)

| Metric | Source | Comparison |
|---|---|---|
| **Word count** | `audit/{slug}.json` `gates.lesson` | Both must hit ≥1200 (A1 target). Baseline-vs-enriched difference is informational only. |
| **Vocabulary unique types** | audit `gates.vocabulary` | Both must hit ≥30. Difference informational. |
| **Activity count + variety** | audit `gates.activities` | Both must hit minimum. |
| **Naturalness score** | audit + reviewer | Threshold 8/10. **Primary head-to-head metric.** |
| **Reviewer score (mean across 9 dims)** | review YAML | **Primary head-to-head metric.** |
| **Russianism / Surzhyk / calque flags** | linter + style-guide check | Both should be 0. Any > 0 is a regression. |
| **VESUM coverage (% of words verified)** | post-build verifier | Both should hit ≥99%. |
| **Citation count** (mentions of textbook authors) | grep | Enriched should be ≥ baseline (more textbook DNA flowing through). |

### Qualitative (the actual signal)

Three things to look at by reading both outputs side by side:

1. **Dialogue authenticity** — does the café dialogue feel like real Ukrainians ordering coffee? Or textbook-drill ("I would like coffee. Yes, here is your coffee.")? The Ukrainian wiki for `at-the-cafe` has authentic patterns; the baseline corpus doesn't. **If enriched is more authentic, the bootstrap works.**
2. **Pedagogical lineage** — does enriched cite/echo Ukrainian textbook authors (Большакова, Заболотний, etc.) more than baseline? More authentic-Ukrainian-pedagogy DNA = bootstrap working.
3. **Decolonization register** — does either version slip Russian-tradition framings (e.g., translating menu items via Russian cognates, calque sentence structures)? If enriched is cleaner, bootstrap working.

### Pass condition

**Enriched arm is adopted as the new default if:**
- All quantitative gates green on enriched (no regression)
- Reviewer mean score on enriched ≥ baseline reviewer mean score (within ±0.2 noise margin treated as tie)
- AT LEAST ONE qualitative dimension shows enriched is meaningfully better OR the two are tied

**Enriched arm is REJECTED (back to design) if:**
- Any quantitative gate fails on enriched but passes on baseline
- Enriched reviewer score < baseline by > 0.2
- Enriched introduces Russianism / Surzhyk flags that baseline doesn't have
- All 3 qualitative dimensions are tied or worse on enriched (no observable lift)

**TIE (proceed but flag):**
- Quantitative tied + qualitative tied → bootstrap doesn't HURT but doesn't HELP. Still proceed to A.9 because the cost (zero) is justified by future B1+ wikis where the corpus is denser, but document the canary as "no measurable lift on at-the-cafe" so we don't oversell.

## Execution sequence (when ready)

```bash
# 0. Verify wire-up landed
gh issue view 1410 --json state                            # CLOSED
sqlite3 data/sources.db "SELECT COUNT(*) FROM ukrainian_wiki WHERE article_slug='at-the-cafe'"  # > 0

# 1. Baseline arm
git switch -c canary-baseline
# Patch v6-write.md: remove search_sources from preferred-tools section
.venv/bin/python scripts/build/v6_build.py a1 18 --slug at-the-cafe --force --writer gemini-tools --reviewer codex-tools --label baseline-pre-wiki
# Capture artifacts: curriculum/l2-uk-en/a1/at-the-cafe.md, audit JSON, review YAML
mv curriculum/l2-uk-en/a1/at-the-cafe.md docs/experiments/a8-canary/baseline/at-the-cafe.md
mv curriculum/l2-uk-en/a1/audit/at-the-cafe.json docs/experiments/a8-canary/baseline/audit.json
mv curriculum/l2-uk-en/a1/review/at-the-cafe-review-*.yaml docs/experiments/a8-canary/baseline/

# 2. Enriched arm (revert prompt patch)
git stash  # or revert the prompt patch
.venv/bin/python scripts/build/v6_build.py a1 18 --slug at-the-cafe --force --writer gemini-tools --reviewer codex-tools --label enriched-with-wiki
mv curriculum/l2-uk-en/a1/at-the-cafe.md docs/experiments/a8-canary/enriched/at-the-cafe.md
mv curriculum/l2-uk-en/a1/audit/at-the-cafe.json docs/experiments/a8-canary/enriched/audit.json
mv curriculum/l2-uk-en/a1/review/at-the-cafe-review-*.yaml docs/experiments/a8-canary/enriched/

# 3. Run measurement script
.venv/bin/python scripts/experiments/a8_compare.py baseline enriched > docs/experiments/a8-canary/measurement-report.md

# 4. Side-by-side qualitative read (Claude + user, ~30 min)
# 5. Decide: adopt / reject / tied
```

`scripts/experiments/a8_compare.py` doesn't exist yet — write it as part of A.8 setup. It reads the two audit JSONs + review YAMLs and prints a structured comparison table (the Quantitative section above).

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Both arms hit the writer-prompt hardening together (#1401) — can't isolate retrieval-surface effect from prompt-effect | Hardening was merged 2026-04-22 17:34 UTC, BEFORE this canary. Both arms use the same hardened prompt. ✅ |
| Reviewer favors enriched purely because it cites more textbook authors (citation gaming) | Reviewer rubric tests for INVENTED citations too (Hard Rule #11). Manual qualitative read catches surface citation-padding. |
| Single slug is a poor sample size | A.8 is intentionally narrow ("Cheap — one measurement before scaling" per EPIC). If the result is ambiguous, run A.8b on a second slug (`my-family` or `colors`) before proceeding to A.9. |
| Plan bug surfaces during canary | Bump plan version per Rule 7. Re-run both arms on the bumped plan. |
| Native reviewer not available before A.8 | A.8 doesn't require native reviewer — that's A.7, separate track. A.8 measures pipeline output, not human-validated quality. |

## What A.8 is NOT

- NOT the full quality validation — that's A.9 + native reviewer (A.7)
- NOT a guarantee of B1+ quality — those tracks have different corpus density
- NOT a publish gate — modules from A.8 are experimental artifacts in `docs/experiments/a8-canary/`, not shipped

## After A.8

| Result | Next step |
|---|---|
| PASS | A.9 — batch rebuild remaining stale A1 modules using the now-validated enriched-corpus pipeline |
| TIE (proceed-with-caution) | A.8b on second slug to confirm; if TIE again, proceed to A.9 with caveat documented |
| FAIL | Diagnose: is the wiki content the right register? Is the retrieval ranking surfacing the right chunks (#1282)? Is the prompt instructing the writer to actually use the new tool? File specific follow-ups, do NOT scale to A.9. |

## Open questions to resolve at execution time

1. Should baseline use `search_text` (textbooks-only) only, or also exclude wikipedia and external? **Default:** keep all current corpora ON in baseline; only `ukrainian_wiki` is the variable. Otherwise we're measuring two things at once.
2. Reviewer is Codex. Does Codex have any built-in bias for/against newly-introduced source corpora? **Mitigation:** ask Codex's adversarial-review tool to audit its own review for bias before we trust the score delta.
3. If both arms show writer ignored the new tool entirely (didn't actually call `search_sources`), the canary is invalid. Detect via writer-side tool-call logs. If observed, treat as a wire-up bug, not an enriched-arm result.

---

**Owner: Claude (architecture) + user (decision).** Execute when wire-up (#1410) and ideally also #1282 (excerpt selection) have landed.
