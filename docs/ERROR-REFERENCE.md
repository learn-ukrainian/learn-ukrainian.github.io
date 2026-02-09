# Error Message Reference

This document provides a comprehensive list of error codes, their meanings, and how to fix them.

---

## 1. Audit Errors (AUD)

These errors are triggered during the structural and quality audit phase (`scripts/audit_module.py`).

| Code | ID (Old) | Category | Description | Fix Suggestion |
|------|----------|----------|-------------|----------------|
| **AUD001** | `VOCABULARY_NOT_DEFINED` | Vocabulary | A word used in activities is not found in any vocabulary sidecar. | Add the word to the module's `vocabulary/{slug}.yaml` or a prior module. |
| **AUD002** | `YAML_SCHEMA_VIOLATION` | Schema | The activity YAML does not conform to the JSON schema. | Check `docs/SCHEMA-REFERENCE.md` for required fields and correct types. |
| **AUD003** | `OUTLINE_SECTION_MISSING` | Structure | A section defined in `meta.yaml` is missing from the markdown content. | Add the missing `##` header to the `.md` file. |
| **AUD004** | `WORD_COUNT_SHORTFALL` | Quality | The core content word count is below the 95% threshold. | Expand explanations, add more examples, or develop existing sections. |
| **AUD005** | `LOW_IMMERSION` | Pedagogy | The ratio of Ukrainian to English is below the target for the current phase. | Convert English scaffolding to Ukrainian or add more Ukrainian narrative. |
| **AUD006** | `DRYNESS_FLAG` | Richness | The module lacks engagement features (dialogues, callouts, cultural hooks). | Add 💡 callouts, **Діалог** sections, or 🇺🇦 Cultural Moments. |
| **AUD007** | `FORBIDDEN_ACTIVITY` | Track | An activity type (e.g., grammar drill) is forbidden in this track (e.g., B2-HIST). | Remove the forbidden activity or replace it with a permitted type (e.g., `reading`). |
| **AUD008** | `LINT_ERROR` | Format | Basic markdown formatting issues (empty headers, AI slop, etc.). | Follow the instructions in the audit log to clean up the formatting. |

---

## 2. Review Errors (REV)

These errors are triggered during the deep quality review phase (`/review-content-v4`).

| Code | Category | Description | Fix Suggestion |
|------|----------|-------------|----------------|
| **REV001** | Naturalness | The Ukrainian text sounds robotic or unnatural. | Re-read the passage; ensure it sounds like a native speaker would say it. Avoid word-for-word translations. |
| **REV002** | Russianism | Found a word or construction influenced by Russian (Surzhyk). | Replace with the correct Ukrainian equivalent (e.g., use «під» instead of «под»). |
| **REV003** | Accuracy | Factual error in history, biography, or grammar explanation. | Verify against primary sources or the State Standard 2024. |
| **REV004** | Activity Logic | An activity has no correct answer, multiple correct answers, or confusing options. | Test the activity manually in the Activity Design Studio and fix the YAML. |

---

## 3. System Errors (SYS)

Errors related to the orchestration and environment.

| Code | Category | Description | Fix Suggestion |
|------|----------|-------------|----------------|
| **SYS001** | Message Broker | Watcher daemon is not responding or task is stuck. | Restart the watcher: `scripts/agent_watcher.py --stop` then `--daemon`. |
| **SYS002** | Context Limit | Gemini has reached its context window limit. | The orchestrator should handle this by using fresh sessions. If it persists, reduce the size of input files. |
| **SYS003** | API Timeout | Subprocess was killed before completion. | Check `scripts/ai_agent_bridge.py` and ensure `--no-timeout` is used for long tasks. |

---

## 4. How to Read Audit Logs

Audit logs are saved to `curriculum/l2-uk-en/{level}/audit/{slug}-audit.log`.

- **❌ FAIL (AUDXXX)**: Must be fixed before the module can be deployed.
- **⚠️ WARN**: Should be addressed but does not block deployment.
- **ℹ️ INFO**: Suggestions for further improvement.

Always check the **FIX** section provided in the log output for actionable steps.
