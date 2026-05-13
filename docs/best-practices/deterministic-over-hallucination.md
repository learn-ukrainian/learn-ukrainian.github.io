# Deterministic-over-Hallucination — TOP PRIORITY (cross-agent)

> **Status:** ACTIVE policy as of 2026-05-09
> **Applies to:** Claude · Codex · Gemini · all dispatched sub-agents · all sessions
> **Canonical:** this file. Pointers in agent rules / MEMORY / dispatch briefs reference back here.

## The rule

**Every verifiable claim must be backed by a tool call.**

The pre-trained guess feels right; it's wrong often enough to break Ukrainian curriculum, code, and orchestration. We have the tools — VESUM (6.7M forms), СУМ-11 (127K entries), Грінченко (67K), ЕСУМ etymology, full code corpus, deterministic Monitor API, project-local scripts. Pretending we don't have them and inferring from training is malpractice.

Skipping the tool = hallucinating with confidence.

## What counts as "verifiable" — the strict scope

**YES, must use a tool:**

| Domain | Claim type | Tool |
|---|---|---|
| Ukrainian morphology | word validity, lemma, stress, gender, case forms | `mcp__sources__verify_word(s)` / `verify_lemma` / `check_modern_form` |
| Russianisms / surzhyk / calques | "is this a Russianism?" | `mcp__sources__search_style_guide`, `check_russian_shadow` |
| Heritage defense | "is this archaism, dialectism, or actually a Russianism?" | `mcp__sources__search_heritage` |
| Definitions / etymology | what a word means or where it's from | `mcp__sources__search_definitions`, `search_grinchenko_1907`, `search_esum`, `search_slovnyk_me` |
| CEFR level | is word A1/A2/B1? | `mcp__sources__query_cefr_level` |
| Textbook citation | does the source actually say this? | `mcp__sources__search_text` (textbooks), `search_literary` (literary), `query_pravopys` (orthography), `query_wikipedia` |
| File contents / line counts / function signatures | "this function takes (x, y, z)" | `Read`, `grep` / `ugrep`, `wc`, `head`/`tail` |
| Build status, ship-readiness, in-flight tasks, git state | "module M is at gate G" | Monitor API at `localhost:8765/api/...` |
| Word counts / target conformance | "this module has N words" | `scripts/audit/audit_module.py` + `scripts/audit/config.py` |
| Stress marks | "ос+тання" | the deterministic `ukrainian-word-stress` annotator (NEVER hand-write) |
| Test pass/fail | "tests pass" | `.venv/bin/pytest <path>` |
| Lint clean | "this is ruff-clean" | `.venv/bin/ruff check <path>` |
| HTML validity | "the HTML parses" | `python3 -c "from html.parser import HTMLParser; HTMLParser().feed(open('X.html').read())"` |
| Module/plan/state | "level X has N modules" | `curriculum/l2-uk-en/curriculum.yaml` + Monitor API endpoints |
| Recent commits / SHAs / PRs | "PR #N landed at SHA" | `git log`, `gh pr view`, never recall |

**NO, exempt (creative output generation):**

- Module narrative writing (within textbook situations + plan)
- Dialogue invention from a verified textbook situation
- Adversarial review reasoning chains
- Architecture design proposals (the design IS the output; cite tools when claiming about existing code)
- Strategic recommendations
- Brainstorming / option generation

The exempt list is for **output generation**. Every **claim about an artifact** — even inside a creative output — must still be tool-backed.

## Decision test — before writing any factual sentence

Ask:
1. Is this a verifiable claim?
2. Is there a tool that can verify it?
3. Did I run the tool in this turn / very recent context?

If 1 + 2 yes and 3 no → STOP. Run the tool. Then write the sentence using the result.

A rule of thumb: **the moment you introduce a number, name, path, SHA, technical claim, or Ukrainian word that wasn't in your very recent tool output, run a tool**.

## Anti-pattern catalog

