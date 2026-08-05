# NON-NEGOTIABLE RULES

All rules are hard requirements. Partial compliance = failure.

<critical>

## Quick Reference

| When... | Do this |
|---|---|
| Building content | Check `config.py` target_words FIRST — never hardcode from memory |
| Module under word target | Add only source-backed necessary pedagogy; if grounded material is exhausted, emit `SIZE_POLICY_MISMATCH` and route to plan review. Never lower the target or auto-pad |
| Audit gate shows ❌ | Fix it. ALL gates must be GREEN or the module fails |
| Fixing a module | Reviewer provides `<fixes>` — apply deterministically (rule 4) |
| Reviewing content | Cite SPECIFIC examples from the text, or the review is invalid (rule 6) |
| Plan can't be met | STOP building. Report to user. Propose new plan version (rule 7) |
| Review verdict REVISE | Reviewer outputs `<fixes>` find/replace pairs → pipeline applies them (rule 4) |
| Creating JSONL/data | Add ingestion flag + update tracking doc in SAME commit (rule 11) |
| Making any verifiable claim | Run a tool — VESUM/Monitor API/grep/etc. (rule 12) |

</critical>

---

## 1. Word Count Targets (Source of Truth: `config.py`)

<critical>

Meet reviewed targets with source-backed necessary pedagogy. Never lower targets
to match content, repeat exposition to reach them, or auto-pad. If grounded
material is exhausted, emit `SIZE_POLICY_MISMATCH` and route to plan review.

**Always read config.py** before generating content_outline or word budgets: `.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); from audit.config import LEVEL_CONFIG; print(LEVEL_CONFIG['{LEVEL}']['target_words'])"`

**Word targets:** A1=1200, A1-cp=1000, A2=2000, A2-cp=1500, B1/B1-cp/B2/B2-cp/B2-cap/C1/C1-cp/C2-cp=4000, C2=5000, HIST/ISTORIO/BIO/LIT/OES/RUTH=5000. If stale, re-read `scripts/audit/config.py`.

**Lesson learned:** Jan 2026 — 270 ISTORIO plans generated at 3500 instead of 4000 because agent hardcoded from memory instead of reading config.py.

</critical>

---

## 2. Audit Gates — ALL Must Pass

ALL gates must be GREEN (✅) or the module FAILS.

| Gate | Requirement |
|---|---|
| Words | ≥ target from config.py |
| Activities | ≥ minimum count for level |
| Unique_types | Sufficient variety |
| Vocab | ≥ minimum vocabulary for level |
| Naturalness | ≥ 8/10 |

Fix every failing gate. No exceptions, no "good enough."

---

## 3. Section-Level Word Targets (Flexible Guidance)

Section targets are guidance, not hard limits.

**Hard requirements:**
1. **Total word count** ≥ `word_target`
2. Each section within **±10% tolerance** of its target

**Flexible:** Redistribute words between sections freely. One section 20% over is fine if no section is >10% under.

**Priority:** Objectives and evidence coverage first → repair genuine section
gaps with sourced pedagogy → route plan-policy mismatch instead of filling a
section quota with repeated prose.

---

## 4. Review + Fix Loop (V6 Pipeline)

V6 uses **reviewer-as-fixer**: Gemini reviews, finds issues, outputs `<fixes>` with exact find/replace pairs. Pipeline applies them deterministically — no LLM regeneration, no rewriting from scratch.

**Flow:**
1. Writer generates content → ENRICH adds tabs/словнік → REVIEW
2. If REVISE: reviewer outputs `<fixes>` → pipeline applies find/replace → re-ENRICH → re-REVIEW
3. Max 2 fix rounds. Score should go UP (9.0→9.4→9.7), never down.
4. If still failing after 2 rounds → problem is in the PROMPT or PLAN, not the content.

**Critical:** Reviewer sees PROSE ONLY (enrichment stripped before review). Deterministic word count injected into review prompt. Reviewer must NOT estimate word count — use the injected number.

**Never rewrite from scratch.** Gemini proved: "FROM SCRATCH" rewrites degrade content (9.6→9.2→8.4). PATCH fixes only what's broken.

---

## 5. Quality Standards

