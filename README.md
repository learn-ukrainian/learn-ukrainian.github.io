# Learn Ukrainian

**Мова -- душа народу** | Language is the soul of a nation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Deploy](https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/workflows/deploy-pages.yml)
[![Modules](https://img.shields.io/badge/modules-1%2C503-orange)](https://learn-ukrainian.github.io)

A free, open-source Ukrainian language course from A1 to C2, based on the **Ukrainian State Standard 2024** and aligned with **CEFR**.

**[Start Learning](https://learn-ukrainian.github.io)**

---

## What is this?

A comprehensive Ukrainian language curriculum with 1,503 modules across 14 tracks:

- **6 core CEFR levels** (A1 -- C2) covering grammar, vocabulary, and communication
- **8 specialization tracks** -- history, biographies, literature, professional Ukrainian, Old East Slavic, and Ruthenian
- **Theory-first approach** -- understand grammar deeply, not just memorize phrases
- **Interactive exercises** -- quizzes, matching, fill-in-the-blank, error correction
- **Cultural context** -- decolonization perspective, authentic Ukrainian sources
- **100% free** -- no ads, no subscriptions, no paywalls

## Tracks

### Core Levels

| Level | Modules | Description |
|-------|---------|-------------|
| [**A1**](https://learn-ukrainian.github.io/a1/) | 64 | Beginner -- Cyrillic alphabet, basic grammar, practical scenarios |
| [**A2**](https://learn-ukrainian.github.io/a2/) | 76 | Elementary -- All 7 cases, aspect intro, practical scenarios |
| [**B1**](https://learn-ukrainian.github.io/b1/) | 100 | Intermediate -- Aspect mastery, motion verbs, communication |
| [**B2**](https://learn-ukrainian.github.io/b2/) | 85 | Upper-Intermediate -- Passive voice, registers, professional basics |
| [**C1**](https://learn-ukrainian.github.io/c1/) | 106 | Advanced -- Stylistics, literature, complex grammar |
| [**C2**](https://learn-ukrainian.github.io/c2/) | 91 | Mastery -- Native-level proficiency |

### Specialization Tracks

| Track | Modules | Description |
|-------|---------|-------------|
| [**HIST**](https://learn-ukrainian.github.io/hist/) | 140 | Ukrainian history from origins to present |
| [**ISTORIO**](https://learn-ukrainian.github.io/istorio/) | 136 | Advanced historiography -- primary sources, imperial mechanisms |
| [**BIO**](https://learn-ukrainian.github.io/bio/) | 176 | Notable Ukrainians through history |
| [**LIT**](https://learn-ukrainian.github.io/lit/) | 221 | Ukrainian classics and literary analysis |
| [**B2-PRO**](https://learn-ukrainian.github.io/b2-pro/) | 40 | Professional -- business communication, technical domains |
| [**C1-PRO**](https://learn-ukrainian.github.io/c1-pro/) | 50 | Professional mastery -- executive, academic, specialized |
| [**OES**](https://learn-ukrainian.github.io/oes/) | 103 | Old East Slavic -- historical linguistics (X--XIII century) |
| [**RUTH**](https://learn-ukrainian.github.io/ruth/) | 115 | Ruthenian -- Middle Ukrainian (XIV--XVIII century) |

## Why Learn Ukrainian?

- **45 million speakers** worldwide
- **Rich literary tradition** -- Shevchenko, Franko, Lesya Ukrainka
- **Unique grammar** -- 7 cases, verbal aspect, motion verb system
- **Growing global interest** -- solidarity with Ukraine

## Getting Started

### Online (Recommended)

Visit **[learn-ukrainian.github.io](https://learn-ukrainian.github.io)** and start with A1.

### Local Development

```bash
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
npm install

# Start the website (Astro Starlight)
npm run dev:starlight
# Opens at http://localhost:4321/
```

**Requirements:** Node.js 20+, Python 3.12+ (for build scripts and audits)

## Project Structure

```
learn-ukrainian/
├── curriculum/l2-uk-en/        # Source curriculum
│   ├── plans/{track}/          # Module plans (source of truth)
│   ├── {track}/                # Content, activities, vocabulary
│   │   ├── meta/               # Build configuration
│   │   ├── activities/         # Interactive exercises (YAML)
│   │   ├── vocabulary/         # Vocabulary lists (YAML)
│   │   ├── research/           # Research notes (seminar tracks)
│   │   └── status/             # Audit results (auto-generated)
│   └── curriculum.yaml         # Module manifest
├── starlight/                  # Website (Astro Starlight)
│   └── src/content/docs/       # Published module pages (MDX)
├── scripts/                    # Build tools, audits, batch processing
├── schemas/                    # JSON Schema for YAML validation
└── docs/                       # Architecture docs, best practices
```

## Standards & Quality

- **CEFR-aligned** -- Common European Framework of Reference for Languages
- **Ukrainian State Standard 2024** -- Official language proficiency requirements
- **Automated audits** -- every module checked for word count, vocabulary, activities, naturalness
- **Cross-agent review** -- AI-assisted build pipeline with adversarial quality gates

## Quick Start (Developers)

Want to run the build pipeline locally or contribute code? The full guide is
in [CONTRIBUTING.md](CONTRIBUTING.md). The short version:

```bash
# 1. Python environment — pyenv + 3.12.8 with sqlite extensions
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.12.8
pyenv local 3.12.8
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Frontend
cd starlight && npm install && cd ..

# 3. Services (RAG on 8766, monitor API on 8765, Starlight on 4321)
./services.sh start
./services.sh status

# 4. Pre-commit hooks — mirror CI locally
pip install pre-commit && pre-commit install

# 5. Build a module
.venv/bin/python scripts/build/v6_build.py a1 2 --writer gemini

# 6. Audit a module
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/sounds-letters-and-hello.md

# 7. Tests
.venv/bin/pytest tests/ -q
```

All work happens on `main` — no feature branches. Use `git worktree` for
isolation when needed. Read `CLAUDE.md` + `docs/best-practices/` before
touching pipeline code.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas where help is especially welcome:
- Native speaker review of Ukrainian text
- Activity design and testing
- Bug reports and content corrections
- Pipeline tooling (Python) — see open issues tagged `infrastructure`

## License

Content (curriculum, wiki, exercises, plans) is
[CC BY-SA 4.0](LICENSE-CONTENT.md) — free to share and adapt.
Code (scripts, build tooling, Starlight components) is [MIT](LICENSE) — free
to use, modify, and distribute.

---

**Слава Україні!** 🇺🇦

*Star us on GitHub to support Ukrainian language education.*