| ❌ Hallucination-prone | ✅ Deterministic |
|---|---|
| "А1 word target is 1200 from memory" | Read `scripts/audit/config.py` `LEVEL_CONFIG` |
| "VESUM has this word" (best-guess) | `mcp__sources__verify_word("кобета")` |
| "The function takes `(prompt, writer, ...)`" (recall) | `grep -n "def func_name" path/` |
| "Last commit was X" (memory) | `git log --oneline -1` |
| "I think 90% of modules pass" | `curl -s http://localhost:8765/api/state/track-health/{level}` |
| "Module M is at audit gate ABC" | `curl -s /api/state/module/{track}/slug/{slug}` |
| "У слові «дерево» 6 літер" (counted by hand) | `python3 -c "print(len('дерево'))"` — and it's 6 only because Cyrillic is 1 codepoint per glyph here; never assume |
| "Russianism: кот → кіт" (memory) | `mcp__sources__search_style_guide("кот")` |
| "Stress falls on the second syllable" | The `ukrainian-word-stress` annotator |
| "This module uses verb X" | `grep -n "verb_lemma" curriculum/.../module.md` |
| "Tests pass on this branch" | `.venv/bin/pytest tests/<file>.py -v` |
| "The module is ship-ready" | `curl /api/artifacts/{track}/{slug}` |

## Why this matters here specifically

- **Ukrainian linguistic claims hallucinated → bad pedagogy.** A Russianism that slips into a learner's first contact with the language is hard to undo. The user has been burned by this.
- **Code claims hallucinated → CI failures + sibling bugs.** Re-implementing the wrong contract because we recalled it wrong.
- **Status claims hallucinated → orchestration drift.** Saying "module M is at gate G" when it isn't sends downstream agents to wrong work.
- **Curriculum claims hallucinated → invented modules, fake plan references.** A plan citing a textbook page that doesn't exist is a quality failure.

## Per-agent enforcement

### Claude (orchestrator + reviewer + UI tester)

- Every `mcp__sources__*` tool call this rule mandates is in scope.
- Reasoning chains are NOT a substitute for verification — even if the chain feels airtight.
- When acting as adversarial reviewer of a dispatched piece of work, use the deterministic verification path the brief listed; if no path was listed, run the tool you'd want a writer to have run.

### Codex (primary coder + adversarial reviewer)

- Dispatch briefs MUST list the deterministic verification path for every load-bearing claim. The brief is the contract.
- CLI `--mode read-only` runs are ideal for verification; `--mode danger` writes only to worktrees, never to main.
- Reviews must cite SPECIFIC examples from the actual code or text — same standard as the linguistic reviewer (see `non-negotiable-rules.md` rule 6).

### Gemini (writer + content reviewer)

- Wiki and curriculum prompts already wire `mcp__sources__*` tools — do not bypass.
- When asked to write content with vocabulary, query VESUM and the dictionary stack BEFORE generating; do not write a vocabulary list and verify after.
- Self-reviews are OFF (per pipeline policy); when reviewing a colleague's work, use the same tool-grounded discipline.

### All dispatched sub-agents

- The orchestrator includes this rule preamble in every brief.
- Brief MUST list:
  1. The verifiable claims the work will produce
  2. The deterministic tool for each
  3. The output format that captures the tool evidence (e.g., quote the VESUM lookup output verbatim, not "I checked VESUM")

### Special case — dispatches that write to `data/sources.db`

