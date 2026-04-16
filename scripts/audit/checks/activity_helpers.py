"""
Shared accessor helpers for activity validation checks.

Provides uniform access to activity fields regardless of whether
the activity is an object (from yaml_activities parser) or a dict.
Also includes error-correction placeholder detection utilities.
"""


def flatten_activities(raw) -> list[dict]:
    """Normalise any known activities-YAML top-level shape to a flat list of
    activity dicts.

    Three shapes exist in the codebase (#1294):

    1. Legacy: bare list at the top level
         ``- id: ...\\n  type: ...``
    2. V6 canonical (``scripts/build/activity_schema.py``): dict with
       ``inline:`` (render inline next to prose) and ``workbook:`` (render
       in the Зошит tab) buckets, plus metadata (``version``, ``module``,
       ``level``)
    3. Older dict wrapper: ``{"activities": [...]}``

    Callers that used ``isinstance(raw, list)`` silently skipped every V6
    module (always a dict), which is why the pre-review structural gate
    never caught phased-out anagrams or item-level hints before publish.
    Route all activities-YAML readers through this helper to avoid that
    class of bug.

    ``None`` / unexpected types produce an empty list. Non-dict entries
    inside a bucket are dropped rather than raised, because the downstream
    checks all assume dicts.
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        collected: list[dict] = []
        # V6 canonical shape
        for bucket_key in ("inline", "workbook"):
            bucket = raw.get(bucket_key)
            if isinstance(bucket, list):
                collected.extend(item for item in bucket if isinstance(item, dict))
        # Older wrapper shape — only honour if we didn't already find V6 buckets
        if not collected:
            wrapped = raw.get("activities")
            if isinstance(wrapped, list):
                collected.extend(item for item in wrapped if isinstance(item, dict))
        return collected
    return []


def get_title(activity) -> str:
    """Get title from an activity object or dict."""
    title = getattr(activity, 'title', None)
    if not title and isinstance(activity, dict):
        title = activity.get('title', 'Untitled')
    return title or 'Untitled'


def get_field(activity, field: str, default='') -> str:
    """Get a string field from an activity object or dict."""
    value = getattr(activity, field, None)
    if not value and isinstance(activity, dict):
        value = activity.get(field, default)
    return value or default


def get_items(activity) -> list:
    """Get items list from an activity object or dict.

    Important: dicts have a built-in `.items()` method, so `getattr(dict, 'items')`
    returns a bound method — not the list we want.  Check `isinstance(dict)` first
    to avoid that trap (#1294).
    """
    if isinstance(activity, dict):
        return activity.get('items', []) or []
    items = getattr(activity, 'items', None)
    return items or []


def get_type(activity) -> str:
    """Get activity type from object or dict."""
    return activity.type if hasattr(activity, 'type') else activity.get('type', '')


def has_hint(obj) -> bool:
    """Check if an object or dict has a non-empty hint field."""
    if isinstance(obj, dict):
        return 'hint' in obj
    return hasattr(obj, 'hint') and obj.hint


# --- Error-correction placeholder detection ---

_QUOTE_MAP = str.maketrans({
    '\u00ab': '"', '\u00bb': '"', '\u201c': '"', '\u201d': '"',
    '\u2018': "'", '\u2019': "'",
})


def _normalize_quotes(s: str) -> str:
    """Normalize various quote characters to plain ASCII quotes."""
    return s.translate(_QUOTE_MAP)


def is_blank_or_placeholder(error: str) -> bool:
    """Check if error field is a blank placeholder."""
    return error == '___' or (isinstance(error, str) and error.strip() == '')


def is_arrow_placeholder(sentence: str) -> bool:
    """Check if sentence uses arrow+placeholder format."""
    return bool(sentence and '\u2192' in sentence and '___' in sentence)


def is_placeholder_error(sentence: str, error: str, answer: str) -> bool:
    """Check if an error-correction item uses placeholder syntax."""
    if is_blank_or_placeholder(error):
        return True
    if is_arrow_placeholder(sentence):
        return True
    if isinstance(error, str) and error.lower() in ('none', 'correct'):
        return False
    if not sentence and error and answer and len(str(error).split()) >= 3 and len(str(answer).split()) >= 3:
        return False
    if error and sentence:
        return _normalize_quotes(str(error).lower()) not in _normalize_quotes(str(sentence).lower())
    return False


def count_error_correction_placeholders(items: list) -> int:
    """Count error-correction items that use placeholder syntax instead of real errors."""
    count = 0
    for item in items:
        sentence = get_field(item, 'sentence')
        error = get_field(item, 'error')
        answer = get_field(item, 'answer')
        if is_placeholder_error(sentence, error, answer):
            count += 1
    return count
