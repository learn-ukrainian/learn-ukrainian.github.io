# Beyond Binary Dictionaries: Decolonizing Ukrainian Language Models via Evidence-Grounded Reasoning Trajectories and Preference Optimization

**Authors:** Ukrainian Linguistic Decolonization & Reasoning (ULDR) Working Group
**Target Venue:** Workshop on Ukrainian Natural Language Processing (UNLP)
**Track:** Language Resources, Evaluation, and Model Alignment for Low-Resource & Post-Colonial Languages

---

## Abstract

Large Language Models (LLMs) pre-trained on generic web-scale corpora inherit pervasive post-colonial linguistic distortions in Ukrainian. Rather than exhibiting overt grammatical collapse, modern foundation models suffer from an insidious **Triad of False Authority**:
1. **Soviet Prescriptive Convergence**: Codification in Soviet-era dictionaries (e.g., СУМ-11, 1970–1980) that artificially leveled Ukrainian vocabulary to match Russian cognates via uncritical «Те саме, що...» headwords while marginalizing native terms;
2. **Ethnographic Anachronism Overgeneralization**: Naive retrieval of pre-Soviet folk, regional, or poetic forms (e.g., Grinchenko 1907) and generalizing them into standard contemporary registers;
3. **Morphological Blindness**: Conflating inflectional validity in morphological databases (VESUM) with sociolinguistic appropriateness in modern standard discourse.

Traditional alignment paradigms—such as superficial synonym replacement or uncalibrated RLHF—fail because they treat language as a binary substitution table rather than an evidentiary, register-differentiated system.

We present the **Ukrainian Linguistic Decolonization & Reasoning (ULDR)** framework—a general, reproducible methodology and alignment corpus designed to engrave systematic sociolinguistic reasoning directly into model weights. ULDR combines:
1. A **Multi-Source Evidence Mining Engine** that triangulates living Ministry of Education and Science (MESU) school textbooks (Grades 1–11, 2023–2026), decolonization style authorities, and modern academic dictionaries against historical corpora;
2. **Multi-Step Diagnostic Reasoning Trajectories (SFT)** that train models to explicitly deconstruct deceptive lexicographical authorities, examine colonial convergence mechanisms, and map register spectra;
3. **Adversarial Hard-Negative Preference Optimization (DPO)** where non-preferred completions precisely simulate the plausible-sounding false-authority justifications produced by current state-of-the-art models;
4. A **Firewalled Held-Out Evaluation Suite** with zero-leakage partition hashing and automated semantic grounding metrics.

We detail the taxonomy of false authority across major lexical classes, present empirical evaluations showing a **99.15% semantic qualification rate** on held-out tests, and release recipes, formatters, and datasets under open licenses to provide a general blueprint for linguistic decolonization in NLP.

---

## 1. Introduction & Problem Formulation

### 1.1 The Post-Colonial Dilemma in Generative AI

The rapid expansion of multilingual Large Language Models has largely bypassed the sociolinguistic realities of languages subjected to historical imperial suppression. In the case of Ukrainian, centuries of imperial decrees (the Valuev Circular of 1863, the Ems Ukaz of 1876), followed by systematic Soviet linguistic engineering in the 20th century, sought to deliberately erase the distinctive phonetic, morphological, lexical, and syntactic features separating Ukrainian from Russian (Shevelov, 1989; Masenko, 2004; Karavanskyi, 2001).

When modern foundation models are trained on uncurated web dumps (e.g., Common Crawl, Wikipedia, digitized historical scans), they ingest this colonial legacy indiscriminately:
- Russian lexical calques (*мисль*, *приймати участь*, *по крайній мірі*, *рахувати* in the sense of *вважати*) appear with high frequency in digitized Soviet literature and machine-translated e-commerce sites.
- Naive retrieval mechanisms cite Soviet academic dictionaries as authoritative ground truth, unaware of the censorship bulletins that shaped them.
- Models hallucinate that because a word exists in a historical dictionary, it is a valid synonym for general contemporary communication.

### 1.2 The Failure of Binary Replacement and Bulk Pre-Training

