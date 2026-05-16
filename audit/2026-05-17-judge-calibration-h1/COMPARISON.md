# H1 Before/After Comparison — Evidence-Rich Judge Prompt

**Date:** 2026-05-17
**Baseline:** `audit/2026-05-17-judge-calibration-matrix/`
**H1:** `audit/2026-05-17-judge-calibration-h1/`
**Same 12-case calibration set** (`eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`).

## Headline

**Hypothesis on the canonical-greeting false positive: CONFIRMED.**
All three cells that previously false-flagged `cal_clean_greeting` ("Доброго дня! Як ваші справи?…") now correctly output CLEAN.

**Hypothesis on net F1: FALSIFIED.**
F1 collapsed on every cell because the strict cite-or-forbid rule made all judges output CLEAN on most dirty cases. Precision is now 1.0 (no false flags survive the citation requirement) but recall fell from a baseline mean of ~0.65 to a uniform 0.06–0.13.

## Per-cell deltas

| Cell | Prior F1 | H1 F1 | ΔF1 | Prior P | H1 P | ΔP | Prior R | H1 R | ΔR | Prior case_acc | H1 case_acc | Δacc | Prior greeting | H1 greeting |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| opus-4.7 xhigh+mcp        | 0.839 | 0.118 | **−0.721** | 0.867 | 1.000 | +0.133 | 0.813 | 0.063 | **−0.750** | 0.917 | 0.500 | −0.417 | ✗ FP | ✓ CLEAN |
| opus-4.7 high −mcp        | 0.828 | 0.118 | **−0.710** | 0.923 | 1.000 | +0.077 | 0.750 | 0.063 | **−0.687** | 0.917 | 0.583 | −0.334 | ✗ FP | ✓ CLEAN |
| haiku-4.5 high −mcp       | 0.546 | 0.118 | **−0.428** | 1.000 | 1.000 |  0.000 | 0.375 | 0.063 | **−0.312** | 0.750 | 0.500 | −0.250 | ✓ CLEAN | ✓ CLEAN |
| gpt-5.5 medium +mcp       | 0.720 | 0.118 | **−0.602** | 1.000 | 1.000 |  0.000 | 0.563 | 0.063 | **−0.500** | 1.000 | 0.500 | −0.500 | ✓ CLEAN | ✓ CLEAN |
| gemini-3.1-pro default+mcp| 0.800 | 0.222 | **−0.578** | 0.857 | 1.000 | +0.143 | 0.750 | 0.125 | **−0.625** | 0.917 | 0.583 | −0.334 | ✗ FP | ✓ CLEAN |
| grok-4.3 hermes xhigh+mcp | 0.786 | 0.118 | **−0.668** | 0.917 | 1.000 | +0.083 | 0.688 | 0.063 | **−0.625** | 1.000 | 0.500 | −0.500 | ✓ CLEAN | ✓ CLEAN |

(Greeting columns: `✗ FP` = judge incorrectly flagged "Доброго дня…" as Russianism. `✓ CLEAN` = correctly judged clean.)

## Greeting FP outcome (the specific motivation)

Quoting the per-case judgments via `jq`:

| Cell | Prior `cal_clean_greeting.case_acc` | H1 `cal_clean_greeting.case_acc` |
|---|:---:|:---:|
| opus-4.7 xhigh+mcp | `false` | `true` |
| opus-4.7 high −mcp | `false` | `true` |
| gemini-3.1-pro default+mcp | `false` | `true` |

Three FPs eliminated. The inverted CLEAN-by-default opener + explicit anti-flag rule for "Доброго дня! Як ваші справи?" + token-level Grinchenko/ESUM attestation (вас, гаразд, усе) all reinforced the correct verdict.

## Why F1 collapsed — evidence-anchor scarcity on this case set

Profiling `retrieve_evidence` over all 12 calibration cases:

```
cal_clean_greeting             CLEAN         ant=0 vu=0 rs=0 her=3
cal_clean_short_prose          CLEAN         ant=0 vu=0 rs=0 her=4
cal_clean_travel               CLEAN         ant=0 vu=0 rs=0 her=1
cal_clean_workplace            CLEAN         ant=0 vu=0 rs=0 her=3
cal_dirty_email_calques        DIRTY (4)     ant=0 vu=0 rs=0 her=1   ← 0 anchors
cal_dirty_medical              DIRTY (3)     ant=0 vu=1 rs=0 her=3   ← 1 anchor (`прийом`)
cal_dirty_workplace            DIRTY (2)     ant=0 vu=0 rs=0 her=4   ← 0 anchors
cal_dirty_meetup               DIRTY (2)     ant=0 vu=0 rs=0 her=2   ← 0 anchors
cal_dirty_register             DIRTY (2)     ant=0 vu=0 rs=0 her=2   ← 0 anchors
cal_debatable_next_steps       DIRTY (1)     ant=0 vu=0 rs=0 her=3   ← 0 anchors
cal_clean_with_lure            CLEAN         ant=0 vu=0 rs=0 her=2
cal_dirty_business_meeting     DIRTY (2)     ant=0 vu=1 rs=0 her=0   ← 1 anchor (`слідуючим`)
```

