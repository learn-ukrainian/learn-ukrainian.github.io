---
date: 2026-05-21
session: "Evening (continued) — 5 PRs merged in cascade, wiki_coverage_gate now PASSES 18/18 on build #10, exposed 6th issue at wiki_coverage_review YAML parse"
status: yellow-cascade-fix-shipping + 5-PRs-merged + 1-PR-pending-dismiss + 0-active-dispatches + 0-active-builds
main_sha: eea2571f87
main_green: clean (all blocking CI green; the `review / review` Gemini-auth advisory failure persists on every PR)
working_tree_dirty: true  # only build worktree + this handoff
prs_merged_this_continuation:
  - "#2185 fix(textbook_grounding): scope blockquote section_title to H1/H2 only"
  - "#2187 security(dashboards+ci): close 5 CodeQL alerts (2 XSS + dependabot cooldown)"
  - "#2193 fix(wiki_coverage_gate): _location_text section ends at sibling, not first H3 child"
  - "#2194 fix(etymology): drop featured slugs sertse + maty (unblock main CI)"
  - "#2197 fix(wiki_coverage_gate): accept | as alternative to ; in implementation_map inline shape"
prs_opened_this_continuation: []
direct_commits_to_main:
  - "1827d074f7 docs(session-state): afternoon evening cascade handoff (rebased into 2bc12d80df)"
active_dispatches: []
active_builds: []
builds_completed_this_continuation:
  - "#7 build/a1/my-morning-20260521-145016 — failed textbook_grounding (topical_mismatch on H3) → fixed by #2185"
  - "#8 build/a1/my-morning-20260521-180202 — failed wiki_coverage at 94.44% (H2 truncates at H3) → fixed by #2193"
  - "#9 build/a1/my-morning-20260521-190246 — failed wiki_coverage at 0% (writer used | as separator) → fixed by #2197"
  - "#10 build/a1/my-morning-20260521-195056 — wiki_coverage PASSED 18/18 (100%) but failed at wiki_coverage_review YAML parse on reviewer prose output"
headline_finding: "The 5-fix gate-detection cascade is RESOLVED for wiki_coverage_gate. Build #10 hit 18/18 (100%) wiki_coverage on first attempt of the post-merge cycle. **But the cascade is not yet terminating** — the build then failed at a 6th distinct phase `wiki_coverage_review` with a YAML parse error: the codex-tools reviewer emitted prose narrative (`I have verified all **18 obligat...`) where the gate expected a structured YAML document. This is a NEW phase, not a regression of any earlier fix. Total gate / parser / phase failures uncovered today: 6. CodeQL also batch-closed (5 alerts in PR #2187, 3 dismissable false positives remaining)."
next_session_first_item: "Investigate `wiki_coverage_review` YAML-shape requirement. Is the reviewer prompt asking for YAML and getting prose? Or is the parser strict about a header that the reviewer omits in 'all-clear' cases? Either way the fix is small (prompt or parser). Then rebuild #11 and likely promote — module.md + activities.yaml are passing every prior gate and have full obligation coverage."
---

# Evening (continued) handoff — five-fix cascade shipped, 18/18 wiki_coverage reached, 6th issue exposed

## TL;DR

The user said "continue" after the first evening handoff documented the 3-bug cascade. I drove 5 more PRs into main during this continuation:

| PR | Fix | Build that exposed it |
|---|---|---|
| #2185 | textbook_grounding: `_extract_blockquote_records` H1/H2 only | #7 (H3 ### Крок hijacked section_title) |
| #2187 | 5 CodeQL alerts (2 XSS + dependabot cooldown) | n/a — proactive batch |
| #2193 | wiki_coverage_gate: `_location_text` section ends at sibling, not first H3 child | #8 (H2 returned 620-char intro, missing H3 paradigm tables) |
| #2194 | etymology featured slugs (unblock main CI) | n/a — main CI was already broken by 7d3ab9d898 etymology regen |
| #2197 | wiki_coverage_gate: accept `\|` as alternative to `;` in implementation_map inline shape | #9 (writer used `\|` as field separator, 0/18 unknown_artifact) |

Build #10 closes the wiki_coverage portion of the cascade: `python_qg` ✅, `wiki_coverage_gate` ✅ **18/18 (100%)** in iter 1 batched (5 fixes), but then **failed at `wiki_coverage_review`** with a YAML parse error: codex-tools emitted prose narrative where the gate expected YAML document structure.

## Section 1 — Cascade timeline (all 10 builds)