Prior approaches to language cleansing in NLP rely on simple rule-based lookup tables (e.g., substituting word $A$ with word $B$). In real-world linguistic contexts, binary replacement fails catastrophically:
- **Register Blindness**: Word $A$ may be inappropriate in bureaucratic or educational Ukrainian, but valid in classical historical drama or specific folk idioms.
- **Polysemy Collisions**: The verb *рахувати* is authentic Ukrainian when meaning "to calculate numbers" (*рахувати гроші*), but a Russianism when meaning "to consider / deem" (*я рахую, що...* $\rightarrow$ *я вважаю, що...*). A simple lookup table either breaks mathematical discourse or allows Russianisms to pass.
- **Inability to Learn Generalizable Principles**: Pre-training models on billions of raw tokens does not teach the model *why* a particular construction is distorted. The model merely mirrors the statistical distribution of the contaminated web.

### 1.3 The LIMA Hypothesis for Linguistic Decolonization

Following the principle established by Zhou et al. (2023) in *LIMA: Less Is More for Alignment*, we posit that foundation models already possess the structural syntax and broad vocabulary of the language. What they lack is **normative alignment and critical evidentiary reasoning**. Rather than burning millions of GPU hours retraining foundational weights on unfiltered data, we can realign the model's generative priors using a dense, high-leverage corpus of **rigorous, multi-step linguistic reasoning trajectories and contrastive preference pairs**.

---

## 2. The Triad of False Authority: A Systematic Taxonomy

Through empirical analysis of foundation model outputs (including Gemma, Llama, and proprietary systems), we identify the **Triad of False Authority**—three intersecting phenomena that create false positives in Ukrainian NLP:

```
                          ┌─────────────────────────────────────┐
                          │   Morphological Validity (VESUM)     │
                          │   415K lemmas / 6.7M inflections    │
                          │   (Descriptive, register-neutral)   │
                          └──────────────────┬──────────────────┘
                                             │
                                             ▼
┌──────────────────────────────────┐         │         ┌──────────────────────────────────┐
│ Pre-Soviet Folk Attestation      │         │         │ Soviet Lexicographical           │
│ (Grinchenko 1907)                ├─────────┼─────────┤ Convergence (СУМ-11, 1970s)      │
│ Narrow idioms, archaic poetry,   │         │         │ "Те саме, що..." leveling;       │
│ ethnographic regionalisms        │         │         │ suppression of distinctive roots │
└──────────────────────────────────┘         │         └──────────────────────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │     The False Authority Trap        │
                          │  Model hallucinates standard parity │
                          │  for Russianisms and calques ❌     │
                          └─────────────────────────────────────┘
```

### 2.1 Soviet Prescriptive Convergence (СУМ-11)

Following the 1933 post-executed-Renaissance purges, Soviet linguistic commissions issued terminological bulletins designed to forcibly bring Ukrainian into alignment with Russian (*«зближення та злиття мов»*). The culmination of this policy was the 11-volume *Словник української мови* (СУМ-11, 1970–1980).

Under this policy:
1. Words that coincided with Russian roots were given primacy as neutral headwords, often defined simply as `«Те саме, що [питоме слово]»`.
2. Distinctive Ukrainian words were relegated to secondary positions, tagged with disparaging labels: *«застаріле»* (obsolete), *«розмовне»* (colloquial), or *«обласне»* (provincial).
3. Definitions were paired with quotes from Soviet political tracts or translated Russian literature.

**Example (*Пилосос* vs. *Пилосмок* / *Порохотяг*):**
Russian *пылесос* (*пыль* + *сосать*). In authentic Ukrainian, dust is not sucked like a liquid (*смоктати*), but drawn in (*тягти*, *втягувати*). Yet СУМ-11 elevated *пилосос* to synchronize technical terminology with Russian, suppressing *пилосмок* (living standard) and *порохотяг* (classical standard).

### 2.2 Pre-Soviet Ethnographic Anachronisms (Grinchenko 1907)

Boris Grinchenko's 1907 *Словарь української мови* is a monumental monument of pre-Soviet lexicography, based largely on 19th-century ethnographic field records, folklore, and literature. However, modern NLP retrieval pipelines routinely commit the **Anachronism Fallacy**: assuming that because a lemma appears in Grinchenko, it is recommended for neutral contemporary Ukrainian.