| Requirement | Threshold |
|---|---|
| Review score | 9+/10 target (8+ minimum PASS) |
| **MIN-score gate** | **`min(dim_scores)` ≥ 8 to PASS, not weighted average.** A single failing dim fails the module. <8 → REVISE; <6 → REJECT. See `docs/best-practices/strict-reviewer-persona.md`. (Threshold dropped from 9 to 8 by user 2026-04-23.) |
| Russian ghost words | Zero (кот → кіт, хорошо → добре) |
| Dialogues | Natural situations from textbooks — not invented. Someone searches for keys, not interrogation. |
| Vocabulary | All words VESUM-verified. Writer generates словнік YAML with contextual translations. |
| Plans | Must have `references` (textbook + ULP links). No plan ships without references. |
| Stress marks | Added by deterministic annotator AFTER review, not by writer. |

Rewrite any text that fails naturalness. No robotic or disconnected prose.

**Reviewer architecture (load-bearing, user-stated 2026-04-23):** Each review dimension runs as an INDEPENDENT model call with its own strict persona — no single-pass multi-dim bundling. Aggregator takes MIN, not weighted average. Persona reference: `docs/best-practices/strict-reviewer-persona.md`. **Do NOT design new review prompts that bundle dims into one pass with a weighted average — that pattern is rejected.**

---

## 6. LLM Self-Validation — Cite Evidence or It's Invalid

Reviews must cite SPECIFIC examples from the actual content.

**FAKE:** `✅ PASS | High-style analytical register with historical terms.` — no evidence, invalid.
**HONEST:** `✅ PASS | Case endings correct ("Данилом Галицьким" — instrumental). Aspects: "зумів об'єднати" (pf), "прагнула" (impf). No Russianisms.` — cites real examples.

Every review must: read content first, verify grammar with examples, list vocabulary found, check facts with evidence. No evidence = failed review.

---

## 7. Plan Versioning (Architecture v2.1)

Plans in `plans/` are the source of truth. They require user approval to change.

> `plans/{level}/{slug}.yaml` → VERSIONED (immutable without approval)

**When build can't meet plan:** STOP → report "Plan requires X but Y isn't achievable because Z" → propose new plan version → user approves → write the new plan with an incremented `version` field. Prior versions live in git history (`git show HEAD:<path>`), not tracked `.bak` files.

**Never** silently modify plan files, lower word_target to match output, or stage plan `.yaml.bak` files.

**Exception**: The pipeline may auto-fix plan `vocabulary_hints` entries that fail VESUM verification. Changes are version-bumped and logged in `plan_fixes`. Content outline, objectives, and word targets remain immutable.

---

## 8. Batch Fixes Within Module

When fixing a module, diagnose ALL issues first, fix ALL at once, verify ONCE.

**Wrong** (O(3N) tokens):
```
Read → Fix A → Audit → Read → Fix B → Audit → Read → Fix C → Audit
```

**Correct** (O(3) tokens):
```
1. DIAGNOSE: Read review findings + audit results
2. EXECUTE: Apply ALL fixes in ONE pass
3. VERIFY: Re-enrich + re-review ONCE
```

---

## 9. Activities Test LANGUAGE, Not Content

Activities practice Ukrainian language skills, not subject knowledge.

### 9a. Content-heavy modules (HIST, BIO, ISTORIO, LIT, RUTH, OES)

**Golden Rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite it.

| Pattern | Verdict |
|---|---|
| "У якому році..." (dates) | ❌ Tests content recall |
| "Хто був..." (names) | ❌ Tests content recall |
| "Згідно з текстом, як автор..." | ✅ Tests comprehension |
| "У тексті модуля автор характеризує..." | ✅ Tests comprehension |

### 9b. ZNO-format activities (EXEMPT from 9a)

ZNO activities test language mechanics directly — наголос, фонетика, орфографія, морфологія. These are standalone language skill tests exempt from 9a.

---

## 10. Complete The Work — No Tech Debt

Every operation must be finished end-to-end in the same commit:

| When you... | You MUST also... |
|---|---|
| Create JSONL data | Add ingestion flag to script + update `DICTIONARY-PIPELINE-STATUS.md` |
| Write plans | Add references (textbook + ULP links) to every plan |
| Build a module | Verify MDX renders correctly (not empty, has all tabs) |
| Fix a bug | Write a test that catches the same bug |
| Close a GH issue | Verify ALL acceptance criteria, not just "most" |

"For now", "batch job for later", "flag for human" = failure. If it needs doing, do it NOW.

---

## 11. Tool-grounded claims — deterministic over hallucination (TOP PRIORITY, 2026-05-09)

<critical>

**Every verifiable claim must be backed by a tool call.** The pre-trained guess feels right; it's wrong often enough to break Ukrainian curriculum, code, and orchestration. Skipping the tool = hallucinating with confidence.

