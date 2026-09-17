# OpenWiki repository instructions and boundary contract

**Status:** Binding control brief for repository `openwiki/` (stream `docs-knowledge`, epic #5535, issue #5541)
**Authority:** [ADR-013](../docs/architecture/adr/adr-013-docs-knowledge-openwiki.md) · [docs-authority-lifecycle.md](../docs/architecture/docs-authority-lifecycle.md) · [plain-Astro ACCEPTED](../docs/architecture/2026-06-09-ui-astro-without-starlight.md)
**Pinned OpenWiki Version:** `0.5.2` (upstream `@langchain/openwiki`)
**Execution Seat:** AGY Gemini Flash (`gemini-3.8-flash-high`)
**Review Seat:** Codex Astra @ `low`

---

## 1. Non-authoritative locator contract

1. The generated documentation in `openwiki/` is a **killable navigation and synthesis layer**. It is **not** an authoritative source of repository truth.
2. If any OpenWiki statement disagrees with code, tests, configuration, binding rules, or curated docs, **OpenWiki is wrong by definition**.
3. OpenWiki **never breaks ties** during conflict resolution. It may only cite winning authorities.
4. Future agents and human contributors must verify any critical fact against cited git-tracked source paths.

---

## 2. Authority precedence (binding per ADR-013)

| Fact type | Sole authority | OpenWiki role |
|---|---|---|
| Runtime behavior | Code + tests (`scripts/`, `tests/`, `site/`) | Cite file paths and line ranges; never redefine behavior |
| Config knobs / immersion | Config-as-policy (`scripts/config.py`, `scripts/config/*.yaml`) | Cite config path; never invent policy |
| Binding agent rules | `agents_extensions/shared/rules/` (+ served `/api/rules`) | Locator only; never duplicate binding text |
| Deployed rule copies | Generated consumers (`.claude/`, `.codex/`, `.agent/`, `.gemini/`) | Out of scope; never write harness deploy trees |
| Curated documentation | Tracked `docs/**` with declared lifecycle (`active`, `draft`, etc.) | Summarize with citations; obey lifecycle state |
| Architectural decisions | Permanent ADRs (`docs/architecture/adr/`) | Cite ADR number; do not assert supersession without ADR |
| Planning state | GitHub issue/epic bodies (SSOT) | Cite issue numbers; GitHub state wins over stale plans |
| Live ops / leases / capacity | Monitor API + session streams (`/api/session/*`, `/api/orient`) | **Strictly forbidden** to mirror or assert as current |
| Research provenance | Project Research Registry (ADR-011) | Cross-link; do not replace attributed fetch |
| Learner UI stack truth | Plain Astro ACCEPTED record + `site/` | **Must not** claim Starlight or Docusaurus as current |
| Ukrainian language claims | VESUM / `sources` / verbatim quoted curriculum | **Verbatim quote only** (FBL-013); zero synthetic Ukrainian prose |
| Immersion policy | Operator contract item 9 + `IMMERSION_POLICIES` | Precedence: config/operator contract win over stale prose |

---

## 3. Allowlist v1 read boundary

OpenWiki reads may **only** inspect regular git-tracked files in a clean dispatch worktree within these approved roots:

1. `scripts/` — Content pipeline, Monitor API, agent runtime, audit and orchestration tooling.
2. `site/` and `site/src/` — Learner-facing plain Astro static product (stack truth only).
3. `docs/architecture/` and `docs/best-practices/` — Curated contracts, ADRs, architectural records.
4. Classified root instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`) — **for classification only**, never as write targets.

### Explicit read exclusions
- `docs/session-state/**` and any Monitor projection dumps.
- Private topology, credentials, secrets, tokens, raw IP addresses, `.env*` files.
- `curriculum/**` lesson bodies as free synthesis (Ukrainian language text must be verbatim quoted only).
- `wiki/**` generated seminar wiki (separate authority).
- Deployed agent harness trees (`.claude/`, `.codex/`, `.agent/`, `.gemini/`, `agents_extensions/`).
- Gitignored or untracked directories (`data/`, `node_modules/`, caches).

---

## 4. Hard write surface confinement (FBL-003)

The **only** approved write surface is `openwiki/**`.

OpenWiki **must not create or modify**:
- Root instruction files: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`.
- Agent extension trees: `agents_extensions/`, `.claude/`, `.codex/`, `.agent/`, `.gemini/`.
- Core repository trees: `docs/`, `scripts/`, `site/`, `curriculum/`, `wiki/`, `tests/`.
- GitHub workflows: `.github/workflows/openwiki-update.yml` (no scheduled automation authorized for pilot).
- Live session state: `docs/session-state/**`.

**Enforcement rule:** Any file created or modified outside `openwiki/**` by upstream tooling (including default `AGENTS.md`/`CLAUDE.md` snippets or scheduled workflows) is classified as a critical defect and must be reverted before committing.

---

## 5. Generator constraints & operational posture

1. **Page count budget:** At most 8 generated concept pages (`openwiki/quickstart.md` plus ≤7 domain pages).
2. **OKF metadata compliance:** Every concept page begins with valid OKF v0.2 YAML frontmatter containing `type`, `title`, `description`, and `tags`.
3. **Plain Astro truth:** Always describe the learner UI as plain Astro (`site/src/layouts/CourseLayout.astro`). Starlight was removed on 2026-06-08/2026-06-09; `@astrojs/starlight/components` is a legacy Vite alias pointing to the local shim `site/src/starlight-compat/` for historical MDX imports.
4. **Telemetry and networking:** LangSmith tracing disabled (`LANGSMITH_TRACING=false`), PostHog/anonymous telemetry disabled, subagent fan-out disabled.
5. **Language rule:** All generated synthesis is English. Any Ukrainian words or phrases cited must be verbatim quotes from tracked files.