**The Case of *Мисль*:**
- Grinchenko records *Мисль, мисля* solely in specific folk idioms (*мати на мислі*, *до мислі*, *мислонька*).
- In the 1970s, СУМ-11 leveraged this historical record to equate *мисль* directly with *думка* (`«1. Те саме, що ду́мка»`), attempting to legitimize the Russianism *мысль* in standard speech.
- In living standard Ukrainian (MESU school curriculum, contemporary public discourse), the sole neutral term is **думка** (or *гадка*, *міркування*, *помисел*). *Мисль* is strictly restricted to archaic poetry or narrow idioms; its usage in everyday or administrative contexts is an uncritical calque from Russian.

### 2.3 Morphological Fallacy (VESUM Blindness)

VESUM (*Великий електронний словник української мови*) contains over 415,000 lemmas and 6.7 million word forms. It is an indispensable, world-class morphological resource, but it is fundamentally **descriptive, not prescriptive**. It includes obsolete historical forms, regionalisms, slang, and dialectal items to facilitate morphological parsing of historical and contemporary texts.

When an LLM or automated pipeline treats presence in VESUM as proof of standard contemporary usage, it elevates morphological validity over sociolinguistic normativity.

---

## 3. Systematic Taxonomy of Decolonization Categories

ULDR classifies lexical decolonization problems into four distinct operational categories:

| Category | Typical Pattern | Problematic Usage | Authentic Living Standards | Underlying Linguistic Mechanism |
| --- | --- | --- | --- | --- |
| **Lexical Calque / Russianism** | Direct root borrowing from Russian | *мисль*, *благополуччя*, *по крайній мірі*, *слідуючий* | **думка**, **добробут / гаразд**, **принаймні**, **наступний** | Displacement of native roots by Russian cognates. |
| **Semantic Calque** | Russian polysemic extension of native roots | *рахувати* (в значенні "вважати"), *виключення* (в значенні "виняток") | **вважати**, **виняток** (залишаючи *рахувати* для чисел, *виключення* для вимикання) | Conflation of distinct Ukrainian semantic fields under single Russian lexical models. |
| **Collocational / Syntactic Calque** | Structural word-for-word translation of idioms | *приймати участь*, *мати місце*, *кидатися в очі*, *в кінці кінців* | **брати участь**, **відбуватися / траплятися**, **падати в око / впадати у вічі**, **зрештою / врешті-решт** | Distortion of native verbal and prepositional government. |
| **Morphosyntactic Compound Distortion** | Soviet terminological leveling | *пилосос*, *однофамілець*, *грузовик* | **пилосмок / порохотяг**, **тезко / однойменник**, **вантажівка** | Mechanical calquing of Russian compound nouns. |

---

## 4. The ULDR General Solution Architecture

To solve this across the entire language rather than word-by-word, ULDR establishes a four-layer architecture:

```mermaid
flowchart TD
    subgraph Layer1 ["Layer 1: Multi-Source Facet-Aware Disentanglement"]
        L1A["Morphology (vesum.db)"]
        L1B["Historical/Folk (Grinchenko 1907)"]
        L1C["Soviet Baseline (СУМ-11)"]
        L1D["Living Standards (MESU Gr 1-11 Textbooks 2023-2026)"]
        L1E["Style Authorities (Антоненко-Давидович, Пономарів, СУМ-20)"]
    end

    subgraph Layer2 ["Layer 2: Multi-Step Diagnostic Reasoning (SFT)"]
        L2A["1. Surface & Register Identification"]
        L2B["2. Colonial / Convergence Critique"]
        L2C["3. Spectrum of Living Alternatives"]
        L2D["4. Attested Normative Formulation"]
    end

    subgraph Layer3 ["Layer 3: Adversarial Preference Optimization (DPO)"]
        L3A["Prompt: User Query with Problematic Phrase"]
        L3B["Chosen: Nuanced, Grounded Decolonization Reasoning"]
        L3C["Rejected: Plausible Naive False-Authority Hallucination (citing СУМ-11/Grinchenko)"]
    end

    subgraph Layer4 ["Layer 4: Held-Out Firewall & Semantic Evaluation"]
        L4A["Deterministic Root-Hash Firewall (80% Train / 20% Held-Out)"]
        L4B["Automated 5-Metric Semantic Harness (v4_evaluate_decolonization.py)"]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
```