`ant`=Antonenko entries; `vu`=VESUM-unknown tokens; `rs`=Russian-shadow morphology hits; `her`=token-level heritage attestation.

Of the 8 dirty cases (16 expected flags total at sev≥2), only **2 cases** had ANY evidence anchor under the H1 strict rules, and those anchors covered only **2 of the 16 expected flags**. The H1 prompt forbids unsupported flags, so the judge correctly defaulted to CLEAN on the other 6 dirty cases — yielding the floor `tp=1, fp=0, fn=15` → P=1.0, R=0.0625, F1=0.118 that 5 of 6 models hit exactly. Gemini caught one extra anchor (medical `прийом`) for F1=0.222.

This is **not a model failure**. Every model behaved identically and correctly under the rules. The bottleneck is the evidence catalog:
- **Antonenko** (279 entries indexed of ~600 — issue #1663) — keyed on isolated headwords; misses none of these phrasings.
- **VESUM** correctly contains nearly every Ukrainian-morphology calque (e.g. `повістка`, `обставини`, `звертайтеся`) — they ARE valid Ukrainian forms morphologically; the russianism is pragmatic / register / phraseological.
- **Russian-shadow** (pymorphy3 over non-VESUM tokens) — fires only on tokens like `спасибо`, `пожалуйста` — outright Russian, not present in this calibration set.

Practical conclusion: the H1 design is well-suited to **morphological** russianism detection. It is structurally unable to detect the **lexical/phraseological/register** calques that dominate this 12-case calibration set.

## Surprises

1. **Five of six models converged on identical numbers** (F1=0.118, P=1.0, R=0.0625, exactly 1 tp). The strict cite-or-forbid rule is more determinative than model intelligence — the bottleneck is the evidence floor, not the model's reasoning.

2. **Opus's case_acc actually DROPPED** despite the FP fix (0.917 → 0.500) because the prior over-flagging was secretly carrying recall.

3. **Haiku's prior recall (0.375) was already evidence-floor-limited** without any prompt change. Haiku H1 matches the others exactly, suggesting Haiku was already roughly at the evidence-anchored floor.

## Decision implications

- **Don't ship this prompt as-is for production reviewer use.** Recall is too low for routing decisions.
- **The H1 design IS valuable for**: surfaces where a single false-flag is more harmful than a missed flag — e.g. user-visible content rejection, where a clean-greeting FP would block correct output. Precision = 1.0 is meaningful when over-flagging is the failure mode.
- **Next experiment (H2):** add a fourth evidence channel for phraseological calques — either (a) a curated list of high-confidence calque phrases (повістка дня, забір крові, наступним питанням) checked against the text, or (b) a register-evidence channel that gives the judge license to flag based on cited Antonenko style-guide register rules even when no headword directly matches the input. Option (b) reopens hallucination risk and needs careful prompting.
- **The proper-noun filter (added during this experiment) was crucial.** Without it, `Львова` (Lviv-gen, missing from VESUM common-form table) would have been a fake russianism candidate on `cal_clean_travel`, regressing a previously-clean case into a false positive across all models.

## Errors

0 errors across all 6 cells. All judges returned parseable JSON.

```
$ for f in audit/2026-05-17-judge-calibration-h1/*/*/*/*.json; do
    jq -r '"\(input_filename): errors=\(.raw_telemetry.errors | length)"' "$f"
  done | sort -u
audit/.../anthropic/claude-haiku-4-5-20251001/native_cli/high-without_mcp.json: errors=0
audit/.../anthropic/claude-opus-4-7/native_cli/high-without_mcp.json: errors=0
audit/.../anthropic/claude-opus-4-7/native_cli/xhigh-with_mcp.json: errors=0
audit/.../google/gemini-3.1-pro-preview/native_cli/default-with_mcp.json: errors=0
audit/.../openai/gpt-5.5/native_cli/medium-with_mcp.json: errors=0
audit/.../xai/grok-4.3/hermes/xhigh-with_mcp.json: errors=0
```
