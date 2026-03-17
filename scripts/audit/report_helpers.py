"""
Helper data and utilities for audit report generation.

Contains dryness flag fix instructions and status cache serialization helpers.
"""

import json
from datetime import datetime
from pathlib import Path

# Mapping from dryness flag names to fix instructions
DRYNESS_FLAG_FIXES = {
    'NO_ENGAGEMENT': '''Add 2+ engagement boxes. Use this exact format:

> 💡 **Чи знали ви?**
>
> [Interesting fact about the grammar/vocabulary topic in Ukrainian]

> 🇺🇦 **Культурний момент**
>
> [Cultural context connecting grammar to Ukrainian life/places]

> 🌍 **У реальному житті**
>
> [Practical scenario where this grammar is used]''',

    'WALL_OF_TEXT': 'Break paragraphs > 500 words. Insert headers (##), bullet lists, or callout boxes every 200-300 words.',

    'REPETITIVE_STARTERS': 'Vary sentence starters. Instead of repeating "Доконаний вид...", use: "Коли...", "Якщо...", "Зверніть увагу:", "Порівняйте:", questions, examples.',

    'NO_DIALOGUE': '''Add 4+ mini-dialogues. The detector counts lines in blockquotes with bold speaker names.

Use ONE of these formats (blockquote is required for detection):

Format 1 — Bold speaker in blockquote (PREFERRED):
> **Студент:** Чому тут знахідний відмінок?
> **Викладач:** Бо дієслово «бачити» вимагає знахідного.
> **Студент:** А якщо це заперечення?
> **Викладач:** Тоді родовий: «не бачу **книжки**».

Format 2 — Em-dash in blockquote:
> — Чому тут знахідний?
> — Бо дієслово вимагає знахідного.

Format 3 — Plain А:/Б: speakers:
А: Чому тут знахідний?
Б: Бо дієслово вимагає знахідного.

IMPORTANT: Dialogues OUTSIDE blockquotes (>) using **Speaker:** format are NOT detected.
Place dialogues inside [!dialogue] callouts or blockquotes.''',

    'LOW_DIALOGUE': '''Add more mini-dialogues (need 4+ total). The detector counts lines in blockquotes with bold speaker names.

Use this format (blockquote required):
> **Студент:** Як правильно сказати?
> **Викладач:** Вживайте форму «збігатися», а не «співпадати».

Or em-dash format:
> — Як правильно сказати?
> — Вживайте «збігатися».

IMPORTANT: **Speaker:** lines NOT inside blockquotes (>) are ignored by the detector.''',

    'NO_EXAMPLES': 'Add 24+ example sentences. Each grammar point needs 3-4 examples showing the pattern in context.',

    'ABSTRACT_ONLY': '''Add 3+ real-world boxes. Use this exact format:

> 🌍 **У реальному житті**
>
> [Specific scenario: "На співбесіді...", "У магазині...", "На вокзалі..."]
> [Example sentence showing grammar in that context]''',

    'NO_COLLOCATIONS': 'Add 5+ collocations in format: **слово** + noun/verb (e.g., **важка** робота, **приймати** рішення)',

    'NO_REGISTER_NOTES': 'Add register notes: Mark words as (розм.) for colloquial, (офіц.) for formal, (книжн.) for literary.',

    'NO_PRIMARY_SOURCES': '''Add 2+ primary source quotes. Use this format:

> «[Exact quote from historical document]»
> — *[Source name], [year]*''',

    'NO_TIMELINE': 'Add 5+ timeline markers: specific years (1876, 1918), periods (XVIII ст.), sequences (спочатку... потім... нарешті).',

    'NO_DECOLONIZATION_PERSPECTIVE': 'Add Ukrainian perspective on historical events. Avoid Russocentric framing. Use Ukrainian names for cities/people.',

    'NO_QUOTES': '''Add 2+ direct quotes from the subject. Use this format:

> «[Exact quote from the person]»
> — *[Person name], [context/year]*''',

    'NO_LEGACY': 'Add a "Спадщина" or "Вплив" section discussing lasting influence on Ukrainian culture/literature/language.',

    'NO_ANALYSIS': '''Add 3+ analysis section headers. Use keywords in headers:

## 1. Аналіз [topic]: [subtitle]
## 2. Інтерпретація [aspect]: [subtitle]
## 3. Символіка [element]: [subtitle]''',

    'NO_LITERARY_CITATIONS': '''Add 3+ literary citations. Use this exact format:

«[Quote from the literary work, minimum 20 characters]»

Example: «Зібравши троянців в остатки / І швидше прийнявши присягу»''',

    'NO_RESOURCES': '''Add 2+ resource blocks. Use this format:

> [!resources] Додаткові ресурси
>
> - [Resource 1 with link or description]
> - [Resource 2 with link or description]''',

    'NO_EXEMPLAR_TEXTS': '''Add 2+ exemplar text excerpts. Use this format:

**Зразок [style type]:**

> «[Extended quote showing the style, 50+ words]»
> — *[Source]*''',

    'NO_REGISTER_ANALYSIS': 'Add 3+ register analysis notes explaining when to use formal vs informal, written vs spoken variants.',

    'NO_CULTURAL_ANCHOR': '''Add 3+ cultural references. Use this exact format:

> 🇺🇦 **Культурний момент**
>
> [Reference to Ukrainian place (Київ, Львів, Одеса, Карпати), tradition, or custom]
> [How it connects to the grammar/vocabulary being taught]
> [Example sentence using the grammar with cultural context]''',

    'LOW_CULTURAL_ANCHOR': '''Add more cultural references (need 3+ total). Include:
- Named Ukrainian places (Поділ, Бесарабський ринок, Острозька академія)
- Ukrainian traditions or customs
- Contemporary Ukrainian life examples''',

    'NO_PROVERBS': '''Add 1+ Ukrainian proverb. Use this format:

Українці кажу|ть: «[Proverb in Ukrainian]»

Зверніть увагу: **[word]** — [aspect] вид, бо [explanation why this aspect is used].

Example: «Не кажи гоп, поки не перескочиш» — **перескочиш** is perfective because it's about the result.''',
}