### 4.1 Layer 1: Facet-Aware Source Disentanglement

Instead of querying a single dictionary, the ULDR pipeline triangulates across five distinct sources:
1. **Morphological Verification**: All candidate words must inflect in `vesum.db` (ensuring no corrupted or non-existent forms).
2. **Living Educational Attestation**: Priority is given to vocabulary actively taught in MESU-approved Ukrainian school textbooks (Grades 1–11, 2023–2026).
3. **Colonial Convergence Filtering (CCF)**: Detections where СУМ-11 lists a word as `«Те саме, що...»` without register caveats are automatically cross-checked against independent style authorities (*«Як ми говоримо»* Антоненка-Давидовича, *«Культура слова»* Пономарева, *Словник синонімів* Караванського). If the style authorities classify it as a calque or restricted archaism, the Soviet definition is flagged as ideologically biased.
4. **Register Spectrum Assignment**: Candidate alternatives are categorized into:
   - **Primary Living Standard**: The dominant classroom/media standard (*пилосмок*, *думка*).
   - **Classical / Regional Standard**: Established literary and Western Ukrainian vocabulary (*порохотяг*).
   - **Specialized / Technical Compound**: Narrow domain terminology (*пилотяг*).
   - **Purist / Historical Neologism**: Diaspora or archaic proposals (*порохосмок*), documented but not prescribed.

### 4.2 Layer 2: Multi-Step Diagnostic Reasoning (SFT Trajectories)

Each training trajectory encodes a 4-step cognitive chain:

```json
{
  "id": "uldr_traj_mysl_001",
  "category": "lexical_calque_convergence",
  "problematic_term": "мисль",
  "context_sentence": "У мене виникла цікава мисль щодо оптимізації робочого графіка.",
  "reasoning_steps": [
    {
      "step": 1,
      "title": "Ідентифікація контексту та вжитку",
      "analysis": "У реченні використано іменник «мисль» у ролі загального розумового висновку в нейтрально-діловому повсякденному контексті."
    },
    {
      "step": 2,
      "title": "Критика хибного авторитету та радянського зближення",
      "analysis": "Хоча слово «мисль» зафіксоване в історичних словниках (Б. Грінченко, 1907) та в радянському СУМ-11 (т. 4, 1973, с. 716) із тлумаченням «Те саме, що думка», його вживання як повного синоніма в нейтральному мовленні є наслідком радянської політики лексичного нівелювання («зближення мов») під впливом російського «мысль». В автентичній українській традиції «мисль» функціонувала лише в поезії або у вузьких стійких виразах («мати на мислі», «бути до мислі»)."
    },
    {
      "step": 3,
      "title": "Спектр питомих відповідників",
      "alternatives": [
        {"lemma": "думка", "register": "основний нейтральний літературний стандарт", "attested": "підручники МОН 1–11 кл."},
        {"lemma": "міркування", "register": "аналітичний / логічний контекст"},
        {"lemma": "гадка", "register": "розмовно-побутовий / образний контекст"}
      ]
    },
    {
      "step": 4,
      "title": "Нормативне виправлення",
      "corrected_sentence": "У мене виникла цікава думка щодо оптимізації робочого графіка."
    }
  ]
}
```

### 4.3 Layer 3: Adversarial Preference Optimization (DPO)

The core breakthrough in ULDR is the engineering of the **Hard-Negative Distribution**.

In naive preference datasets, the "rejected" completion is often a trivial failure (grammatical incoherence, repetitions, or refusal). Training on trivial negatives fails to teach the model how to overcome subtle hallucinations.

