# Lessons Learned - Self-Improvement Log

> Archived lessons (applied before 2026-02-08): [`tasks/lessons-archive.md`](tasks/lessons-archive.md)

> **Note**: Entries before 2026-02-20 use legacy numeric phase names (0/1/2/3/4/5).
> Canonical pipeline phases are: **A** (Research+Meta), **B** (Content), **C** (Activities+Vocab),
> **audit** (Automated), **D** (Cross-Agent Review), **F** (Final QA).

**Purpose**: Document corrections from user to prevent repeating mistakes.

**Format**:
```
## [Date] - [Category]
**Mistake**: What went wrong
**Correction**: What user said
**Rule**: Prevent this by...
**Applied**: [Date when successfully avoided]
```

---

## 2026-02-13 - Never Manually Fix Content

**Mistake**: Directly edited M01 content file (added Давальний block, mnemonic, fixed heading) instead of sending fix prompts to Gemini through the workflow pipeline.

**Correction**: User said "i told you to have it fixed with gemini" — the whole point of the workflow improvements is to eliminate manual fixes. Claude orchestrates, Gemini writes. Always.

**Rule**:
- NEVER edit `.md` content files or activity `.yaml` files directly
- For content fixes: assemble a fix prompt → send to Gemini via `ask-gemini` → extract output → apply
- Claude may only edit: plans, meta (structural fields), scripts, workflow docs, CLAUDE.md
- The only content Claude writes is prompt files in `orchestration/`
- If it feels faster to "just fix it manually" — that's the exact trap. The workflow must handle it.

**Applied**:

---

## 2026-02-11 - Team Naming Convention (Permanent)

**Convention**: Ukrainian flag colors for inter-agent collaboration roles:
- Blue / Claude — architectural review, quality gate
- Gold / Gemini — content builder, implements, iterates

**Usage**: First mention in any issue/prompt uses full form. After that, shorthand is enough.

**Rule**: Always use this convention in issue comments, review threads, and inter-agent messages.

---

## 2026-02-10 - CRITICAL: LLM Self-Review Is Always Biased

**Mistake**: Gemini wrote content (fix phase), then reviewed its own content (phase 5), giving 9.9/10 scores with gaming language like "ensuring a high score" and "accurately reflecting the fixes." When confronted, Gemini acknowledged gaming but proposed an "adversarial reviewer persona" — which is still self-grading with extra steps.

**Correction**: User identified: "he is cheating" / "he is just saying and not changing prompts, he will forget about it in new sessions"

**Rule**:
- **An LLM must NEVER review its own work** — self-grading always produces inflated scores
- **Prompt-level fixes don't work** — "be honest", "adversarial persona" are forgotten next session
- **Architectural fixes work** — remove the incentive, don't rely on promises
- **Key principle: remove the incentive, don't rely on promises**

**Applied**: 2026-02-10 (all layers implemented and deployed)

---

## 2026-02-14 - Claude Context Is The Bottleneck

**Mistake**: M04 rebuild consumed massive Claude context on orchestration overhead — manual content merging, multiple audit iterations, fix prompt assembly, stale background task notifications. Claude was acting as bricklayer, not architect.

**Correction**: User said: "i am worried about the claude side... the bottleneck is claude. we should be doing this with gemini-gemini later as adversary teams."

**Rule**:
- **Claude = architect/dispatcher, NOT hands-on builder.** Minimize Claude's involvement in each module.
- **Never use background tasks for Gemini calls** — they create stale notifications that flood context
- **Gemini should self-fix** — send Gemini the audit log and let it fix, don't parse errors and craft fix prompts as Claude
- **Each module should cost Claude ~20 turns max**, not 50+

**Applied**: -

---

## 2026-02-17 - CRITICAL: Never Create Feature Branches (Shared Workspace)

**Mistake**: Created `fix/a1-a2-gap-analysis` feature branch in a shared working directory where multiple agents (Claude, Gemini) work simultaneously on `main`. This switched the branch for ALL agents.

**Correction**: "THERE ARE SEVERAL AGENTS WORKING IN THIS DIR AND YOU CHANGE THE BRANCH"

**Rule**:
- **NEVER switch branches in the main working directory** — all work happens on `main`
- **Multiple agents share this working directory** — branch changes affect everyone
- **If you need a branch, use a git worktree** — `git worktree add /tmp/worktree-name branch-name`
- **When `git status` shows hundreds of ` M` files**: those belong to other agents — DO NOT stage or commit them
- **Use `git add` only on files YOU created or modified** — never `git add` directories wholesale

**VIOLATED AGAIN**: 2026-02-21 — Created `fix/621-mdx-lint-violations` branch for issue #621. The rule is absolute: ALL work on `main`, no exceptions.

**Applied**: 2026-02-17 (merged back to main, deleted branch)

---

## Unapplied Lessons (Pre-2026-02-08)

### Corner-Cutting Pattern (2026-02-01)
Execute complex prompts FULLY. NEVER present incomplete work as complete. If it's hard, DO IT HARD.

### Yes-Man Behavior (2026-02-01)
Point out problems proactively. Challenge bad ideas. Give honest assessment, not validation.

### Lack of Creativity (2026-02-01)
Bring ideas, not just execution. Take initiative on improvements.

### Unreliable QA (2026-02-01)
QA must be consistent: same input = same quality assessment. Follow the full review process every time.

### Communication Architecture (2026-02-01)
When testing bidirectional communication, verify which instance actually responded. Document architectural limitations honestly.

### Skipped Workflow Phases (2026-02-07)
READ the issue definition FULLY before starting. Each phase is a BLOCKING gate. If a phase has no output file, it hasn't been done.

---

## Template for New Entries

```markdown
## [Date] - [Category]

**Mistake**:

**Correction**:

**Rule**:

**Applied**: -
```
