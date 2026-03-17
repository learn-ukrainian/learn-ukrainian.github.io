"""Reporting and failure display for the batch Gemini runner.

Includes show_failures for reviewing failed modules and summary report generation.
"""

import json

from .constants import FAILURES_DIR


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
