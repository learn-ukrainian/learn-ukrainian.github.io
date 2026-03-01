"""Fix stale sequence references in plan connects_to/prerequisites fields.

After the 44→64 A1 restructure (and similar restructures for other tracks),
many plans have connects_to/prerequisites that reference old sequence numbers.
E.g. "a1-26 (Adjectives)" when seq 26 is now "the-accusative-ii-people".

This script:
1. Builds slug↔seq maps from curriculum.yaml manifest
2. Builds title→slug maps from plan files themselves
3. For each reference like "track-NN (Description)":
   - Matches the description to a slug (via title, slug derivation, or fuzzy match)
   - Rewrites the reference with the correct sequence number
4. Fixes malformed YAML (colons in values that broke into dicts)

Usage:
  .venv/bin/python scripts/fix_plan_references.py --dry-run   # preview
  .venv/bin/python scripts/fix_plan_references.py             # fix in place
"""

import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import yaml


CURRICULUM_YAML = Path("curriculum/l2-uk-en/curriculum.yaml")
PLANS_ROOT = Path("curriculum/l2-uk-en/plans")


def _load_track_maps(manifest: dict) -> dict:
    """Build per-track lookup maps from manifest + plan files.

    Returns {track_id: {slug_to_seq, seq_to_slug, title_to_slug, desc_to_slug}}.
    """
    tracks = {}
    for track_id, track_data in manifest.get("levels", {}).items():
        modules = track_data.get("modules", [])
        slug_to_seq = {}
        for i, mod in enumerate(modules):
            slug = mod if isinstance(mod, str) else mod.get("slug", mod)
            slug_to_seq[slug] = i + 1
        seq_to_slug = {v: k for k, v in slug_to_seq.items()}

        # Build title→slug and description→slug from plan files
        title_to_slug = {}
        plan_dir = PLANS_ROOT / track_id
        if plan_dir.exists():
            for f in plan_dir.glob("*.yaml"):
                try:
                    p = yaml.safe_load(f.read_text())
                except Exception:
                    continue
                if not p or not isinstance(p, dict):
                    continue
                slug = p.get("slug", f.stem)
                if slug not in slug_to_seq:
                    continue
                title = p.get("title", "")
                if title:
                    title_to_slug[title.lower().strip()] = slug
                subtitle = p.get("subtitle", "")
                if subtitle:
                    title_to_slug[subtitle.lower().strip()] = slug

        tracks[track_id] = {
            "slug_to_seq": slug_to_seq,
            "seq_to_slug": seq_to_slug,
            "title_to_slug": title_to_slug,
        }
    return tracks


def _desc_to_slug_candidates(desc: str) -> list[str]:
    """Generate possible slug forms from a description string."""
    d = desc.lower().strip()
    candidates = []
    # Direct slug conversion
    slug = re.sub(r"[^a-z0-9\s-]", "", d)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    candidates.append(slug)
    # Without common prefixes like "Checkpoint: " or "Синтез: "
    for prefix in ["checkpoint:", "checkpoint -", "checkpoint", "синтез:", "синтез"]:
        if d.startswith(prefix):
            rest = d[len(prefix):].strip(" -")
            rest_slug = re.sub(r"[^a-z0-9\s-]", "", rest)
            rest_slug = re.sub(r"\s+", "-", rest_slug).strip("-")
            candidates.append("checkpoint-" + rest_slug)
            candidates.append(rest_slug)
    # Replace & with "and"
    if "&" in d:
        d2 = d.replace("&", "and")
        slug2 = re.sub(r"[^a-z0-9\s-]", "", d2)
        slug2 = re.sub(r"\s+", "-", slug2).strip("-")
        candidates.append(slug2)
    # Roman numerals: "I" → "i", "II" → "ii"
    candidates.append(slug.replace("-i-", "-i-").replace("-ii-", "-ii-"))
    return candidates