def serialize_gate(res) -> dict:
    """Serialize a GateResult or dict to a JSON-friendly status dict."""
    if not res:
        return {"status": "skipped", "violations": 0}

    status = "pass"
    if hasattr(res, 'status'):
        status = res.status.lower()
    elif isinstance(res, dict):
        status = res.get('status', 'pass').lower()

    # INFO status with "Deferred" in message = content-only audit deferral
    if status == 'info':
        raw_msg = ""
        if hasattr(res, 'msg'):
            raw_msg = res.msg
        elif isinstance(res, dict):
            raw_msg = res.get('msg', '')
        if 'Deferred' in raw_msg or 'content-only' in raw_msg.lower():
            status = 'deferred'

    msg = ""
    if hasattr(res, 'msg'):
        msg = res.msg
    elif isinstance(res, dict):
        msg = res.get('msg', '')

    violations = 1 if status == 'fail' else 0

    return {
        "status": status,
        "violations": violations,
        "message": msg
    }


def gather_source_mtimes(md_path: Path, module_slug: str) -> dict:
    """Collect modification times for all source files of a module."""
    base_path = md_path.parent

    paths = {
        'md': md_path,
        'meta': base_path / 'meta' / f"{module_slug}.yaml",
        'activities': base_path / 'activities' / f"{module_slug}.yaml",
        'vocabulary': base_path / 'vocabulary' / f"{module_slug}.yaml",
        'research': base_path / 'research' / f"{module_slug}-research.md",
    }

    # Plan path with bare-slug fallback
    track_dir_name = base_path.name
    plan_path = base_path.parent / 'plans' / track_dir_name / f"{module_slug}.yaml"
    if not plan_path.exists():
        from slug_utils import to_bare_slug
        bare = to_bare_slug(module_slug)
        alt_path = base_path.parent / 'plans' / track_dir_name / f"{bare}.yaml"
        if alt_path.exists():
            plan_path = alt_path
    paths['plan'] = plan_path

    source_mtimes = {}
    for key, p in paths.items():
        if p.exists():
            source_mtimes[key] = datetime.fromtimestamp(p.stat().st_mtime).isoformat() + "Z"
        else:
            source_mtimes[key] = None

    return source_mtimes


