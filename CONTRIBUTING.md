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

### Code Contributions

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-description`
3. Make your changes
4. Submit a pull request

## Project Architecture

### Curriculum Structure

Modules live in `curriculum/l2-uk-en/{track}/` with this structure per module:

| File | Purpose |
|------|---------|
| `plans/{track}/{slug}.yaml` | Module plan (immutable source of truth) |
| `meta/{slug}.yaml` | Build configuration |
| `{slug}.md` | Lesson content (Ukrainian prose) |
| `activities/{slug}.yaml` | Interactive exercises |
| `vocabulary/{slug}.yaml` | Vocabulary lists |

### Website

The website is built with [Astro Starlight](https://starlight.astro.build/) and lives in `starlight/`. Module content is published as MDX files in `starlight/src/content/docs/`.

### Build Pipeline

Content is generated through a multi-agent pipeline:
- **Gemini** builds content (research, prose, activities)
- **Claude** reviews for quality (adversarial cross-agent review)
- Automated audits check word counts, vocabulary, activity schemas, and naturalness

### Local Development

```bash
# Website
npm run dev:starlight  # http://localhost:4321

# Python tools (audits, batch processing)
.venv/bin/python scripts/audit_module.py <path-to-module.md>
```

**Requirements:** Node.js 20+, Python 3.12+ with venv

## Quality Standards

- **Word count minimums**: A1: 2000, A2: 3000, B1-B2: 4000, Seminar: 5000
- **All Ukrainian text** must be grammatically correct and natural-sounding
- **No Russian calques** (e.g., use "добре" not "хорошо", "кіт" not "кот")
- **Activities test language comprehension**, not content recall
- **CEFR alignment** -- grammar and vocabulary must match the target level

## Code of Conduct

Please be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
