# Contributing to Learn Ukrainian

Thank you for your interest in contributing! This project is a comprehensive Ukrainian language curriculum, and we appreciate help from both native speakers and developers.

## How to Contribute

### Content Review (Native Speakers Welcome!)

The most valuable contribution is reviewing Ukrainian text for naturalness and accuracy:

1. Browse modules at [learn-ukrainian.github.io](https://learn-ukrainian.github.io)
2. If you find errors in Ukrainian grammar, vocabulary, or cultural context, [open an issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new)
3. Include the module name, the problematic text, and your suggested correction

### Bug Reports

Found something broken? [Open an issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new) with:
- What you expected to happen
- What actually happened
- The module/page where the issue occurred

---

## Developer Setup

### Prerequisites

- macOS (primary dev platform)
- [pyenv](https://github.com/pyenv/pyenv) with Python 3.12.8
- Node.js 20+ (for Starlight frontend)

### Installation

```bash
# 1. Clone
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io

# 2. Python environment (sqlite extensions required for VESUM)
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.12.8
pyenv local 3.12.8
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Frontend
cd starlight && npm install && cd ..

# 4. Start services
./services.sh start   # RAG on 8766, API on 8765, Starlight on 4321

# 5. Verify
./services.sh status
```

### Services

| Service | Port | Command |
|---------|------|---------|
| MCP sources server | 8766 | `./services.sh start` |
| Monitor API | 8765 | `./services.sh start` |
| Starlight dev | 4321 | `./services.sh start` |

```bash
./services.sh start    # Start all
./services.sh stop     # Stop all
./services.sh status   # Check status
```

---

## Workflow

### Git: all work on `main`

No feature branches. Use `git worktree` for isolation when needed. Only `git add` files you modified.

### GitHub Issues

Every non-trivial change needs a GH issue. Before starting: find or create an issue. After completing: update and close it. Master tracking: issue #1093.

### Build a module

```bash
# Full build
.venv/bin/python scripts/build/v6_build.py a1 2 --writer gemini

# Single step
.venv/bin/python scripts/build/v6_build.py a1 2 --step review

# With MCP tools (VESUM/RAG during writing)
.venv/bin/python scripts/build/v6_build.py a1 2 --writer claude-tools
```

### Audit a module

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/sounds-letters-and-hello.md
```

### Run tests

```bash
# Specific file (preferred)
.venv/bin/pytest tests/test_audit_core.py -v --tb=short

# Full suite (~2-3 min)
.venv/bin/pytest tests/ -q

# Per-file coverage with missing lines
.venv/bin/pytest --cov=scripts --cov-report=term-missing tests/ -q  # per-file coverage with missing lines
```

### Lint

```bash
.venv/bin/ruff check scripts/          # Check
.venv/bin/ruff check --fix scripts/    # Auto-fix
```

### Pre-commit hooks

The repo ships a `.pre-commit-config.yaml` that mirrors the CI checks locally. Install once per clone:

```bash
pip install pre-commit
pre-commit install
```

After that, every `git commit` runs:

- `ruff check` on changed `scripts/` files (blocks bad imports, multi-statement lines, etc.)
- `gitleaks` secret scan on staged changes
- YAML syntax check + large-file / merge-conflict detection
- Block accidental `.yaml.bak` / `.yaml.orig` commits, except versioned plan snapshots under `curriculum/*/plans/**`
- Block bare `python` / `python3` in new shell scripts

Run manually across the whole repo:

```bash
pre-commit run --all-files
```

If a hook fires unexpectedly, fix the underlying issue — do NOT bypass with `--no-verify` unless there's a real emergency. Hooks that need updating belong in `.pre-commit-config.yaml`, not in commit messages.

Claude Code also has its own in-session pre-commit logic that runs ruff + pytest on affected files when it commits. Both layers are intentional: Claude Code catches bugs at agent-commit time, and `pre-commit` catches them at human-commit time. They should never disagree — if they do, investigate.

---

## Project Architecture

### Curriculum Structure

```
curriculum/l2-uk-en/
  plans/{level}/{slug}.yaml      # Module plan (source of truth, immutable)
  {level}/{slug}.md              # Generated content
  {level}/activities/{slug}.yaml # Exercise YAML
  {level}/vocabulary/{slug}.yaml # Vocabulary
  {level}/review/                # Review outputs
  {level}/audit/                 # Audit reports
  curriculum.yaml                # Module manifest (ordering)
```

### Pipeline V6

The only active build pipeline. Phases: check → research → skeleton → write → activities → annotate → enrich → verify → review → publish.

- **Gemini** writes content (default), **Claude** reviews (cross-agent adversarial)
- Publish produces MDX with 4 tabs: Урок / Словник / Зошит / Ресурси

### Website

Built with [Astro Starlight](https://starlight.astro.build/). 50+ React components for interactive exercises. MDX files in `starlight/src/content/docs/`.

---

## Quality Standards

- **Word targets** (minimums): A1: 1200, A2: 2000, B1-C1: 4000, C2: 5000, Seminar: 5000
- **All Ukrainian text** must be grammatically correct and natural
- **No Russianisms**: use добре not хорошо, кіт not кот
- **No calques**: use брати участь not приймати участь
- **Activities test language skill**, not content recall
- **VESUM-verified**: every Ukrainian word checked against the morphological dictionary
- **Правопис 2019**: Ukrainian orthography standard

## Code of Conduct

Please be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