def build_gates_dict(results: dict) -> dict:
    """Build the gates dictionary from audit results for status cache."""
    gates = {}

    gates['meta'] = serialize_gate(results.get('structure'))
    lint_res = results.get('lint')
    if lint_res and lint_res.status == 'FAIL':
        gates['meta']['status'] = 'fail'
        gates['meta']['violations'] += 1
        gates['meta']['message'] += f" | Lint: {lint_res.msg}"

    gates['lesson'] = serialize_gate(results.get('words'))
    for k in ['engagement', 'audio', 'pedagogy', 'content_heavy', 'immersion', 'richness']:
        res = results.get(k)
        if res and hasattr(res, 'status') and res.status == 'FAIL':
            gates['lesson']['status'] = 'fail'
            gates['lesson']['violations'] += 1
            gates['lesson']['message'] += f" | {k}: {res.msg}"

    gates['activities'] = serialize_gate(results.get('activities'))
    for k in ['density', 'unique_types', 'priority', 'activity_quality']:
        res = results.get(k)
        if res and hasattr(res, 'status') and res.status == 'FAIL':
            gates['activities']['status'] = 'fail'
            gates['activities']['violations'] += 1
            gates['activities']['message'] += f" | {k}: {res.msg}"

    gates['vocabulary'] = serialize_gate(results.get('vocab'))
    gates['naturalness'] = serialize_gate(results.get('naturalness'))
    gates['research'] = serialize_gate(results.get('research'))

    return gates


def compute_overall_status(gates: dict, has_critical_failure: bool,
                           critical_failure_reasons: list[str]) -> dict:
    """Compute overall status from gate results."""
    pass_count = sum(1 for g in gates.values() if g['status'] == 'pass')
    fail_count = sum(1 for g in gates.values() if g['status'] == 'fail')
    deferred_count = sum(1 for g in gates.values() if g['status'] == 'deferred')

    if has_critical_failure or fail_count > 0:
        overall_status = "fail"
    elif deferred_count > 0:
        overall_status = "content-complete"
    else:
        overall_status = "pass"

    return {
        "status": overall_status,
        "blocking_issues": critical_failure_reasons,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "deferred_count": deferred_count,
    }


# Type-specific fix suggestions for low-density activities
LOW_DENSITY_SUGGESTIONS = {
    'fill-in': 'gap-fill sentences with [blank] placeholders',
    'match-up': 'matching pairs (Ukrainian \u2194 English)',
    'quiz': 'multiple-choice questions',
    'true-false': 'true/false statements',
    'unjumble': 'sentences to unscramble',
    'group-sort': 'items to sort into categories',
    'error-correction': 'sentences with errors to find',
    'cloze': 'blanks in the passage',
    'anagram': 'words to unscramble',
    'translate': 'translation items',
    'mark-the-words': 'words to mark in the text',
    'select': 'multi-select questions',
}


def sync_batch_state(base_path: Path, module_slug: str, status: str) -> None:
    """Update batch_state/state_{track}.json if it exists.

    Keeps the batch manager dashboard in sync when audits run outside batch.
    """
    try:
        from slug_utils import to_bare_slug
        track = base_path.name
        batch_state_file = base_path.parent.parent.parent / "batch_state" / f"state_{track}.json"
        if not batch_state_file.exists():
            return

        with open(batch_state_file, encoding='utf-8') as f:
            state = json.load(f)

        bare = to_bare_slug(module_slug)
        modules = state.get("modules", {})
        if bare in modules:
            modules[bare]["status"] = status
            with open(batch_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
    except Exception:
        pass  # Non-critical
