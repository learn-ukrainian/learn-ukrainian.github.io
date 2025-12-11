# Curricula Opus

**A Theory-First Language Learning Platform**

---

## 🌐 Mission

Curricula Opus is a comprehensive language learning platform that provides structured, high-quality educational curricula. We believe in a **Theory-First** approach—deep understanding of grammar, culture, and history alongside practical application.

Currently building a complete **Ukrainian as a Second Language (L2)** curriculum for English speakers.

## ✨ Features

- **📚 Comprehensive Curriculum** — A1 to C2 pathway aligned with CEFR and Ukrainian State Standards
- **🎓 Theory-First Approach** — Deep grammar explanations, cultural context, and historical insights
- **🎮 Interactive Activities** — Drag-and-drop exercises, quizzes, match-ups, and more
- **🌍 Cultural Immersion** — Authentic materials, folklore, literature, and decolonization lens
- **📖 Static Textbooks** — Human-readable Markdown and HTML for offline study

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/krisztiankoos/curricula-opus.git
cd curricula-opus
npm install

# Generate MDX content for Docusaurus
npm run generate l2-uk-en a1

# Start the interactive learning platform
cd docusaurus
npm start
# Opens at http://localhost:3000/curricula-opus/
```

## 📂 Project Structure

```
curricula-opus/
├── curriculum/l2-uk-en/     # Source curriculum in Markdown
│   ├── a1/                  # A1 modules (01-30)
│   ├── a2/                  # A2 modules (01-50)
│   └── ...                  # B1, B2, C1, C2
├── docs/l2-uk-en/           # Curriculum plans & guidelines
├── docusaurus/              # Interactive web platform (Docusaurus)
│   ├── docs/                # Generated MDX content
│   └── src/components/      # Interactive activity components
├── output/                  # Generated static HTML/JSON
└── scripts/                 # Build & generation tools
```

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `npm run generate l2-uk-en a1` | Generate HTML/JSON for A1 modules |
| `python3 scripts/audit_module.py <file>` | Audit a module for quality |
| `npx ts-node scripts/generate-mdx.ts l2-uk-en a1` | Generate MDX for Docusaurus |

## 📈 Progress

| Level | Modules | Status |
|-------|---------|--------|
| **A1** | 30 | 11 complete, 19 in progress |
| **A2** | 50 | Planning complete |
| **B1** | 80 | Planning complete |
| **B2** | 125 | Planning complete |
| **C1** | 115 | Planning complete |
| **C2** | 80 | Planning complete |

## 🗺️ Roadmap

- [x] A1-C2 Curriculum Planning
- [x] Interactive Web Platform (Docusaurus)
- [x] Drag-and-Drop Activities
- [ ] Complete A1 Content (30 modules)
- [ ] Audio Integration
- [ ] Mobile App

## 🤝 Contributing

See `docs/` for content guidelines and `CLAUDE.md` / `GEMINI.md` for AI agent instructions.

---

**Слава Україні! 🇺🇦**