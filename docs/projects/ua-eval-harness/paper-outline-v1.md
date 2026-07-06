# Paper outline v1 — "Tool-Grounded Factuality Evaluation for Ukrainian: A Fabrication-Trap Benchmark" (#4312, UNLP 2027)

Status: v2 — hostile-seat review (grok, task review-4312-outline-r2) APPLIED 2026-07-06: "first" claim
scoped with explicit UAlign/shared-task differentiation; tier-independence reframed as a scoped anchor
finding; marketing tone moved out of §1; §6 gaps filled (transport parity, folk skew, internal origin,
trap-count low-N as primary signal). Verdict path: "not argument-sound" → repairs below → re-reviewable.
Numbers marked `[FINAL-MATRIX]` come from the frozen reference run; everything else is settled evidence.
Working title deliberately plain; alternatives at the end.

## The one-sentence thesis (sober form — punchline lives in §5/§7 discussion, not the intro)
We present, to our knowledge, the first tool-grounded factuality benchmark for Ukrainian built on
engineered fabrication traps with verified gold, and show that on these traps a curated-source
harness with citation-admissibility gates produces large honesty gains (harness lift) on cheap open
models — while bare models across tiers, including frontier seats, confirmed seeded fabrications
on the anchor passage [scoped: our traps, our domains, stated N].

## 1. Introduction
- Hook (method-first, per hostile review — no leaderboard-bashing): existing Ukrainian evaluation
  measures capability on translated tasks; none measures whether a model, asked to fact-check
  culturally specific claims, confirms fabrications or honestly withholds. We built the instrument;
  the motivating production failure and the scoped bare-vs-tooled findings follow in §5.
- Why Ukrainian, why culture: mid-resource language; cultural-heritage content is where parametric
  "knowledge" is thinnest and confident fabrication most harmful (education, decolonization stakes).
  Motivating incident: a production curriculum reviewer confirmed fabricated folk "facts"
  (гаї=ribbon-trees; melody mischaracterization) — the benchmark was born from a real failure.
- Contributions (4):
  C1 benchmark: N passages [FINAL-MATRIX: 21 public + private held-out], 3 domains (folk ritual,
     history, biography), per-claim gold with two engineered trap classes (M: real-source distractor,
     twisted fact; U: verified zero-attestation) + repeat-run protocol.
  C2 harness: tool-grounded reviewer with deterministic admissibility gates (citation ⊆ captured
     tool output; theatre gate; coverage mandate; budget caps) — model judgment isolated from
     retrieval honesty.
  C3 findings (each stated with N/domain/transport qualifiers inline): harness lift on cheap open
     models [+310 gemma-4-31b at n=4 folk-only; FINAL-MATRIX with variance bars]; on the seeded
     anchor, bare frontier seats also scored negative [same-transport caveat: subscription-runtime
     bare rows are a separate measurement profile pending raw-parity #4634 — never aggregated with
     opencode rows; "best bare < worst tooled" is claimed WITHIN the opencode profile only].
  C4 release: public split + lm_eval-compatible results emitter + contamination defenses
     (held-out split, per-passage canaries, versioned freeze).

## 2. Related work (positioning — all claims source-verified 2026-07-06)
- Ukrainian eval landscape: lang-uk leaderboard = 17 translated capability tasks (Belebele, MMLU-UK,
  FLORES/WMT, SQuAD, XLSum, TriviaQA, ARC, Winogrande, GSM8K, IFEval, ZNO×4) — verified from
  leaderboard source code: zero grounding/fabrication/citation measurement; roadmap (UAlign,
  API providers, quantized evals) adds none. UNLP GEC line (UA-GEC; Karpov-Chernodub) = grammar,
  not factuality. Lapa LLM / MamayLM = models + capability self-evals, no truth instrument.
- English factuality line: TruthfulQA (static misconception probes), FActScore (atomic-claim
  retrieval scoring), SAFE (search-augmented evaluator) — we differ: (a) engineered trap classes
  with verified ground truth rather than found errors; (b) ADMISSIBILITY gating (the evaluator's
  citations must be sub-spans of captured tool output — fabricated grounding is structurally
  detectable); (c) harness-lift as the measured quantity (same model ± tools), not model ranking
  alone; (d) mid-resource cultural domain.
