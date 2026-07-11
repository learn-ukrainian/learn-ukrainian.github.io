# UNLP 2025/2026 — detailed reading notes with excerpts

> Companion to `unlp-2025-2026-findings.md` (the one-line digest). THIS file holds the
> details we intend to USE: numbers, methods, excerpts with page refs, and what each fact
> changes in our pipeline. PDFs: `docs/references/private/unlp-papers/` (gitignored local
> library; ACL Anthology is CC BY 4.0). **Read-status is tracked honestly per paper —
> "FULL" means a complete read with page-referenced notes; "ABSTRACT" means only the
> abstract was digested and details must not be cited from memory.**

## Read-status ledger

| Paper | Status | Notes section |
| --- | --- | --- |
| 2026.unlp-1.18 CEFR assessment (Kanishcheva & Kopotev) | **FULL** (driver, 2026-07-11) | below |
| 2025.unlp-1.11 Stress/phonemization TTS (Senyk) | ABSTRACT | queued deep-read |
| 2026.unlp-1.12 Proficiency benchmark (Galeshchuk) | ABSTRACT | queued deep-read |
| 2026.unlp-1.13 GEC via prompting (Karpo & Chernodub) | ABSTRACT | queued deep-read |
| 2026.unlp-1.17 Native paraphrases (Fesenko) | ABSTRACT | queued deep-read |
| 2025.unlp-1.2 ZNO-Vision (Paniv) | ABSTRACT | queued deep-read |
| 2025.unlp-1.14 Kobza + Modern-LiBERTa (Haltiuk) | ABSTRACT | queued deep-read |
| 2026.unlp-1.7 OCR old Ukrainian (Chaplynskyi) | ABSTRACT | later wave |
| 2026.unlp-1.19 Local Ukrainian RAG (Trokhymovych) | ABSTRACT | later wave (backend phase) |
| 2026.unlp-1.5 SimIdioms (Petruniv) | ABSTRACT | later wave |
| 2025.unlp-1.4 UAlign (Kravchenko) | ABSTRACT | later wave |
| 2025.unlp-1.15 Synonym attacks (Mudryi) | ABSTRACT | later wave |
| 2025.unlp-1.17 OmniGEC (Kovalchuk) | ABSTRACT | later wave |

---

## 2026.unlp-1.18 — Automated CEFR-Level Assessment for Ukrainian Texts — **FULL READ**
**Kanishcheva (Heidelberg U / SET U) & Kopotev (Stockholm U / U Helsinki).** pp. 209–222.
Funding: Research Council of Finland (partial).

### Dataset (§3, Table 1, p. 211-212)
- 437 texts total: A1=89, A2=123, B1=110, B2=115. SHORT texts: avg 89–242 tokens;
  total ≈ 84K tokens. Digitized from print textbooks for Ukrainian-as-foreign-language
  (Appendix A lists them: Палінська «Крок-1», Карпенко practicums, Бакум «Калейдоскоп
  культур», Дерба, Малюга/Городецька test items — Крок overlaps our corpus inventory).
- **"curated from diverse educational resources that remain copyright-protected and
  therefore cannot be distributed directly"** (§3, p. 211; reaffirmed in Ethical
  Considerations p. 218). Feature values for all texts + code + prompts ARE public:
  github.com/kopotev/fluencymeter.
- Coverage limitation (p. 217): **no C1/C2 materials** — "limits the model's ability to
  assess advanced proficiency."

### Features (§3.2, p. 211-212) — all deterministically computable
Four dimensions: descriptive character-based (token length, syllables/token, token count);
lexical diversity (unique tokens/lemmas, hapax legomena, MATTR for tokens and lemmas);
morphological diversity (POS distribution, function-word proportion); syntactic complexity
(sentence length stats, clauses/sentence, dependency tree depth — max root-to-node chain
per tree, arithmetic mean per text). UD parsing via spaCy `uk_core_news_sm`.

### Key quantitative results (Table 2 p. 213, §3.3)
27 of 30 metrics significant across levels (p<0.001). Monotonic-trend verified via
polynomial contrasts. The numbers to remember (A1 mean → B2 mean):
- **Avg dependency tree depth: 3.68 → 5.06 (F=41.60) — the single strongest marker.**
- Hapax legomena: 43.11 → 120.86 (F=39.78) · Unique lemmas: 57.85 → 158.66 (F=34.33)
- Avg sentence length: 7.35 → 13.07 tokens (F=36.92) · Clauses/sentence: 1.04 → 1.75
- MATTR(lemmas): 0.77 → 0.88 · Noun frequency: 35.13 → 99.28 · Token length: 5.22 → 5.85
- NOT significant: gerunds (p=.094), numerals (p=.134) — don't use as level features.
- Topic-bias validation via BERTopic (multilingual-e5-base + UMAP + HDBSCAN): classification
  is driven by structural complexity, not topic vocabulary (§3.4). Topic markers anyway:
  classroom/student vocab dominates A1 (32.6%); culture/technology/profession marks B2 (25.2%).

### Model comparison (Table 3, p. 217; stratified 5-fold CV)
- **Random Forest (all features): macro-F1 0.576** — best F1 overall.
- XLM-RoBERTa fine-tuned: F1 0.574 (best accuracy 0.591). mBERT: 0.537.
- GPT-5.5 few-shot: 0.564 (self-consistency: no gain, 0.561). GPT-4.1: 0.498.
- Confusion concentrates in A2/B1 (Fig. 5: A1 recall 70.8%, B2 68.7%; B1 only 40%).
- LLM caveat (p. 217): "longer input texts may bias the models toward higher-level
  predictions" — relevant when we run ANY LLM-based level checks on long modules.

### What we USE from this paper
1. **#4952** — build our own deterministic difficulty gate from their feature set
   (tree depth + lexical diversity core), calibrated on OUR corpus (orders of magnitude
   more tokens, and it extends to C1/C2 which they lack).
2. Outreach (drafts local, `.agent/tmp/`): offer the openly licensed corpus (kills their
   copyright constraint), ask about fluencymeter classifier state/license. Their Future
   Work #2 (corpus expansion w/ professional instructors) = literally our offer incl.
   teachers.
3. Method hygiene we adopt: topic-bias validation for any difficulty classifier we train;
   interpretability argument for deterministic features in pedagogy tooling.

---

*(Deep-read notes for the queued papers land below as they are completed; each entry
must carry page-referenced numbers before we cite it in briefs or decisions.)*
