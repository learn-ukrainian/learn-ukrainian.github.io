#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_mdx_embeds(file_path: Path) -> list[list[dict]]:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

    # Regex to match <ErrorCorrection ... items={JSON.parse(`...`)} ... />
    # Handles potential newlines and single/double curly braces around items prop
    pattern = r"<ErrorCorrection\b[\s\S]*?items=\{JSON\.parse\(`([\s\S]*?)`\)\}[\s\S]*?/>"
    matches = re.findall(pattern, content)

    parsed_activities = []
    for idx, match in enumerate(matches):
        # The JSON inside the backticks is javascript-escaped.
        # Key/value quotes are escaped like \"
        # We need to unescape them.
        try:
            # Unescape backslash-escaped quotes and other escapes
            # Simple replacement works for most cases
            cleaned = match.replace('\\"', '"')
            # Handle escaped backticks
            cleaned = cleaned.replace("\\`", "`")
            # Handle double-escaped backslashes
            cleaned = cleaned.replace("\\\\", "\\")

            activity_items = json.loads(cleaned)
            if not isinstance(activity_items, list):
                print(f"Warning: items in {file_path.name} embed {idx} is not a list")
                continue
            parsed_activities.append(activity_items)
        except Exception as e:
            print(f"Error parsing JSON in {file_path.name} embed {idx}: {e}")
            # Try a secondary more aggressive replacement
            try:
                # Replace literal \" with " and \\ with \
                cleaned = re.sub(r'\\"', '"', match)
                cleaned = re.sub(r"\\\\", "\\", cleaned)
                activity_items = json.loads(cleaned)
                parsed_activities.append(activity_items)
            except Exception as e2:
                print(f"Secondary parse attempt failed: {e2}")

    return parsed_activities


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


def run_scan(
    docs_dir: Path, output_file: Path | None = None
) -> tuple[dict, int, int]:
    mdx_files = sorted(docs_dir.glob("**/*.mdx"))

    total_files = len(mdx_files)
    flagged_files = {}
    total_activities = 0
    total_flagged_items = 0
    total_items = 0

    for file_path in mdx_files:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))
        activities = parse_mdx_embeds(file_path)
        if not activities:
            continue

        file_flagged_items = []
        for act_idx, act in enumerate(activities):
            total_activities += 1
            for item_idx, item in enumerate(act):
                total_items += 1
                correct_form = item.get("correctForm", "")
                error_word = item.get("errorWord", "")
                sentence = item.get("sentence", "")

                if is_defect(correct_form, sentence, error_word):
                    item_info = {
                        "activity_index": act_idx,
                        "item_index": item_idx,
                        "sentence": sentence,
                        "errorWord": error_word,
                        "correctForm": correct_form,
                        "options": item.get("options", []),
                        "explanation": item.get("explanation", ""),
                    }
                    file_flagged_items.append(item_info)
                    total_flagged_items += 1

        if file_flagged_items:
            flagged_files[rel_path] = file_flagged_items

    report = {
        "total_scanned_files": total_files,
        "total_flagged_files": len(flagged_files),
        "total_activities": total_activities,
        "total_items": total_items,
        "total_flagged_items": total_flagged_items,
        "flagged_files": flagged_files,
    }

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return report, total_files, len(flagged_files)



def main():
    parser = argparse.ArgumentParser(
        description="Scan MDX ErrorCorrection embeds for sentence-shaped correctForm values"
    )
    parser.add_argument("--dir", default="site/src/content/docs", help="Directory to scan")
    parser.add_argument("--output", default="audit/errorcorrection_baseline_report.json", help="Path to save report")
    args = parser.parse_args()

    docs_dir = PROJECT_ROOT / args.dir
    output_file = PROJECT_ROOT / args.output

    if not docs_dir.exists():
        print(f"Error: Directory {docs_dir} does not exist.")
        sys.exit(1)

    print(f"Scanning MDX files in {docs_dir}...")
    report, total_files, flagged_count = run_scan(docs_dir, output_file)

    print("\nScan Summary:")
    print(f"  Total MDX files scanned: {total_files}")
    print(f"  Total flagged files:     {flagged_count}")
    print(f"  Total activities:        {report['total_activities']}")
    print(f"  Total items checked:     {report['total_items']}")
    print(f"  Total flagged items:     {report['total_flagged_items']}")
    print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
