"""Pipeline v5 fix helpers — snapshot, diff, FIND/REPLACE application.

Extracted from pipeline_v5.py — module file management, fix text cleaning,
FIND/REPLACE parsing and application, rollback support.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.core import ModuleContext, log

# ---------------------------------------------------------------------------
# Module file helpers
# ---------------------------------------------------------------------------

def _module_file_paths(ctx: ModuleContext) -> list[tuple[str, Path | None]]:
    """Return [(label, path)] for the three module files."""
    return [
        ("md", ctx.paths.get("md")),
        ("activities", ctx.paths.get("activities")),
        ("vocabulary", ctx.paths.get("vocabulary")),
    ]


def _snapshot_module_files(ctx: ModuleContext) -> dict[str, str]:
    """Snapshot content/activities/vocab before an edit pass."""
    snapshots = {}
    for label, p in _module_file_paths(ctx):
        if p and p.exists():
            snapshots[label] = p.read_text("utf-8")
    return snapshots


def _count_diff_lines(before: str, after: str) -> int:
    """Count the number of changed lines between two texts."""
    import difflib
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff = list(difflib.unified_diff(before_lines, after_lines, n=0))
    return sum(1 for line in diff if line.startswith(('+', '-'))
               and not line.startswith(('+++', '---')))


def _log_d1_edits(ctx: ModuleContext, pre_snapshots: dict[str, str]) -> None:
    """Log what D.1 changed via Edit tool by diffing pre/post snapshots."""
    import difflib

    any_changes = False
    diff_lines: list[str] = []

    for label, p in _module_file_paths(ctx):
        old = pre_snapshots.get(label, "")
        if not p or not p.exists():
            continue
        new = p.read_text("utf-8")
        if old == new:
            continue

        any_changes = True
        diff = list(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{label} (before D.1)",
            tofile=f"{label} (after D.1)",
            n=1,
        ))
        n_changed = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        log(f"  D.1 edit: {label} — {n_changed} line(s) changed")
        diff_lines.extend(diff)

    if any_changes:
        diff_path = ctx.orch_dir / "d1-edits.diff"
        diff_path.write_text("".join(diff_lines), "utf-8")
        log(f"  D.1 edit: Full diff saved → {diff_path.name}")
    else:
        log("  D.1 edit: No file changes detected (Edit tool not used or all edits reverted)")


def _apply_module_fixes(ctx: ModuleContext, raw_output: str) -> int:
    """Apply FIND/REPLACE fix pairs from LLM output to all module files."""
    if "===SECTION_FIX_START===" not in raw_output:
        return 0
    total = 0
    for _label, p in _module_file_paths(ctx):
        if p and p.exists():
            total += _apply_find_replace_fixes(p, raw_output)
    return total


def _apply_fixes_with_rollback(
    ctx: ModuleContext, raw_output: str, log_prefix: str,
) -> tuple[bool, int]:
    """Apply FIND/REPLACE fixes with diff-size guard and rollback."""
    if "===SECTION_FIX_START===" not in raw_output:
        return True, 0

    before = _snapshot_module_files(ctx)
    n_fixes = _apply_module_fixes(ctx, raw_output)

    fix_pair_count = raw_output.count("FIND:") if "FIND:" in raw_output else 1
    after = _snapshot_module_files(ctx)

    changed_lines = 0
    for label in before:
        if label in after:
            changed_lines += _count_diff_lines(before[label], after[label])

    max_allowed = max(fix_pair_count * 25, 50)

    if changed_lines > max_allowed:
        log(f"  {log_prefix}: REJECTED — {changed_lines} lines changed "
            f"(max {max_allowed} for {fix_pair_count} fix pairs)")
        for label, p in _module_file_paths(ctx):
            if label in before and p:
                p.write_text(before[label], "utf-8")
        return False, n_fixes

    log(f"  {log_prefix}: Fixes applied ({changed_lines} lines, {fix_pair_count} pairs)")
    return True, n_fixes


# ---------------------------------------------------------------------------
# Clean fix text + FIND/REPLACE parser
# ---------------------------------------------------------------------------

def _clean_fix_text(text: str) -> str:
    """Strip LLM formatting artifacts from FIND/REPLACE text."""
    lines = text.split("\n")
    cleaned: list[str] = []
    for line in lines:
        s = line.strip()
        if re.match(r'^Section:\s*["\u201c\u00ab]', s, re.IGNORECASE):
            continue
        if s.startswith("```"):
            continue
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    if result.startswith("«") and result.endswith("»"):
        result = result[1:-1]
    if result.startswith("\u201e") and result.endswith("\u201c"):
        result = result[1:-1]
    return result


def _apply_find_replace_fixes(file_path: Path, raw_output: str) -> int:
    """Apply FIND/REPLACE fix pairs from D.2 output to a file."""
    if not file_path.exists():
        return 0

    fix_matches = re.findall(
        r"===SECTION_FIX_START===\s*\n(.*?)===SECTION_FIX_END===",
        raw_output, re.DOTALL,
    )
    if not fix_matches:
        return 0

    fix_block = fix_matches[-1]

    current_file_active = True
    file_name = file_path.name
    pairs: list[tuple[str, str]] = []
    current_find: list[str] | None = None
    current_replace: list[str] | None = None
    mode = None

    for line in fix_block.split("\n"):
        stripped = line.strip()

        if stripped.startswith("FILE:"):
            file_ref = stripped[5:].strip()
            current_file_active = (
                file_name in file_ref
                or str(file_path) in file_ref
                or file_path.name == Path(file_ref).name
            )
            mode = None
            current_find = None
            current_replace = None
            continue

        if not current_file_active:
            continue

        if stripped == "---":
            if current_find is not None and current_replace is not None:
                pairs.append(("\n".join(current_find), "\n".join(current_replace)))
            current_find = None
            current_replace = None
            mode = None
            continue

        if stripped == "FIND:":
            current_find = []
            mode = "find"
            continue
        if stripped == "REPLACE:":
            current_replace = []
            mode = "replace"
            continue

        if mode == "find" and current_find is not None:
            current_find.append(line)
        elif mode == "replace" and current_replace is not None:
            current_replace.append(line)

    if current_find is not None and current_replace is not None:
        pairs.append(("\n".join(current_find), "\n".join(current_replace)))

    if not pairs:
        return 0

    content = file_path.read_text("utf-8")
    applied = 0
    skipped = []

    for i, (find_text, replace_text) in enumerate(pairs, 1):
        find_text = _clean_fix_text(find_text)
        replace_text = _clean_fix_text(replace_text)
        if not find_text or find_text == replace_text:
            skipped.append((i, "empty/identical", find_text[:60].replace('\n', ' ') if find_text else ""))
            continue

        if find_text in content:
            content = content.replace(find_text, replace_text, 1)
            applied += 1
            continue

        normalized_find = re.sub(r'\s+', ' ', find_text).strip()
        normalized_content = re.sub(r'\s+', ' ', content)
        if normalized_find in normalized_content:
            idx = normalized_content.index(normalized_find)
            char_count = 0
            orig_start = 0
            for i_ch, ch in enumerate(content):
                if char_count >= idx:
                    orig_start = i_ch
                    break
                if ch in (' ', '\t', '\n', '\r'):
                    if i_ch == 0 or content[i_ch-1] not in (' ', '\t', '\n', '\r'):
                        char_count += 1
                else:
                    char_count += 1
            end_count = 0
            orig_end = orig_start
            target_len = len(normalized_find)
            for i_ch in range(orig_start, len(content)):
                ch = content[i_ch]
                if ch in (' ', '\t', '\n', '\r'):
                    if i_ch == orig_start or content[i_ch-1] not in (' ', '\t', '\n', '\r'):
                        end_count += 1
                else:
                    end_count += 1
                if end_count >= target_len:
                    orig_end = i_ch + 1
                    break

            content = content[:orig_start] + replace_text + content[orig_end:]
            applied += 1
        else:
            find_preview = find_text[:60].replace('\n', ' ')
            skipped.append((i, "no match", find_preview))

    total_pairs = len(pairs)
    parts = [f"{applied}/{total_pairs} applied"]
    if skipped:
        parts.append(f"{len(skipped)} skipped")
    log(f"    FIND/REPLACE {file_path.name}: {', '.join(parts)}")
    for idx_s, reason, preview in skipped:
        log(f"      ⚠ #{idx_s} {reason}: {preview}...")
    if applied > 0:
        file_path.write_text(content, "utf-8")

    return applied