The 2026-05-13 Pohribnyi YT ingest (PR #1973) is the canonical
cautionary tale: Codex returned a clean success summary claiming "DB
migration inserted 35 chunks for channel_id='pohribnyi_pronunciation'"
but the **canonical `data/sources.db` received zero rows**. The summary
text was a result-message hallucination; the actual INSERT never landed
(transaction not committed, wrong path, or some other silent failure).
Detection lag: ~9 hours, during which the corpus appeared to have data
it did not.

**Briefs for any ingest / migration / re-chunk dispatch MUST require all
THREE of the following in the PR body — quoted raw output, not paraphrase:**

1. **BEFORE** — quoted `sqlite3 data/sources.db "SELECT COUNT(*) FROM <table> WHERE <scope>"` output, taken before any write.
2. **AFTER** — quoted `sqlite3 data/sources.db "SELECT COUNT(*) FROM <table> WHERE <scope>"` output, taken after the write.
3. **SAMPLE** — quoted `SELECT chunk_id, substr(text, 1, 80) FROM <table> WHERE <scope> LIMIT 3` showing 2-3 real rows with the new metadata visible.

The path must be the canonical `data/sources.db` from the dispatch
worktree (which is a symlink to main's DB via
`scripts/delegate.py:_provision_data_symlinks`). If the path is wrong,
the symlink is missing, or the migration rolled back, the BEFORE/AFTER
counts will be identical — that's the deterministic signal we need.

Orchestrator MUST independently re-run the AFTER count from the main
checkout before merging. A merge gated only on the brief's quoted
output is insufficient — Codex/Gemini might quote a worktree-local DB
that doesn't propagate. Re-verify against canonical, then merge.

Inline-orchestrator ingestion (the pattern the user established
2026-05-14 after the Pohribnyi loss) follows the same evidence
convention — the in-progress run prints BEFORE/AFTER and a sample, and
the PR body quotes those exact lines.

## When this rule isn't broken

A short summary that cites no specific facts beyond what was just observed in this turn does NOT need a redundant tool call. ("I just committed X, here's the SHA from the `git push` output we just saw" — the tool was used; the citation is correct.)

The rule is broken when you introduce a fact that couldn't have come from your recent tool output and you didn't run a tool to confirm it.

## When deterministic isn't possible

Genuine creative work, persuasive writing, novel reasoning, design choices — these are LLM strengths. Don't waste tools on them. The rule applies to **verifiable claims and references**, not to opinion or invention.

If you're tempted to skip a tool because "the answer is obvious" — that's exactly when hallucination is most expensive. Run the tool.

## Pointer locations (this file is the canonical one)

| Pointer | Location |
|---|---|
| Claude — runtime memory | `~/.claude/projects/<project>/memory/MEMORY.md` rule `#M-4` |
| Claude — repo memory | `claude_extensions/memory/MEMORY.md` rule `#M-4` |
| Claude — non-negotiable rules | `claude_extensions/rules/non-negotiable-rules.md` section "12. Tool-grounded claims" |
| Cross-agent reference | `docs/best-practices/agent-cooperation.md` § "Deterministic-over-hallucination" |
| Gemini briefs | included in dispatch-brief preamble template |
| Codex briefs | included in dispatch-brief preamble template |
| Channel `architecture` context | `docs/agent-channels/architecture/context.md` (pointer) |

## Failure record (encode here when broken)

When this rule is broken in a way that costs real work, append the case here so the next agent reads it before repeating.

### 2026-05-13 — PR #1973 Pohribnyi YT ingest, phantom-shipped DB rows

**Symptom:** Codex dispatch `ingest-pohribnyi-pronunciation-2026-05-13`
ran 1341 s, returned `status=done` with a polished result summary
claiming `"DB migration inserted 35 chunks for channel_id='pohribnyi_pronunciation'"`.
PR #1973 was merged on that summary's strength. **No data actually
landed in canonical `data/sources.db`.** Detection: 2026-05-14 morning
corpus audit, ~9 h after merge:

```
$ sqlite3 data/sources.db "SELECT channel_id, COUNT(*) FROM external_articles WHERE channel_id LIKE '%pohrib%'"
(empty)

$ sqlite3 data/sources.db "SELECT MAX(id), COUNT(*) FROM external_articles"
1199|1199
```

The JSONL file `data/external_articles/pohribnyi_pronunciation.jsonl`
also didn't exist on disk despite Codex's claim. Codex's stdout +
stderr logs from the dispatch were both **0 bytes** for 22 minutes of
work — no execution trace at all.

**Root cause:** the dispatch brief did not require deterministic
quoted SELECT-COUNT evidence. The result summary was trusted on its
own. A separate bug in `build_sources_db.py` (only inserting 8 of 16
external_articles columns) compounded the failure for the historical
1199 rows, but the new-row gap was a pure dispatch-trust gap.

**Cost:** ~9 h of phantom corpus state. Required a re-fetch of all 6
videos + a separate fix PR (#1976) for the column-coverage bug + a
manual migration to backfill 1199 rows' channel_id from
`source_file`. Plus this rule update.

**Prevention:** Special-case subsection above ("Special case —
dispatches that write to `data/sources.db`"). Every DB-write brief
now mandates BEFORE / AFTER / SAMPLE quoted output; the orchestrator
independently re-verifies against canonical before merging.

## Related

- `MEMORY.md` `#1` (QUALITY ABOVE ALL — same family: no shortcuts, no good-enough)
- `MEMORY.md` `#M-3` (don't assume colleague tool capabilities — query them)
- `non-negotiable-rules.md` rule 6 (LLM self-validation: cite evidence or it's invalid)
- `claude_extensions/rules/mcp-sources-and-dictionaries.md` (catalog of `mcp__sources__*` tools — your verification toolbox)
- `docs/MONITOR-API.md` (Monitor API endpoints — the deterministic state surface)