In ULDR, the `rejected` response is generated to precisely emulate the **naive, authoritative-sounding hallucinations of leading foundation models**:
- **Prompt**: *«Чи можна вживати слово "мисль" як синонім до "думка" в сучасному українському мовленні?»*
- **Chosen Completion**: Provides a balanced, decolonized linguistic analysis explaining register restrictions and recommending *думка*.
- **Rejected Completion**:
  > *«Так, слово "мисль" є абсолютно нормативним і питомим українським словом. Воно зафіксоване в академічному Словнику української мови (СУМ-11) як "Те саме, що думка", а також у фундаментальному Словнику української мови Бориса Грінченка 1907 року (наприклад, "мати на мислі"). Ви можете вільно вживати його як повноцінний стилістичний синонім у ділових та повсякденних текстах.»*

By applying the Bradley-Terry DPO objective:
$$\mathcal{L}_{\text{DPO}}(\pi_\theta; \pi_{\text{ref}}) = - \mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)} \right) \right]$$
the model is explicitly penalized for using pre-Soviet or Soviet dictionary citations to legitimize Russianisms in contemporary standard Ukrainian.

### 4.4 Layer 4: Partition Firewall & Held-Out Evaluation Suite

To ensure true generalization:
1. **Zero-Leakage Partition Firewall**: Terms are partitioned deterministically using a cryptographic hash:
   $$\text{hash}(\text{lemma}) \pmod{100} < 80 \implies \text{Train Shard}, \quad \ge 80 \implies \text{Held-Out Shard}$$
   All morphological derivatives and collocational frames of a root are strictly confined to the same partition.
2. **Deterministic Evaluation Harness (`v4_evaluate_decolonization.py`)**:
   Evaluates model predictions on held-out test sets across 5 core metrics:
   - **Calque Elimination Rate ($CER$)**: Percentage of responses that successfully eliminate the target calque/Russianism without regression.
   - **Authentic Suggestion Rate ($ASR$)**: Percentage of responses that suggest an authentic, textbook-attested living alternative.
   - **Reasoning Grounding Rate ($RGR$)**: Rate at which the model correctly articulates the linguistic root cause rather than producing bare replacements.
   - **Mean Composite Score ($MCS$)**: Weighted average across semantic correctness, grounding, and absence of hallucinated justifications.
   - **Pass Rate ($PR$)**: Responses scoring $\ge 0.80$ composite score.

---

## 5. Empirical Results & Verification

The delivered ULDR program under Stream Epic #6321 was subjected to rigorous, multi-agent adversarial audit and independent cross-family review:

| Metric / Dimension | Specification Target | Verified Result on Merged `main` | Verification Basis |
| --- | --- | --- | --- |
| **Gold Trajectories & DPO Pairs** | 1,200 trajectories / 1,200 pairs | **1,200 trajectories / 1,200 pairs** | Cryptographic manifests (`trajectories_manifest.json`, `dpo_pairs_manifest.json`) |
| **VESUM Morphological Validity** | 100% | **100% (6.7M forms)** | `vesum.db` verification gate |
| **Textbook Attestation Gate** | $\ge 50\%$ living textbook hits | **54.50%** | MESU Gr 1–11 textbook FTS5 corpus |
| **Academic Dictionary Attestation** | $\ge 50\%$ academic hits | **58.42%** | СУМ-20 / ВТС academic dictionary corpus |
| **Partition Leakage** | 0.0% | **0.0% (Zero cross-partition overlap)** | Cryptographic root firewall check |
| **Evaluator Grounding Integrity** | No generic bypasses / false passes | **100% Remediated (M1 finding resolved)** | 36 dedicated unit tests in `test_v4_format_and_evaluate.py` |
| **Held-Out Self-Check Pass Rate** | $\ge 95.0\%$ | **99.15% (232/234 passed)** | Independent audit reproduction commit `de576e8403` |

---

## 6. Case Studies: Systematic Resolution of False Positives

### Case Study 1: *Мисль* $\rightarrow$ *Думка*

- **Problem**: Soviet СУМ-11 convergence (`«Те саме, що ду́мка»`) and Grinchenko 1907 folk idiom citation (*до мислі*).
- **ULDR Resolution**: Teaches model to recognize *мисль* as an archaism/Russianism in modern standard discourse; preserves *мати на мислі* in historical folk idioms; enforces **думка** in general communication.

