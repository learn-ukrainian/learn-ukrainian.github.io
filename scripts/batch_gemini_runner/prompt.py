"""Prompt generation for the batch Gemini runner.

Builds prompts from templates with module data substitution.
"""

import re

import yaml
from batch_gemini_config import PROJECT_ROOT, num_for_slug
from slug_utils import review_path as _review_path

from .constants import log
from .utils import (
    _filter_schema_for_track,
    _get_core_activity_examples,
    _get_seminar_activity_examples,
)


def generate_prompt(runner, phase, slug, paths, error_msg=None):
    """Build a prompt from template + module data.

    Args:
        runner: BatchRunner instance (used for track, config access).
        phase: Build phase identifier.
        slug: Module slug.
        paths: Dict of module file paths.
        error_msg: Optional error message from previous attempt.

    Returns:
        Prompt string, or None if no template exists for this phase.
    """
    template_path = runner.config["templates"].get(phase)
    if not template_path:
        return None

    template = _read_file_safe(template_path)

    # Load module data for inlining
    plan_content = _read_file_safe(paths["plan"])
    research_content = _read_file_safe(paths["research"])
    if not research_content:
        research_content = "(no research file available)"
    meta_content = _read_file_safe(paths["meta"])
    quick_ref_content = _read_file_safe(runner.config.get("quick_ref"))
    content_content = _read_file_safe(paths["md"])
    activities_content = _read_file_safe(paths["activities"])
    vocabulary_content = _read_file_safe(paths["vocabulary"])

    # Read activity schema reference
    schema_path = PROJECT_ROOT / "docs" / "ACTIVITY-YAML-REFERENCE.md"
    schema_content = _read_file_safe(schema_path)

    # Read review file (needed by fix phase template)
    review_file = _review_path(paths["md"].parent, slug)
    review_content = _read_file_safe(review_file)

    # Parse plan for WORD_TARGET
    word_target = 3000
    topic_title = slug
    if paths["plan"].exists():
        try:
            plan_data = yaml.safe_load(plan_content)
            word_target = plan_data.get("word_target", 3000)
            topic_title = plan_data.get("title", slug)
        except yaml.YAMLError as e:
            log.warning(f"Failed to parse plan YAML for {slug}: {e}")

    # Get module number from curriculum index
    try:
        module_num = num_for_slug(runner.track, slug)
    except ValueError:
        module_num = 0

    # Parse level from meta or derive from track
    level = runner.track.upper()
    if paths["meta"].exists():
        try:
            meta_data = yaml.safe_load(meta_content)
            if isinstance(meta_data, dict):
                level = meta_data.get("level", level)
        except yaml.YAMLError:
            pass

    # Activity/vocabulary count targets
    is_seminar = runner.config.get("type") == "seminar"
    activity_count_target = "4-9" if is_seminar else "6-12"
    vocab_count_target = "15-25"

    # Resolve allowed/forbidden activity types from audit config
    from audit.config import LEVEL_CONFIG
    _TRACK_TO_CONFIG = {
        "bio": "biography",
        "istorio": "istorio",
        "hist": "history",
        "lit": "LIT",
        "oes": "OES",
        "ruth": "RUTH",
    }
    config_key = _TRACK_TO_CONFIG.get(runner.track, level)
    track_level_config = LEVEL_CONFIG.get(config_key, {})
    priority_types = track_level_config.get('priority_types', set())
    forbidden_types = track_level_config.get('forbidden_types', set())
    allowed_types_str = ", ".join(sorted(priority_types)) if priority_types else "all standard types"
    forbidden_types_str = ", ".join(sorted(forbidden_types)) if forbidden_types else "none"

    # Immersion rule
    if is_seminar:
        immersion_rule = "100% Ukrainian immersion. No English except for specific terminology comparisons if needed."
        immersion_target = "100"
    else:
        immersion_rule = "Write in Ukrainian, except for grammar explanations which should be in English."
        immersion_target = "varies"

    # Compute audit metrics (useful for review phase)
    audit_word_count = len(content_content.split()) if content_content else 0
    word_percent = round(audit_word_count / word_target * 100) if word_target > 0 else 0

    activity_count = 0
    if activities_content:
        try:
            acts = yaml.safe_load(activities_content)
            if isinstance(acts, list):
                activity_count = len(acts)
        except yaml.YAMLError:
            pass

    vocab_count = 0
    if vocabulary_content:
        try:
            vocab = yaml.safe_load(vocabulary_content)
            if isinstance(vocab, list):
                vocab_count = len(vocab)
        except yaml.YAMLError:
            pass

    engagement_count = len(re.findall(
        r'\[!(tip|myth-buster|quote|history-bite|context|decolonization|culture|warning)\]',
        content_content
    )) if content_content else 0

    output_path = str(_review_path(paths["md"].parent, slug))

    # Generate track-appropriate activity examples
    if is_seminar:
        activity_examples = _get_seminar_activity_examples(runner.track)
        filtered_schema = _filter_schema_for_track(schema_content, priority_types)
    else:
        activity_examples = _get_core_activity_examples()
        filtered_schema = schema_content  # Full schema for core tracks

    # For fix-activities phase, include audit errors
    audit_errors = ""
    if phase == "fix-activities" and error_msg:
        audit_errors = error_msg

    replacements = {
        "{PLAN_PATH}": plan_content,
        "{RESEARCH_PATH}": research_content,
        "{META_PATH}": meta_content,
        "{QUICK_REF_PATH}": quick_ref_content,
        "{CONTENT_PATH}": content_content,
        "{ACTIVITIES_PATH}": activities_content,
        "{VOCAB_PATH}": vocabulary_content,
        "{SCHEMA_PATH}": filtered_schema,
        "{REVIEW_PATH}": review_content,
        "{WORD_TARGET}": str(word_target),
        "{OVERSHOOT_TARGET}": str(word_target if level.upper().startswith(('A1', 'A2')) else int(word_target * 1.5)),
        "{TOPIC_TITLE}": topic_title,
        "{TRACK}": runner.track,
        "{LEVEL}": level,
        "{MODULE_NUM}": str(module_num),
        "{PREV_MODULE}": str(max(0, module_num - 1)),
        "{ENGAGEMENT_MIN}": "5",
        "{EXAMPLE_MIN}": "24",
        "{IMMERSION_RULE}": immersion_rule,
        "{IMMERSION_TARGET}": immersion_target,
        "{ACTIVITY_COUNT_TARGET}": activity_count_target,
        "{VOCAB_COUNT_TARGET}": vocab_count_target,
        "{AUDIT_WORD_COUNT}": str(audit_word_count),
        "{WORD_PERCENT}": str(word_percent),
        "{ACTIVITY_COUNT}": str(activity_count),
        "{VOCAB_COUNT}": str(vocab_count),
        "{ENGAGEMENT_COUNT}": str(engagement_count),
        "{IMMERSION_PERCENT}": immersion_target,
        "{AUDIT_STATUS}": "pending review",
        "{OUTPUT_PATH}": output_path,
        "{ALLOWED_ACTIVITY_TYPES}": allowed_types_str,
        "{FORBIDDEN_ACTIVITY_TYPES}": forbidden_types_str,
        "{ACTIVITY_EXAMPLES}": activity_examples,
        "{AUDIT_ERRORS}": audit_errors,
    }

    prompt = template
    for k, v in replacements.items():
        prompt = prompt.replace(k, v)

    if error_msg:
        fix_instructions = f"""

## FIX PREVIOUS ERRORS
Your previous attempt failed validation with these errors:

```
{error_msg}
```

Please fix these issues and regenerate the content."""
        prompt += fix_instructions

    return prompt


def _read_file_safe(path):
    """Read a file, returning empty string if missing or unreadable."""
    if path and path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except (OSError, UnicodeDecodeError) as e:
            log.warning(f"Failed to read {path}: {e}")
    return ""