def _fuzzy_match_slug(desc: str, slug_to_seq: dict, title_to_slug: dict) -> str | None:
    """Try to match a description to a slug using multiple strategies."""
    desc_lower = desc.lower().strip()

    # Strategy 1: Exact title match
    if desc_lower in title_to_slug:
        return title_to_slug[desc_lower]

    # Strategy 2: Slug derivation
    for candidate in _desc_to_slug_candidates(desc):
        if candidate in slug_to_seq:
            return candidate

    # Strategy 3: Fuzzy match against titles (threshold 0.8 — high to avoid false positives)
    best_ratio = 0.0
    best_slug = None
    for title, slug in title_to_slug.items():
        ratio = SequenceMatcher(None, desc_lower, title).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_slug = slug
    if best_ratio >= 0.8:
        return best_slug

    # Strategy 4: Fuzzy match against slugs (threshold 0.7)
    desc_slug = re.sub(r"[^a-z0-9\s-]", "", desc_lower)
    desc_slug = re.sub(r"\s+", "-", desc_slug).strip("-")
    for slug in slug_to_seq:
        ratio = SequenceMatcher(None, desc_slug, slug).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_slug = slug
    if best_ratio >= 0.7:
        return best_slug

    return None


def _fix_malformed_refs(refs: list) -> list[str]:
    """Fix references that YAML parsed as dicts due to unquoted colons.

    E.g. {'a1-30 (Prepositions': 'Direction & Origin)'} → 'a1-30 (Prepositions: Direction & Origin)'
    """
    fixed = []
    for ref in refs:
        if isinstance(ref, dict):
            # Reconstruct the string from the dict
            parts = []
            for k, v in ref.items():
                parts.append(f"{k}: {v}")
            fixed.append(", ".join(parts))
        else:
            fixed.append(str(ref))
    return fixed


def _fix_reference(ref_str: str, track_id: str, track_maps: dict) -> str | None:
    """Fix a single reference string. Returns fixed string or None if no fix needed."""
    maps = track_maps.get(track_id)
    if not maps:
        return None

    slug_to_seq = maps["slug_to_seq"]
    seq_to_slug = maps["seq_to_slug"]
    title_to_slug = maps["title_to_slug"]

    # Match pattern: "track-NN (Description)"
    match = re.match(r"(\w[\w-]*?)-(\d+)\s*\((.+?)\)\s*$", ref_str)
    if not match:
        return None

    ref_track = match.group(1)
    ref_seq = int(match.group(2))
    ref_desc = match.group(3).strip()

    # Skip cross-track references — they connect different levels and
    # need manual review, not automated fuzzy matching
    if ref_track != track_id:
        return None

    target_track = ref_track
    target_maps = track_maps.get(target_track)
    if not target_maps:
        return None

    # Try to find the correct slug for this description
    matched_slug = _fuzzy_match_slug(ref_desc, target_maps["slug_to_seq"], target_maps["title_to_slug"])

    # If the matched slug is at the same seq → already correct
    if matched_slug:
        correct_seq = target_maps["slug_to_seq"].get(matched_slug)
        if correct_seq == ref_seq:
            return None  # Already correct

    # If the current seq points to a valid module, we need high confidence
    # that the description actually belongs to a DIFFERENT module before moving it.
    # Otherwise we'd "fix" a valid reference with a stale description into a wrong one.
    actual_slug_at_seq = target_maps["seq_to_slug"].get(ref_seq)
    if actual_slug_at_seq and matched_slug and matched_slug != actual_slug_at_seq:
        # Double-check: is the existing slug at this seq a plausible match for the description?
        # Compare against the plan title AND slug at the current seq.
        desc_lower = ref_desc.lower()
        desc_tokens = set(re.split(r"[\s:,—\-]+", desc_lower)) - {"", "і", "та", "of", "the", "and", "in"}

        # Check against slug words (handles English desc → English slug)
        slug_tokens = set(actual_slug_at_seq.split("-")) - {"", "i", "ii", "iii", "iv"}
        if desc_tokens & slug_tokens:
            return None  # Slug matches description

        # Check against plan title (handles Ukrainian desc → Ukrainian title)
        actual_plan = PLANS_ROOT / target_track / f"{actual_slug_at_seq}.yaml"
        if actual_plan.exists():
            try:
                ap = yaml.safe_load(actual_plan.read_text())
                actual_title = (ap.get("title", "") if ap else "").lower()
                title_tokens = set(re.split(r"[\s:,—\-]+", actual_title)) - {"", "і", "та"}
                if desc_tokens & title_tokens:
                    return None  # Title matches description
            except Exception:
                pass

    if not matched_slug:
        return None  # No match — leave as-is

    correct_seq = target_maps["slug_to_seq"].get(matched_slug)
    if not correct_seq or correct_seq == ref_seq:
        return None

    # Get the plan title for a clean description
    plan_file = PLANS_ROOT / target_track / f"{matched_slug}.yaml"
    new_desc = ref_desc  # default: keep original description
    if plan_file.exists():
        try:
            p = yaml.safe_load(plan_file.read_text())
            if p and isinstance(p, dict) and p.get("title"):
                new_desc = p["title"]
        except Exception:
            pass

    return f"{target_track}-{correct_seq:02d} ({new_desc})"