| Build | Time UTC | Outcome | Failure phase | Root cause | Resolved by |
|---|---|---|---|---|---|
| #5 | 2026-05-21 10:10 | 21/22 python_qg | vesum_verified (stem fragment `**користу**-`) | morphological stem not in VESUM | PR #2173 (morning) |
| #6 | 14:06 | failed | wiki_coverage 83.33% | `_location_text` picked H1 title over H2 + YAML re-escape doubled apostrophes | PR #2184 (afternoon) |
| #7 | 14:50 | failed | textbook_grounding `topical_mismatch` | `_extract_blockquote_records` treated H3 as section_title | PR #2185 (this continuation) |
| #8 | 18:02 | failed | wiki_coverage 94.44% | `_location_text` ended H2 at first H3 child, excluding H3 sub-content | PR #2193 |
| #9 | 19:02 | failed | wiki_coverage 0% | `parse_implementation_map` only accepted `;` as field separator (writer used `\|`) | PR #2197 |
| #10 | 19:51 | failed | wiki_coverage_review YAML parse | reviewer emitted prose instead of YAML | not yet fixed — next session |

Each build closed ONE distinct issue before exposing the next. The cascade pattern documented in the first evening handoff (`docs/session-state/2026-05-21-evening-gate-cascade-three-bugs-one-after-another.md`) continued exactly as predicted: every fix unblocks one more gate phase, until you either reach `module_done` or find another brittle assumption.

## Section 2 — The 5-fix cascade in this continuation, by smoking gun

### PR #2185 — textbook_grounding H3 hijack

