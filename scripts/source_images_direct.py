#!/usr/bin/env python3
"""Find textbook images for l2-uk-direct module items via RAG search.

Two-pass search:
  1. Local RAG: search textbook images via Qdrant (10K+ images)
  2. Pixabay fallback: search CC0 stock images for unmatched items

Takes a module YAML, searches Qdrant for each item with `image_url: null`,
and suggests best-matching textbook images with confidence scores.

Usage:
    # Show suggestions (dry run)
    .venv/bin/python scripts/source_images_direct.py curriculum/l2-uk-direct/a1/abetka-1.yaml

    # Auto-populate image_ref fields
    .venv/bin/python scripts/source_images_direct.py curriculum/l2-uk-direct/a1/abetka-1.yaml --apply

    # Filter by grade and minimum score
    .venv/bin/python scripts/source_images_direct.py curriculum/l2-uk-direct/a1/abetka-1.yaml --grade 1 --min-score 0.3

    # Process all modules in a directory
    .venv/bin/python scripts/source_images_direct.py curriculum/l2-uk-direct/a1/ --all

    # Skip Pixabay (RAG only)
    .venv/bin/python scripts/source_images_direct.py curriculum/l2-uk-direct/a1/ --all --skip-pixabay
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from rag.query import search_images

# ── Pixabay fallback ─────────────────────────────────────────────────────────
PIXABAY_API_URL = "https://pixabay.com/api/"
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

if not PIXABAY_API_KEY:
    _vibe_env = Path.home() / "projects/vibe/.env"
    if _vibe_env.exists():
        for _line in _vibe_env.read_text().splitlines():
            if _line.startswith("VITE_PIXABAY_API_KEY="):
                PIXABAY_API_KEY = _line.split("=", 1)[1].strip()
                break


def search_pixabay(query: str, per_page: int = 3) -> list[dict]:
    """Search Pixabay for CC0 images. Returns list of candidates."""
    if not PIXABAY_API_KEY:
        return []
    params = urllib.parse.urlencode({
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "per_page": per_page,
        "safesearch": "true",
        "lang": "uk",
    })
    try:
        req = urllib.request.Request(
            f"{PIXABAY_API_URL}?{params}",
            headers={"User-Agent": "learn-ukrainian/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return [
            {
                "source": "pixabay",
                "image_path": hit["webformatURL"],
                "preview": hit["previewURL"],
                "tags": hit["tags"],
                "page_url": hit["pageURL"],
                "score": 0.5,  # nominal score for Pixabay results
            }
            for hit in data.get("hits", [])
        ]
    except Exception as e:
        print(f"  Pixabay error for '{query}': {e}", file=sys.stderr)
        return []


def extract_search_items(module_data: dict) -> list[dict]:
    """Extract items that need images from a module YAML.

    Returns list of dicts with:
        - query: Ukrainian text to search for
        - path: dotted path in YAML for reporting (e.g., "letters[0]")
        - current_url: current image_url value (null if needs sourcing)
        - context: extra context about the item
    """
    items = []

    # Letters (abetka modules)
    for i, letter in enumerate(module_data.get("letters", [])):
        if letter.get("image_url") is not None:
            continue  # Already has an image
        key_word = letter.get("key_word", "")
        upper = letter.get("upper", "")
        if key_word:
            items.append({
                "query": key_word,
                "path": f"letters[{i}]",
                "current_url": letter.get("image_url"),
                "context": f"Letter {upper}/{letter.get('lower', '')} — key word: {key_word}",
            })

    # Vocabulary items
    for i, vocab in enumerate(module_data.get("vocabulary", [])):
        if vocab.get("image_url") is not None and vocab.get("image_ref") is not None:
            continue
        word = vocab.get("word", "") or vocab.get("term", "")
        if word:
            items.append({
                "query": word,
                "path": f"vocabulary[{i}]",
                "current_url": vocab.get("image_url"),
                "context": f"Vocabulary: {word}",
            })

    # Activities with image references
    for i, activity in enumerate(module_data.get("activities", [])):
        if activity.get("type") in ("classify", "image_to_letter"):
            for j, item in enumerate(activity.get("items", [])):
                if item.get("image_url") is not None and item.get("image_ref") is not None:
                    continue
                label = item.get("label", "") or item.get("word", "")
                if label:
                    items.append({
                        "query": label,
                        "path": f"activities[{i}].items[{j}]",
                        "current_url": item.get("image_url"),
                        "context": f"Activity '{activity.get('type', '')}' item: {label}",
                    })

    return items


def source_images_for_module(
    module_path: Path,
    grade: int | None = None,
    teaching_value: str | None = None,
    min_score: float = 0.2,
    limit: int = 3,
    apply: bool = False,
    skip_pixabay: bool = False,
) -> dict:
    """Find matching images for a module's null image_url fields.

    Returns summary dict with matched/unmatched counts and suggestions.
    """
    with open(module_path, "r", encoding="utf-8") as f:
        module_data = yaml.safe_load(f)

    if not module_data:
        print(f"  Empty or invalid YAML: {module_path}")
        return {"matched": 0, "unmatched": 0, "total": 0}

    items = extract_search_items(module_data)
    if not items:
        print(f"  No items need images in {module_path.name}")
        return {"matched": 0, "unmatched": 0, "total": 0}

    print(f"\n{'=' * 60}")
    print(f"Module: {module_path.name}")
    print(f"Items needing images: {len(items)}")
    print(f"{'=' * 60}")

    matched = 0
    unmatched = 0
    suggestions = []

    for item in items:
        hits = search_images(
            query=item["query"],
            grade=grade,
            teaching_value=teaching_value,
            limit=limit,
        )

        # Filter by minimum score
        good_hits = [h for h in hits if h["score"] >= min_score]

        print(f"\n  {item['context']}")
        print(f"  Search: \"{item['query']}\"")

        if good_hits:
            matched += 1
            best = good_hits[0]
            print(f"  -> MATCH (score: {best['score']:.4f})")
            print(f"     Path: {best['image_path']}")
            if best.get("description_uk"):
                print(f"     Desc: {best['description_uk']}")
            if best.get("associated_text_uk"):
                print(f"     Text: {best['associated_text_uk']}")
            if best.get("teaching_value"):
                print(f"     Value: {best['teaching_value']}")

            if len(good_hits) > 1:
                print(f"     + {len(good_hits) - 1} more candidates")

            suggestions.append({
                "path": item["path"],
                "query": item["query"],
                "best_match": {
                    "image_path": best["image_path"],
                    "image_id": best["image_id"],
                    "score": best["score"],
                    "description_uk": best.get("description_uk"),
                    "associated_text_uk": best.get("associated_text_uk"),
                },
                "alternatives": [
                    {"image_path": h["image_path"], "score": h["score"]}
                    for h in good_hits[1:]
                ],
            })
        else:
            # Pixabay fallback
            if not skip_pixabay and PIXABAY_API_KEY:
                pixabay_hits = search_pixabay(item["query"])
                time.sleep(0.7)  # Rate limit: 100 req/min
                if pixabay_hits:
                    best_px = pixabay_hits[0]
                    matched += 1
                    print(f"  -> PIXABAY MATCH")
                    print(f"     URL: {best_px['image_path']}")
                    print(f"     Tags: {best_px['tags']}")
                    if len(pixabay_hits) > 1:
                        print(f"     + {len(pixabay_hits) - 1} more candidates")
                    suggestions.append({
                        "path": item["path"],
                        "query": item["query"],
                        "best_match": {
                            "source": "pixabay",
                            "image_path": best_px["image_path"],
                            "image_id": best_px.get("page_url", ""),
                            "score": best_px["score"],
                            "description_uk": best_px.get("tags"),
                        },
                        "alternatives": [
                            {"image_path": h["image_path"], "score": h["score"], "source": "pixabay"}
                            for h in pixabay_hits[1:]
                        ],
                    })
                    continue

            unmatched += 1
            print(f"  -> NO MATCH (best score: {hits[0]['score']:.4f})" if hits else "  -> NO RESULTS")

    total = matched + unmatched
    print(f"\n{'─' * 40}")
    print(f"Results: {matched}/{total} matched (min_score={min_score})")

    if apply and suggestions:
        _apply_suggestions(module_path, module_data, suggestions)

    return {"matched": matched, "unmatched": unmatched, "total": total, "suggestions": suggestions}


def _apply_suggestions(module_path: Path, module_data: dict, suggestions: list[dict]):
    """Apply image suggestions by setting image_ref in the YAML."""
    changes = 0
    for suggestion in suggestions:
        path = suggestion["path"]
        best = suggestion["best_match"]

        # Navigate to the item in module_data
        obj = module_data
        parts = _parse_path(path)
        for part in parts[:-1]:
            if isinstance(part, int):
                obj = obj[part]
            else:
                obj = obj[part]

        last = parts[-1]
        if isinstance(last, int):
            target = obj[last]
        else:
            target = obj[last]

        # Set image_ref (relative path from project root)
        target["image_ref"] = best["image_path"]
        changes += 1

    if changes:
        with open(module_path, "w", encoding="utf-8") as f:
            yaml.dump(module_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"\n  Applied {changes} image references to {module_path.name}")


def _parse_path(path: str) -> list[str | int]:
    """Parse a dotted path like 'letters[0]' into ['letters', 0]."""
    import re
    parts = []
    for segment in path.split("."):
        m = re.match(r"(\w+)\[(\d+)\]", segment)
        if m:
            parts.append(m.group(1))
            parts.append(int(m.group(2)))
        else:
            parts.append(segment)
    return parts


def main():
    parser = argparse.ArgumentParser(
        description="Find textbook images for l2-uk-direct modules via RAG"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Module YAML file or directory (with --all)",
    )
    parser.add_argument("--all", action="store_true", help="Process all YAML files in directory")
    parser.add_argument("--grade", type=int, help="Filter images by grade")
    parser.add_argument("--teaching-value", type=str, choices=["high", "medium", "low"],
                        help="Filter by teaching value")
    parser.add_argument("--min-score", type=float, default=0.2, help="Minimum similarity score (default: 0.2)")
    parser.add_argument("--limit", type=int, default=3, help="Max candidates per item (default: 3)")
    parser.add_argument("--apply", action="store_true", help="Auto-populate image_ref in YAML files")
    parser.add_argument("--skip-pixabay", action="store_true", help="Skip Pixabay fallback (RAG only)")

    args = parser.parse_args()
    target = Path(args.path)

    if args.all and target.is_dir():
        yaml_files = sorted(target.glob("*.yaml"))
        if not yaml_files:
            print(f"No YAML files found in {target}")
            sys.exit(1)
    elif target.is_file():
        yaml_files = [target]
    else:
        print(f"Path not found: {target}")
        sys.exit(1)

    total_matched = 0
    total_unmatched = 0

    for yaml_file in yaml_files:
        if yaml_file.name == "manifest.yaml":
            continue
        result = source_images_for_module(
            yaml_file,
            grade=args.grade,
            teaching_value=args.teaching_value,
            min_score=args.min_score,
            limit=args.limit,
            apply=args.apply,
            skip_pixabay=args.skip_pixabay,
        )
        total_matched += result["matched"]
        total_unmatched += result["unmatched"]

    if len(yaml_files) > 1:
        total = total_matched + total_unmatched
        print(f"\n{'=' * 60}")
        print(f"TOTAL: {total_matched}/{total} items matched across {len(yaml_files)} modules")


if __name__ == "__main__":
    main()
