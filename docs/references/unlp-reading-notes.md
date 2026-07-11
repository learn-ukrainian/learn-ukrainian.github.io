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
| 2025.unlp-1.11 Stress/phonemization TTS (Senyk) | **FULL** (this session, 2026-07-11) | below |
| 2026.unlp-1.12 Proficiency benchmark (Galeshchuk) | **FULL** (this session, 2026-07-11) | below |
| 2026.unlp-1.13 GEC via prompting (Karpo & Chernodub) | **FULL** (this session, 2026-07-11) | below |
| 2026.unlp-1.17 Native paraphrases (Fesenko) | **FULL** (this session, 2026-07-11) | below |
| 2025.unlp-1.2 ZNO-Vision (Paniv) | **FULL** (this session, 2026-07-11) | below |
| 2025.unlp-1.14 Kobza + Modern-LiBERTa (Haltiuk) | **FULL** (this session, 2026-07-11) | below |
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
2. The paper's Future Work items (corpus expansion; educator-facing analysis tooling)
   are adjacent to our roadmap — our graded corpus is CC BY-SA 4.0 and our #4952 gate +
   backend phase cover similar ground independently.
3. Method hygiene we adopt: topic-bias validation for any difficulty classifier we train;
   interpretability argument for deterministic features in pedagogy tooling.

---

## 2025.unlp-1.11 — Context-Aware Lexical Stress Prediction and Phonemization for Ukrainian TTS Systems — **FULL READ**
**Anastasiia Senyk & Yurii Paniv (Ukrainian Catholic University); Mykhailo Lukianchuk & Valentyna
Robeiko (Taras Shevchenko National University of Kyiv).** pp. 96–104 (UNLP 2025).
Compute grant: "Talents for Ukraine" project of Kyiv School of Economics; advice from Tetiana
Zakharchenko & Mariana Romanyshyn (Acknowledgments, p. 102).

### Release status — PUBLIC (all three artifacts)
- p. 97 (§1 end): "The benchmark, datasets, and source code are available at the following link:
  https://github.com/lang-uk/ukrainian-tts-preprocessing" — verbatim, one link for benchmark + code
  + phonemizer. p. 98 reaffirms "The dataset will be publicly available to encourage further research
  and reproducibility." No license string is printed in the paper body (check the repo for the license).

### Benchmark: Ukrainian Lexical Stress Corpus (§3.1, Table 1 p. 98)
- **First public sentence-level stress benchmark for Ukrainian.** 1,026 sentences, manually annotated
  with primary stress by a native speaker; OOV words + misspellings deliberately retained.
- Table 1 counts: 1,026 sentences · 6,439 unique word forms · **640 words with stress ambiguity (meaning
  or inflection)** · 296 words with ≥2 stress forms present · **1,005 OOV words.**
- Sources (§3.1.1): 300 sentences from Wikipedia + 438 from the Pluperfect GRAC corpus (Shvedova &
  Lukashevskyi 2024). Plus 288 commonly-used stress-ambiguous words drawn from "Dictionaries of Ukraine"
  (Ukrainian Lingua-Information Foundation, 2008), each given a second sentence with the alternate stress
  → +288 examples for balanced heteronym coverage.

### What "context-aware" actually covers (homograph/heteronym method)
- The disambiguation is **sentence-level**, done two ways and compared: (a) a **ByT5 G2P** model (byte-level,
  ZY et al. 2022) trained on synthetically stress-labeled text to predict stress over the whole sentence; and
  (b) the dictionary-based **Ukrainian Word Stress** tool that resolves heteronyms via **POS tags + grammatical
  features of the retrieved word forms** in context (§3.2.3, p. 99). Two fallback modes: `OnAmbiguity.First`
  (pick first listed variant) and `OnAmbiguity.Skip` (leave unlabeled).
- Synthetic training data (§3.2.1, p. 98): Wav2Vec2 ASR configured to emit stress marks, trained on Common
  Voice 19 (~30k sentences); pseudo-labels from Ukrainian Word Stress (Syvokon 2022, `OnAmbiguity.Skip`) with
  Ukrainian Accentor fallback + dictionary post-correction → **93.81% word / 72.00% sentence** stress accuracy;
  then applied to Voice-of-America speech → **~135,000 sentences, ~80,000 unique words** synthetic corpus.

### Key quantitative results
- **Stress (Table 2, p. 101).** Best sentence-level = **hybrid ByT5 G2P + Word Stress(Skip): 52.0% sentence /
  92.5% word.** Best on ambiguous words = **Ukrainian Word Stress(First): 64.3% ambiguous-word acc, 47.3% mean
  macro-F1** (a dictionary+POS method, *not* the neural model). Standalone ByT5 G2P: 35.3% sent / 87.7% word /
  58.1% ambiguous / 37.2% F1. All evals exclude words with <2 vowels.
