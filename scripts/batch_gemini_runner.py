#!/usr/bin/env python3
"""
Autonomous Gemini Batch Runner
Drives curriculum generation using Gemini CLI.

Modes:
  build - Run all phases, overwrite everything (default for new modules)
  fix   - Audit-driven: diagnose what's broken, fix only that
  auto  - If .md exists and >500 bytes, use fix mode; otherwise build
"""

import logging
import os
import shutil
import sys
import json
import yaml
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path
import re

# Ensure scripts/ is on sys.path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

from slug_utils import to_bare_slug, review_path as _review_path
from batch_gemini_config import (
    get_track_config, get_module_paths, get_module_index, slug_for_num,
    num_for_slug, PROJECT_ROOT,
)
from gemini_output import (
    extract_delimited, extract_yaml, has_any_end_marker,
    find_complete_pairs,
)
from batch_utils import (
    atomic_write, atomic_write_json, ExponentialBackoff,
    BatchLock, LockConflictError, classify_error, ErrorCategory,
)

# Constants
GEMINI_BIN = shutil.which("gemini") or "/opt/homebrew/bin/gemini"
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "audit_module.sh"
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
MAX_RETRIES = 3
MAX_FIX_ITERATIONS = 5
TIMEOUT_SECONDS = 900  # 15 minutes
FAILURES_DIR = PROJECT_ROOT / "batch_state" / "failures"
API_USAGE_DIR = PROJECT_ROOT / "batch_state" / "api_usage"
LOCK_DIR = PROJECT_ROOT / "batch_state" / "locks"

# Logging (configured by setup_logging, defaults to human-readable)
log = logging.getLogger("batch")


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


GEMINI_ACCOUNTS_FILE = Path.home() / ".gemini" / "google_accounts.json"

# Quota retry settings
QUOTA_RETRY_WAIT_SECONDS = 90
QUOTA_MAX_RETRIES = 2  # retries before switching account


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
            # Timeout — force acquire (stale lock from crashed process)
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

        log.info(f"  Switched Gemini account: {old_active} → {new_account}")
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
    - "### quiz (8+ items for B1)" — H3 for type definitions
    - "## Activity Type Reference" — H2 for sections
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
                # New header at same or higher level — stop skipping
                skipping = False

        if not skipping:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


