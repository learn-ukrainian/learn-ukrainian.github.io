# UA Contact Quality Evidence Schema

Issue: [#4307](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4307)

This is the shared evidence contract for #2156 calque and grammar scoring. The
Python helpers live in `scripts/audit/qg_schema.py`.

The schema is additive. Existing `curriculum_ua_qg_evidence.v1` and
`llm_qg_evidence.v1` records remain valid as projection profiles; this contract
does not require a migration of PR1 compact evidence.

## Version

Canonical record version:

```text
ua_contact_quality_evidence.v1
```

Supported profiles:

| Profile | Use |
| --- | --- |
| `curriculum_deterministic` | PR1 deterministic curriculum findings and fixtures. |
| `curriculum_llm_compact` | Compact LLM-QG evidence projected into the shared fields. |
| `ua_gec_eval` | UA-GEC-backed gold/eval rows. |
| `leaderboard` | Future UNLP/leaderboard result rows. |

## Core Fields

Record fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | `ua_contact_quality_evidence.v1`. |
| `profile` | Projection profile listed above. |
| `evidence_kind` | `module`, `fixture`, or `eval_item`. |
| `module_id` / `eval_item_id` / `fixture_id` | One stable target id. |
| `level_policy` | Curriculum policy family and English/register rules, when applicable. |
| `content_sha` | Content hash for module-bound evidence. |
| `checker_runs` | Adapter/version/config/provider/model metadata. |
| `dimensions` | Per-dimension score, verdict, and canonical findings. |
| `aggregate` | Min score, min dimension, failing/warning dimensions. |
| `verdict` / `terminal_verdict` | Human-visible and build-gate verdicts. |
| `provenance` | Run id, timestamp, source, and related fixture/corpus ids. |

Finding fields:

| Field | Meaning |
| --- | --- |
| `finding_id` | Stable hash over issue, locator, excerpt, and detector id. |
| `issue_id` | Canonical uppercase issue id. |
| `issue_class` | `calque`, `grammar`, `collocation`, `false_friend`, `register`, `leakage`, `pedagogy`, `fluency`, `mechanics`, or `other`. |
| `dimension` | Scoring bucket. |
| `severity` | `critical`, `warning`, or `info`. |
| `contact_source_lang` | Contact language of the error: `ru`, `pl`, `en`, `unknown`, or `other`. |
| `source_lang` | Compatibility alias for `contact_source_lang`. |
| `track_l1` | Learner-track L1, separate from contact source language. |
| `ua_gec_tag` | Original UA-GEC tag, if any. |
| `confidence` | `deterministic`, `lookup_heuristic`, or `llm_judgment`. |
| `disposition` | `defect`, `teaching_contrast`, `quoted_bad_form`, `heritage_allowed`, or `suppressed_fp`. |
| `file`, `line`, `span`, `excerpt` | Bounded locator and quote. Excerpts are capped at 160 characters. |
| `message` | Short human reason. |
| `suggested_replacement` | Zero or more suggested forms. |
| `detector` | Adapter, rule id, and pattern id. |
| `attribution` | Corpus/license/doc/pair/evidence metadata. |
| `sense_context` | Required for semantic false friends and sense-restricted calques. |

Dimensions:

| Dimension | Primary signal |
| --- | --- |
| `contact_calque` | Russian/Polish/English contact calques and false friends. |
| `contact_grammar` | UA-GEC G/* case, gender, agreement, or government findings. |
| `ukrainian_style` | Curriculum phrase rules and unnatural learner-facing Ukrainian. |
| `level_policy` | Level-aware English scaffolding and support rules. |
| `surface_leakage` | AI/persona/path/internal leakage. |
| `naturalness` | LLM-only idiom, collocation, and register judgment. |
| `pedagogical` | Teaching quality. |
| `decolonization` | Historical/framing sensitivity. |
| `engagement` | Learner value beyond filler. |
| `tone` | Teacher voice and pathos. |
| `seminar_sensitivity` | Advanced seminar-specific risk. |
| `mechanics` | Orthography/punctuation when explicitly in scope. |

## UA-GEC Mapping

The helper `map_ua_gec_tag()` encodes the initial tag mapping:

| UA-GEC tag | Issue id | Issue class | Dimension | Default severity | Default contact source |
| --- | --- | --- | --- | --- | --- |
| `F/Calque` | `CONTACT_CALQUE_UA_GEC` | `calque` | `contact_calque` | `info` | `ru` |
| `F/Collocation` | `UNNATURAL_COLLOCATION` | `collocation` | `contact_calque` | `warning` | `ru` |
| `G/Case` | `UKRAINIAN_GRAMMAR_CASE` | `grammar` | `contact_grammar` | `warning` | `ru` |
| `G/Gender` | `UKRAINIAN_GRAMMAR_GENDER` | `grammar` | `contact_grammar` | `warning` | `ru` |
| other `G/*` | `UKRAINIAN_GRAMMAR_UA_GEC` | `grammar` | `contact_grammar` | `warning` | `ru` |
| other `F/*` | `UA_GEC_FLUENCY_OTHER` | `fluency` | `naturalness` | `info` | `unknown` |

`F/Style` remains out of automated scorer scope for now. The schema can carry
it as `UA_GEC_FLUENCY_OTHER` if a manual or LLM reviewer emits it, but #4308
should not ingest it as a deterministic blocking rule.

Bulk UA-GEC lookup defaults to `info`; confirmed phrase rules or reviewer
judgment can escalate severity.

## Examples

Deterministic B1-27 finding:

```json
{
  "issue_id": "AWKWARD_PASSIVE_RESULT_STATE",
  "issue_class": "calque",
  "dimension": "ukrainian_style",
  "severity": "critical",
  "contact_source_lang": "unknown",
  "source_lang": "unknown",
  "track_l1": "en",
  "ua_gec_tag": null,
  "confidence": "deterministic",
  "disposition": "defect",
  "file": "module.md",
  "line": 3,
  "span": { "start": 42, "end": 73 },
  "excerpt": "застосунок має бути відкритий",
  "message": "Use active/impersonal Ukrainian instead of a literal passive state.",
  "suggested_replacement": [],
  "detector": {
    "adapter": "curriculum_qg_harness",
    "rule_id": "b1_awkward_passive_result_state",
    "pattern_id": "b1_awkward_passive_result_state"
  },
  "attribution": {
    "corpus": "curriculum_phrase_rules",
    "license": null,
    "doc_id": null,
    "pair_id": null,
    "evidence": "B1-27 calibration fixture"
  }
}
```

UA-GEC F/Calque finding:

```json
{
  "issue_id": "CONTACT_CALQUE_UA_GEC",
  "issue_class": "calque",
  "dimension": "contact_calque",
  "severity": "info",
  "contact_source_lang": "ru",
  "source_lang": "ru",
  "ua_gec_tag": "F/Calque",
  "confidence": "lookup_heuristic",
  "disposition": "defect",
  "file": "module.md",
  "line": 18,
  "span": { "start": 210, "end": 218 },
  "excerpt": "являється",
  "message": "UA-GEC F/Calque pair: являється -> є (frequency 47).",
  "suggested_replacement": ["є"],
  "detector": {
    "adapter": "ua_gec_lookup",
    "rule_id": "F/Calque",
    "pattern_id": "0301"
  },
  "attribution": {
    "corpus": "UA-GEC v2",
    "license": "CC-BY-4.0",
    "doc_id": "0301",
    "pair_id": null,
    "evidence": "Syvokon et al., UNLP 2023"
  }
}
```

Semantic false friend finding for #912:

```json
{
  "issue_id": "SEMANTIC_FALSE_FRIEND",
  "issue_class": "false_friend",
  "dimension": "contact_calque",
  "severity": "critical",
  "contact_source_lang": "ru",
  "ua_gec_tag": null,
  "confidence": "deterministic",
  "file": "vocabulary.yaml",
  "line": 12,
  "excerpt": "**лук** (onion)",
  "suggested_replacement": ["цибуля"],
  "sense_context": {
    "word": "лук",
    "calque_sense": "onion",
    "authentic_sense": "bow (weapon)",
    "matched_gloss_pattern": "**лук** (onion)"
  },
  "detector": {
    "adapter": "semantic_false_friends",
    "rule_id": "SEMANTIC_FALSE_FRIEND",
    "pattern_id": "лук"
  }
}
```

## False-Positive Controls

Adapters must normalize false-positive decisions into `disposition`:

| Disposition | Use |
| --- | --- |
| `defect` | Penalized finding. |
| `quoted_bad_form` | The bad form is quoted, blockquoted, or shown as a bad example. |
| `teaching_contrast` | The form appears in a contrast pair such as "not X, use Y". |
| `heritage_allowed` | Heritage/SUM/Grinchenko evidence clears an otherwise suspicious form. |
| `suppressed_fp` | Adapter matched text but the profile/track policy suppresses it. |

Sense-restricted calques and semantic false friends must include
`sense_context`. Do not blanket-fail words such as `любий`, `біля`,
`на протязі`, or `лук` without the relevant sense/gloss context.

## Stability Rules

- New adapters should emit `ua_contact_quality_evidence.v1` records or
  canonical findings from `scripts/audit/qg_schema.py`.
- Existing PR1 evidence remains valid; do not rewrite `qg_evidence.json`
  artifacts just to adopt this schema.
- Additive fields can be introduced under `metadata`, `detector`, or
  `attribution`.
- Breaking changes require `ua_contact_quality_evidence.v2` and compatibility
  tests against PR1 evidence plus UA-GEC fixtures.
- Raw LLM transcripts, telemetry DBs, and generated audit/status files remain
  out of git.

## Before #4308

The scorer-adapter issue should not start until these are stable:

- `contact_source_lang` inference order: UA-GEC/source row, rule metadata,
  Russian default for prioritized F/G tags, then `unknown`.
- UA-GEC attribution is preserved on every emitted finding.
- Teaching quotes, contrast pairs, heritage-safe forms, and OES/RUTH/historical
  exemptions normalize to non-penalizing dispositions.
- #912 semantic false friends emit `SEMANTIC_FALSE_FRIEND` with
  `sense_context`, not a lexical-russicism finding.