- **Phonemization / G2P (§4; Table 4 p. 101).** Rule-based Python-regex system, **52-phoneme IPA inventory**
  (Appendix A / Table 5, p. 104). WER: **1.23%** on the 487-word hand-built diverse set (incorrect only);
  3.07% (incorrect) / **6.15%** (incorrect+controversial) on the 553-word VESUM-generated set; baseline
  letter→phoneme mapper **48.75%**. PER not computed (≤1 error type per word). Notable design calls: /в/ split
  into bilabial /w/ and labio-dental /v/ as distinct phonemes; neutral gemination (treat doubled letters as two
  phonemes); ordered rule pipeline (mapping → cluster reduction → assimilation → allophony), worked example for
  шістдесят in Table 3 p. 101.

### Limitations + future work (p. 102, verbatim-adjacent)
- Ambiguous-word performance "is limited by sparse coverage in the training data and the reliance on
  automatically labeled examples using Wav2Vec-based model" — heteronym representation is their key future
  direction.
- Phonemizer "operates strictly at the word level and does not handle abbreviations or numerical expressions";
  future extension to sentence level.
- "neither pipeline accounts for non-standard language varieties, such as regional dialects."

### What we USE from this paper (#4696 TTS audio)
1. **Reuse the released rule-based phonemizer directly** for flashcard/sentence audio: it is public, pure
   Python-regex, IPA-out, 52 phonemes, 1.23% WER on clean text, and MIT-style easy to vendor (verify repo
   license). It cleanly separates stress placement from G2P, which matches our need (mark stress on a UA
   word/sentence, then phonemize for TTS).
2. **For stress, adopt the hybrid**: dictionary Word Stress(First) for known/ambiguous words (best ambiguous
   64.3%), ByT5 fallback for OOV. Their own numbers say the neural model does NOT win on heteronyms — so our
   audio pipeline should lean on the VESUM/dictionary path we already have, using the model only for OOV.
3. **Gap to mind:** no abbreviations/numbers, no dialects, word-level only. Our sentence audio must pre-expand
   numerals/abbreviations before handing text to their phonemizer.
4. Outreach hook: their explicit future work is heteronym coverage + sentence-level phonemization — areas where
   our curated sentence corpus (with human-verified stress) could be offered as labeled data.

---

## 2026.unlp-1.12 — Toward a Gold-Standard Benchmark for Evaluating Ukrainian Language Proficiency in LLMs — **FULL READ**
**Svitlana Galeshchuk (BNP Paribas / West Ukrainian NU); Yuliia Maksymiuk (independent); Yuliia
Chernobrov (National Commission for State Language Standards); Oleksandra Antoniv, Nina Stankevych,
Nataliia Faryna (Ivan Franko NU of Lviv); Oksana Popkova (Kherson State U).** pp. 121–135 (UNLP 2026).
Correspondence y.chernobrov@mova.gov.ua. Thanks to the Kyivstar team for testing within their eval
framework (Acknowledgments, p. 128).

### Benchmark mechanics + release status — PUBLIC on HF
- **347 expert-curated multiple-choice questions**, each with 4 or 5 options (K∈{4,5}) and exactly one
  normatively-correct answer (§2, p. 121–122; §4.1, p. 123). Built by professional philologists with 10–30
  years of university teaching; each item reviewed by ≥1 other expert; ambiguous items revised/removed.
- Release (p. 128, footnote 1): dataset "openly accessible to the community," at
  **https://huggingface.co/datasets/SGaleshchuk/ULP-Ukrainian-Language-Proficiency**.
- **Task format = MCQ classification, not generation.** This is a *model*-knowledge probe (can an LLM pick the
  normatively-correct Ukrainian form), NOT a text-correction/GEC set.
- Coverage (§2, pp. 122–123): grammar (morphology + syntax), lexical norms, orthography. Morphology phenomena
  (p. 122) include genitive -а(-я)/-у(-ю) in masc. sg. nouns, instrumental/vocative endings, genitive plural,
  gender of indeclinable loanwords/abbreviations, comparative/superlative, numeral+noun agreement, case of
  numerals, pronouns, personal/future/imperative verb forms, participles & gerunds. Syntax (p. 123): prepositional
  vs non-prepositional government, complex agreement, participial phrases, homogeneous parts, subject–predicate
  agreement. Full worked examples w/ EN gloss + translit in Appendices A–C (pp. 129–134).
- Sources compiled from Matsiuk & Stankevych 2017, Serbenska 2019, Voloshchak 2007, Maznichenko et al. 2019
  (p. 122). Question length mean 7.4 words (Fig. 2); answer position roughly uniform, slot 4/Д underused because
  only some items have 5 options (Fig. 1).
- **Error taxonomy = 4 categories** (grammar-morphology, grammar-syntax, vocabulary/lexical norms, orthography).
  Question-hardness (Table 1, p. 126): Hard 70 (20.1%), Difficult 90 (26.0%), Medium 88 (25.3%), Easy 99 (28.6%).
  Hardness is defined by how many of 4 large models answer correctly (0→hard … 3–4→easy).

