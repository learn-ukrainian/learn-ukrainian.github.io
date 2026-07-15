#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_embeds_from_text(content: str) -> list[list[dict]]:
    pattern = r"<ErrorCorrection\b[\s\S]*?items=\{+JSON\.parse\(`([\s\S]*?)`\)\}+[\s\S]*?/>"
    matches = re.findall(pattern, content)

    results = []
    for idx, match in enumerate(matches):
        cleaned = match.replace('\\"', '"').replace("\\`", "`").replace("\\\\", "\\")
        try:
            items = json.loads(cleaned)
            results.append(items)
        except Exception as e:
            print(f"Error parsing JSON in embed {idx}: {e}")
            results.append([])
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

    mismatches = []
    total_embeds_checked = 0
    total_files_checked = 0

    for file_path in mdx_files:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))

        try:
            curr_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading current {rel_path}: {e}")
            continue

        base_content = get_base_content(rel_path)
        if not base_content:
            continue

        base_embeds = parse_embeds_from_text(base_content)
        curr_embeds = parse_embeds_from_text(curr_content)

        if not base_embeds and not curr_embeds:
            continue

        total_files_checked += 1

        if len(base_embeds) != len(curr_embeds):
            mismatches.append(f"{rel_path}: Embed count mismatch (Base: {len(base_embeds)}, Curr: {len(curr_embeds)})")
            continue

        for idx, (base_items, curr_items) in enumerate(zip(base_embeds, curr_embeds, strict=True)):
            total_embeds_checked += 1
            if len(base_items) != len(curr_items):
                mismatches.append(
                    f"{rel_path} embed {idx}: Item count mismatch (Base: {len(base_items)}, Curr: {len(curr_items)})"
                )

    if mismatches:
        print(f"\nAssertion FAILED: {len(mismatches)} mismatch(es) found:")
        for m in mismatches:
            print(f"  {m}")
        sys.exit(1)
    else:
        print("\nAssertion PASSED: All embed and item counts perfectly match base commit d3f4b29325!")
        print(f"  Files checked:  {total_files_checked}")
        print(f"  Embeds checked: {total_embeds_checked}")


if __name__ == "__main__":
    main()
