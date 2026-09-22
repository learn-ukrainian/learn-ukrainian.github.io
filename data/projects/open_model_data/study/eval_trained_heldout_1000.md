# ULDR Phase 5.1 Evaluation Audit Report
>
> **Evaluation Timestamp:** `2026-09-22T13:28:01.832774+00:00`
> **Overall Gate Verdict:** **❌ FAIL**
> **Total Evaluated Cases:** `1000` (`28` format-valid, `972` format-errors)

---

## 1. Quality Gate Scorecard

| Production Gate | Target Threshold | Measured Score | Status |
| :--- | :--- | :--- | :--- |
| **Gate 1: Calque Elimination Rate** | >= 90.0% | **0.00%** (0/400) | ❌ FAIL |
| **Gate 2: Harmful-Edit Rate** | <= 1.0% (Clopper-Pearson 95%) | **99.83%** (Upper bound: **99.99%**, N=600) | ❌ FAIL |
| **Gate 3: Span Integrity Gate** | 100% (0 mutations outside span) | **0.00%** (1000 violations) | ❌ FAIL |
| **Gate 4: Citation Whitelist Gate** | 0% foreign hallucinations | **30** violations (rate: 3.00%) | ❌ FAIL |
| **Gate 5: High-Frequency Calque Floor** | 100% on top 50 calques (50 distinct required) | **0.00%** (0/50 distinct covered, 0/18 total) | ❌ FAIL |

---

## 2. Gate Definitions & Statistical Criteria
* **Gate 1 (Calque Elimination):** Measures eradication of Russianisms and calques in final recommendations on held-out cases.
* **Gate 2 (Harmful Edits):** Exact one-sided 95% Clopper-Pearson binomial upper bound U = Beta^-1(0.95; k+1, n-k) <= 0.01 on >= 300 clean controls.
* **Gate 3 (Span Integrity):** Prevents collocation hallucinations (*побитися об заклад* -> *побитися об друга*). Tokens outside designated error spans must not be mutated.
* **Gate 4 (Citation Whitelist):** Rejects hallucinated foreign dictionaries (*COBUILD*, *LexicalLab*). Only approved authorities (ВЕСУМ, СУМ-20, Правопис 2019, Антоненко-Давидович, Грінченко, УЛІФ, UA-GEC) permitted.
* **Gate 5 (High-Frequency Calque Floor):** Requires 100% recall on the 50 most common Ukrainian calques (*приймати участь*, *на протязі*, *приймати міри*).