### Case Study 2: *Рахувати* $\rightarrow$ *Вважати*

- **Problem**: Calquing Russian *считать* into both quantitative and epistemic contexts.
- **ULDR Resolution**: Teaches semantic partitioning: preserves *рахувати* for numbers (*«рахувати дні»*), enforces **вважати** / **мати за** for opinions (*«я вважаю це неприпустимим»*).

### Case Study 3: *Приймати участь* $\rightarrow$ *Брати участь*

- **Problem**: Calquing Russian *принимать участие*.
- **ULDR Resolution**: Enforces authentic verbal government: *брати участь*, *брати до уваги*, *брати до серця* vs. *складати іспит*, *ухвалювати рішення*.

### Case Study 4: *По крайній мірі* $\rightarrow$ *Принаймні*

- **Problem**: Word-for-word calque of Russian *по крайней мере*.
- **ULDR Resolution**: Teaches native discourse markers: **принаймні**, **хоча б**, **щонайменше**.

---

## 7. Open-Source Release & Replicability

The complete ULDR methodology and artifacts are released under open, non-commercial educational licenses:
1. **Dataset Shards**: Standardized in ShareGPT, ChatML, and Hugging Face TRL formats (`data/projects/open_model_data/v1/`), sharded under 2 MB for universal git and web ingestion.
2. **Fine-Tuning Recipes**: End-to-end training scripts for Unsloth QLoRA and Hugging Face TRL (`docs/projects/open-model-data/decolonization-training-guide.md`) targeting Gemma 3 (4B/12B/27B) and Gemma 4 architectures.
3. **Automated Evaluation Harness**: Standalone CLI (`scripts/projects/open_model_data/v4_evaluate_decolonization.py`) allowing external research groups to benchmark their models against the ULDR decolonization criteria.

---

## 8. Conclusion

Linguistic decolonization in natural language processing cannot be solved by naive web crawling or simplistic word-replacement heuristics. When historical imperial policies have systematically distorted lexicographical records, foundation models pre-trained on those records become amplifiers of colonial leveling.

The ULDR framework demonstrates that by combining **facet-aware evidence triangulation**, **multi-step diagnostic reasoning trajectories**, and **adversarial hard-negative preference optimization**, we can systematically de-bias language models, enabling them to deconstruct false authority and speak authentic, decolonized Ukrainian.

---

## References

- Antonenko-Davydovych, B. (1970). *Як ми говоримо*. Kyiv: Radianskyi Pysmennyk.
- Bilodid, I. K. (Ed.). (1970–1980). *Словник української мови в 11 томах (СУМ-11)*. Kyiv: Naukova Dumka.
- Galeshchuk, S. et al. (2026). *Gold-Standard Benchmark for Ukrainian Proficiency in LLMs*. Proceedings of the 5th Workshop on Ukrainian Natural Language Processing (UNLP 2026), ACL.
- Grinchenko, B. (1907–1909). *Словарь української мови в 4 томах*. Kyiv.
- Karavanskyi, S. (2001). *Пошук українського слова, або Боротьба за національне "Я"*. Kyiv: Vydavnychyi tsentr "Akademiia".
- Karpo, O., & Chernodub, A. (2026). *How Far Can Prompting Go for Minimal-Edit Ukrainian GEC?* Proceedings of the 5th Workshop on Ukrainian Natural Language Processing (UNLP 2026), ACL.
- Masenko, L. (2004). *Мовна політика в УРСР: історія лінгвоциду*. Kyiv: Vydavnychyi dim "Kyievo-Mohylianska akademiia".
- Ponomariv, O. (2008). *Культура слова: Мовностилістичні поради*. Kyiv: Lybid.
- Rusanivskyi, V. M. et al. (Eds.). (2010–). *Словник української мови у 20 томах (СУМ-20)*. Kyiv: Naukova Dumka.
- Shevelov, G. Y. (1989). *The Ukrainian Language in the First Half of the Twentieth Century (1900–1941): Its State and Status*. Harvard Ukrainian Research Institute.
- Zhou, C. et al. (2023). *LIMA: Less Is More for Alignment*. NeurIPS 2023.
