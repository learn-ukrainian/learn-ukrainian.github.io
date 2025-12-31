# Ukrainian NLP Contribution Plan

## Mission

**Primary:** Build the best Ukrainian language curriculum possible
**Secondary:** Contribute valuable datasets to Ukrainian NLP community

---

## What Makes Our Curriculum Valuable for NLP

### 1. Scale
- 539 modules across 6 CEFR levels (A1→C2)
- ~10,000+ pedagogically-validated Ukrainian sentences
- ~12,000 vocabulary entries with translations

### 2. Structure
- **CEFR-graded content** (A1 simple → C2 complex)
- **Error annotations** (error-correction activities)
- **Grammatical progression** (cases, aspect, syntax)
- **Authentic Ukrainian** (no Russianisms, reviewed for purity)

### 3. Educational Focus
- **Pedagogical simplifications** documented (A1: "Я є студент" → B2: "Я студент")
- **Learner error patterns** (realistic mistakes in error-correction activities)
- **Calque detection** (English thinking → Ukrainian expression)

---

## Contribution Opportunities

### Phase 1: Low-Hanging Fruit (Now - 3 months)

#### 1.1 Graded Ukrainian Corpus
**What:** Extract all Ukrainian text from modules, tag by CEFR level

**Format:**
```json
{
  "level": "A2",
  "module": 5,
  "sentence": "Я дав книгу моєму другу.",
  "context": "Teaching dative case",
  "grammar_focus": ["dative_case", "pronouns"]
}
```

**NLP Use Cases:**
- CEFR text classification
- Readability prediction for Ukrainian
- Educational content generation

**Effort:** ~2 days (write extraction script)

**Deliverable:** `ukrainian-curriculum-corpus.json` + README

---

#### 1.2 Error Correction Dataset
**What:** Extract error→correct pairs from error-correction activities

**Format:**
```json
{
  "level": "A2",
  "error_sentence": "Я дав книгу мій друг",
  "correct_sentence": "Я дав книгу моєму другу",
  "error_type": "case_agreement",
  "error_span": {"start": 17, "end": 25, "text": "мій друг"},
  "correction_span": {"start": 17, "end": 29, "text": "моєму другу"},
  "explanation_uk": "Дативний відмінок після дієслова 'дати'",
  "explanation_en": "Dative case required after verb 'to give'"
}
```

**NLP Use Cases:**
- Training grammar error correction models
- Ukrainian spell/grammar checker improvement
- Learner error analysis research

**Effort:** ~3 days (parse error-correction activities, validate)

**Deliverable:** `ukrainian-error-correction-dataset.json` + paper

---

#### 1.3 Vocabulary Progressions
**What:** All vocabulary entries with CEFR level + first occurrence

**Format:**
```json
{
  "word": "книга",
  "ipa": "/ˈkn̪ɪɦɑ/",
  "pos": "noun",
  "gender": "feminine",
  "english": "book",
  "level": "A1",
  "first_module": 3,
  "frequency_in_corpus": 145
}
```

**NLP Use Cases:**
- Ukrainian vocabulary learning tools
- CEFR-aligned text simplification
- Vocabulary difficulty prediction

**Effort:** ~1 day (export vocabulary.db to JSON)

**Deliverable:** `ukrainian-cefr-vocabulary.json`

---

### Phase 2: Medium Effort (3-6 months)

#### 2.1 Calque Detection Dataset
**What:** English loan translations flagged by Gemini, validated manually

**Process:**
1. Run Gemini validation on all modules
2. Collect flagged calques (e.g., "робити сенс" → "мати сенс")
3. Annotate with source construction + natural Ukrainian

**Format:**
```json
{
  "calque": "робити сенс",
  "source_language": "English",
  "source_phrase": "make sense",
  "natural_ukrainian": "мати сенс",
  "alternative": "бути логічним",
  "level_taught": "B1",
  "explanation": "Verb 'make' incorrectly transferred from English"
}
```

**NLP Use Cases:**
- Training calque detection models
- Improving Ukrainian language quality tools
- Research on language interference patterns

**Effort:** ~2 weeks (validate all modules with Gemini, annotate calques)

**Deliverable:** `ukrainian-calque-detection-dataset.json` + research paper

---

#### 2.2 Pedagogical Simplifications Corpus
**What:** Compare A1/A2 teaching language vs natural Ukrainian

**Examples:**
- A1: "Я є студент" (explicit copula for teaching)
- Natural: "Я студент" (dropped copula)

- A2: "Я буду читати" (analytic future for teaching)
- Natural: "Я читатиму" (synthetic future)

**Format:**
```json
{
  "pedagogical_sentence": "Я є студент",
  "natural_sentence": "Я студент",
  "level": "A1",
  "teaching_purpose": "Explicit copula to teach sentence structure",
  "difference": "Copula 'є' dropped in natural speech",
  "grammaticality": "both_correct"
}
```

