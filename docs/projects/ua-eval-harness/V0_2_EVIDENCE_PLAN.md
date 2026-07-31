# v0.2 evidence plan

v0.1.1 has 677 held-out items and two comparable frozen real-model runs:
GPT-5.6 Terra and Gemma 4 31B IT. It is not evidence for a general claim about
the “best Ukrainian model”. Gemini qualification artifacts used different tasks,
prompts, criteria, and product paths, so they are excluded from comparisons.

## Frozen evidence

The deterministic analysis has 181 GPT measurement wins, 147 Gemma measurement
wins, and 349 exact-measurement ties. These are exact source-span/replacement
measurements, not linguistic verdicts. GPT has 144 TP / 319 FP / 956 FN
(F0.5 0.2439); Gemma has 114 TP / 351 FP / 974 FN (F0.5 0.1934). Both leave
many items unchanged (310 and 341) and under-edit (572 and 595).

Twelve items have a possible ambiguity/benchmark-defect signal; three have a
protected heritage/dialect/register signal. Fourteen require Ukrainian review.
Dictionary/VESUM markers are supporting evidence only, not contextual
adjudication. Exact mismatch is likewise not a linguistic error. No matched
prompt-variation evidence exists, so prompt sensitivity is uninterpretable.

## v0.2 category map and coverage targets

Targets are per-stratum evidence minima, not a symbolic total row count.
For ordinary reported rates, a stratum must have at least 50 reviewed items:
at the worst-case proportion of 0.5, that gives an approximate two-sided 95%
Wilson half-width below 14 percentage points. Safety strata use at least 30
items; if a baseline produces zero unwanted normalizations, the rule-of-three
upper 95% bound is then below 10%. More items are required whenever the
observed Wilson interval misses those precision limits.

The frozen gap receipt reports 0 clean controls, 557 grammar items, 194 calque
items, 0 hard positives, 14 contested/protected review seeds, and 241
multi-reference items. Raw presence is not reviewed category coverage:
v0.1.1 has no clean or must-not-normalize contract, its calques lack the
planned subtypes, and its multi-reference rows are not balanced by protection
family.

| Category | Frozen v0.1.1 evidence | v0.2 minimum and derivation |
| --- | --- | --- |
| Clean no-change controls | 0 | 120: 30 each in four source/register strata; zero failures would bound each stratum below 10% by the rule of three. |
| Core grammar/agreement | 557 total, but tag support ranges from 1 to 193 | At least 50 reviewed items per reported grammar tag. Current deficits include Aspect +35, Comparison +44, Conjunction +5, Gender +3, Other +37, PartVoice +39, Participle +49, Particle +46, Tense +1, VerbAForm +41, and VerbVoice +12. |
| Calque/lexical choice | 194 without the planned subtype labels | At least 50 each for semantic transfer, collocation/government, bureaucratic/translation-like phrasing, and clear lexical choice: at least 200 subtype-reviewed examples. |
| Hard positives that must not normalize | 0; the 3 protected-risk rows are ambiguity seeds, not positives | 30 each for heritage, regional, dialectal, conversational register, archaic/rare, and slang/marked use: 180 reviewed positives. |
| Cognates/contested cases | 14 review seeds | 50 authentic-cognate and 50 contested examples: 100 reviewed cases, seeded by all 14 current rows. |
| Multi-reference items | 241, not balanced by category | At least 50 within each of grammar, calque, and protected/contested families: 150 category-attributed items; rows may overlap other minima. |

Category overlap is allowed. Every protected or contested item needs qualified
Ukrainian review and separate reporting. Seed review with every v0.1.1
`needs_ua_review` row; do not silently relabel such rows as model or gold
errors.

## Data and contamination controls

Keep development material renewable and held-out material sequestered. Release
only source-only requests to a runner; retain the exact prompt and decoding
receipt; never send references, edits, dispositions, or review notes during
generation. Freeze split IDs and hashes before a baseline; rotate the held-out
split before publishing examples that expose a current held-out row. Report
source provenance, reference count, protection flag, uncertainty, and review
state per item.

## Stop conditions

Do not admit v0.2 until every named stratum reaches its minimum; every reported
ordinary-rate stratum has a two-sided 95% Wilson half-width at or below 14
percentage points; every safety stratum has at least 30 independently
adjudicated examples; all clean controls and protected hard positives have
qualified Ukrainian adjudication; and every unresolved disagreement remains
non-headline `needs_ua_review`. Manifest, dispositions, prompt, and responses
must validate by hash with complete unique manifest-ordered joins. Reports
must separate exact measurement from protection, defect, and uncertainty.
Any baseline must have a predeclared question, smallest sufficient model set,
uncertainty report, and stopping rule.

## Future questions and baseline admission

Gemini 3.6 Flash could change only the decision whether to retain a closed-model
comparison ceiling: under the identical frozen split and minimal-edit prompt,
does it lower over-editing on the 120 clean controls relative to the smallest
predeclared open-weight anchor while producing zero normalizations on protected
hard positives? Gemini 3.1 Pro could change only the prompt-contract decision:
under matched data and decoding, does the specialized Ukrainian prompt improve
reviewed multi-reference calque recall without worsening clean-control or
protected-positive errors relative to the minimal prompt? The smallest
sufficient sets are respectively Gemini 3.6 Flash plus one open-weight anchor,
and Gemini 3.1 Pro under the two frozen prompt variants. A future model must
name its Ukrainian failure or prompt-sensitivity question and the decision its
run could change before generation.

Admission requires the named question, decision changed, frozen data/split,
exact prompt, smallest sufficient model set, uncertainty/protection/defect
reporting, stopping rule, and contamination isolation. Otherwise no provider
artifact is admitted and no run is made.
