# UK-writing bakeoff — which agent authors our curriculum content? (2026-07-04)

**Question (user):** gpt-5.5 is the current author and tends to go solo. We need
data to delegate Ukrainian *content authoring* (we AUTHOR, we do NOT translate)
across three routing profiles:

1. **A2, English-support immersion** — Ukrainian teaching voice, English only as vocab glosses.
2. **B1–C2, pure immersion** — full-immersion Ukrainian, zero English.
3. **Seminar** — culture content (folk topic), decolonized framing, factually careful.

Same brief to every candidate (`.agent/tmp/probe-uk-writing-brief.md`); one output,
three `## SECTION N` blocks. Candidates: **codex (gpt-5.5)**, **agy (gemini-3.1-pro)**,
**claude**, **deepseek-v4-pro**, **cursor (auto)**. (pool/glm excluded — code models.)

## Method — deterministic backbone + observable qualitative

Deterministic scorer `scripts/audit/probe_uk_writing_score.py` (reuses the existing
QG infra — no LLM): VESUM-valid token %, russicism rate (VESUM-gated pymorphy3
russian-shadow **minus** Grinchenko/ESUM heritage attestation), VESUM-unknown rate,
non-canonical apostrophe count, and English/immersion discipline vs the per-level
`content_surface_gates` policy (A1 scaffolding → A2 warn 0.45 → B1+ warn 0.08/fail
0.18 → seminar warn 0.05/fail 0.12).

> ⚠️ **Two scorer bugs caught + fixed during the run (or the ranking would have been WRONG):**
> 1. **Apostrophe variant.** cursor emitted the typographic apostrophe (U+2019 ’) 13×;
>    VESUM indexes the ASCII apostrophe (U+0027). `з'являються`/`кав'ярню`/`пам'ятники`
>    with U+2019 miss VESUM → got **false-flagged as russicisms** (cursor showed a fake
>    "5 russicisms" on B2 + seminar). Fixed: normalize apostrophes before every check;
>    report the non-canonical count separately (it is a real normalization need, not a defect).
> 2. **Junk tokens.** `---` (markdown rule) and `ххі` (ХХІ, a Cyrillic-homoglyph Roman
>    numeral) were false-flagged. Fixed: require a Cyrillic vowel.
> After both fixes: **0 real russicisms for every candidate on these topics.**

## Deterministic scorecard (apostrophe-normalized, junk-filtered)

| candidate | A2 support | B1–C2 pure | seminar | non-canonical apostrophes |
|---|---|---|---|---|
| **codex (gpt-5.5)** | 97.8% · 0 rus | 100% · 0 | 100% · 0 | 0 |
| **agy** | 100% · 0 | 100% · 0 | 99.2% · 0 | 0 |
| **claude** | 100% · 0 | 97.6% · 0 | 100% · 0 | 0 |
| **deepseek** | 98.5% · 0 | 99.2% · 0 | 98.3% · 0¹ | 0 |
| **cursor** | 95% · 0 | 99.2% · 0 | 100% · 0 | **13** |

(% = VESUM-valid content tokens · rus = real russicisms. ¹deepseek's single flag was
ХХІ, the Roman numeral — a false positive.) All five wrote **russicism-free, 95–100%
VESUM-valid** Ukrainian across all three profiles, all within the immersion policy
(A2 English confined to glosses; B2/seminar ~zero English).

## Observable qualitative (from the text — low-subjectivity facts)

- **Immersion-rule adherence (A2):** **agy** opens with a Ukrainian teaching voice
  («Сьогодні ми йдемо в кав'ярню. Спочатку вивчимо нові слова») — the cleanest immersion.
  codex clean. claude/deepseek carry a minor meta-label header. **cursor leaked the
  English task label** («A2, English-support immersion (topic:… / at the café)») into
  both S1 and S3 — an instruction-following slip.
- **Seminar — a caution, not a ranking:** all avoided Soviet framing (decolonized ✓) and
  were russicism-clean. deepseek *sounded* most scholarly (typology власне веснянки/гаївки/
  **царинні пісні** + archaic-melos detail); agy richest regional detail. **BUT "sounds
  scholarly" ≠ "is accurate"** — for factual seminar content that instinct is backwards
  (confident specificity can be confident fabrication). A manual fact-check of deepseek's
  specifics vs the Енциклопедія українознавства + Wikipedia found them **grounded** (царинні
  is a real subtype; narrow-scale melody confirmed) with **2 minor imprecisions** ("до Зелених
  свят" should be ~Купала; the царинні gloss slightly conflates field-boundary songs with the
  cattle-drive). The scorer never did this check — so it CANNOT rank seminar quality.
- **Length:** all adequate (S2/S3 160–191 UK words); codex slightly short on the seminar.

## Ranking (per profile) — and the answer to "can gpt-5.5 delegate?"

**YES.** gpt-5.5 is genuinely strong, but **not uniquely so — agy, claude, and deepseek
match or beat it** on clean, russicism-free, immersion-correct UK content. Delegate:

| Profile | Recommended lanes (in order) |
|---|---|
| **A1–A2 English-support** | **agy** (best immersion teaching-voice) ≈ **codex** > deepseek > claude |
| **B1–C2 pure immersion** | **codex ≈ agy ≈ claude** (all ~100% clean) > deepseek |
| **Seminars (culture)** | **NOT probe-rankable.** All 5 wrote clean, decolonized, immersion-correct prose — but the scorer does NOT measure factual accuracy, the thing that matters most for folk/hist/bio. Rank seminar authors with the seminar review process (`plan-review-seminar` + Wikipedia/literary RAG fact-check + decolonization rubric), not this bakeoff. |
| any UK content via **cursor** | usable, but keep a **VESUM + apostrophe-normalization gate** — it emits non-canonical apostrophes and had a text-dependent russicism («перекатні») on harder text elsewhere |

## Honest caveats

- **Self-judgment:** claude (this reviewer's family) is a candidate. Its *deterministic*
  numbers are unbiased (tool-backed, top-tier); the qualitative notes are observable facts.
  A **blind cross-family panel** would add subjective-quality resolution within the clean
  top tier — not run here (all fleet writers are candidates).
- **Topic-dependence:** the clean russicism result is for these three topics. cursor's
  earlier «перекатні» shows russicism risk is text-dependent — keep the VESUM gate on any
  writer for long/hard UK content.
- **Reproduce:** `python -m scripts.audit.probe_uk_writing_score <output.md>` (needs
  data/vesum.db + data/sources.db). Samples: `.agent/tmp/probe-out/*.md` (gitignored).