- REQUIRED differentiation paragraph (hostile-seat finding 1 — the "first" claim survives only via
  explicit deltas, named): **UAlign (UNLP 2025)** — Ukrainian alignment benchmark with a factuality
  dimension; translated/adapted material (TruthfulQA-derived, machine-translated subsets); NOT
  tool-grounded, no retrieval harness, no evaluator citation-admissibility, no engineered M/U traps
  on native cultural facts, no harness-lift measurement. **UNLP shared tasks** (2025 manipulation
  detection; 2026 RAG/doc-QA) — system evaluations grounding answers to provided documents, not a
  fabrication-trap benchmark isolating reviewer honesty and lift. **PandaChat-RAG-sl** (Slovenian) —
  RAG-system benchmark, different language and design. Scoped position sentence: to our knowledge
  the first TOOL-GROUNDED factuality benchmark for Ukrainian with engineered, verification-receipted
  fabrication traps, and the first to take harness lift as the dependent variable on culturally
  specific fabrication.

## 3. Benchmark construction
- Passage authoring: native-source-grounded (corpus + wiki), 150-200 words, claims are literal
  sub-spans (loader-enforced). Per passage: 6 true / 2 M / 1 U (founding-four exceptions documented).
- Trap engineering: M = real quote from a real source with one fact twisted (distractor evidence
  pre-verified to EXIST — the trap is alignment, not existence); U = claim whose key term has
  verified ZERO attestation across all sources (the honesty probe: correct answer is "unattested").