def fix_all_plans(dry_run: bool = True) -> dict:
    """Fix stale references in all plan files. Returns summary stats."""
    manifest = yaml.safe_load(CURRICULUM_YAML.read_text())
    track_maps = _load_track_maps(manifest)

    stats = {"files_scanned": 0, "files_modified": 0, "refs_fixed": 0, "refs_unfixed": 0, "malformed_fixed": 0}

    for track_id in sorted(manifest.get("levels", {}).keys()):
        plan_dir = PLANS_ROOT / track_id
        if not plan_dir.exists():
            continue

        for f in sorted(plan_dir.glob("*.yaml")):
            stats["files_scanned"] += 1
            try:
                raw = f.read_text()
                p = yaml.safe_load(raw)
            except Exception:
                continue
            if not p or not isinstance(p, dict):
                continue

            modified = False
            for field in ["connects_to", "prerequisites"]:
                refs = p.get(field)
                if not refs or not isinstance(refs, list):
                    continue

                # Step 1: Fix malformed refs (dicts from YAML colon issues)
                n_dicts = sum(1 for r in refs if isinstance(r, dict))
                if n_dicts:
                    if dry_run:
                        for r in refs:
                            if isinstance(r, dict):
                                print(f"  {track_id}/{f.stem} [{field}]: MALFORMED {r}")
                    refs = _fix_malformed_refs(refs)
                    p[field] = refs
                    stats["malformed_fixed"] += n_dicts
                    modified = True

                # Step 2: Fix stale sequence numbers
                new_refs = []
                for ref in refs:
                    if not isinstance(ref, str):
                        new_refs.append(ref)
                        continue
                    fixed = _fix_reference(ref, track_id, track_maps)
                    if fixed:
                        if dry_run:
                            print(f"  {track_id}/{f.stem} [{field}]: {ref}")
                            print(f"    → {fixed}")
                        new_refs.append(fixed)
                        stats["refs_fixed"] += 1
                        modified = True
                    else:
                        new_refs.append(ref)

                p[field] = new_refs

            if modified:
                stats["files_modified"] += 1
                if not dry_run:
                    # Write back with consistent YAML formatting
                    with open(f, "w") as fh:
                        yaml.dump(p, fh, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Fix stale sequence references in plan files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    print("Scanning all plan files for stale references...\n")
    stats = fix_all_plans(dry_run=args.dry_run)

    print(f"\n{'=== DRY RUN ===' if args.dry_run else '=== APPLIED ==='}")
    print(f"  Files scanned:    {stats['files_scanned']}")
    print(f"  Files modified:   {stats['files_modified']}")
    print(f"  Refs fixed:       {stats['refs_fixed']}")
    print(f"  Malformed fixed:  {stats['malformed_fixed']}")

    if args.dry_run and stats["refs_fixed"] > 0:
        print("\nRun without --dry-run to apply fixes.")


if __name__ == "__main__":
    main()