class BatchRunner:
    def __init__(self, track, range_str=None, resume=False, from_idx=None,
                 mode="auto", max_consecutive_failures=3, max_failure_rate=0.5,
                 retry_failures=False):
        self.track = track
        self.config = get_track_config(track)
        self.range_str = range_str
        self.resume = resume
        self.from_idx = from_idx
        self.mode = mode
        self.retry_failures = retry_failures
        self.max_consecutive_failures = max_consecutive_failures
        self.max_failure_rate = max_failure_rate

        # State files go into a dedicated directory (not repo root)
        state_dir = PROJECT_ROOT / "batch_state"
        state_dir.mkdir(exist_ok=True)

        self.state_file = state_dir / f"state_{track}.json"
        self.checkpoint_file = state_dir / f"checkpoint_{track}.json"
        self.failure_queue_file = state_dir / "failure_queue.json"
        self.global_error_log = state_dir / f"errors_{track}.log"

        self.state = self._load_state()
        self.checkpoint = self._load_checkpoint()
        self._abort = False
        self._abort_reason = ""

    def _load_state(self):
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "batch": self.track,
            "range": self.range_str,
            "started": datetime.now().isoformat() + "Z",
            "current_module": None,
            "modules": {},
        }

    def _save_state(self):
        atomic_write_json(self.state_file, self.state)

    def _load_checkpoint(self):
        if self.checkpoint_file.exists() and self.resume:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"completed": [], "failed": []}

    def _save_checkpoint(self):
        atomic_write_json(self.checkpoint_file, self.checkpoint)

    def _log_failure(self, slug, phase, error, prompt_file, output_file):
        failure = {
            "module": slug,
            "slug": slug,
            "phase": phase,
            "retries": MAX_RETRIES,
            "last_error": str(error)[:500],
            "prompt_file": str(prompt_file),
            "output_file": str(output_file),
            "timestamp": datetime.now().isoformat() + "Z",
        }

        try:
            failures = []
            if self.failure_queue_file.exists():
                failures = json.loads(
                    self.failure_queue_file.read_text(encoding="utf-8")
                )

            # Avoid duplicates — replace existing entry for same slug+phase
            failures = [
                f for f in failures if not (f["slug"] == slug and f["phase"] == phase)
            ]
            failures.append(failure)

            atomic_write_json(self.failure_queue_file, failures)
        except (OSError, json.JSONDecodeError) as e:
            log.warning(f"Failed to write failure queue: {e}")

    def _get_modules_to_process(self):
        """Get modules from curriculum.yaml (the source of truth for ordering).

        Module N = levels.{track}.modules[N-1] in curriculum.yaml.
        --range: "39" = module 39, "1-10" = modules 1 through 10.
        --from: start from this module number.
        --retry-failures: only re-run modules with "fail" or "running" status in state.
        """
        try:
            idx = get_module_index(self.track)
        except ValueError as e:
            log.error(str(e))
            return []

        log.info(f"Track {self.track}: {idx['total']} modules in curriculum.yaml")

        # --retry-failures: scan state file for failed/stuck modules
        if self.retry_failures:
            modules_state = self.state.get("modules", {})
            retry_slugs = [
                slug for slug, info in modules_state.items()
                if info.get("status") in ("fail", "running")
            ]
            if not retry_slugs:
                log.info("No failed or stuck modules found in state. Nothing to retry.")
                return []
            # Sort by module number for consistent ordering
            slug_to_num = {v: k for k, v in idx["num_to_slug"].items()}
            retry_slugs.sort(key=lambda s: slug_to_num.get(s, 9999))
            log.info(f"Retrying {len(retry_slugs)} failed/stuck modules: {', '.join(retry_slugs)}")
            return retry_slugs

        # Determine which module numbers to process
        all_nums = list(range(1, idx["total"] + 1))

        if self.range_str:
            try:
                if "-" in self.range_str:
                    start, end = map(int, self.range_str.split("-"))
                    all_nums = [n for n in all_nums if start <= n <= end]
                else:
                    num = int(self.range_str)
                    if num not in idx["num_to_slug"]:
                        log.error(f"Module {num} not in {self.track} (range 1-{idx['total']})")
                        return []
                    all_nums = [num]
            except ValueError:
                log.error(f"Invalid range format: {self.range_str}")
                return []

        if self.from_idx is not None:
            all_nums = [n for n in all_nums if n >= self.from_idx]

        # Convert numbers to slugs
        all_plans = [idx["num_to_slug"][n] for n in all_nums]

        # Filter completed if resuming
        if self.resume:
            all_plans = [
                p for p in all_plans if p not in self.checkpoint["completed"]
            ]

        return all_plans

    def _read_file_safe(self, path):
        """Read a file, returning empty string if missing or unreadable."""
        if path and Path(path).exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except (OSError, UnicodeDecodeError) as e:
                log.warning(f"Failed to read {path}: {e}")
        return ""

    def _generate_prompt(self, phase, slug, paths, error_msg=None):
        """Build a prompt from template + module data."""
        template_path = self.config["templates"].get(phase)
        if not template_path:
            return None

        template = self._read_file_safe(template_path)

        # Load module data for inlining
        plan_content = self._read_file_safe(paths["plan"])
        research_content = self._read_file_safe(paths["research"])
        if not research_content:
            research_content = "(no research file available)"
        meta_content = self._read_file_safe(paths["meta"])
        quick_ref_content = self._read_file_safe(self.config.get("quick_ref"))
        content_content = self._read_file_safe(paths["md"])
        activities_content = self._read_file_safe(paths["activities"])
        vocabulary_content = self._read_file_safe(paths["vocabulary"])

        # Read activity schema reference
        schema_path = PROJECT_ROOT / "docs" / "ACTIVITY-YAML-REFERENCE.md"
        schema_content = self._read_file_safe(schema_path)

        # Read review file (needed by fix phase template)
        review_file = _review_path(paths["md"].parent, slug)
        review_content = self._read_file_safe(review_file)

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
            module_num = num_for_slug(self.track, slug)
        except ValueError:
            module_num = 0

        # Parse level from meta or derive from track
        level = self.track.upper()
        if paths["meta"].exists():
            try:
                meta_data = yaml.safe_load(meta_content)
                if isinstance(meta_data, dict):
                    level = meta_data.get("level", level)
            except yaml.YAMLError:
                pass

        # Activity/vocabulary count targets
        is_seminar = self.config.get("type") == "seminar"
        activity_count_target = "4-9" if is_seminar else "6-12"
        vocab_count_target = "15-25"

        # Resolve allowed/forbidden activity types from audit config
        from audit.config import LEVEL_CONFIG
        _TRACK_TO_CONFIG = {
            "c1-bio": "C1-biography",
            "c1-hist": "C1-history",
            "b2-hist": "B2-history",
            "lit": "LIT",
            "oes": "OES",
            "ruth": "RUTH",
        }
        config_key = _TRACK_TO_CONFIG.get(self.track, level)
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
            activity_examples = _get_seminar_activity_examples(self.track)
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
            "{OVERSHOOT_TARGET}": str(int(word_target * 1.5)),
            "{TOPIC_TITLE}": topic_title,
            "{TRACK}": self.track,
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

    def _resolve_mode_for_module(self, slug, paths):
        """Determine whether to build or fix a specific module.

        Returns "build" or "fix".
        """
        if self.mode == "build":
            return "build"
        if self.mode == "fix":
            return "fix"
        # auto mode: if .md exists and >500 bytes, use fix; otherwise build
        md_path = paths["md"]
        if md_path.exists() and md_path.stat().st_size > 500:
            return "fix"
        return "build"

    def run_batch(self):
        """Main entry point: process all modules in the batch."""
        try:
            with BatchLock(self.track, LOCK_DIR):
                self._run_batch_inner()
        except LockConflictError as e:
            log.error(f"Cannot start batch: {e}")
            return

    def _run_batch_inner(self):
        """Inner batch loop (called under lock)."""
        modules = self._get_modules_to_process()
        total = len(modules)
        log.info(f"Starting batch for {total} modules in {self.track} (mode={self.mode})")

        for i, slug in enumerate(modules):
            idx = i + 1
            if self.from_idx:
                idx += self.from_idx - 1

            paths = get_module_paths(self.track, slug)
            effective_mode = self._resolve_mode_for_module(slug, paths)

            log.info(f"[{idx}/{total}] Processing {slug} (mode={effective_mode})...")
            self.state["current_module"] = idx
            self.state["modules"][slug] = {
                "status": "running",
                "mode": effective_mode,
                "start_time": datetime.now().isoformat() + "Z",
            }
            self._save_state()

            if effective_mode == "fix":
                success = self.process_module_fix(slug)
            else:
                success = self.process_module(slug)

            duration = (
                datetime.now()
                - datetime.fromisoformat(
                    self.state["modules"][slug]["start_time"].replace("Z", "")
                )
            ).total_seconds()
            self.state["modules"][slug]["duration"] = duration
            self.state["modules"][slug]["end_time"] = (
                datetime.now().isoformat() + "Z"
            )

            if success:
                self.state["modules"][slug]["status"] = "pass"
                self.checkpoint["completed"].append(slug)
            else:
                self.state["modules"][slug]["status"] = "fail"
                self.checkpoint["failed"].append(slug)

            self._save_state()
            self._save_checkpoint()

            # --- Graceful abort (e.g., all accounts exhausted) ---
            if self._abort:
                log.error(f"ABORT: {self._abort_reason}")
                self.state["abort_reason"] = self._abort_reason
                self._save_state()
                break

            # --- Error rate abort checks ---
            if self._should_abort_batch(idx, total):
                break

        # Batch summary
        passed = len(self.checkpoint.get("completed", []))
        failed = len(self.checkpoint.get("failed", []))
        processed = passed + failed
        failure_rate = (failed / processed * 100) if processed > 0 else 0

        # Calculate average duration
        durations = [
            m.get("duration", 0) for m in self.state.get("modules", {}).values()
            if m.get("status") in ("pass", "fail") and m.get("duration")
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Save summary stats to state
        self.state["summary"] = {
            "passed": passed,
            "failed": failed,
            "processed": processed,
            "total": total,
            "failure_rate": round(failure_rate, 1),
            "avg_duration_s": round(avg_duration, 1),
            "total_duration_s": round(sum(durations), 1),
        }
        self._save_state()

        log.info(f"Batch complete. State: {self.state_file}")
        log.info(f"  Results: {passed} passed, {failed} failed out of {total} ({failure_rate:.1f}% failure rate)")
        log.info(f"  Avg duration: {avg_duration:.0f}s | Total: {sum(durations):.0f}s")
        if failed:
            failures_path = FAILURES_DIR / self.track
            log.info(f"  Failures saved to: {failures_path}")
            log.info(f"  Review with: .venv/bin/python scripts/batch_gemini_runner.py --failures {self.track}")

        self._generate_summary_report(passed, failed, total, durations)

    def _should_abort_batch(self, current_idx, total):
        """Check if batch should abort due to excessive failures."""
        completed = self.checkpoint.get("completed", [])
        failed = self.checkpoint.get("failed", [])
        processed = len(completed) + len(failed)

        if processed < 3:
            return False  # Need minimum sample size

        # Check consecutive failures
        if self.max_consecutive_failures > 0 and len(failed) >= self.max_consecutive_failures:
            # Look at the last N module results in order
            all_modules = list(self.state.get("modules", {}).items())
            recent = [m[1]["status"] for m in all_modules[-self.max_consecutive_failures:]]
            if all(s == "fail" for s in recent):
                log.error(
                    f"ABORT: {self.max_consecutive_failures} consecutive failures detected. "
                    f"Likely systemic issue. Processed {processed}/{total}."
                )
                self.state["abort_reason"] = f"{self.max_consecutive_failures} consecutive failures"
                self._save_state()
                return True

        # Check failure rate (only after 5+ modules to avoid early noise)
        if self.max_failure_rate > 0 and processed >= 5:
            rate = len(failed) / processed
            if rate > self.max_failure_rate:
                log.error(
                    f"ABORT: Failure rate {rate:.0%} exceeds threshold {self.max_failure_rate:.0%}. "
                    f"{len(failed)} failed out of {processed} processed."
                )
                self.state["abort_reason"] = f"Failure rate {rate:.0%} > {self.max_failure_rate:.0%}"
                self._save_state()
                return True

        return False

    def _generate_summary_report(self, passed, failed, total, durations):
        """Generate and save a JSON summary report for the batch run."""
        report_dir = PROJECT_ROOT / "batch_state"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"report_{self.track}_{timestamp}.json"

        # Find slowest modules
        module_durations = [
            (slug, info.get("duration", 0))
            for slug, info in self.state.get("modules", {}).items()
            if info.get("duration")
        ]
        module_durations.sort(key=lambda x: x[1], reverse=True)
        slowest_5 = [
            {"slug": slug, "duration_s": round(dur, 1)}
            for slug, dur in module_durations[:5]
        ]

        # Failed module list
        failed_modules = [
            slug for slug, info in self.state.get("modules", {}).items()
            if info.get("status") == "fail"
        ]

        processed = passed + failed
        report = {
            "track": self.track,
            "mode": self.mode,
            "timestamp": datetime.now().isoformat() + "Z",
            "results": {
                "passed": passed,
                "failed": failed,
                "processed": processed,
                "total": total,
                "pass_rate": round(passed / processed * 100, 1) if processed else 0,
            },
            "timing": {
                "total_s": round(sum(durations), 1) if durations else 0,
                "avg_s": round(sum(durations) / len(durations), 1) if durations else 0,
                "slowest_5": slowest_5,
            },
            "failed_modules": failed_modules,
            "abort_reason": self.state.get("abort_reason"),
        }

        atomic_write_json(report_file, report)
        log.info(f"  Summary report: {report_file}")

    def _handle_quota_error(self, slug, phase, stderr):
        """Handle 429/quota errors with wait-retry and account rotation.

        Returns True if we should retry (waited or switched account).
        Returns False if all accounts exhausted (caller should exit).
        """
        all_accounts = _get_all_gemini_accounts()
        current = _get_active_gemini_account()

        # First: try waiting (transient server overload) with exponential backoff
        backoff = ExponentialBackoff(
            base=QUOTA_RETRY_WAIT_SECONDS, max_wait=600, jitter=0.2
        )
        for attempt in range(1, QUOTA_MAX_RETRIES + 1):
            wait = backoff.wait_time(attempt)
            log.warning(
                f"  Quota/capacity error on {current}. "
                f"Waiting {wait:.0f}s before retry ({attempt}/{QUOTA_MAX_RETRIES})..."
            )
            time.sleep(wait)

            # Quick test: try a minimal gemini call to check if capacity is back
            test_result = subprocess.run(
                [GEMINI_BIN, "-p", "Say OK", "-o", "text"],
                capture_output=True, text=True, timeout=30,
            )
            if test_result.returncode == 0:
                log.info(f"  Capacity restored for {current}. Resuming.")
                return True

        # Waiting didn't help — try switching accounts
        log.warning(f"  Account {current} exhausted after {QUOTA_MAX_RETRIES} waits.")

        if len(all_accounts) <= 1:
            log.error("  No other accounts available. Saving checkpoint.")
            return False

        # Find next account in rotation
        try:
            current_idx = all_accounts.index(current)
        except ValueError:
            current_idx = -1

        tried_accounts = {current}
        for i in range(1, len(all_accounts)):
            next_idx = (current_idx + i) % len(all_accounts)
            next_account = all_accounts[next_idx]
            if next_account in tried_accounts:
                continue
            tried_accounts.add(next_account)

            log.info(f"  Trying account: {next_account}")
            if _switch_gemini_account(next_account):
                # Test the new account
                test_result = subprocess.run(
                    [GEMINI_BIN, "-p", "Say OK", "-o", "text"],
                    capture_output=True, text=True, timeout=30,
                )
                if test_result.returncode == 0:
                    log.info(f"  Account {next_account} works. Resuming batch.")
                    return True
                else:
                    log.warning(f"  Account {next_account} also failing.")

        log.error("  All accounts exhausted. Saving checkpoint and exiting.")
        return False

    def _delete_review_files(self, paths, slug):
        """Delete review files from both audit/ and review/ directories."""
        bare = to_bare_slug(slug)
        base_dir = paths["md"].parent
        deleted = False
        # Check both dirs during transition period
        for subdir in ("audit", "review"):
            rp = base_dir / subdir / f"{bare}-review.md"
            if rp.exists():
                rp.unlink()
                deleted = True
        return deleted

    def process_module(self, slug):
        """Run all phases for a single module (build mode)."""
        paths = get_module_paths(self.track, slug)
        orch_dir = paths["orchestration"]
        orch_dir.mkdir(parents=True, exist_ok=True)

        # In build mode, delete existing review upfront so audit doesn't fail
        # on a stale/fake review during content/activity phases.
        if 5 in self.config["phases"]:
            if self._delete_review_files(paths, slug):
                log.info("  Removing existing review (will be regenerated in phase 5)")

        for phase in self.config["phases"]:
            log.info(f"  Phase {phase}...")
            self.state["modules"][slug]["phase"] = phase
            self._save_state()

            success = self.run_phase(phase, slug, paths)
            if not success:
                return False
        return True

    def process_module_fix(self, slug):
        """Audit-driven fix loop for an existing module.

        1. Check required files exist
        2. Loop: audit -> diagnose -> act (fix_content / fix_activities / apply_fixes)
        3. Stall detection: if same gates fail for 3 consecutive iterations → break early
        4. Return True when all gates pass, False if exhausted
        """
        paths = get_module_paths(self.track, slug)
        orch_dir = paths["orchestration"]
        orch_dir.mkdir(parents=True, exist_ok=True)

        # Precondition checks
        if not paths["md"].exists():
            log.error(f"  Fix mode requires existing content. Missing: {paths['md']}")
            return False

        content = self._read_file_safe(paths["md"])
        word_count = len(content.split())
        if word_count < 200:
            log.error(f"  Content too thin for fix mode ({word_count} words). Use build mode.")
            return False

        if not paths["meta"].exists():
            log.error(f"  Fix mode requires meta file. Missing: {paths['meta']}")
            return False

        if not paths["plan"].exists():
            log.error(f"  Fix mode requires plan file. Missing: {paths['plan']}")
            return False

        fix_state = {
            "slug": slug,
            "iterations": [],
            "started": datetime.now().isoformat() + "Z",
        }
        review_regen_count = 0
        max_review_regens = 2
        # Stall detection: track failing gates across iterations
        previous_failing_gates = []
        stall_count = 0
        max_stall = 3

        for iteration in range(1, MAX_FIX_ITERATIONS + 1):
            log.info(f"  Fix iteration {iteration}/{MAX_FIX_ITERATIONS}")
            iter_state = {
                "iteration": iteration,
                "started": datetime.now().isoformat() + "Z",
            }

            # Step 1: Run audit
            audit_result = self._run_audit(paths["md"])
            iter_state["audit_passed"] = audit_result["passed"]

            # Step 2: Read status JSON for diagnosis
            status_data = self._read_status_json(paths, slug)
            if not status_data:
                log.warning("  Could not read status JSON after audit. Retrying audit...")
                continue

            # Step 3: Diagnose
            action = self._diagnose_module(status_data, paths, slug)
            iter_state["action"] = action
            log.info(f"  Diagnosis: {action}")

            # Stall detection: check if same gates keep failing
            current_failing = sorted([
                g for g in ("meta", "lesson", "activities", "vocabulary", "naturalness")
                if status_data.get("gates", {}).get(g, {}).get("status") == "fail"
            ])
            if current_failing == previous_failing_gates and current_failing:
                stall_count += 1
                if stall_count >= max_stall:
                    log.error(f"  STALL: Same gates {current_failing} failing for {stall_count} iterations. Breaking early.")
                    iter_state["result"] = "stall_detected"
                    fix_state["iterations"].append(iter_state)
                    break
            else:
                stall_count = 0
            previous_failing_gates = current_failing

            if action == "done":
                iter_state["result"] = "success"
                fix_state["iterations"].append(iter_state)
                fix_state["result"] = "success"
                self._save_fix_state(orch_dir, fix_state)
                log.info(f"  Module {slug} passes all gates.")
                return True

            elif action == "generate_fix_plan":
                # Generate review ONLY for its Fix Plan — review scores are ignored.
                review_regen_count += 1
                if review_regen_count > max_review_regens:
                    log.warning(f"  Fix plan generation exhausted ({review_regen_count}/{max_review_regens}).")
                    iter_state["result"] = "fix_plan_gen_exhausted"
                    fix_state["iterations"].append(iter_state)
                    self._save_fix_state(orch_dir, fix_state)
                    continue

                # Delete old review if present
                if self._delete_review_files(paths, slug):
                    log.info("  Deleting old review...")

                log.info(f"  Running phase 5 for Fix Plan only (attempt {review_regen_count}/{max_review_regens})...")
                success = self.run_phase(5, slug, paths)
                if not success:
                    iter_state["result"] = "phase5_failed"
                    fix_state["iterations"].append(iter_state)
                    self._save_fix_state(orch_dir, fix_state)
                    log.error("  Phase 5 (fix plan generation) failed.")
                    return False

                iter_state["result"] = "fix_plan_generated"
                log.info("  Fix Plan generated. Next iteration will apply fixes...")

            elif action == "fix_content":
                log.info("  Running content-only fix phase...")
                success = self.run_phase("fix-content", slug, paths)
                if not success:
                    iter_state["result"] = "fix_content_failed"
                    fix_state["iterations"].append(iter_state)
                    self._save_fix_state(orch_dir, fix_state)
                    log.error("  Content fix phase failed.")
                    # Don't return False — try again next iteration
                    continue

                iter_state["result"] = "content_fixed"
                if self._check_content_gates_pass(paths, slug):
                    iter_state["result"] = "success_after_content_fix"
                    fix_state["iterations"].append(iter_state)
                    fix_state["result"] = "success"
                    self._save_fix_state(orch_dir, fix_state)
                    log.info(f"  Module {slug} passes all content gates after content fix.")
                    return True

            elif action == "fix_activities":
                log.info("  Running activities-only fix phase...")
                # Pass audit errors so the template knows what to fix
                audit_errors = audit_result.get("errors", "")
                success = self.run_phase("fix-activities", slug, paths, error_msg=audit_errors)
                if not success:
                    iter_state["result"] = "fix_activities_failed"
                    fix_state["iterations"].append(iter_state)
                    self._save_fix_state(orch_dir, fix_state)
                    log.error("  Activities fix phase failed.")
                    continue

                iter_state["result"] = "activities_fixed"
                if self._check_content_gates_pass(paths, slug):
                    iter_state["result"] = "success_after_activities_fix"
                    fix_state["iterations"].append(iter_state)
                    fix_state["result"] = "success"
                    self._save_fix_state(orch_dir, fix_state)
                    log.info(f"  Module {slug} passes all content gates after activities fix.")
                    return True

            elif action == "apply_fixes":
                log.info("  Running combined fix phase (applying review Fix Plan)...")
                success = self.run_phase("fix", slug, paths)
                if not success:
                    iter_state["result"] = "fix_phase_failed"
                    fix_state["iterations"].append(iter_state)
                    self._save_fix_state(orch_dir, fix_state)
                    log.error("  Fix phase failed.")
                    return False

                iter_state["result"] = "fixes_applied"
                if self._check_content_gates_pass(paths, slug):
                    iter_state["result"] = "success_after_fix"
                    fix_state["iterations"].append(iter_state)
                    fix_state["result"] = "success"
                    self._save_fix_state(orch_dir, fix_state)
                    log.info(f"  Module {slug} passes all content gates after fix (review skipped — anti-gaming).")
                    return True

            fix_state["iterations"].append(iter_state)
            self._save_fix_state(orch_dir, fix_state)

        # Exhausted all iterations — save to failure queue for Claude review
        fix_state["result"] = "exhausted"
        self._save_fix_state(orch_dir, fix_state)
        self._save_failure(slug, fix_state, status_data)
        log.error(f"  Fix mode exhausted {MAX_FIX_ITERATIONS} iterations for {slug}.")
        return False

    def _check_content_gates_pass(self, paths, slug):
        """Check if all content gates pass (anti-gaming: ignore review gate)."""
        post_fix_status = self._read_status_json(paths, slug)
        if not post_fix_status:
            return False
        post_fix_gates = post_fix_status.get("gates", {})
        gates_ok = all(
            post_fix_gates.get(g, {}).get("status") != "fail"
            for g in ("meta", "lesson", "activities", "vocabulary", "naturalness")
        )
        post_blocking = post_fix_status.get("overall", {}).get("blocking_issues", [])
        post_content_blocking = [
            i for i in post_blocking
            if not any(kw in i.lower() for kw in ("review", "review validation"))
        ]
        return gates_ok and not post_content_blocking

    def _diagnose_module(self, status_data, paths, slug):
        """Analyze status JSON and decide what action to take.

        Returns one of: "done", "fix_content", "fix_activities", "apply_fixes",
                         "generate_fix_plan"

        ARCHITECTURAL RULE: Gemini NEVER reviews its own batch work.
        Self-review is inherently biased (self-grading produces inflated scores).
        The automated audit gates (meta, lesson, activities, vocabulary, naturalness)
        are the quality check in fix mode. When all content gates pass, the module
        is done — no LLM review needed. Reviews are only meaningful when done by
        a DIFFERENT agent (e.g., Claude reviewing Gemini's work via /review-content).
        """
        overall = status_data.get("overall", {})
        gates = status_data.get("gates", {})

        # Check if everything passes (including review if it exists)
        if overall.get("status") == "pass":
            return "done"

        # Check content gates only — review gate is IGNORED in fix mode
        failing_gates = []
        for gate_name in ("meta", "lesson", "activities", "vocabulary", "naturalness"):
            gate = gates.get(gate_name, {})
            if gate.get("status") == "fail":
                failing_gates.append(gate_name)

        # Also check blocking_issues (e.g., outline compliance errors)
        # These set has_critical_failure in audit but aren't captured in gates
        blocking_issues = overall.get("blocking_issues", [])
        # Filter out review-related blocking issues (anti-gaming)
        content_blocking = [
            issue for issue in blocking_issues
            if not any(kw in issue.lower() for kw in ("review", "review validation"))
        ]

        # All content gates pass AND no content blocking issues → done
        if not failing_gates and not content_blocking:
            log.info("  All content gates pass. Skipping self-review (anti-gaming).")
            return "done"

        if content_blocking:
            failing_gates.extend([f"blocking:{issue}" for issue in content_blocking])

        # Categorize failures for targeted fix routing
        content_failed = (
            "lesson" in failing_gates or
            "naturalness" in failing_gates or
            any(g.startswith("blocking:") for g in failing_gates)
        )
        activities_failed = "activities" in failing_gates or "vocabulary" in failing_gates

        # Route to targeted fix (split phases to avoid truncation)
        if content_failed:
            # Content issues — check if review has a Fix Plan for content
            rev_path = _review_path(paths["md"].parent, slug)
            review_exists = rev_path.exists()
            has_fix_plan = False
            if review_exists:
                review_content = self._read_file_safe(rev_path)
                has_fix_plan = "Fix Plan" in review_content or "fix plan" in review_content.lower()

            if review_exists and has_fix_plan:
                return "fix_content"

            # No Fix Plan — generate review to get one
            log.info(f"  Content gates failing: {failing_gates}. Generating review for Fix Plan...")
            return "generate_fix_plan"

        elif activities_failed:
            # Only activities/vocabulary failed — use targeted fix
            log.info(f"  Activity gates failing: {failing_gates}. Running targeted activity fix...")
            return "fix_activities"

        # Fallback: if only meta fails, try the combined fix
        if _review_path(paths["md"].parent, slug).exists():
            return "apply_fixes"

        log.info(f"  Gates failing: {failing_gates}. Generating review for Fix Plan...")
        return "generate_fix_plan"

    def _read_status_json(self, paths, slug):
        """Read the status JSON for a module."""
        # Status JSON uses the md stem (which may have numeric prefix)
        status_dir = paths["md"].parent / "status"
        status_file = status_dir / f"{paths['md'].stem}.json"
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                log.warning(f"  Failed to read status JSON: {e}")
        return None

    def _save_fix_state(self, orch_dir, fix_state):
        """Save fix tracking state to orchestration dir."""
        fix_state_file = orch_dir / "fix-state.json"
        atomic_write_json(fix_state_file, fix_state)

    def _save_failure(self, slug, fix_state, last_status):
        """Save failure details for Claude review.

        Creates batch_state/failures/{track}/{slug}.json with:
        - Which gates failed and why
        - What actions were tried
        - Last audit status
        - Enough context for Claude to diagnose the root cause
        """
        failures_dir = FAILURES_DIR / self.track
        failures_dir.mkdir(parents=True, exist_ok=True)

        # Extract failed gates from last status
        gates = last_status.get("gates", {})
        failed_gates = {
            name: info for name, info in gates.items()
            if isinstance(info, dict) and info.get("status") == "fail"
        }

        # Extract dryness flags from last status
        dryness_flags = last_status.get("dryness_flags", [])

        # Summarize iterations
        actions_tried = []
        for it in fix_state.get("iterations", []):
            actions_tried.append({
                "iteration": it.get("iteration"),
                "diagnosis": it.get("action"),
                "result": it.get("result"),
            })

        # Extract word count from lesson gate message (e.g. "4234/4300 (raw: 4337)")
        lesson_msg = gates.get("lesson", {}).get("message", "")
        word_count = {}
        wc_match = re.match(r"(\d+)/(\d+)", lesson_msg)
        if wc_match:
            word_count = {
                "actual": int(wc_match.group(1)),
                "target": int(wc_match.group(2)),
            }

        failure = {
            "track": self.track,
            "slug": slug,
            "timestamp": datetime.now().isoformat() + "Z",
            "iterations_used": len(fix_state.get("iterations", [])),
            "failed_gates": failed_gates,
            "dryness_flags": dryness_flags,
            "actions_tried": actions_tried,
            "blocking_issues": last_status.get("overall", {}).get("blocking_issues", []),
            "word_count": word_count,
        }

        failure_file = failures_dir / f"{slug}.json"
        atomic_write_json(failure_file, failure)
        log.info(f"  Failure saved: {failure_file}")

    def run_phase(self, phase, slug, paths, error_msg=None):
        """Run a single phase with retries."""
        orch_dir = paths["orchestration"]
        prompt_file = orch_dir / f"phase-{phase}-prompt.md"
        output_file = orch_dir / f"phase-{phase}-output.md"
        error_log = orch_dir / "errors.log"

        retry_count = 0
        # Keep error_msg from parameter (used by fix-activities to pass audit errors)

        while retry_count <= MAX_RETRIES:
            if retry_count > 0:
                log.info(f"    Retry {retry_count}/{MAX_RETRIES}...")
                self.state["modules"][slug]["retry"] = retry_count
                self._save_state()

            prompt_content = self._generate_prompt(phase, slug, paths, error_msg)
            if not prompt_content:
                log.warning(f"    No template for phase {phase}, skipping.")
                return True

            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(prompt_content)

            # Call Gemini with the prompt file content
            result = self._call_gemini(prompt_file, slug=slug, phase=phase, retry=retry_count)

            if result["returncode"] != 0:
                stderr = result["stderr"]
                category = classify_error(
                    result["returncode"], stderr,
                    result.get("elapsed_ms", 0), TIMEOUT_SECONDS * 1000,
                )

                if category == ErrorCategory.QUOTA:
                    resolved = self._handle_quota_error(slug, phase, stderr)
                    if resolved:
                        # Retry this phase with (potentially new) account
                        retry_count += 1
                        continue
                    else:
                        # All accounts exhausted — graceful abort
                        self._save_checkpoint()
                        self._abort = True
                        self._abort_reason = "All Gemini accounts exhausted"
                        return False

                if category == ErrorCategory.PERMANENT:
                    log.error(f"    Permanent error (no retry): {stderr[:300]}")
                    self._log_failure(slug, phase, stderr[:500], prompt_file, output_file)
                    return False

                error_msg = f"Gemini exit code {result['returncode']}.\nStderr: {stderr[:500]}"
                self._append_log(
                    error_log,
                    f"Phase {phase} Retry {retry_count} Gemini Error:\n{error_msg}",
                )
                self._append_log(
                    self.global_error_log,
                    f"[{slug}] Phase {phase} Gemini Error: {error_msg[:200]}",
                )
                retry_count += 1
                continue

            output = result["stdout"]

            # Truncation detection — check for end delimiters
            if not has_any_end_marker(output):
                # For fix phase: check if at least one complete section pair exists
                # (start AND end). If so, accept partial output and apply what we can.
                complete_pairs = find_complete_pairs(
                    output, ["CONTENT", "ACTIVITIES", "VOCABULARY", "CHANGES"]
                )

                if phase in ("fix", "fix-content", "fix-activities") and complete_pairs:
                    log.warning(f"    Partial output accepted: {', '.join(complete_pairs)} complete (others truncated).")
                else:
                    log.warning("    Output truncated (missing end delimiter).")
                    error_msg = "Your output was truncated (missing end delimiter). Please continue exactly where you left off, starting from the last complete sentence."
                    retry_count += 1
                    continue

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)

            # Apply output to actual curriculum files
            self._apply_output(phase, output, paths)

            # Validation: content/activity phases trigger audit
            if phase in self.config.get("validation_phases", []):
                audit_result = self._run_audit(paths["md"])
                if audit_result["passed"]:
                    log.info(f"    Phase {phase} passed audit.")
                    return True
                else:
                    error_msg = audit_result["errors"]
                    log.warning(f"    Phase {phase} failed audit.")
                    # Save audit report snapshot
                    review_file = _review_path(paths["md"].parent, slug)
                    if review_file.exists():
                        orch_review = (
                            orch_dir / f"phase-{phase}-audit-retry-{retry_count}.md"
                        )
                        with open(orch_review, "w", encoding="utf-8") as f:
                            f.write(self._read_file_safe(review_file))

                    self._append_log(
                        error_log,
                        f"Phase {phase} Retry {retry_count} Audit Failed:\n{error_msg[:1000]}",
                    )
                    self._append_log(
                        self.global_error_log,
                        f"[{slug}] Phase {phase} Audit Failed (Retry {retry_count})",
                    )
                    retry_count += 1
            elif phase in ("fix", "fix-content", "fix-activities"):
                # Fix phases: run audit to verify fixes worked
                audit_result = self._run_audit(paths["md"])
                if audit_result["passed"]:
                    log.info(f"    {phase} phase passed audit.")
                return True
            else:
                # Non-validation phases (research, review) pass through
                return True

        # All retries failed
        self._log_failure(slug, phase, error_msg, prompt_file, output_file)
        return False

    def _append_log(self, log_path, message):
        """Append a timestamped message to a log file."""
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] {message}\n")

    def _call_gemini(self, prompt_file, slug="unknown", phase="unknown", retry=0):
        """Call gemini-cli with the prompt file content. Returns parsed output + stats."""
        # Read the prompt file and pass content via -p
        prompt_content = prompt_file.read_text(encoding="utf-8")

        cmd = [GEMINI_BIN, "-p", prompt_content, "-o", "json"]
        start_time = time.monotonic()
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
                cwd=str(PROJECT_ROOT),
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            # Decode with error handling (Gemini output can be truncated mid-character)
            res.stdout = res.stdout.decode("utf-8", errors="replace") if isinstance(res.stdout, bytes) else res.stdout
            res.stderr = res.stderr.decode("utf-8", errors="replace") if isinstance(res.stderr, bytes) else res.stderr

            # Parse JSON output — extract response text and stats
            stdout_text = ""
            gemini_json = {}
            if res.returncode == 0 and res.stdout.strip():
                try:
                    gemini_json = json.loads(res.stdout)
                    stdout_text = gemini_json.get("response", "")
                    # Log API usage
                    _log_api_usage(self.track, slug, phase, retry, gemini_json, elapsed_ms)
                except json.JSONDecodeError:
                    # Fallback: treat as plain text (non-JSON mode)
                    stdout_text = res.stdout

            return {
                "returncode": res.returncode,
                "stdout": stdout_text,
                "stderr": res.stderr,
                "gemini_json": gemini_json,
                "elapsed_ms": elapsed_ms,
            }
        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Timeout expired ({TIMEOUT_SECONDS}s)",
                "gemini_json": {},
                "elapsed_ms": elapsed_ms,
            }

    def _apply_output(self, phase, output, paths):
        """Parse Gemini output and write to curriculum files."""
        if phase == 0:  # Research
            content = extract_delimited(output, "RESEARCH")
            if content:
                paths["research"].parent.mkdir(parents=True, exist_ok=True)
                with open(paths["research"], "w", encoding="utf-8") as f:
                    f.write(content)

        elif phase == 1:  # Meta
            content = extract_delimited(output, "META_OUTLINE")
            if content:
                meta_data = {}
                if paths["meta"].exists():
                    with open(paths["meta"], "r", encoding="utf-8") as f:
                        meta_data = yaml.safe_load(f) or {}

                try:
                    outline_data = yaml.safe_load(content)
                    meta_data.update(outline_data)
                    with open(paths["meta"], "w", encoding="utf-8") as f:
                        yaml.dump(
                            meta_data, f, allow_unicode=True, sort_keys=False
                        )
                except yaml.YAMLError as e:
                    log.error(f"Failed to parse meta YAML: {e}")

        elif phase == 2:  # Content
            content = extract_delimited(output, "CONTENT")
            if content:
                with open(paths["md"], "w", encoding="utf-8") as f:
                    f.write(content)

        elif phase == 3:  # Activities
            act_data = extract_yaml(output, "ACTIVITIES")
            if act_data is not None:
                paths["activities"].parent.mkdir(parents=True, exist_ok=True)
                with open(paths["activities"], "w", encoding="utf-8") as f:
                    yaml.dump(act_data, f, allow_unicode=True, sort_keys=False)
            elif extract_delimited(output, "ACTIVITIES") is not None:
                log.error("Failed to parse activities YAML")

            # Also check for vocabulary block
            vocab_data = extract_yaml(output, "VOCABULARY")
            if vocab_data is not None:
                paths["vocabulary"].parent.mkdir(parents=True, exist_ok=True)
                with open(paths["vocabulary"], "w", encoding="utf-8") as f:
                    yaml.dump(vocab_data, f, allow_unicode=True, sort_keys=False)
            elif extract_delimited(output, "VOCABULARY") is not None:
                log.error("Failed to parse vocabulary YAML")

        elif phase == 5:  # Review
            content = extract_delimited(output, "REVIEW")
            if content:
                rev_path = _review_path(paths["md"].parent, paths["md"].stem)
                rev_path.parent.mkdir(parents=True, exist_ok=True)
                with open(rev_path, "w", encoding="utf-8") as f:
                    f.write(content)

        elif phase in ("fix", "fix-content", "fix-activities"):
            self._apply_fix_output(phase, output, paths)

    def _apply_fix_output(self, phase, output, paths):
        """Apply fix phase output (shared logic for fix, fix-content, fix-activities)."""
        orch_dir = paths["orchestration"]

        # Content fixes (fix and fix-content phases)
        if phase in ("fix", "fix-content"):
            new_content = extract_delimited(output, "CONTENT")
            if new_content is not None:
                if len(new_content) >= 100:
                    with open(paths["md"], "w", encoding="utf-8") as f:
                        f.write(new_content)
                    log.info(f"    Applied content fixes.")
                else:
                    log.warning(f"    Content fix too short ({len(new_content)} chars), skipping.")

        # Activities fixes (fix and fix-activities phases)
        if phase in ("fix", "fix-activities"):
            act_content = extract_delimited(output, "ACTIVITIES")
            if act_content is not None:
                if len(act_content) >= 50:
                    try:
                        act_data = yaml.safe_load(act_content)
                        paths["activities"].parent.mkdir(parents=True, exist_ok=True)
                        with open(paths["activities"], "w", encoding="utf-8") as f:
                            yaml.dump(act_data, f, allow_unicode=True, sort_keys=False)
                        log.info(f"    Applied activities fixes.")
                    except yaml.YAMLError as e:
                        log.error(f"    Failed to parse fixed activities YAML: {e}")
                else:
                    log.warning(f"    Activities fix too short ({len(act_content)} chars), skipping.")

        # Vocabulary fixes (fix and fix-activities phases)
        if phase in ("fix", "fix-activities"):
            vocab_content = extract_delimited(output, "VOCABULARY")
            if vocab_content is not None:
                if len(vocab_content) >= 50:
                    try:
                        vocab_data = yaml.safe_load(vocab_content)
                        paths["vocabulary"].parent.mkdir(parents=True, exist_ok=True)
                        with open(paths["vocabulary"], "w", encoding="utf-8") as f:
                            yaml.dump(vocab_data, f, allow_unicode=True, sort_keys=False)
                        log.info(f"    Applied vocabulary fixes.")
                    except yaml.YAMLError as e:
                        log.error(f"    Failed to parse fixed vocabulary YAML: {e}")
                else:
                    log.warning(f"    Vocabulary fix too short ({len(vocab_content)} chars), skipping.")

        # Save changes report
        changes_content = extract_delimited(output, "CHANGES")
        if changes_content:
            suffix = {"fix": "fix", "fix-content": "fix-content", "fix-activities": "fix-activities"}
            changes_file = orch_dir / f"{suffix[phase]}-changes.md"
            with open(changes_file, "w", encoding="utf-8") as f:
                f.write(changes_content)

    def _run_audit(self, md_path):
        """Run audit_module.sh and check exit code."""
        cmd = [str(AUDIT_SCRIPT), str(md_path)]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,
                cwd=str(PROJECT_ROOT),
            )
            stdout = res.stdout.decode("utf-8", errors="replace") if isinstance(res.stdout, bytes) else res.stdout
            return {
                "passed": res.returncode == 0,
                "errors": stdout if res.returncode != 0 else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "errors": "Audit timed out after 120s",
            }