### Key quantitative results (Table 2, p. 127)
- **Ceiling is low: smaller models ≤42.1%, large models up to ~59.6%** (abstract; Table 2). "even the
  best-performing model demonstrates maximum accuracy of approximately 60%" (p. 128).
- Best overall: **gpt-oss-120b — 59.6% XM zero-shot (EN)**, 55.0/55.2 (EN/UK) at 5-shot XM/EM.
- mistral-medium-2508: 46.7–49.1%. mistral-small-2506: 33.5–41.0%. Meta-Llama-3.3-70B: 33.7–36.9%.
- Ukrainian-focused: **Lapa 12B IT is the strongest UA-adapted model, 42.1% XM 5-shot (EN)**; LL zero-shot
  38.7/37.6 (EN/UK). MamayLM consistently *lower* despite the same Gemma-3 base ("adaptation data and tuning
  strategy matter more than the underlying base," p. 125–126).
- Smaller multilingual: Gemma-3-12B-IT best in group (LL 36.2/35.8; XM5 36.3/37.0), essentially tying Lapa.
- Qwen3-8B (reasoning): XM 34–38% but **EM UK only 6.4%** — includes the right answer without following the
  answer format; authors flag XM as the fairer metric for reasoning models.
- Prompt-language effect small/inconsistent; English instructions sometimes help LLaMA (better instruction-
  following). GPT-OSS *drops* ~5pp under few-shot (mixed EN-instructions + UA-examples). Hardware (§4.3, p. 124):
  single 96 GB GPU, vLLM 0.10.1.1, LightEval 0.13.1.dev0.

### Limitations + future work (§6, pp. 126–128)
- Fixed prompt + 5 few-shot may under-showcase models; per-model prompt customization is future work.
- Reasoning models not run in the log-likelihood setting (long thinking traces don't fit LL scoring).
- Answer-label bias (fixed A/B/C/D order) acknowledged; future work = alternative label formats + full-answer
  generation. Generation capped at 15 output tokens (extraction-vs-final-answer trade-off unresolved).

### What we USE from this paper (#4913 harness · model selection)
1. **Direct model-selection probe, not a harness eval.** The benchmark tests whether a given LLM *knows*
   normative Ukrainian grammar/orthography. Our concrete use: **run our candidate writer/reviewer models
   against ULP-347** to rank them on normative-UA knowledge before assigning pipeline lanes — it is public, small,
   and cheap to run. (It does NOT evaluate our writer/reviewer *pipeline* end-to-end; it scores the underlying
   model.)
2. **Reviewer-dimension mapping:** their 4-category taxonomy + the explicit morphology/syntax phenomena list
   (genitive endings, vocative, numeral agreement, prepositional government, participial phrases…) is a ready
   checklist to cross-check our reviewer rubric coverage.
3. **Sobering calibration number to cite in briefs:** best LLM ≈60% on normative Ukrainian MCQ → do NOT trust
   any single model's grammar judgment un-gated; keep VESUM/`sources`-backed verification (#M-4) in the loop.
4. Honest scope note: it is *not* a generation benchmark, so it cannot score our produced module text; pair it
   with the GEC paper (1.13) for the correction side.

---

## 2026.unlp-1.13 — How Far Can Prompting Go for Minimal-Edit Ukrainian Grammatical Error Correction? — **FULL READ**
**Kateryna Karpo (Ukrainian Catholic University / YouScan) & Artem Chernodub (Zendesk).** pp. 136–154
(UNLP 2026). Karpo's UCU M.Sc. thesis (footnote 3, p. 136). Correspondence a.chernodub@gmail.com.
**This is the single most reusable paper in the set for our reviewer-fixer prompts.**

### Release status + data — PUBLIC code/prompts/outputs
- p. 136 (footnote 2): "Code, prompts, and outputs are publicly available" at
  **https://github.com/katerynkarpo/gec_unlp_2026**.
- Data (§2, p. 137): **GEC-only track of the UNLP-2023 Shared Task** (Syvokon & Romanyshyn 2023), built on
  UA-GEC. Splits: **train 31,038 / valid 1,422 / test 1,274** (test gold held out). Metric = span-level
  Precision/Recall/**F0.5** via a **Ukrainian ERRANT adaptation**; per-error-type from ERRANT alignment.
- Models tested (§2, p. 137): 11 API LLMs (exact snapshot IDs given) — GPT-4.1, GPT-4.1-mini, GPT-5.1, GPT-5.2,
  GPT-5.4; Kimi-K2; Gemini-3-Flash, Gemini-3-Pro, Gemini-3.1-Pro; Claude Sonnet 4.6, Claude Opus 4.6; plus
  open-source Lapa v0.1.2. Temperature 0 where available.

### The exact best prompt configuration (the driver's ask) — Appendix A, pp. 147–153
- **Winner: minimal-edits + few-shot + LLM-optimized prompt, in UKRAINIAN.** Best single result =
  **Gemini-3.1-Pro, minimal-edits + few-shot + optimized-v2 (UA): P 70.77 / R 63.63 / F0.5 69.22** (Table 3,
  p. 142), closing >90% of the gap from the prior API result (GPT-3.5 F0.5 27.4) to fine-tuned SOTA (mT5-large
  F0.5 73.14).
- **Language:** minimal-edits prompts are UA "as the language-specific rules they encode require Ukrainian to
  express precisely" (§3, p. 138 / §5, p. 144); zero-shot & few-shot use EN for most models — **only the Claude
  family benefits from UA prompts even at zero-shot** (Opus 47.30→49.70; Sonnet 42.54→43.63, Table 1 p. 140).
- **Framing = strict minimal-edit.** The UA minimal-edits system prompt (Appendix A.3, pp. 148–149) enumerates a
  **16-category error taxonomy** — Spelling, Punctuation, G/Case, G/Gender, G/Number, G/Aspect, G/Tense,
  G/VerbVoice, G/PartVoice, G/VerbAForm, G/Prep, G/Participle, G/UngrammaticalStructure, G/Comparison,
  G/Conjunction, G/Other — plus explicit UA rules (у before consonants / в before vowels & sentence start;
  об/о before одинадцятій/consonants; em-dash — in dialogue not hyphen; parenthetical words comma-set; vocative
  in address Настя→Насте, Олег→Олеже, мама→мамо) and **STRICT rules**: smallest possible change · NEVER substitute
  synonyms or rephrase · never change a word unless misspelled · preserve quote style · preserve capitalization ·
  "If in doubt, do NOT change" · return original if no errors · "Return ONLY the corrected text."
- **Few-shot count = the same fixed set of exemplars** drawn from UA-GEC train, including "no-change" pairs
  (Appendix A.2 / A.4), prepended to the minimal-edits system prompt.
- **LLM-assisted optimization (§3, p. 139):** implemented as a **Claude Code skill powered by Claude Opus 4.6**
  acting as error-analyst + prompt-engineer. Loop: eval candidate on valid set (span TP/FP/FN) → cluster
  mismatches into linguistic patterns by frequency → insert a prohibition rule OR a targeted example → keep the
  edit only if F0.5 improves, else revert; repeat to plateau. optimized-v1 tuned on GPT-4.1-mini; optimized-v2
  on Gemini-3-Flash. Prompt length grows 43 tokens (zero-shot EN) → **3,474 tokens** (min-edits+few-shot+opt-v2
  UA), ~32× (Fig. 1, p. 139).

### Per-error-category results (which categories prompting handles worst)
- **Minimal-edits helps most on the rule-clear categories** (Fig. 2 / Table 4, p. 143, F0.5, GPT-4.1-mini
  zero-shot EN → Gemini-3.1-Pro opt-v2 UA): **Punctuation 50.67→77.56 (+26.9), G/Case 32.82→61.83 (+29.0),
  G/Gender 64.94→77.59 (+12.7).** Spelling and G/Number reliable under both.
- **Where detailed instructions BACKFIRE (the low-frequency-category finding):** under the optimized prompt
  **G/Prep, G/VerbVoice, G/Conjunction collapse to F0.5 = 0** — the model, told to be conservative, abandons these
  corrections entirely (baselines scored 51.47 / 34.48 / 69.44). **G/UngrammaticalStructure stays broken in both**
  (28.17→28.04). Net: precision +8–21pp but a long tail of low-frequency grammar goes uncorrected.
- **Five Ukrainian-specific over-correction patterns** (§4/RQ4, p. 143; false-positive counts / 1,274 sentences)
  — all caused by "correction heuristics calibrated to English":
  1. **En-dash over-normalization** (– → —; ~49 FP, 3.8%) — em-dash obligatory only in direct speech; model
     applies it everywhere.
  2. **Dialogue reformatting** («текст», — сказав → dash-style; ~40 FP, 3.1%) — a single prohibition rule fixes it.
  3. **Synonym/register substitution** (~30 FP, 2.4%) — e.g. знаходиться → перебуває, violating minimal-edit.
  4. **Euphonic preposition alternation** (в/у, з/із/зі; ~17 FP, 1.3%) — phonetically conditioned, model over- &
     under-corrects.
  5. **Collapse of acceptable morphological variants** (навчались/навчалися, їх/їхній) — model forces one preferred
     form; "space of acceptable alternations is open-ended and cannot be exhaustively covered by prompt examples."
- **Optimization does NOT transfer across families:** opt-v2 (tuned on Gemini) *degrades* both Claude models
  (Opus 63.73→57.98, recall 49.75→38.27; Sonnet 59.06→57.29) — "Claude appears to interpret the optimized rules
  too conservatively" (p. 142).

### Limitations (pp. 144) + reusable inference plumbing (Appendix B, p. 154)
- Single benchmark; API models opaque/non-deterministic (each config run once); UA-GEC train is public so few-shot
  exemplars may have been seen in pretraining (possible recall inflation); optimized prompts ~32× longer (cost/
  latency, amortized by prompt caching).
- **Structured-output pattern we can copy:** per-sentence, one LLM call, **document-marker lines `# <digits>`
  emitted verbatim (never sent to the model)**; LiteLLM router; response constrained by a **Pydantic→strict
  JSON-schema `response_format`** (`GECResponse.corrected_sentence`), `model_validate` on return, fallback to
  `{"type":"json_object"}` then single-field recovery — "every non-marker sentence yields exactly one validated
  correction," bijective and replayable from a run YAML.

### What we USE from this paper (reviewer-fixer prompts, harness)
1. **Port the 16-category taxonomy + STRICT minimal-edit rules verbatim-in-spirit into our reviewer/fixer
   prompts** — especially "smallest possible change · never substitute synonyms · preserve quote style · if in
   doubt do NOT change · return only corrected text." This is exactly the minimal-edit framing our fixer needs so
   it stops rewriting authorial voice.
2. **Hard-code the five UA over-correction prohibitions** as explicit "do NOT change" rules in our fixer: no
   en-dash normalization outside direct speech, no dialogue re-quoting, no synonym swaps, leave в/у & з/із/зі
   euphony alone, leave acceptable short-form/variant morphology alone. These are the top false-positive sources
   and each is cheap to suppress.
3. **Watch the low-frequency-category trap:** a very strict/conservative prompt zeroes out G/Prep, G/VerbVoice,
   G/Conjunction. If our fixer runs minimal-edit-strict, keep a *separate* pass (or a less-conservative reviewer
   dimension) for these so real errors aren't silently skipped.
4. **Model-routing evidence:** Claude wants UA prompts and resists aggressive optimization (stays conservative);
   Gemini/GPT respond to heavy optimized rule-lists. Matches our "route by model×harness fit" policy — our
   claude-tools writer/reviewer should get UA-native minimal-edit instructions, not an over-tuned rule dump.
5. **Adopt the Pydantic→strict-JSON-schema + marker-passthrough inference contract** for any sentence-level
   correction step in the harness (#4913) — deterministic, replayable, one-validated-output-per-sentence.

---

## 2026.unlp-1.17 — Mining Native Ukrainian Paraphrases: A Multi-Source Comparison — **FULL READ**
**Vladyslav Fesenko, Hanna Dydyk-Meush, Volodymyr Mudryi (Ukrainian Catholic University, Lviv).**
pp. 199–208 (UNLP 2026). {fesenko.pn, hanna_dydykmeush, mudryi.pn}@ucu.edu.ua.

### Release status — PUBLIC (exact URLs are hyperlinks, not printed)
- p. 203 (Data and Code Availability): "The implementation for data construction, fine-tuning, and evaluation is
  released at GitHub. The dataset and trained checkpoints are released through Hugging Face…" — **the raw
  GitHub/HF URLs are hyperlink anchor text ("GitHub", "dataset repository", "model repository") and are NOT
  rendered as plain text on the page I read, so I cannot transcribe them here.** Verify by opening the ACL
  Anthology PDF links. The upstream source IS printed (references, p. 205): the Ukrainian News corpus
  huggingface.co/datasets/zeusfsx/ukrainian-news (22.5M titles).

### Dataset construction + the constraint pipeline (the driver's ask, §3, p. 200)
- Corpus = event-aligned news headlines from **Ukrainian News (22.5M titles)**. Candidate pairs via a multilingual
  sentence-transformer (encoder checkpoint **paraphrase-multilingual-mpnet-base-v2**, Appendix A.1 p. 206) +
  approximate-NN index, restricted to **cosine similarity ≥ 0.5**.
- **Filtering thresholds (the reusable recipe):** drop near-duplicates with **Jaccard word-overlap > 0.8**; drop
  **cosine < 0.6** (too semantically divergent); drop **len_ratio < 0.67** (length mismatch); drop pairs with
  **inconsistent numeric values**; drop mirror duplicates, mixed-language, non-Cyrillic markup, and **pairs whose
  publication dates differ by > 3 days**. Retained band = cosine ∈ [0.6, high], Jaccard ≤ 0.8, len_ratio ≥ 0.67,
  numbers consistent, same event within 3 days. Retained/discarded worked examples in Appendix A.1.4 / A.1.5
  (pp. 206–207).

### Key quantitative results — the finding that matters for us
- **LLM paraphrases are "safe near-copies."** Human eval (professional linguist; meaning 0–2, lexical divergence
  0–2, fluency 0/1; §4.2, p. 201):
  - Table 2 (p. 201) aggregate: LLM-gen. Meaning 1.94 / **Lex.div 0.12** / Fluency 0.91 (n=141) — highest meaning,
    **lowest lexical change**; News pairs 1.48 / 0.36 / 0.94 (n=213); Translated 1.39 / 0.49 / 0.70 (n=144);
    Spivavtor 1.44 / 0.44 / 0.65 (n=152).
  - Table 3 (p. 201), strict subset (meaning ≥1 & fluency=1), lexical divergence: **News 0.259 > Translated 0.209 >
    Spivavtor 0.153 > LLM-generated 0.078.** Kruskal–Wallis all significant (p<10⁻⁶).
- Fine-tuning (§5, Table 4, p. 203): adapter-tuned mT5-large / mT0-large on ~16k mixed pairs; **iBScore =
  BERTScore_in − BLEU_in/100** (a copy-penalized quality metric). mT5-large best non-XXL (iBScore 0.2984 combined;
  0.2838 human-validated). Bottleneck is **fluency, not lexical variation** (manual 100-output check, p. 202).

### Limitations (§Limitations, p. 203)
- Only two ~1.2B backbones fine-tuned. **Dataset is news headlines only** — "short, compressed, strongly
  event-centered… models trained on this data may not transfer reliably to longer inputs or broader domains" and
  the pipeline assumes a 1:1 headline↔headline relation. Combined-corpus training only (no per-source models);
  no ≥10B-class fine-tune.

### What we USE from this paper (#4950 synonyms / practice distractors) — LESS than the abstract implies
1. **Honest scope finding:** this is a **meaning-PRESERVING** paraphrase resource in the **news domain**. Practice
   distractors need meaning-DIVERGENT, pedagogically-controlled options, and the dataset itself is the wrong
   domain/register for our learners. **So the dataset is not directly reusable as distractors.**
2. **The reusable parts are the METHOD, not the data:**
   - **Anti-copy metric:** adopt **iBScore = BERTScore − BLEU/100** (or the Jaccard/cosine gate) to reject
     generated "alternatives" that are trivial copies — directly useful for accept-multiple-phrasings and for any
     sentence-variation we generate.
   - **Hard evidence that naive LLM paraphrasing yields near-copies** (lex.div 0.078–0.12). If we ever LLM-generate
     alternative correct answers or paraphrase-style distractors, we MUST impose an explicit lexical-divergence
     floor (their Jaccard≤0.8 / cosine≥0.6 band) or we get near-duplicates.
   - The **filtering thresholds** (cosine≥0.6 semantic floor, Jaccard≤0.8 lexical-change floor, len_ratio≥0.67,
     numeric-consistency) are a clean recipe for corpus-intake dedup/quality gating too.
3. Not a corpus-intake source for curriculum content (news headlines, not textbook/literary material).

---

## 2025.unlp-1.2 — Benchmarking Multimodal Models for Ukrainian Language Understanding (ZNO-Vision) — **FULL READ**
**Yurii Paniv (UCU); Artur Kiulian, Mykola Khandoga, Anton Polishko, Guillermo Gabrielli (OpenBabylon);
Dmytro Chaplynskyi (lang-uk initiative); Tetiana Bas (Minerva University).** pp. 14–26 (UNLP 2025).
Compute: alliance of De Novo & MK-Consulting, ELEKS grant, AWS (H200) + GCP credits (Acknowledgments, p. 20).

### Release status — PUBLIC
- p. 14 (abstract end): "Code, evaluation scripts, and datasets are available at this link:
  **https://github.com/lang-uk/mmzno-benchmark**." Underlying ZNO items scraped from the Osvita portal
  (osvita.ua, §3 p. 15).

### Benchmark mechanics
- **ZNO-Vision: 4,306 question-pairs, 13 categories** (Math, Geography, Ukrainian language & literature, Teaching,
  History, Spanish/German/French/English, Chemistry, Physics, Biology, Other), from Ukraine's ZNO university-
  entrance / teacher-certification exam (§3, p. 15). Answers reduced to a single letter; multi-image / image-as-
  answer / choice-matching items filtered out.
- Split (Table 1, p. 15): **Dev 491 / Val 490 / Test 3,325**, 10/10/80 following MMMU. **54.16% of items are
  "visual-only"** = require OCR of the image to answer (2,332 / 4,306).
- **Text-only subset IS extractable** (the driver's ask). Per-category visual-only share (Table 2, p. 16): STEM is
  ~90%+ visual-only (Chemistry 92.65%, Math 93.91%, Physics 90.02%) while the humanities are **0% visual-only** —
  **Ukrainian language & literature 56 items (0% visual-only), History 434, Geography 374, Biology 332, English
  204, French 199, Teaching 134, Other 31, German 17 — all answerable from text alone.** So a text-only UA-language
  slice exists but is **small (56 Ukr-lang-&-lit items; ~1,974 non-visual items total across the whole set).**
- Two companion sets: **Multi30K-UK** caption generation (SacreBLEU + multilingual-BERT-cased BERTScore) and
  **UACUISINE** (20 Ukrainian dishes × 7 question types = 140 QA; EM / Intersection-Match / BERTScore).

### Scoring protocol vs ours (for zno_tasks) + which models cleared baseline
- Protocol (§3–4, pp. 16–17): image+question → single letter (Ukrainian letters, except EN/ES/DE/FR tests);
  **temperature 1, max 1024 output tokens**; letter extracted by rules (they dropped strict format instructions
  because "models struggled with specific format instructions"). **Baselines: always-first-choice = 22%; text-only
  (no image) ≈ 34%** — models scoring near text-only are treated as failing.
- Table 3 (p. 17) ZNO accuracy (Val / Test) — cleared baseline: **Claude-3.7-Sonnet 0.75 / 0.72 (best)**,
  Gemini-2.5-Pro 0.64 / 0.69, GPT-4o 0.62 / 0.63, **Qwen2.5-VL-7B 0.54 / 0.56 (best open source)**, Llama-4-Maverick
  0.53 / 0.53, Qwen2.5-VL-72B 0.51 / 0.52, Llama-4-Scout 0.48 / 0.49. At/below baseline (~0.31–0.40): Qwen2.5-VL-3B,
  Qwen2-VL-7B, Gemma-3-27B/12B-IT, Qwen2.5-VL-32B, Llama-3.2-90B-Vision, Pixtral-12B, Qwen2-VL-2B, Aya-Vision-8B.
- Humanities/STEM breakdowns in Appendix A (Tables 6–7, pp. 23–24): on the **Ukrainian language & literature**
  column, GPT-4o and Gemini-2.5-Pro both 83.33, Claude-3.7-Sonnet / Gemma-3-12B 66.67 (only 56 items — small n).

### Limitations (§7, p. 20) + a decolonization-relevant finding
- Single shared prompt prefix (bias); no CoT/reasoning models; proprietary models exceed the 1024-token cap; ZNO
  skewed toward STEM; Multi30K bilingual translation not tested.
- **Cultural misattribution (p. 19):** models mislabel UNESCO-recognized Ukrainian borsch as "Russian Red Borscht"
  and default recipes/answers to Russian or English even when prompted in Ukrainian — "systematic bias… that risk
  reinforcing narratives diminishing Ukrainian cultural identity."

### What we USE from this paper — mostly a VISION benchmark, limited direct use
1. **Honest finding: this is primarily a multimodal/OCR benchmark; its direct value to our text curriculum is
   narrow.** The text-only extractable UA slice is small (56 Ukr-lang-&-lit items). Useful only as a *supplementary*
   model-knowledge probe alongside ULP-347 (1.12), not a core eval.
2. **zno_tasks scoring reference:** their letter-extraction protocol + baseline definitions (first-choice 22%,
   text-only 34%, temp 1 / 1024 tokens, rule-based letter extraction, dropped-strict-format) are a concrete
   comparison point if our zno_tasks uses ZNO items — in particular, treat "beats text-only baseline" as the pass
   bar and prefer rule-based letter extraction over strict format demands.
3. **Model-selection + decolonization caution:** the Borsch/Russian-default misattribution is a documented failure
   mode — reinforces our need to VESUM/`sources`-verify cultural attributions and to prefer models (Claude-3.7-Sonnet
   led here) that handle Ukrainian cultural content, never trusting an ungated model for folk/culture facts.
4. Public dataset (github.com/lang-uk/mmzno-benchmark) if we ever add an image-based ZNO practice mode (backend/
   Atlas), but that is out of current scope.

---

## 2025.unlp-1.14 — On the Path to Make Ukrainian a High-Resource Language (Kobza + Modern-LiBERTa) — **FULL READ**
**Mykola Haltiuk & Aleksander Smywiński-Pohl (AGH University of Krakow).** pp. 120–130 (UNLP 2025).
Compute: PLGrid / ACK Cyfronet AGH (grant PLG/2024/017168); funded by the Polish Ministry of Science &
Higher Education (Acknowledgments, p. 128).

### Release status — PUBLIC (license not printed in-text)
- p. 121 (footnotes 1–3): Kobza corpus **https://huggingface.co/datasets/Goader/kobza**; Modern-LiBERTa model
  **https://huggingface.co/Goader/modern-liberta-large**; source **https://github.com/Goader/ukr-lm**. The paper
  body states availability but **prints no license string** — check the HF cards before redistributing.

### Kobza corpus mechanics (§3)
- **~60 billion tokens, ~97M documents, 474 GB Parquet/Snappy** — "the largest publicly available Ukrainian
  corpus to date" (§1, p. 120). Built by **merging curated corpora, not raw Common Crawl** (§3.1, p. 122).
- Table 1 (p. 123) sub-corpora (docs / tokens): CulturaX 24.94M / 15.00B · FineWeb 2 32.12M / 19.11B ·
  HPLT 2.0 26.24M / 20.71B · UberText 2.0 6.43M / 2.90B · Ukrainian News 7.18M / 1.85B →
  **Total 96.92M docs / 59.58B tokens.** Every doc keeps metadata (source, subsource, timestamp, URL).
- **Deduplication (§3.2, the driver's ask) — two stages:**
  1. **Metadata-based** (URLs + timestamps), validated by normalized-LCS similarity
     `sim(a,b)=LCS(a,b)/min(|a|,|b|)`; matched pairs averaged **92.9%** similarity → removes **~12%** of the corpus.
  2. **MinHashLSH** over **5-grams, Jaccard threshold 0.7** (text-dedup on Apache Spark) → removes an **additional
     ~33%** of documents.
- Data-quality caveat (§3.3, p. 123): component filters "were not always optimized for Ukrainian"; authors flag the
  need for a dedicated Ukrainian document-quality scorer (open problem; future work = expand Kobza to ≥100B tokens).

### Modern-LiBERTa mechanics (§4)
- **First Ukrainian long-context encoder — up to 8,192 tokens.** ModernBERT-Large architecture: **28 layers,
  hidden 1,024, 410M params**, RoPE + Flash-Attention + alternating attention (§4.2, p. 124). It is a **masked-LM
  ENCODER, not a generative model.**
- Training (§4.1–4.5, Table 2 p. 125): deduplicated Kobza (~60B) + English Wikipedia (~6B, ~10%, for NER/IR).
  LiBERTa-v2 tokenizer, 64k vocab. **Weights initialized from English ModernBERT-Large** via Trans-Tokenization
  (FastAlign, transtokenizers). Two phases: 1,024-len for 140B tokens, then context-extension to 8,192 for 20B
  tokens (mixture stratified across doc lengths to preserve short-input performance). MLM full-word masking 30%,
  StableAdamW, 16× GH200, effective batch 4,096; 133 h + 24 h.

### Key quantitative results
- **MLM perplexity / token-acc (Table 3, p. 127; all truncated to 512 for fairness) — Modern-LiBERTa beats
  LiBERTa-v2 everywhere:** UD 8.96 ppl / 58.82% (vs 15.51 / 52.81%); Spivavtor 18.01 / 48.42% (vs 54.07 / 37.00%);
  UA-GEC 22.22 / 44.71% (vs 76.00 / 33.77%); Wikipedia 4.28 / 69.03% (vs 8.77 / 59.87%).
- **NLU (Table 4, p. 127; 5-seed averages):** NER-UK micro-F1 91.66; NER-UK-2.0 84.17; **WikiANN 93.37 (best of all
  models)**; UD-POS 98.78; News-Class macro-F1 96.37. Competitive with LiBERTa-v2 / WECHSEL-RoBERTa; best on
  WikiANN (credited to English-Wikipedia background knowledge); trails best on NER-UK-2.0 by ~1.3pp.
- **Caveat the authors stress:** these NLU tasks are short-input, so they "do not take advantage of Modern-LiBERTa's
  extended context window of up to 8,192 tokens" (p. 126), and **no Ukrainian IR/retrieval benchmark exists**, so
  its retrieval quality is **unmeasured** in the paper.

### Limitations (§Limitations, pp. 127–128)
- Kobza inherits web biases (sensationalist-news over-representation, marginalized-voice under-representation,
  genre/register imbalance, some misinformation / spam / MT text); no Ukrainian quality scorer to filter it; these
  biases may propagate into Modern-LiBERTa.

### What we USE from this paper (retrieval backend phase · corpus intake)
1. **Modern-LiBERTa as a retrieval encoder/reranker — plausible base, NOT a drop-in.** It is the strongest
   available Ukrainian **long-context (8,192) encoder** and best-on-WikiANN (knowledge-dependent), so it is a
   sound base to **fine-tune into a dense bi-encoder / cross-encoder reranker** for our backend retrieval. But:
   (a) it is a masked-LM, so out-of-the-box it is NOT a sentence-embedding model — it needs contrastive/retrieval
   fine-tuning; (b) the paper provides **zero retrieval evaluation** (no UA IR benchmark), so its rerank quality is
   unproven. Verdict: promising encoder to fine-tune when we reach the retrieval phase, pending our own IR eval.
2. **Kobza is a background-LM corpus, not pedagogical material** — web/news/CC-derived with the documented biases;
   for our curriculum corpus we still want textbook/literary sources. Its main value to us is (a) a large UA corpus
   for any in-house encoder training, and (b) the **dedup recipe** we can reuse for corpus intake: metadata+LCS
   (sim = LCS/min-length, ~92.9% on matches) as a cheap first pass, then **MinHashLSH 5-grams @ Jaccard 0.7** for
   near-duplicates.
3. Shared-theme note across 1.14 + 1.17 + 1.11: **every one of these teams flags the absence of a Ukrainian
   document-quality scorer** — a concrete, high-leverage gap our curated corpus + reviewers partly already address,
   and a credible collaboration/outreach angle.

---

*(All six queued deep-reads above are complete with page-referenced numbers. Remaining
"later wave" papers in the ledger stay ABSTRACT until their own deep-read; do not cite
their details from memory.)*
