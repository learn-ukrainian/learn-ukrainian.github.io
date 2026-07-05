# Scorer Adapter Boundaries

Issue: [#4308](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4308)

The adapter layer lives in `scripts/audit/qg_adapters.py`. Its only job is to
normalize scorer signals into `scripts/audit/qg_schema.py` findings; it does
not define new scoring policy, dispatch LLM prompts, or bulk-run curriculum
modules.

## Adapter Sources

| Adapter | Source | Confidence |
| --- | --- | --- |
| `DeterministicRuleAdapter` | `scan_curriculum_module()`, `check_russicisms()`, and #912 `scan_plan_for_russianisms()` | `deterministic` |
| `UaGecGoldFixtureAdapter` | `data/ua-gec-gold/ua-gec-gold.json` curated rows | `lookup_heuristic` |
| `LlmJudgmentAdapter` | Pre-supplied structured placeholder judgments only | `llm_judgment` |

## Deterministic Before LLM

Cheap deterministic checks stay in `DeterministicRuleAdapter` so routing can run
them before any future LLM-only reviewer work. The #912 semantic false-friends
linter is wired through `scan_plan_for_russianisms(plan_path)` and converted
with `qg_schema.build_semantic_false_friend_finding()`. The content Russicism
gate is normalized from `check_russicisms(content, file_path=...)`.

## UA-GEC Gold Limitations

`UaGecGoldFixtureAdapter` preserves each fixture row's gold tag and canonical
finding. It intentionally does not re-label `F/Calque` rows, because the fixture
documents known noise on that axis. The adapter carries a metadata hook:

```json
{
  "ua_gec_gold": {
    "gold_relabelled": false,
    "contested_flag": null,
    "contested_flag_follow_up": "#4364"
  }
}
```

That hook is for the contested-flag review layer tracked separately in #4364.

## LLM Placeholder

`LlmJudgmentAdapter` accepts already-structured judgments and sets
`confidence: llm_judgment`. Prompt templates, model selection, reviewer
profiles, and dispatch belong to #4309 and are deliberately out of this layer.
