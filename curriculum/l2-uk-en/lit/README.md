# LIT Track: Ukrainian Literature & Classics

**Prerequisite:** C1 Core (Strict)
**Total Modules:** 30 (LIT-001 to LIT-030)
**Immersion:** 100% Ukrainian
**Pedagogy:** Academic seminar style (essay-based, no traditional activities)

---

## 📚 Creating a New LIT Module

### Step 1: Read the References

**BEFORE writing, consult archived reference modules:**

📂 **Location:** `curriculum/l2-uk-en/lit/reference/`

**Available:**
- `module-LIT-001.md` - Kotliarevsky biography
- `module-LIT-002.md` - Eneida Part I
- `module-LIT-003.md` - Eneida vocabulary
- `module-LIT-004.md` - Eneida military terms
- `module-LIT-005.md` - Natalka Poltavka
- `module-LIT-006.md` - Kvitka-Osnovianenko

**Extract from references:**
- Historical facts and biographical details
- Pre-compiled vocabulary lists
- Essay topics and model answers
- Engagement box ideas
- Reading recommendations

### Step 2: Use the Template

📄 **Template:** `docs/l2-uk-en/templates/lit-module-template.md`

The template includes:
- Complete structure guide
- Word count requirements (2200+ words)
- Vocabulary specifications (30-40 terms)
- Essay requirements (1-2 analytical essays)
- Engagement box guidelines (6-8 boxes)

### Step 3: Follow the Curriculum Plan

📋 **Plan:** `docs/l2-uk-en/LIT-CURRICULUM-PLAN.md`

The plan provides:
- Module topics and literary works
- Phase organization (LIT.1-LIT.6)
- Key concepts for each module
- Learning objectives

---

## 🎯 Module Requirements Quick Reference

| Element | Specification |
|---------|--------------|
| **Word count** | 2200+ words (core prose only) |
| **Vocabulary** | 30-40 literary/historical terms |
| **Content sections** | 15-20 themed sections (Частини I-XX) |
| **Essays** | 1-2 analytical essays (300-500 words each) |
| **Model answers** | Required for ALL essay prompts |
| **Engagement boxes** | 6-8 academic/cultural depth boxes |
| **Reading resources** | Links to UkrLib or scholarly sources |
| **Immersion** | 100% Ukrainian (English only in MDX description) |
| **Activities** | NONE (essay-based learning only) |

---

## 📁 Directory Structure

```
curriculum/l2-uk-en/lit/
├── README.md              # This file
├── reference/             # Archived original modules (research reference)
│   ├── README.md
│   ├── module-LIT-001.md
│   ├── module-LIT-002.md
│   ├── module-LIT-003.md
│   ├── module-LIT-004.md
│   ├── module-LIT-005.md
│   └── module-LIT-006.md
├── gemini/                # Review files (if any)
└── review/                # Module reviews
```

**New modules go in:** `curriculum/l2-uk-en/lit/` (root of lit folder)

---

## 🔄 Workflow

1. **Check curriculum plan** - Identify module topic and literary work
2. **Read reference modules** - Extract relevant research material
3. **Read template** - Understand required structure
4. **Write module** - Follow template, use references for content
5. **Run audit** - `python3 scripts/audit_module.py curriculum/l2-uk-en/lit/{module-file}.md`
6. **Generate MDX** - `npm run generate l2-uk-en lit {module-num}`
7. **Validate** - `npm run pipeline l2-uk-en lit {module-num}`

---

## ⚠️ Critical Reminders

- **DO NOT** copy-paste from reference modules verbatim
- **DO USE** them for research, vocabulary, and inspiration
- **DO NOT** create traditional activities (quiz, fill-in, etc.)
- **DO CREATE** analytical essay prompts with model answers
- **DO NOT** write in English except MDX description field
- **DO VERIFY** all historical facts and dates are accurate

---

*Last updated: 2024-12-24*
