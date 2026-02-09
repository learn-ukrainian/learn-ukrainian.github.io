# Learn Ukrainian

**Мова – душа народу • Language is the soul of a nation**

A free, open-source Ukrainian language course from A1 to C2, based on the **Ukrainian State Standard 2024**.

**[Start Learning →](https://learn-ukrainian.github.io)**

---

## What is this?

A complete Ukrainian language curriculum for English speakers:

- **6 CEFR levels** (A1 → C2) with 500+ interactive lessons
- **Theory-first approach** — understand grammar deeply, not just memorize phrases
- **Interactive exercises** — quizzes, drag-and-drop, fill-in-the-blank, error correction
- **Cultural context** — Ukrainian history, traditions, music, and literature
- **100% free** — no ads, no subscriptions, no paywalls

## Quick Links

| Level | Description | Status |
|-------|-------------|--------|
| [**A1 Beginner**](https://learn-ukrainian.github.io/docs/a1/) | Cyrillic alphabet, basic phrases, simple grammar | ✅ Complete (34 lessons) |
| [**A2 Elementary**](https://learn-ukrainian.github.io/docs/a2/) | All 7 cases, verb aspects, comparisons | ✅ Complete (57 lessons) |
| [**B1 Intermediate**](https://learn-ukrainian.github.io/docs/b1/) | Complex sentences, motion verbs, participles | 🔍 In QA (85 lessons) |
| [**B2 Upper-Intermediate**](https://learn-ukrainian.github.io/docs/b2/) | Grammar mastery, phraseology, Ukrainian history | 📋 Planned (110 lessons) |
| [**C1 Advanced**](https://learn-ukrainian.github.io/docs/c1/) | Biographies, stylistics, folk culture, literature | 📋 Planned (160 lessons) |
| [**C2 Mastery**](https://learn-ukrainian.github.io/docs/c2/) | Native-level proficiency, professional specialization | 📋 Planned (100 lessons) |

## Why Learn Ukrainian?

- **45 million speakers** worldwide
- **Rich literary tradition** — Shevchenko, Franko, Lesya Ukrainka
- **Unique grammar** — 7 cases, verbal aspect, motion verb system
- **Growing global interest** — solidarity with Ukraine

## Features

### For Learners

- Step-by-step progression from zero to fluency
- IPA pronunciation guides for every word
- Authentic YouTube videos and podcasts
- Self-assessment checkpoints every 10 lessons

### For Developers

- Open-source curriculum in Markdown
- Automated quality audits
- JSON export for app integration
- Docusaurus-powered web platform

## Getting Started

### Online (Recommended)

Visit **[learn-ukrainian.github.io](https://learn-ukrainian.github.io)** and start with A1 Module 1.

### Local Development

The project requires Python 3.10+ and Node.js.

```bash
# Clone and setup
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
npm install

# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the web platform
cd docusaurus && pnpm start
# Opens at http://localhost:3000/
```

See [DEVELOPER-GUIDE.md](docs/DEVELOPER-GUIDE.md) for more details.

## Documentation

- **[Developer Guide](docs/DEVELOPER-GUIDE.md)**: Setup, workflow, and testing.
- **[Orchestration Workflow](docs/ORCHESTRATE-REBUILD.md)**: Automated module generation.
- **[Batch Operations](docs/BATCH-OPERATIONS.md)**: Large-scale curriculum updates.
- **[Playgrounds](docs/PLAYGROUNDS.md)**: Interactive visualization tools.
- **[Schema Reference](docs/SCHEMA-REFERENCE.md)**: YAML file formats and validation.
- **[Error Reference](docs/ERROR-REFERENCE.md)**: Audit and review error codes.

## Project Structure

```
learn-ukrainian/
├── curriculum/l2-uk-en/     # Source lessons (Markdown)
│   ├── a1/                  # A1: 34 modules
│   ├── a2/                  # A2: 57 modules
│   ├── b1/                  # B1: 85 modules (in progress)
│   └── ...                  # B2, C1, C2
├── docusaurus/              # Web platform
│   ├── docs/                # Generated lesson pages
│   └── src/components/      # Interactive activities
├── scripts/                 # Build tools & quality audits
└── docs/                    # Curriculum plans
```

## Standards & Quality

- **CEFR-aligned** — Common European Framework of Reference
- **Ukrainian State Standard 2024** — Official language proficiency requirements
- **Automated audits** — Every lesson checked for vocabulary, grammar, activity counts
- **Looking for native reviewers** — Help us improve linguistic accuracy!

## Contributing

We welcome contributions! See:
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` — Content quality standards
- `CLAUDE.md` — AI agent instructions

## License

Content is provided for educational use. See LICENSE for details.

---

**Слава Україні! 🇺🇦**

*Learn Ukrainian is an open-source project. Star us on GitHub to support Ukrainian language education.*