**NLP Use Cases:**
- Understanding formal vs colloquial Ukrainian
- Educational content generation (simplify for learners)
- Research on pedagogical language

**Effort:** ~1 week (annotate differences, validate with Gemini)

**Deliverable:** `ukrainian-pedagogical-corpus.json`

---

### Phase 3: Long-term Research (6-12 months)

#### 3.1 Integration with nlp_uk/Stanza
**What:** Test our curriculum against Ukrainian NLP tools, report findings

**Process:**
1. Run nlp_uk on all modules
2. Document false positives (pedagogical simplifications flagged as errors)
3. Create exception rules
4. Submit issues/PRs to nlp_uk with pedagogical context

**Deliverable:**
- GitHub issues on brown-uk/nlp_uk with examples
- Exception list for educational content
- Blog post: "Challenges in NLP for Ukrainian Language Education"

---

#### 3.2 UNLP Workshop Paper Submission
**What:** Submit to UNLP 2026 (May 29-30)

**Possible Topics:**
- "A Large-Scale CEFR-Graded Ukrainian Corpus for Educational NLP"
- "Error Correction Dataset for Ukrainian Language Learners"
- "Calque Detection in Ukrainian: Patterns from English Interference"

**Deadline:** ~March 2026 (estimated - check unlp.org.ua)

**Effort:** ~1 month (write paper, prepare dataset release)

**Impact:**
- Get feedback from Ukrainian NLP researchers
- Connect with community
- Formal contribution to research

---

## Contribution Workflow

### Immediate (This Month)
1. ✅ Use Gemini for curriculum validation (primary goal)
2. 📝 Document interesting patterns (calques, errors) as you find them
3. 📊 Start collecting data for Phase 1 contributions

### Short-term (Next 3 Months)
1. Complete A2 level (50 modules)
2. Extract Phase 1 datasets (corpus, errors, vocabulary)
3. Share on GitHub with CC-BY-4.0 license

### Medium-term (6 Months)
1. Complete B1 level (85 modules)
2. Create calque detection dataset
3. Write blog post about findings
4. Engage with Ukrainian NLP community (GitHub issues, discussions)

### Long-term (12 Months)
1. Complete B2 level (110 modules)
2. Prepare UNLP 2026 paper submission
3. Release comprehensive dataset
4. Present at workshop (if accepted)

---

## Community Engagement Strategy

### 1. Start Small (Low Commitment)
- ⭐ Star repos: brown-uk/nlp_uk, osyvokon/awesome-ukrainian-nlp
- 🐛 Submit issues when you find edge cases
- 💬 Join Ukrainian NLP discussions (GitHub, forums)

### 2. Share Work in Progress
- 📝 Blog posts about curriculum development
- 🗂️ Interim dataset releases (A1, A2, B1 as completed)
- 🧪 Experiments: "Testing nlp_uk on Educational Content"

### 3. Formal Contribution
- 📄 Research paper at UNLP workshop
- 📊 Full dataset release with documentation
- 🤝 Collaboration offers (if researchers are interested)

---

## Licensing & Attribution

**Curriculum License:** MIT (your content)
**Dataset License:** CC-BY-4.0 (recommended for data sharing)

**Attribution:**
- "Krisztián Koos - Learn Ukrainian Language Curriculum"
- "Developed with support from Ukrainian NLP community tools (nlp_uk, Stanza)"
- "Validated using Gemini Pro (Google)"

---

## Success Metrics

### Curriculum Quality (Primary)
- ✅ All modules pass audit
- ✅ High learner satisfaction
- ✅ Zero Russianisms/calques in final content

### NLP Contribution (Secondary)
- 🎯 **Year 1:** Release 3 datasets (corpus, errors, vocabulary)
- 🎯 **Year 2:** 1 paper published or submitted
- 🎯 **Year 3:** Active collaboration with 1+ Ukrainian NLP researcher

---

## Why This Matters

**For Ukrainian NLP:**
- Educational content is underrepresented in NLP research
- CEFR-graded corpora are rare for any language
- Your pedagogical focus provides unique value

**For You:**
- Engage with community around shared passion
- Learn about NLP while building curriculum
- Contribute to Ukrainian language preservation & education

**For Learners:**
- Better curriculum (primary benefit)
- Potential future tools built on this data (secondary benefit)

---

## Next Steps

1. **Finish this conversation** - Decide on Phase 1 scope
2. **Create extraction scripts** - Automate dataset generation
3. **Document as you go** - Track interesting patterns
4. **Share early & often** - Get feedback from community

---

**Document Status:** Draft v1.0
**Author:** Krisztián Koos
**Last Updated:** 2025-12-27
**Next Review:** After A2 completion (50 modules)
