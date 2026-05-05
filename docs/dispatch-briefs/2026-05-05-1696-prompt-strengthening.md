# Codex dispatch brief — Strengthen V7 prompts in PR #1696 (CoT mandate + per-dim evidence + heritage-defense)

> **Branch base:** existing branch `claude/1673-1661-cot-tier1-prompts` (PR #1696 DRAFT)
> **Worktree:** `.worktrees/dispatch/codex/1696-prompt-strengthening/`
> **Branch:** `codex/1696-prompt-strengthening` (separate branch — will merge into #1696's branch via PR-into-PR pattern, OR open a fresh PR that supersedes #1696)
> **Mode:** danger
> **Hard timeout:** 3600s
> **Effort:** medium
> **Reviewer:** Claude (cross-family; you are author)

## Goal

Apply your own Q4+Q5+Q6+Q7 verbatim edits from msg 528 to the V7 writer + reviewer prompts in PR #1696. Tonight's bakeoff baseline showed all writers register 0 CoT emissions — partly because we ran on main (old prompts), but Q4 of your diagnosis shows that even #1696's NEW prompts have soft language that won't actually flip emissions to 1+. The edits below are the verbatim text YOU produced; this dispatch is just applying them and adding the heritage-defense language you specified. Edit 5 (Slovnyk.me) was originally a deferral note, but #1717 has since shipped `mcp__sources__search_heritage` + `mcp__sources__search_slovnyk_me`, so that edit has been re-cast as explicit tool routing — see the updated Edit 5 section.

## Pre-flight

The dispatching orchestrator passes `--base claude/1673-1661-cot-tier1-prompts`, so the worktree's branch (`codex/1696-prompt-strengthening`) is already branched from #1696's tip. You should NOT run `git checkout -b ...` — the branch already exists.

1. Fetch and rebase onto current `origin/main` so #1706, #1711, #1714, #1716, #1717 are present:
   ```bash
   git fetch origin main
   git rebase origin/main
   ```
   Resolve conflicts (most likely in `linear-write.md` since #1706 touched the `{X}` fix and #1716 strengthened the unnamed-fence prompt). Prefer the main-side change when conflicting on infrastructure; preserve #1696's CoT/Tier-1 additions when conflicting on prompt body.

2. Confirm both prompt files exist before applying edits:
   ```bash
   ls -la scripts/build/phases/linear-write.md scripts/build/phases/linear-review-dim.md
   ```

## Edits (verbatim from your msg 528)

### Edit 1 — Writer mandatory `<plan_reasoning>` block (Q4)

Replace `scripts/build/phases/linear-write.md` lines 11-47 (the soft-CoT preamble) with:

```md
## Mandatory visible verification block (emit BEFORE drafting — #1673/#1661)

Before the four artifact fences, you MUST emit one `<plan_reasoning section="...">...</plan_reasoning>` block for each contracted section. This is not optional hidden thinking. If any section lacks this visible block, the writer has failed the protocol.

Each block MUST contain:
1. `word_budget`: section word allocation and running total check against `{WORD_TARGET}±5%`.
2. `plan_vocab`: required plan-vocabulary lemmas used in this section, with the exact Ukrainian sentence that grounds each lemma.
3. `register`: the immersion ratio from the Immersion Rule and how this section preserves it.
4. `teaching_sequence`: which Knowledge Packet facts/citations this section uses.
5. `verification`: explicit Tier-1 checks: VESUM/modern-form check for example words, source-grounding check for dictionary/style claims, quote-contiguity check for attributed quotes, and heritage-defense check for possible archaism/historism/dialectism versus Russianism/surzhyk.

Only after all `<plan_reasoning>` blocks are complete and passed may you emit the four fenced artifact blocks.
```

Replace `linear-write.md` lines 88-89 (the "Return only these four fenced blocks" instruction) with:

```md
Return the visible `<plan_reasoning>` blocks first, then exactly these four fenced blocks, in this exact order. Do not add any other prose before, between, or after them.
```

**Important:** use `<plan_reasoning>` not `<Fact_Check>` — telemetry detects writer CoT via `<plan_reasoning>` blocks at `scripts/build/linear_pipeline.py:993-1008`. If you change to `<Fact_Check>` you'd also have to change telemetry — out of scope here.

### Edit 2 — Reviewer per-dim evidence schema (Q5)

Replace `scripts/build/phases/linear-review-dim.md` lines 37-39 (single-quote evidence) with:

```md
The JSON response MUST include `evidence_quotes` with 3 verbatim quotes from step 1 and `rubric_mapping` explaining how each quote maps to `{DIM}` before the score. The `evidence` field MUST be one of those verbatim quotes, wrapped in escaped quotes. A summary or paraphrase in any evidence field is a reviewer-protocol failure.
```

Replace `linear-review-dim.md` lines 85-89 (the JSON schema example) with:

```md
Return only JSON:

\`\`\`json
{"score": 0.0, "evidence_quotes": ["verbatim quote 1", "verbatim quote 2", "verbatim quote 3"], "rubric_mapping": "Quote 1: ...; Quote 2: ...; Quote 3: ...", "evidence": "\"verbatim quote from evidence_quotes\"", "verdict": "REVISE"}
\`\`\`
```

### Edit 3 — Writer heritage-defense (Q6, writer side)

Replace `linear-write.md` lines 63-67 (current "modern Ukrainian" rule) with:

```md
2. **Modern Ukrainian + heritage-defense discipline.** Default to post-2019 Pravopys standard forms for learner-facing standard Ukrainian. However, NEVER classify a word as Russianism, surzhyk, or calque merely because it is archaic, historical, dialectal, or shares Proto-Slavic roots with Russian. For any non-modern or suspicious form, verify with VESUM/check_modern_form plus available historical/etymological evidence (`search_grinchenko_1907`, `search_esum`, literary/wiki source context). If authentic but non-standard, keep it only when pedagogically required, tag it `[Archaism]`, `[Historism]`, or `[Dialectism]`, give the modern standard equivalent, and briefly state its Ukrainian heritage. If unverified, omit or emit `<!-- VERIFY: heritage status for "X" unresolved -->`.
```

### Edit 4 — Reviewer heritage-defense (Q6, reviewer side)

Replace `linear-review-dim.md` lines 73-78 (current "modern form guard") with:

```md
D. **Modern Ukrainian + heritage-defense audit (naturalness, decolonization).** Flag historical / Old East Slavic / Russian-shadow / pre-Pravopys-2019 forms presented as modern Ukrainian. Also flag the opposite error: authentic Ukrainian archaisms, historisms, or dialectisms mislabeled as Russianism/surzhyk/calque without VESUM/check_modern_form plus historical/etymological/source-context verification. Authentic non-standard forms must carry `[Archaism]`, `[Historism]`, or `[Dialectism]`, a modern standard equivalent, and a brief heritage note. Missing tag/equivalent → FLAG `untagged heritage form`; false Russianism claim → FLAG `heritage form misclassified`.
```

### Edit 5 — Heritage-defense MCP tool routing (Q7 — supersedes the original deferral language)

> **Update 2026-05-05 night**: PR #1717 shipped `mcp__sources__search_heritage` and `mcp__sources__search_slovnyk_me` (commit `567ee66094`). The original Q7 deferral wording ("Slovnyk.me is the desired future aggregator … until then, do not claim Slovnyk.me verification") is now obsolete. Replace it with explicit tool routing instead.

Find the source-citation discipline section in `linear-write.md` (around lines 68-72). Add this paragraph at the end of that section, OR in the heritage-defense section if it's adjacent:

```md
For heritage defense, route lookups through the canonical MCP tools in this order: (1) `mcp__sources__search_heritage` is the primary entry point — it merges Грінченко 1907, ЕСУМ, slovnyk.me modern/regional dictionaries, and Антоненко-Давидович style warnings, ranking pre-Soviet attestations above modern-only rows. (2) Use `mcp__sources__search_slovnyk_me` only when you specifically need a slovnyk.me single-source result (e.g. СУМ-20 or a regional dictionary not surfaced by `search_heritage`). (3) Standard tools — `check_modern_form` (VESUM), `search_grinchenko_1907`, `search_esum`, literary corpus, and compiled wiki/source citations — remain valid evidence sources alongside the merged heritage tool. Cite the tool name and the dictionary slug in your `<plan_reasoning verification="...">` block. Do not claim heritage verification without naming a concrete tool result.
```

Apply the same routing rule to `linear-review-dim.md` so the reviewer can mirror-check it. Add this sentence at the end of section D (the heritage-defense audit you just wrote in Edit 4):

```md
Reviewers verifying a heritage flag MUST themselves call `mcp__sources__search_heritage` (or `mcp__sources__search_slovnyk_me` for a slovnyk.me-only check) before sustaining or rejecting a heritage claim. A reviewer evidence_quote that asserts heritage status without a tool-grounded citation is a reviewer-protocol failure.
```

If the section structure makes it natural to inline the rule, that's fine — exact placement is your call as long as the wording is preserved verbatim and lands somewhere both writer + reviewer agents will see it during prompt processing.

## Validation

1. After applying edits: `.venv/bin/pytest tests/test_prompt_template_render.py -v` — must pass (the render guard from #1706 catches any unregistered placeholders).
2. Word-count diff: `wc -l` on both prompts before vs after — additions should be ~30-50 lines net.
3. Verify the `<plan_reasoning>` token spelling is consistent with `linear_pipeline.py:993-1008` (telemetry parser).

## Get Claude review

```bash
git add -A
git diff --cached > /tmp/1696-prompt-strengthening-diff.txt
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
    "Adversarial review for #1696 prompt strengthening. Read /tmp/1696-prompt-strengthening-diff.txt. Focus: (1) does the visible `<plan_reasoning>` block requirement actually preclude hidden CoT (check the contradicting language at original lines 88-89 is fully replaced)? (2) heritage-defense — is the writer-prompt language tight enough that a writer would NOT flag an archaism as Russianism? (3) reviewer JSON schema — does the new `evidence_quotes` array match what telemetry parser at linear_pipeline.py:1615-1652 actually extracts? (4) Heritage-MCP routing (Edit 5) — is the writer + reviewer language specific enough that an agent will actually call `mcp__sources__search_heritage` (or `search_slovnyk_me`) and cite the tool result, rather than fabricating a 'verified via Slovnyk.me' claim or skipping the lookup entirely?" \
    --task-id 1696-prompt-strengthening-review
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1696-prompt-strengthening-review)` trailer.

## PR strategy

Open as a fresh PR titled `feat(prompts): mandate visible <plan_reasoning> + per-dim evidence + heritage-defense (#1673 #1661 #1696 follow-up)`. In PR body, note that this supersedes #1696's pending prompt diff — once this PR merges, #1696 should be closed (or rebased on main and converted to housekeeping).

DO NOT merge #1696 first; this branch already has #1696's foundational changes via the rebase, plus the strengthening edits on top.

## Constraints

- No auto-merge.
- Don't change `linear_pipeline.py` (gate fixes are in a separate parallel dispatch).
- Verbatim wording above is non-negotiable — don't paraphrase. If a snippet doesn't fit cleanly into existing structure, ask in the PR body rather than improvising.
