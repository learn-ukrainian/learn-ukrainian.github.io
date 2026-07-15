#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def is_corrected_sentence(sentence: str, error_word: str, correct_form: str) -> bool:
    if not error_word or not correct_form:
        return False

    # Normalize space to be robust
    norm_sentence = " ".join(sentence.split())
    norm_error = " ".join(error_word.split())
    norm_correct = " ".join(correct_form.split())

    idx = norm_sentence.find(norm_error)
    if idx == -1:
        return False

    start = 0
    while True:
        idx = norm_sentence.find(norm_error, start)
        if idx == -1:
            break
        prefix = norm_sentence[:idx]
        suffix = norm_sentence[idx + len(norm_error):]
        if norm_correct.startswith(prefix) and norm_correct.endswith(suffix) and (len(prefix) > 0 or len(suffix) > 0):
            return True
        start = idx + 1

    return False


def is_defect(correct_form: str, sentence: str, error_word: str) -> bool:
    if not correct_form:
        return False
    cf = correct_form.strip()
    if cf in (".", "!", "?"):
        return False
    if cf.endswith(".") or cf.endswith("!") or cf.endswith("?"):
        return True
    return is_corrected_sentence(sentence, error_word, correct_form)


def dump_safe_json(data) -> str:
    """Canonical serialisation for JSX template literals."""
    s = json.dumps(data, ensure_ascii=False)
    s = s.replace("\\", "\\\\")
    s = s.replace("`", "\\`")
    s = s.replace("${", "\\${")
    return s


def parse_embeds_from_text(content: str) -> list[tuple[str, list[dict], str, int, int]]:
    pattern = r"(<ErrorCorrection\b[\s\S]*?items=\{+JSON\.parse\(`)([\s\S]*?)(`\)\}+[\s\S]*?/>)"
    matches = list(re.finditer(pattern, content))

    results = []
    for m in matches:
        prefix = m.group(1)
        json_str = m.group(2)
        suffix = m.group(3)

        cleaned = json_str.replace('\\"', '"').replace("\\`", "`").replace("\\\\", "\\")
        try:
            items = json.loads(cleaned)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            items = []
        results.append((prefix, items, suffix, m.start(), m.end()))
    return results


def get_base_content(rel_path: str) -> str:
    try:
        res = subprocess.run(
            ["git", "show", f"d3f4b29325:{rel_path}"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout
    except Exception as e:
        print(f"Error getting base content for {rel_path}: {e}")
        return ""


def main():
    docs_dir = PROJECT_ROOT / "site/src/content/docs"
    mdx_files = sorted(docs_dir.glob("**/*.mdx"))

    total_restored = 0
    total_migrated = 0
    total_non_defect = 0
    total_files_updated = 0

    manual_queue = []

    print(f"Reworking {len(mdx_files)} MDX files...")

    for file_path in mdx_files:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))

        # Read current content
        try:
            curr_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading current {rel_path}: {e}")
            continue

        # Get base content
        base_content = get_base_content(rel_path)
        if not base_content:
            continue

        base_embeds = parse_embeds_from_text(base_content)
        if not base_embeds:
            # If no embeds in base, make sure we revert to base if there are diffs (clean state)
            if curr_content != base_content:
                file_path.write_text(base_content, encoding="utf-8")
                total_files_updated += 1
            continue

        curr_embeds = parse_embeds_from_text(curr_content)
        if len(base_embeds) != len(curr_embeds):
            print(f"Warning: embed count mismatch in {rel_path}. Base: {len(base_embeds)}, Curr: {len(curr_embeds)}")
            # Fallback: parse curr embeds as best as we can or use empty list for current
            curr_embeds = curr_embeds + [("", [], "", 0, 0)] * (len(base_embeds) - len(curr_embeds))

        new_content = ""
        last_idx = 0

        for idx, base_embed in enumerate(base_embeds):
            base_prefix, items_base, base_suffix, base_start, base_end = base_embed
            _, items_curr, _, _, _ = curr_embeds[idx]

            items_new = []
            curr_idx_item = 0

            for _, base_item in enumerate(items_base):
                sentence = base_item.get("sentence", "")
                error_word = base_item.get("errorWord", "")
                correct_form = base_item.get("correctForm", "")

                if is_defect(correct_form, sentence, error_word):
                    # Check if it was migrated
                    match_found = False
                    for c_idx in range(curr_idx_item, len(items_curr)):
                        curr_item = items_curr[c_idx]
                        if curr_item.get("sentence") == sentence and curr_item.get("errorWord") == error_word:
                            # It was migrated! Keep the migrated version.
                            items_new.append(curr_item)
                            curr_idx_item = c_idx + 1
                            match_found = True
                            total_migrated += 1
                            break
                    if not match_found:
                        # Restore verbatim
                        items_new.append(base_item)
                        total_restored += 1
                else:
                    # Non-defect item, keep verbatim
                    items_new.append(base_item)
                    total_non_defect += 1
                    # Advance current index if it matches the current item
                    if curr_idx_item < len(items_curr):
                        curr_item = items_curr[curr_idx_item]
                        if curr_item.get("sentence") == sentence and curr_item.get("errorWord") == error_word:
                            curr_idx_item += 1

            # Add true defects in the reworked list to the manual queue
            for b_idx, item in enumerate(items_new):
                if is_defect(item.get("correctForm", ""), item.get("sentence", ""), item.get("errorWord", "")):
                    manual_queue.append({
                        "file": rel_path,
                        "item_index": b_idx,
                        "reason": "non_derivable_correct_form",
                        "item": item
                    })

            new_json_str = dump_safe_json(items_new)
            new_content += base_content[last_idx:base_start]
            new_content += f"{base_prefix}{new_json_str}{base_suffix}"
            last_idx = base_end

            # Assert counts are exactly matched
            assert len(items_new) == len(items_base), f"Parity count mismatch in {rel_path} embed {idx}"

        new_content += base_content[last_idx:]

        # Write back if changed
        if new_content != curr_content:
            file_path.write_text(new_content, encoding="utf-8")
            total_files_updated += 1

    # Write manual queue
    queue_output_file = PROJECT_ROOT / "audit/errorcorrection_manual_queue.json"
    queue_output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(queue_output_file, "w", encoding="utf-8") as mq_file:
        json.dump(manual_queue, mq_file, indent=2, ensure_ascii=False)

    print("\nRework Summary:")
    print(f"  Files scanned:              {len(mdx_files)}")
    print(f"  Files updated:              {total_files_updated}")
    print(f"  Total items processed:      {total_migrated + total_restored + total_non_defect}")
    print(f"  Items migrated:             {total_migrated}")
    print(f"  Items restored:             {total_restored}")
    print(f"  Non-defect items kept:      {total_non_defect}")
    print(f"  Queue size (unmigrated):    {len(manual_queue)}")
    print(f"  Queue saved to:             {queue_output_file.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
