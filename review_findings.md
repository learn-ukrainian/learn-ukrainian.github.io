Here is the adversarial code review of the Phase 4 JSON writer contract PR:

### CRITICAL

*   **`_strip_outer_code_fence` is missing (file: `scripts/build/linear_pipeline.py:287`):** `parse_writer_output_strict_json` iterates over `output.splitlines()` without calling `_strip_outer_code_fence(output)` first. If the LLM wraps its multi-block response in a global ` ```markdown ... ``` ` fence (a common LLM quirk), the parser will instantly fail with `Writer output contains unnamed fenced block at line 1`. The old parser also failed silently on this by messing up state. Calling `output = _strip_outer_code_fence(output)` before the loop would elegantly fix this and save an expensive redispatch cycle.

### IMPORTANT

*   **Arbitrary extra keys are silently allowed (file: `scripts/build/linear_pipeline.py:643`):** The schema validation only iterates over `required_item_fields` using `item.get(field)`. Any extra keys hallucinated by the LLM (e.g., `"notes": "..."` in activities where it's not expected) are ignored by the validator but passed directly into `yaml.safe_dump`. Consider enforcing exact key matches (`set(item.keys()) == set(schema.required_item_fields.keys())`) or adding an `optional_fields` list to prevent garbage data from entering the final artifacts.
*   **Opaque type-mismatch errors (file: `scripts/build/linear_pipeline.py:648`):** If the LLM generates `{"id": 123}`, the error is `item 1 requires id as str`. It doesn't show the offending value or type. Changing the message to `requires {field} as {expected_type.__name__} (got {type(value).__name__}: {value})` will make diagnosing LLM failures significantly easier in the logs.

### NIT

*   **Misleading empty-string error (file: `scripts/build/linear_pipeline.py:648`):** The condition `expected_type is str and not value.strip()` raises the same `requires {field} as str` error. Since `""` *is* a string, the message is confusing. It should specifically state "must be a non-empty string".
*   **Goofy `fence_lang` fallback (file: `scripts/build/linear_pipeline.py:315`):** If the LLM writes ` ```file=activities.yaml ` (omitting the language entirely), `_fence_language` evaluates to `"file=activities.yaml"`. The resulting error is `must be fenced as json, got file=activities.yaml`, which is slightly awkward but functionally correct.
*   **Line math is spot-on:** Your line number math (`absolute_line = content_start_line + exc.lineno - 1`) in `_parse_and_dump_writer_json_artifact` is completely correct. `json.JSONDecodeError` uses 1-based lines, and since `fence_start_line + 1` maps to line 1 of the JSON body, the absolute line correctly aligns with the original output string.
*   **`yaml.safe_dump` round-trip:** No risk here. `yaml.safe_dump` correctly quotes strings like `"yes"` or `"no"` that would otherwise be parsed as booleans in YAML 1.1. Deep nesting is technically a risk, but naturally capped by the LLM's output token limits.