- Verification protocol: every claim tool-verified at authoring (VESUM/corpus/wiki receipts in
  verification_log); driver spot-verification; [if #4632 lands: native-expert blind validation, IAA].
- Domains + split: DOMAIN_BY_SLUG; public/held-out at passage level; founding-four forced public
  (already burned in repo history — honesty note); held-out authored privately, never in the public
  repo (repo is public; git history is forever).
- Contamination defenses: per-passage canary sentences (external-detection only — documented scope),
  held-out divergence as the published contamination signal, versioned freeze (MANIFEST hashes,
  never-edit-v1 CI guard).
- Repeat-run protocol: 3 runs/cell, outer-sweep interleaving; variance reported as mean ± sd + range
  (no t-CIs at n=3 — stated); stability metric = per-claim verdict-class consistency across runs
  (partial/error/parse-lenient cells flagged and excluded from stability aggregates).

## 4. Harness (measurement instrument)
- Route: reviewer prompt (claim enumeration mandate + 5-verdict taxonomy incl. UNATTESTED_AFTER_SEARCH
  vs REFUTED — bounded-corpus epistemics) through opencode + sources MCP (VESUM, dictionaries,
  corpus, wiki) with full tool telemetry.
- Deterministic gates OUTSIDE the model: grounding match (segment-wise normalized), citation
  admissibility (positive verdicts require deep-source grounding; downgrade path preserves
  original_verdict for scoring), theatre gate (tool-call fabrication = infra invalidation),
  budget cap, coverage mandate. Un-gateable residual: claim↔evidence ALIGNMENT (the −100 class) —
  this is precisely what the benchmark measures.
- Scoring: locked asymmetric constants (CONFIRMED-on-fabricated = −100 fatal; honest-withhold
  rewarded); missing-claim penalty; two-column reporting (model judgment vs live admissible).
- Bare arm = same passages/format, no tools, prompts share the verdict taxonomy verbatim
  (taxonomy-slice reuse — no fork possible).
- Transport identity: {pin, transport, entrypoint} never mixed in aggregates; subscription-runtime
  bare rows carry a do-not-compare banner pending raw-parity (#4634) [resolve before submission].

## 5. Results [FINAL-MATRIX everywhere]
- Headline table: per model × arm, model-judgment mean ± sd (3 runs), U-honesty, M-alignment,
  harness lift over paired passage means. [n=4 preview: gemma-4 −70→+240 (lift +310),
  ds-flash −30→+220, ds-pro +110→+290; best bare < worst tooled.]
- Scoped anchor finding (NOT sold as general "tier-independence"): on the fabrication-seeded anchor,
  bare frontier seats (claude/gpt/gemini, subscription-runtime profile) scored negative alongside the
  cheap pins — reported with the transport caveat, the raw-parity status (#4634), and per-row low-N
  flags. Generalization language deferred to whatever the FINAL-MATRIX + held-out data support.
- Domain generalization: per-domain splits (folk/history/bio) [+ Tier-2 core-level calibration
  pilot as out-of-benchmark supporting evidence, #4637].
- Stability: run-to-run verdict-class consistency per model×arm; error/flake accounting by transport
  (OpenRouter vs first-party deepseek if #4358 comparison lands — serving matters to measurement).
- Cost/latency: tooled gemma ≈ commodity price + ~1 min/passage; the "cheap model + curated grounding
  beats expensive model guessing" economics.

## 6. Limitations (write these FIRST — reviewer-honesty is the brand)
- Scale: N passages / 3 domains; low-N flags carried through every table; benchmark v1 is a focused
  probe, not a general leaderboard.
- Bounded corpus: harness knows what we ingested; UNATTESTED ≠ false; ablation arm (sources-only vs
  sources+web, #4633) [include if run].
- Split biases: founding-four forced-public (folk-heavy public set); prompt-template + taxonomy
  shared across splits (format learning transfers); domain knowledge leaks within domains.
- Canary asymmetry (founding-four have none) + known +1 unmatched-fact-check perturbation on
  canary passages (diagnostic column only).
- Gold labels: pipeline-verified [+ native-expert validation status honestly stated, #4632].
- Judge residual: claim↔evidence alignment remains model judgment — measured, not gated; tooled runs
  still show substantial ungrounded_findings rates (gates reduce, not eliminate).
- Transport: two bare-arm profiles (opencode vs subscription-runtime) are distinct measurements;
  raw-parity (#4634) bounds but does not erase the difference.
- Evidence skew: motivating incident and founding passages are folk-ritual; history/bio status stated
  explicitly per-table; domain generalization claims limited accordingly.
- Origin bias: the benchmark grew from internal curriculum failures — passage/trap selection may
  reflect the failure modes we happened to hit first (disclosed; held-out authoring protocol as partial
  mitigation).
- Absolute trap counts are small — low-N is not a footnote but the PRIMARY qualifier on all honesty
  statistics.
- Scope note: this is the factuality sub-line of the broader #2156 contact-linguistics harness
  (calque/grammar eval) — relationship stated so reviewers see the research program, not a one-off.
- AI-assisted development disclosed; verification regime (cross-family adversarial review,
  fail-closed CI, tool-backed claims) described in an appendix — the instrument was built under the
  distrust regime it measures.

## 7. Release & community integration
- Public split + harness core + public-source adapter profile (#4628) + lm_eval-compatible emitter
  (#4630, shipped) — a factuality track ingestible by the existing leaderboard without adopting our
  stack; UA-first bilingual docs (#4631); versioning + v2-from-production-content growth path.

## Venue/format notes
- UNLP 2027 (co-located ACL family); long paper. arXiv preprint at OSS release (July-Aug 2026)
  claims the niche ahead of the submission cycle.
- Title alternatives: «Найкраща брехня звучить правдиво»…no — keep sober; alt: "Harness Lift:
  Measuring Tool-Grounded Honesty on Ukrainian Cultural Fabrication Traps".

## TODO before draft-1 prose (owner: any driver, no Fable dependency)
1. [FINAL-MATRIX] numbers + variance bars into §5 tables (source: frozen SCORECARD + emitter JSONs).
2. #4634 raw-parity result → §4 transport note; #4633 ablation → §6 if run.
3. #4632 native-expert IAA → §3/§6 validation paragraphs (status either way).
4. Freeze manifest hashes → §7 reproducibility statement.
5. Bibliography: lang-uk leaderboard (RANLP-2025 Paniv), ZNO-Eval, UA-GEC, MamayLM misc, Lapa cite,
   TruthfulQA/FActScore/SAFE — keys collected in docs/projects/ua-eval-harness/model-evidence.md.