**Bug**: `_extract_blockquote_records` matched H1-H6 as `section_title`. Writer used `### Крок N: ...` H3 sub-headings (pedagogically clearer than build #6's inline-bold), and the H3's long technical title flooded `topic_tokens`, locking out concrete-content quotes from satisfying the topic overlap rule.

**Smoking gun**: Running `_textbook_grounding_gate` on unchanged build #6 artifacts (inline-bold Крок) returned `passed=True`. Same gate on build #7 artifacts (H3 Крок) returned `passed=False reason=topical_mismatch`. Same writer, same plan, same chunk_id retrievals — only the heading depth differed.

**Fix**: Restrict heading regex to `#{1,2}`. H3+ sub-step markers stay rendered but no longer hijack the topic context.

### PR #2193 — wiki_coverage section ends at sibling, not first H3 child

**Bug**: My PR #2184 made `_location_text` prefer the deeper heading (so H2 wins over H1 title collision), but it computed `end = next heading regardless of depth`. When chosen H2 was followed by H3 sub-section, the returned target text was only the H2 intro before the first H3 — H3+ sub-content excluded.

**Smoking gun**: Build #8 implementation_map's location for step-2 was `'§Дієслова на -ся (subsection "Крок 2: Зворотні дієслова + вимова")'`. The writer used a different (longer, wiki-aligned) H3 title, so only the parent H2 matched as a candidate. The 620-char H2 intro returned by `_location_text` lacked the substance terms step-2's wiki claim required (`прокидатися`, `одягатися`, `вмиватися`, `закінчення`) — all inside the H3 paradigm blocks.

**Fix**: Compute `end` as the next heading whose depth is `<=` chosen depth. H3+ sub-content stays in `target_text`. Re-running fixed gate on unchanged build #8 artifacts: **18/18 PASS**.

### PR #2197 — accept `|` as field separator in implementation_map inline shape

**Bug**: `parse_implementation_map` originally accepted only `;` as separator. The writer-prompt template at `scripts/build/phases/linear-write.md:29` describes the artifact field as `<module.md | activities.yaml | vocabulary.yaml | resources.yaml>` (pipes denote alternatives). The writer copied the `|` pattern as a field separator across all four fields:
```
- obligation_id: step-1 | artifact: module.md | location: §... | treatment: ...
```
With only `;` accepted, `artifact` value captured the rest of the line, all 18 obligations returned `unknown_artifact`, coverage stuck at 0%.

**Smoking gun**: Build #9 narrow iter 2 applied 20 valid content fixes but coverage stayed at 0.0 → 0.0 — the gate failed earlier on artifact identification. With fix: running `parse_implementation_map` on unchanged build #9 writer output returns all 18 entries with valid artifact filenames.

**Fix**: Extend the inline-field regex to accept either `;` or `|`. Symmetric value class `[^;|]+?`, lookahead `[;|]`.

### PR #2194 — etymology featured slug unblock

Main CI started failing on every push after commit `7d3ab9d898` (etymology manifest regen from new ABBYY+text.pdf parsers). The featured slugs `sertse` (серце) and `maty` (мати) were dropped — landing page LinkCards pointed at 404s, and the `tests/unit/etymology-featured-slugs.test.ts` quality gate enforced the mismatch as a hard fail. PR #2193 inherited the same failure.

**Fix**: Drop the two missing entries from the `featured` array. Kept the remaining four (`dim`, `zhinka`, `khlib`, `voda`) which verify present in the regenerated manifest. Etymology team can re-add when a future ingest covers the missing headwords.

### PR #2187 — CodeQL batch (proactive, not cascade-related)

User asked me to "do something useful" while a build ran. I triaged 8 open code-scanning alerts and shipped real fixes for 5:

- **#179** xss-through-exception in `dashboards/channels.html` lines 399, 476 — wrap `${e.message}` in `escapeHTML()`
- **#178** xss-through-dom in `dashboards/image-explorer.html` lines 718–741 — escape `imgUrl` (HTML), `img.image_path` (HTML + JS-string), `img.description_uk` (HTML)
- **#185 / #186 / #187** zizmor/dependabot-cooldown — added `cooldown: { default-days: 5 }` per ecosystem stanza

**Not addressed (dismiss-with-reason on GitHub after merge, next session):**
- **#181** py/path-injection in `scripts/api/docs_router.py` — already has `safe_join` (commonpath) + `_assert_under_root` (`resolve().relative_to()`) + extension allowlist + hidden-file block. Existing `codeql[py/path-injection]` suppression comments at lines 412/416/429 document the defense; flow analysis can't trace through `_assert_under_root`.
- **#180** js/unvalidated-dynamic-method-call in `dashboards/admin.html` — `sectionLoaders[section]()` guarded by `Object.prototype.hasOwnProperty.call(sectionLoaders, section)`.
- **#184** py/stack-trace-exposure in `scripts/ai_agent_bridge/openai_proxy.py` — every caller of `_openai_error` sanitizes via `_first_error_line` (one-line truncation) or `_validation_error_message` (msg + location only).

## Section 3 — Build #10 final state (the headline result)

```
phase=python_qg duration_s=145.777 PASSED
phase=wiki_coverage_gate duration_s=50.202 PASSED (18/18, 100%)
phase=wiki_coverage_review FAILED — YAML parse error on reviewer prose:
  "expected '<document start>', but found '<scalar>'
   in '<unicode string>', line 4, column 1:
       I have verified all **18 obligat ..."
```

The codex-tools reviewer emitted a prose narrative ("I have verified all 18 obligations...") as its `wiki_coverage_review` response. The phase parser expected a YAML document (probably with a `obligations:` mapping or `verdict: PASS/FAIL` header). Reviewer output started with prose → YAML parser found a scalar where a document was expected.

Worktree preserved per #M-10: `.worktrees/builds/a1-my-morning-20260521-195056/` — branch `build/a1/my-morning-20260521-195056` — all artifacts auto-committed.

## Section 4 — What the 6th issue actually is (handoff investigation queue)

`wiki_coverage_review` is a phase that runs AFTER `wiki_coverage_gate` per build #10's event sequence. Three hypotheses for the next session to triage:

1. **Reviewer prompt expects YAML but model emitted prose.** The "all 18 obligations verified" prose suggests the reviewer was given a passing case and chose narrative confirmation over structured output. Fix: prompt must demand YAML even on all-clear, with a worked YAML example for the empty-fixes case.
2. **Parser is strict about a YAML document marker that the reviewer omits when there's nothing to flag.** Some YAML parsers require `---` document start; the reviewer may emit a JSON-style or bare block. Fix: parser should tolerate bare YAML blocks.
3. **The reviewer added a prose preamble before the YAML block.** Many LLMs do this — "I'll now provide the review:" followed by ```yaml...```. The parser may not strip preamble. Fix: extract YAML fenced block, ignore surrounding prose.

Investigation entry points:
- `grep -n 'wiki_coverage_review\|wiki-coverage-review' scripts/build/linear_pipeline.py scripts/build/phases/*.md`
- `curriculum/l2-uk-en/_orchestration/a1/my-morning/runs/20260521-195056/` (orchestration run output, search for the reviewer's raw response)
- The reviewer prompt that produces the prose is likely `scripts/build/phases/linear-review-wiki-coverage.md`

Once fixed, build #11 should reach `module_done`. The module content has been verified to pass every gate; the only remaining bug is response-format.

## Section 5 — Active state at handoff

- **0 active dispatches** — agy V7 integration merged earlier (PR #2182, `67648a1ce2`); esum work consolidated by other commits (`7d3ab9d898`, `42055e269c`, `35d35e9994`, `583fa3d698`)
- **0 active builds** — #10 completed and auto-committed
- **0 unread inbox items**
- **Origin/main at** `eea2571f87` (PR #2197 squash merge)
- **6 build worktrees preserved per #M-10** for forensic continuity:
  - `a1-my-morning-20260521-101042` (build #5, vesum stem)
  - `a1-my-morning-20260521-140634` (build #6, wiki_coverage H1/H2)
  - `a1-my-morning-20260521-145016` (build #7, textbook H3)
  - `a1-my-morning-20260521-180202` (build #8, wiki_coverage H2/H3)
  - `a1-my-morning-20260521-190246` (build #9, parser |)
  - `a1-my-morning-20260521-195056` (build #10, wiki_coverage_review YAML)

## Section 6 — CodeQL state at handoff

- **5 alerts fixed** via PR #2187: #178, #179, #185, #186, #187
- **3 alerts pending dismiss-with-reason** on GitHub UI: #180, #181, #184 (see PR #2187 body for the rationale to paste into each dismiss form)

## Section 7 — Cold-start sequence for next session

1. Read this handoff (you're here).
2. Read the first evening handoff for cascade context: `docs/session-state/2026-05-21-evening-gate-cascade-three-bugs-one-after-another.md`.
3. Orient via Monitor API.
4. **First action**: find `wiki_coverage_review` phase code + reviewer prompt + parse logic. Diagnose YAML-vs-prose mismatch.
5. Fix in a single PR (likely prompt-side: demand YAML even on all-clear).
6. Run claude-tools build #11 — expect `module_done` if no 7th issue.
7. If 22/22 → `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` → **first complete V7 module on main**.
8. Then dismiss CodeQL alerts #180, #181, #184 on GitHub with rationale from PR #2187 body.
9. P1: cross-validate gemini-tools + deepseek-tools rebuilds against the gate-hardened main.
10. Optional P2: holistic gate-quality audit pass (recommended in the first evening handoff) — may now be moot if cascade truly terminates at #6.

## Section 8 — Open follow-ups (renumbered against the first evening handoff)

| # | Subject | Priority | Notes |
|---|---|---|---|
| 1 | `wiki_coverage_review` YAML parse fix | **P0 next session** | 6th cascade issue; module content is good — this is the only blocker for first complete V7 module |
| 2 | Promote a1/my-morning if build #11 hits module_done | P0 right after #1 | `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` |
| 3 | Dismiss CodeQL alerts #180, #181, #184 | P1 | Rationale already in PR #2187 body |
| 4 | Cross-validate gemini-tools + deepseek-tools | P1 | Inherited from first handoff |
| 5 | Holistic gate-quality audit | P2 | May be moot if cascade terminates; revisit after build #11 |
| 6 | codex-tools rollout-flush race | P2 | Inherited |
| 7 | PR #2168 amelina stub blocker | low | Inherited |
| 8 | `review / review` CI auth broken | P2 | Inherited |
| 9 | etymology team to re-add `серце`/`мати` to manifest when ingest covers those headwords | low | Out of scope; PR #2194 dropped them from featured |

## Sign-off

10 PRs merged today in total across the session and continuation. Gate-detection cascade is fully resolved for wiki_coverage and textbook_grounding. The 5-fix combo brought build #10 to 18/18 wiki_coverage on first attempt — a clean inflection point from the morning's "21/22 stem fragment" to "wiki_coverage 100%". Module content is correct.

The 6th issue is at a different phase (`wiki_coverage_review`, a post-gate phase), and the failure shape (YAML parse on prose) suggests a small prompt or parser tweak. One PR away from first complete V7 module — but per the cascade pattern, I should not promise "next build is the one" until the predicate-bounded `/goal`-style verification holds.

Five direct quotes from the cascade:
- "the build's correction loop produced valid content all along; the gate detection bug was eating 7 successful fix applications" — PR #2184
- "Same writer, same plan, same chunk_id retrievals — only the heading depth differs" — PR #2185
- "The H3 is structurally INSIDE the H2 section; the section boundary should be the next heading whose depth is <= chosen depth" — PR #2193
- "The writer-prompt template uses `\|` to denote alternatives; the writer copied the pattern as a field separator" — PR #2197
- "Wiki_coverage_gate ✅ 18/18 (100%) but failed at wiki_coverage_review YAML parse on reviewer prose output" — build #10 close