The project has VESUM (6.7M forms), СУМ-11 (127K), Грінченко (67K), ЕСУМ, Monitor API, full code corpus, deterministic scripts. **Use them.**

| Domain | Don't recall — run | |
|---|---|---|
| Ukrainian word | `mcp__sources__verify_word(s)`, `verify_lemma`, `check_modern_form` |
| Russianism / surzhyk | `mcp__sources__search_style_guide`, `check_russian_shadow` |
| Heritage defense | `mcp__sources__search_heritage` |
| Definitions / etymology | `search_definitions`, `search_grinchenko_1907`, `search_esum`, `search_slovnyk_me` |
| File contents / signatures | `Read`, `grep` / `ugrep`, `wc` |
| Build status / module gates / git state | Monitor API at `localhost:8765/api/...` |
| Word counts | `scripts/audit/audit_module.py` + `config.py` |
| Stress marks | `ukrainian-word-stress` annotator (NEVER hand-write) |
| Test pass / lint clean | `pytest`, `ruff check` |

**Decision test:** if you introduce a number, name, path, SHA, or Ukrainian word that wasn't in your very recent tool output and you didn't run a tool to confirm — STOP, run it.

**Exempt (creative output):** narrative writing, dialogue invention from textbook situation, design proposals, brainstorming. But every CLAIM about an artifact inside that creative output is still tool-backed.

Full rule + anti-pattern catalog + per-agent enforcement: **`docs/best-practices/deterministic-over-hallucination.md`**. Applies to Claude · Codex · Gemini · all dispatched sub-agents.

</critical>

---

## 11a. Blocker claims — the four-line template (TOP PRIORITY, advisor ruling 2026-08-05)

<critical>

Rule 11 governs whether a tool produced a claim. It does **not** govern whether the sentence says
more than the tool result said — and that gap has its own failure mode.

A claim of **incapacity** — "I can't", "I'm blocked", "this needs your permission", "access is
denied" — is the worst place for that gap, for a structural reason: **a wrong fact gets caught
downstream by gates and tests, but a wrong blocker is never tested.** Its whole function is to stop
work and hand the problem to the operator. Nothing catches it except the operator's attention.

**A refusal is a fact about one exact command string, never about a capability.**

Incident that produced this rule (2026-08-05, hramatka lane): the driver ran
`ssh -o BatchMode=yes hramatka 'hostname; uname -a'` and it **succeeded**. Later one command —
`ssh hramatka "... sudo -n ... register_review_record ..."` — was refused by the permission
classifier. The driver then told the operator, twice, that it needed permission "to run `ssh` to
the hramatka host", and that this blocked a queue of six PRs. That was false. SSH was never
blocked. The disproof was already in the same transcript when the false claim was made. No new
evidence was needed — only the discipline to look at evidence already held.

**Every blocker claim MUST carry all four lines. No line may be omitted.**

```text
BLOCKED:     <the verbatim command that was refused or failed>
ERROR:       <the literal error / refusal text, quoted, not paraphrased>
STILL WORKS: <output of a probe showing the surrounding capability is intact>
ASK:         <the narrowest grant that unblocks — must match BLOCKED, not a category containing it>
```

`STILL WORKS` is the load-bearing line. It forces the discriminating test that separates "one
`sudo` write was refused" from "ssh is blocked". In the incident above that line could not have
been filled in honestly, which would have exposed the error before it reached the operator.

**ASK must not widen.** If `BLOCKED` is one `sudo` subcommand, `ASK` is that subcommand — not
"ssh access", not "host access", not any category containing it.

**Before asserting a capability is gone, run the cheapest probe of that capability.** If a probe of
it already succeeded earlier in the session, the claim is refuted — say so instead of asking.

**Operator audit is one glance:** any missing line ⇒ reject the claim unread. A fabricated quote is
falsifiable against the transcript in seconds.

**Honest limit, stated rather than hidden:** no hook can verify that a quoted line is *accurate*.
Enforcement makes the format mandatory; the format makes a fiction falsifiable at a glance; the
glance is the real verifier. This reduces recurrence — it does not eliminate it, and no mechanism
will. Treat a violation as grounds to pull the lane, not as something to argue about.

</critical>

---

## Enforcement

Negotiating requirements down, skipping audit gates, producing under-length modules, shipping without references, leaving incomplete work, giving up before PASS, **or making verifiable claims without running the tool** = task failure.