def show_failures(track):
    """Show failure queue for a track (or all tracks)."""
    if track == "all":
        tracks = sorted(d.name for d in FAILURES_DIR.iterdir() if d.is_dir()) if FAILURES_DIR.exists() else []
    else:
        tracks = [track]

    if not tracks:
        print("No failures found.")
        return

    # Group failures by reason
    by_reason = {}
    total = 0
    for t in tracks:
        track_dir = FAILURES_DIR / t
        if not track_dir.exists():
            continue
        for f in sorted(track_dir.glob("*.json")):
            data = json.loads(f.read_text())
            total += 1
            # Primary failure reason = first failed gate or first dryness flag
            failed_gates = list(data.get("failed_gates", {}).keys())
            dryness = data.get("dryness_flags", [])
            reason = failed_gates[0] if failed_gates else (dryness[0] if dryness else "unknown")
            by_reason.setdefault(reason, []).append({
                "track": t,
                "slug": data["slug"],
                "iterations": data.get("iterations_used", 0),
                "gates": failed_gates,
                "flags": dryness,
            })

    print(f"\n{'='*60}")
    print(f"Failure Queue: {total} modules across {len(tracks)} tracks")
    print(f"{'='*60}\n")

    for reason, modules in sorted(by_reason.items(), key=lambda x: -len(x[1])):
        print(f"  {reason} ({len(modules)} modules):")
        for m in modules[:10]:
            extra = f" gates={m['gates']}" if len(m['gates']) > 1 else ""
            extra += f" flags={m['flags']}" if m['flags'] else ""
            print(f"    {m['track']}/{m['slug']} ({m['iterations']} iters){extra}")
        if len(modules) > 10:
            print(f"    ... and {len(modules) - 10} more")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini Batch Runner")
    parser.add_argument("track", help="Track to process (e.g., c1-bio, all)")
    parser.add_argument("--range", help="Range of modules (e.g., 1-10 or 5)")
    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--from", dest="from_idx", type=int, help="Start from module index"
    )
    parser.add_argument(
        "--mode",
        choices=["build", "fix", "auto"],
        default="auto",
        help="Processing mode: build (all phases), fix (audit-driven), auto (detect per module)",
    )
    parser.add_argument(
        "--failures", action="store_true",
        help="Show failure queue instead of running batch",
    )
    parser.add_argument(
        "--max-consecutive-failures", type=int, default=3,
        help="Abort batch after N consecutive failures (0=disable, default=3)",
    )
    parser.add_argument(
        "--max-failure-rate", type=float, default=0.5,
        help="Abort batch if failure rate exceeds threshold (0=disable, default=0.5)",
    )
    parser.add_argument(
        "--retry-failures", action="store_true",
        help="Re-run only failed/stuck modules from the state file",
    )
    parser.add_argument(
        "--json-log", action="store_true",
        help="Use JSON structured logging instead of human-readable format",
    )

    args = parser.parse_args()
    setup_logging(json_mode=args.json_log)

    if args.failures:
        show_failures(args.track)
    else:
        runner = BatchRunner(
            args.track, args.range, args.resume, args.from_idx, args.mode,
            args.max_consecutive_failures, args.max_failure_rate,
            args.retry_failures,
        )
        runner.run_batch()
