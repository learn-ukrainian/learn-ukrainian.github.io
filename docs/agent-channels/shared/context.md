# shared — project-wide pinned context

This file is auto-included in every channel. It holds STABLE project
state that every agent needs to see on every post. Volatile state
(current sprint, recent commits, build status) comes from the Monitor
API snapshot per-post — do NOT put that here.

## Project

**learn-ukrainian** — an open-source Ukrainian language curriculum for
English speakers (A1→C2 core + seminar tracks: HIST, BIO, LIT, OES,
RUTH, ISTORIO, and literary sub-tracks). Built by Claude + Gemini with
adversarial review between agents.

- Repo: `learn-ukrainian` (all paths in this file are relative to the repo root)
- License: CC BY-SA 4.0 for content, MIT for build tooling
- Source of truth: `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`
- Module manifest: `curriculum/l2-uk-en/curriculum.yaml`

## Agents & roles

- **Claude** — architecture, code, pipeline, integration, synthesis
- **Gemini (3.1-pro-preview)** — content writer, code reviewer, adversarial critic
- **Codex** — code investigations, root-cause analysis, bug hunts. **Reserved — do not delegate coding to Codex on ticket #1190.**

## Non-negotiable rules (every agent, every post)

1. **Quality over speed.** No heuristics when a proper algorithm exists. No lowering thresholds. No "for now".
2. **Investigate before acting.** Read design docs + trace flows end-to-end before modifying any non-trivial code.
3. **Adversarial review is mandatory.** Nothing commits or merges without a sign-off from another agent. Reference the review task-id in the commit message.
4. **Sequence discipline.** One working end-to-end example first, then scale. Never build components in isolation.
5. **No tech debt.** Create data + ingestion + tracking in the same commit. No "flag for later".
6. **Cite evidence.** Reviews must cite specific file:line or example output. No vibes-based verdicts.
7. **Action bias.** When a decision is clear, act. Don't ask procedural permission for already-agreed-upon work.

## Ukrainian linguistic principles (content agents)

- **Admit uncertainty, never invent.** Flag unverified claims with `<!-- VERIFY -->`. Always check VESUM first.
- **Four separate checks:** Russianisms, Surzhyk, Calques, Paronyms — four different problems, each with its own fix.
- **Authority hierarchy:** VESUM → Правопис 2019 → Горох → Антоненко-Давидович → Грінченко
- **Your pre-training is contaminated by Russian** — always verify Ukrainian forms against local dictionaries.

## Tooling conventions

- **Python:** `.venv/bin/python` — never bare `python3` or `python`
- **Tests:** `.venv/bin/pytest` — colocated in `tests/`
- **Lint:** `.venv/bin/ruff check` — pre-commit hook enforced
- **Bridge CLI:** `scripts/ai_agent_bridge/__main__.py` — for agent delegations
- **Channel bridge (#1190):** `ab channel`, `ab p`, `ab post`, `ab discuss`
- **GH issues as memory:** reference issue numbers in commits, close when all ACs met

## Active major workstreams

- **#1190** — channel bridge rewrite (this one)
- **#1189** — B1 friction fixes in V6 write prompt
- **#1188** — diasporiana PDF pipeline (Doroshenko, deferred)
- **#1122** — A2 build pipeline fixes
- **#1142** — v6_build refactor into pipeline modules (blocked)
