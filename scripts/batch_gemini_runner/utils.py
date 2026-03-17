"""Utility functions for the batch Gemini runner.

Includes logging setup, Gemini account management, API usage tracking,
activity example generation, and schema filtering.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from batch_utils import atomic_write_json

from .constants import API_USAGE_DIR, log

# Gemini account config path
GEMINI_ACCOUNTS_FILE = Path.home() / ".gemini" / "google_accounts.json"


def setup_logging(json_mode: bool = False):
    """Configure logging format. Call before any log output."""
    if json_mode:
        fmt = '{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
    else:
        fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt="%H:%M:%S",
    )


def _get_active_gemini_account() -> str:
    """Read active Google account from gemini-cli config."""
    try:
        data = json.loads(GEMINI_ACCOUNTS_FILE.read_text(encoding="utf-8"))
        return data.get("active", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


def _get_all_gemini_accounts() -> list[str]:
    """Get all available Google accounts (active first, then old)."""
    try:
        data = json.loads(GEMINI_ACCOUNTS_FILE.read_text(encoding="utf-8"))
        active = data.get("active", "")
        old = data.get("old", [])
        accounts = [active] + [a for a in old if a != active]
        return [a for a in accounts if a]  # filter empty
    except (OSError, json.JSONDecodeError):
        return []


def _switch_gemini_account(new_account: str) -> bool:
    """Switch active Gemini account by updating the config file.

    Uses a lock file to prevent concurrent read-modify-write races when
    multiple batch runners for different tracks hit quota simultaneously.
    """
    lock_file = GEMINI_ACCOUNTS_FILE.with_suffix(".lock")
    fd = None
    try:
        # Acquire lock (spin with short sleep for up to 10s)
        for _ in range(100):
            try:
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
                break
            except FileExistsError:
                time.sleep(0.1)
        else:
            # Timeout -- force acquire (stale lock from crashed process)
            lock_file.unlink(missing_ok=True)
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)

        data = json.loads(GEMINI_ACCOUNTS_FILE.read_text(encoding="utf-8"))
        old_active = data.get("active", "")
        if old_active == new_account:
            return True  # Already active

        # Move old active to "old" list, set new active
        old_list = data.get("old", [])
        if old_active and old_active not in old_list:
            old_list.append(old_active)
        if new_account in old_list:
            old_list.remove(new_account)

        data["active"] = new_account
        data["old"] = old_list

        atomic_write_json(GEMINI_ACCOUNTS_FILE, data)

        log.info(f"  Switched Gemini account: {old_active} -> {new_account}")
        return True
    except (OSError, json.JSONDecodeError) as e:
        log.error(f"  Failed to switch account: {e}")
        return False
    finally:
        if fd is not None:
            os.close(fd)
        lock_file.unlink(missing_ok=True)


def _log_api_usage(track: str, slug: str, phase, retry: int, gemini_json: dict, elapsed_ms: int):
    """Log structured API usage from gemini-cli JSON output."""
    API_USAGE_DIR.mkdir(parents=True, exist_ok=True)

    stats = gemini_json.get("stats", {})
    models = stats.get("models", {})

    # Aggregate token counts across all models used
    total_input = 0
    total_output = 0
    total_cached = 0
    total_latency = 0
    model_names = []
    for model_name, model_data in models.items():
        model_names.append(model_name)
        tokens = model_data.get("tokens", {})
        total_input += tokens.get("input", 0) + tokens.get("prompt", 0)
        total_output += tokens.get("candidates", 0)
        total_cached += tokens.get("cached", 0)
        api_data = model_data.get("api", {})
        total_latency += api_data.get("totalLatencyMs", 0)

    entry = {
        "timestamp": datetime.now().isoformat() + "Z",
        "account": _get_active_gemini_account(),
        "track": track,
        "slug": slug,
        "phase": phase,
        "retry": retry,
        "models": model_names,
        "tokens": {
            "input": total_input,
            "output": total_output,
            "cached": total_cached,
            "total": total_input + total_output,
        },
        "latency_ms": total_latency,
        "elapsed_ms": elapsed_ms,
        "tools": stats.get("tools", {}).get("totalCalls", 0),
    }

    # Append to daily JSONL log (one JSON object per line)
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = API_USAGE_DIR / f"usage_{track}_{date_str}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        logging.getLogger("batch").warning(f"Failed to write API usage log: {e}")

    # Update running totals in summary file
    try:
        summary_file = API_USAGE_DIR / f"summary_{track}.json"
        summary = {}
        if summary_file.exists():
            try:
                summary = json.loads(summary_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                summary = {}

        summary.setdefault("track", track)
        summary["total_calls"] = summary.get("total_calls", 0) + 1
        summary["total_input_tokens"] = summary.get("total_input_tokens", 0) + total_input
        summary["total_output_tokens"] = summary.get("total_output_tokens", 0) + total_output
        summary["total_cached_tokens"] = summary.get("total_cached_tokens", 0) + total_cached
        summary["total_latency_ms"] = summary.get("total_latency_ms", 0) + total_latency
        summary["last_updated"] = datetime.now().isoformat() + "Z"

        # Per-account breakdown
        account = entry["account"]
        by_account = summary.setdefault("by_account", {})
        acct = by_account.setdefault(account, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
        acct["calls"] += 1
        acct["input_tokens"] += total_input
        acct["output_tokens"] += total_output

        atomic_write_json(summary_file, summary)
    except OSError as e:
        logging.getLogger("batch").warning(f"Failed to write API usage summary: {e}")


def _get_seminar_activity_examples(track: str) -> str:
    """Return YAML example block showing only allowed seminar activity types."""
    return """```
===ACTIVITIES_START===
- type: reading
  id: {slug}-reading-1
  title: "Читання першоджерела"
  text: "Lengthy primary source text in Ukrainian. This should be a substantial passage (200-500 words) that provides rich material for analysis. Include historical context, key arguments, and specific details that students can engage with critically..."
  questions:
    - question: "Яка основна ідея тексту?"
      answer: "Model answer explaining the main idea with evidence from the text..."
    - question: "Які аргументи наводить автор?"
      answer: "Model answer analyzing the author's arguments..."

- type: critical-analysis
  title: "Критичний аналіз"
  source_reading: "{slug}-reading-1"
  prompt: "Проаналізуйте, як автор використовує..."
  model_answer: "Detailed analysis in Ukrainian (150-300 words)..."
  rubric:
    - criteria: "Аргументація"
      description: "Логічність та обґрунтованість аргументів"
      points: 3
    - criteria: "Текстуальні докази"
      description: "Використання цитат з тексту"
      points: 2

- type: essay-response
  title: "Аналітичне есе"
  source_reading: "{slug}-reading-1"
  prompt: "Напишіть есе про значення..."
  model_answer: "Detailed model answer in Ukrainian (250-400 words)..."
  rubric:
    - criteria: "Тезисність"
      description: "Чіткість тези та висновків"
      points: 3
    - criteria: "Мовна якість"
      description: "Граматична правильність і стиль"
      points: 2

- type: comparative-study
  title: "Порівняльний аналіз"
  source_reading: "{slug}-reading-1"
  prompt: "Порівняйте два підходи до..."
  model_answer: "Detailed comparison in Ukrainian..."
  rubric:
    - criteria: "Порівняльні категорії"
      description: "Систематичність порівняння"
      points: 3
    - criteria: "Висновки"
      description: "Обґрунтованість підсумків"
      points: 2
===ACTIVITIES_END===

===VOCABULARY_START===
- term: "слово"
  translation: "word"
  ipa: "/ˈslɔwɔ/"
  pos: "noun"

# ... more vocabulary items
===VOCABULARY_END===
```"""


def _get_core_activity_examples() -> str:
    """Return YAML example block showing standard core activity types."""
    return """```
===ACTIVITIES_START===
- type: quiz
  title: "Перевірка знань"
  questions:
    - question: "Яке правильне закінчення?"
      options:
        - "варіант А"
        - "варіант Б"
        - "варіант В"
        - "варіант Г"
      correct: 0

- type: fill-in
  title: "Заповніть пропуски"
  items:
    - sentence: "Я ___ до магазину."
      answer: "іду"
      hint: "to go (present)"

- type: match-up
  title: "З'єднайте пари"
  pairs:
    - left: "слово"
      right: "word"

- type: mark-the-words
  title: "Визначте ключові терміни"
  text: "Гарний день приніс радість у серце."
  answers:
    - день
    - радість
    - серце

# ... more activities
===ACTIVITIES_END===

===VOCABULARY_START===
- term: "слово"
  translation: "word"
  ipa: "/ˈslɔwɔ/"
  pos: "noun"

# ... more vocabulary items
===VOCABULARY_END===
```"""


def _filter_schema_for_track(schema_content: str, allowed_types: set) -> str:
    """Filter activity schema to only include sections for allowed types.

    Reduces prompt token usage by stripping irrelevant type definitions.
    For core tracks (empty allowed_types set), returns full schema.

    The ACTIVITY-YAML-REFERENCE.md uses headers like:
    - "### quiz (8+ items for B1)" -- H3 for type definitions
    - "## Activity Type Reference" -- H2 for sections
    We detect type names at H3 level and filter those sections.
    """
    if not allowed_types or not schema_content:
        return schema_content

    # All known activity types for matching
    ALL_TYPES = {
        'quiz', 'fill-in', 'match-up', 'true-false', 'group-sort',
        'unjumble', 'error-correction', 'anagram', 'select',
        'translate', 'cloze', 'mark-the-words', 'reading',
        'essay-response', 'critical-analysis', 'comparative-study',
        'authorial-intent', 'creative-writing', 'transcription',
        'etymology-trace', 'grammar-identify', 'phonology-lab',
        'grammar-lab', 'parallel-text', 'paleography-analysis',
        'historical-writing', 'register-identify', 'loanword-trace',
        'comparative-style',
    }

    lines = schema_content.split('\n')
    filtered_lines = []
    skipping = False  # True when we're inside a forbidden type section
    skip_level = 0    # Header level that started the skip

    for line in lines:
        stripped = line.strip()

        # Detect headers
        if stripped.startswith('#'):
            # Count header level
            level = 0
            for ch in stripped:
                if ch == '#':
                    level += 1
                else:
                    break

            header_text = stripped[level:].strip().lower()

            # Check if this header starts a type-specific section
            found_type = None
            for atype in ALL_TYPES:
                # Match "quiz", "quiz (8+ items...)", "type: quiz", etc.
                if header_text.startswith(atype) or f'type: {atype}' in header_text:
                    found_type = atype
                    break

            if found_type:
                if found_type in allowed_types:
                    skipping = False
                else:
                    skipping = True
                    skip_level = level
            elif skipping and level <= skip_level:
                # New header at same or higher level -- stop skipping
                skipping = False

        if not skipping:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)
