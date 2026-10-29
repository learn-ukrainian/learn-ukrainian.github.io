"""Run the ordered Method 1 audit using existing V7 and fresh structural rules."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.build.activity_renderer import (
    order_correct_indices,
    quiz_correct_indices,
    unjumble_tokens,
)
from scripts.build.activity_validator import _check_match_up
from scripts.build.fresh.draft_schema import _alias_conflicts
from scripts.build.fresh.runner import _normal_letters, _structural_activity_error
from scripts.verification.vesum import verify_words

TOKEN = re.compile(r"[А-Яа-яІіЇїЄєҐґ]+(?:['’ʼ`][А-Яа-яІіЇїЄєҐґ]+)*")
COMPONENTS = re.compile(
    r"<(Quiz|FillIn|Translate|TrueFalse|MatchUp|GroupSort|Order|Unjumble|ErrorCorrection|CountSyllables|DivideWords|OddOneOut|WatchAndRepeat)\b(.*?)/>",
    re.S,
)
JSON_PROP = re.compile(r"(\w+)=\{JSON\.parse\(`((?:\\.|[^`])*)`\)\}")


def rendered_audit(mods: list[str]) -> list[dict]:
    """Inspect the tracked learner payloads after parser coercions and deduplication."""
    result = []
    for slug in mods:
        page = ROOT / f"site/src/content/docs/a1-v1/{slug}.mdx"
        text = page.read_text()
        for ai, (kind, body) in enumerate(COMPONENTS.findall(text)):
            props = {
                name: json.loads(re.sub(r"\\(.)", r"\1", raw, flags=re.S)) for name, raw in JSON_PROP.findall(body)
            }
            items = props.get("items", props.get("questions", props.get("pairs", [])))
            if kind == "GroupSort":
                items = [item for entries in props["groups"].values() for item in entries]
            if not items:
                raise ValueError(f"{slug}/rendered/{ai}: no item payload")
            for ii, item in enumerate(items):
                problems = []
                value = item if isinstance(item, dict) else {}
                try:
                    if kind in {"Quiz", "Translate"}:
                        quiz_correct_indices(value)
                    elif kind == "FillIn":
                        if not value.get("options"):
                            problems.append("empty options; reserved for dropdown gap")
                        elif value["options"].count(value["answer"]) != 1:
                            problems.append("rendered fill-in key missing or repeated")
                    elif kind == "TrueFalse" and type(value.get("isTrue")) is not bool:
                        problems.append("rendered truth key is not boolean")
                    elif kind == "MatchUp":
                        problems.extend(f.message for f in _check_match_up(slug, "rendered", items))
                    elif kind == "Order":
                        indices = order_correct_indices(items, props["correct_order"])
                        error = _structural_activity_error({"items": items, "correct_order": indices}, "order", {})
                        if error:
                            problems.append(error)
                    elif kind == "Unjumble":
                        error = _structural_activity_error(
                            {"items": [{"words": unjumble_tokens(value), "answer": value["answer"]}]}, "unjumble", {}
                        )
                        if error:
                            problems.append(error)
                    elif kind in {"CountSyllables", "DivideWords"}:
                        adapted = {k: v.replace("\u0301", "") if isinstance(v, str) else v for k, v in value.items()}
                        typ = "count-syllables" if kind == "CountSyllables" else "divide-words"
                        if typ == "divide-words":
                            adapted["answer"] = "-".join(adapted["answer"].split())
                        error = _structural_activity_error({"items": [adapted]}, typ, {})
                        if error:
                            problems.append(error)
                    elif kind == "ErrorCorrection":
                        error = value.get("errorWord")
                        if error and error not in value["sentence"]:
                            problems.append("rendered error span absent from sentence")
                        if value.get("options") and value.get("correctForm") not in value["options"]:
                            problems.append("rendered correction key absent from choices")
                    elif kind == "OddOneOut":
                        quiz_correct_indices({**value, "options": value["words"]})
                except (KeyError, TypeError, ValueError) as exc:
                    problems.append(str(exc))
                candidates = value.get("options", value.get("words", []))
                if kind == "MatchUp":
                    candidates = [value["left"], value["right"]]
                elif kind in {"GroupSort", "Order"}:
                    candidates = [item]
                elif kind == "Unjumble":
                    candidates = unjumble_tokens(value)
                elif kind in {"CountSyllables", "DivideWords", "WatchAndRepeat"}:
                    candidates = [value.get("word", "")]
                option_tokens = []
                for oi, opt in enumerate(candidates):
                    candidate = opt.get("text", "") if isinstance(opt, dict) else str(opt)
                    tokens = [
                        t.replace("’", "'").replace("ʼ", "'").replace("`", "'").casefold()
                        for t in TOKEN.findall(candidate.replace("\u0301", ""))
                    ]
                    option_tokens.append({"index": oi, "text": candidate, "tokens": tokens})
                result.append(
                    {
                        "location": f"{slug}/rendered/{ai}/{ii}",
                        "component": kind,
                        "status": "FLAG" if problems else "PASS",
                        "problems": problems,
                        "option_tokens": option_tokens,
                    }
                )
    return result


def audit() -> dict:
    mods = yaml.safe_load((ROOT / "curriculum/l2-uk-en/curriculum.yaml").read_text())["levels"]["a1-v1"]["modules"]
    assert len(mods) == 55
    rows = []
    words = {}
    activities = []

    def add_check(row, name, error=None):
        row["checks"][name] = {"status": "FLAG" if error else "PASS", "detail": error}

    for pos, slug in enumerate(mods, 1):
        path = ROOT / f"curriculum/l2-uk-en/a1-v1/{slug}/activities.yaml"
        data = yaml.safe_load(path.read_text())
        sections = [("root", data)] if isinstance(data, list) else data.items()
        for section, acts in sections:
            if not isinstance(acts, list):
                continue
            for ai, act in enumerate(acts):
                typ = act["type"]
                ident = act.get("id", f"{section}-{ai}")
                activities.append({"module": pos, "slug": slug, "section": section, "activity": ident, "type": typ})
                if typ == "group-sort":
                    units = [
                        (f"groups/{gi}/items/{ii}", value)
                        for gi, g in enumerate(act["groups"])
                        for ii, value in enumerate(g["items"])
                    ]
                elif typ == "match-up":
                    units = [(f"pairs/{i}", value) for i, value in enumerate(act["pairs"])]
                else:
                    units = [(f"items/{i}", value) for i, value in enumerate(act.get("items", []))]
                if not units:
                    raise ValueError(f"{slug}/{ident}: zero units")
                order_error = None
                if typ == "order":
                    try:
                        order = order_correct_indices(act["items"], act["correct_order"])
                        order_error = _structural_activity_error(
                            {"items": act["items"], "correct_order": order}, "order", {}
                        )
                    except (ValueError, TypeError, KeyError) as exc:
                        order_error = str(exc)
                for unit, item in units:
                    loc = f"{slug}/{section}/{ident}/{unit}"
                    row = {
                        "module": pos,
                        "slug": slug,
                        "section": section,
                        "activity": ident,
                        "type": typ,
                        "unit": unit,
                        "location": loc,
                        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "checks": {
                            k: {"status": "N/A"}
                            for k in ["key", "aliases", "multiset", "matching", "syllables", "options_vesum"]
                        },
                        "option_tokens": [],
                    }
                    value = item if isinstance(item, dict) else {}
                    aliases = []
                    _alias_conflicts(aliases, typ, value, loc)
                    if typ == "true-false":
                        claims = [value[k] for k in ["correct", "answer", "is_true", "isTrue"] if k in value]
                        if len(claims) > 1 and any(type(v) is not bool or v != claims[0] for v in claims):
                            aliases.append("true/false alias conflict")
                    add_check(row, "aliases", str(aliases) if aliases else None)
                    options = value.get("options", [])
                    if typ == "odd-one-out":
                        options = value.get("words", [])
                    try:
                        if typ in {"quiz", "translate"}:
                            quiz_correct_indices(value)
                            add_check(row, "key")
                        elif typ in {"fill-in", "odd-one-out"}:
                            answer = value.get("answer")
                            texts = [v.get("text") if isinstance(v, dict) else v for v in options]
                            if not isinstance(answer, str):
                                add_check(row, "key", "missing answer")
                            elif not texts:
                                add_check(row, "key", "empty options; reserved for dropdown gap")
                            else:
                                add_check(
                                    row,
                                    "key",
                                    None if texts.count(answer) == 1 else "key missing or repeated in options",
                                )
                        elif typ == "true-false":
                            add_check(
                                row,
                                "key",
                                None
                                if type(value.get("correct", value.get("answer"))) is bool
                                else "non-boolean truth key",
                            )
                        elif typ == "error-correction":
                            correction = value.get("correction", value.get("answer"))
                            error = value.get("error")
                            problem = None
                            if not correction or not error or error not in value.get("sentence", ""):
                                problem = "missing correction or error span"
                            elif options and correction not in options:
                                problem = "correction absent from options"
                            add_check(row, "key", problem)
                        elif typ == "order":
                            add_check(row, "key", order_error)
                            add_check(row, "multiset", order_error)
                        elif typ == "unjumble":
                            tokens = unjumble_tokens(value)
                            answer = value.get("answer") or " ".join(value.get("correct_order", []))
                            problem = _structural_activity_error(
                                {"items": [{"words": tokens, "answer": answer}]}, typ, {}
                            )
                            # Word tiles are indivisible in the actual component.
                            if Counter(_normal_letters(w) for tile in tokens for w in tile.split()) != Counter(
                                _normal_letters(w) for w in answer.split()
                            ):
                                problem = "word token multiset mismatch"
                            add_check(row, "key", None if answer else "missing answer")
                            add_check(row, "multiset", problem)
                        elif typ in {"count-syllables", "divide-words"}:
                            adapted = {
                                k: v.replace("\u0301", "") if isinstance(v, str) else v for k, v in value.items()
                            }
                            if typ == "divide-words":
                                adapted["answer"] = "-".join(str(adapted.get("answer", "")).split())
                            problem = _structural_activity_error({"items": [adapted]}, typ, {})
                            add_check(row, "key", problem)
                            add_check(row, "syllables", problem)
                        elif typ == "match-up":
                            findings = _check_match_up(slug, section, act["pairs"])
                            add_check(row, "matching", "; ".join(f.message for f in findings) if findings else None)
                            add_check(
                                row, "key", None if value.get("left") and value.get("right") else "empty matching side"
                            )
                        elif typ == "group-sort":
                            add_check(row, "key", None if item else "empty group member")
                    except (KeyError, TypeError, ValueError) as exc:
                        add_check(row, "key", str(exc))
                    lexical_options = options
                    if typ == "group-sort":
                        lexical_options = [item]
                    elif typ == "match-up":
                        lexical_options = [value["left"], value["right"]]
                    elif typ == "order":
                        lexical_options = [item]
                    elif typ == "unjumble":
                        lexical_options = unjumble_tokens(value)
                    elif typ in {"count-syllables", "divide-words", "watch-and-repeat"}:
                        lexical_options = [value.get("word", "")]
                    if lexical_options:
                        for oi, opt in enumerate(lexical_options):
                            text = opt.get("text", "") if isinstance(opt, dict) else str(opt)
                            toks = [
                                t.replace("’", "'").replace("ʼ", "'").replace("`", "'").casefold()
                                for t in TOKEN.findall(text.replace("\u0301", ""))
                            ]
                            row["option_tokens"].append({"index": oi, "text": text, "tokens": toks})
                            for token in toks:
                                words.setdefault(token, []).append({"location": loc, "option": oi, "text": text})
                        row["checks"]["options_vesum"] = {
                            "status": "PENDING",
                            "detail": "Sources batch verification required",
                        }
                    rows.append(row)

    report = {
        "snapshot": None,
        "modules": len(mods),
        "activities": len(activities),
        "units": len(rows),
        "type_counts": dict(Counter(a["type"] for a in activities)),
        "rows": rows,
        "option_words": words,
        "findings": [
            {"location": r["location"], "type": r["type"], "check": k, "detail": v.get("detail")}
            for r in rows
            for k, v in r["checks"].items()
            if v["status"] == "FLAG"
        ],
    }
    report["rendered_rows"] = rendered_audit(mods)
    report["rendered_findings"] = [r for r in report["rendered_rows"] if r["problems"]]
    for row in report["rendered_rows"]:
        for option in row["option_tokens"]:
            for token in option["tokens"]:
                words.setdefault(token, []).append(
                    {"location": row["location"], "option": option["index"], "text": option["text"]}
                )
    surfaces = sorted(set(words) | {w.capitalize() for w in words} | {w.upper() for w in words})
    analyses = verify_words(surfaces)
    for row in rows + report["rendered_rows"]:
        if not row["option_tokens"]:
            continue
        missing = sorted(
            {
                w
                for option in row["option_tokens"]
                for w in option["tokens"]
                if not any(analyses.get(form) for form in (w, w.capitalize(), w.upper()))
            }
        )
        row.setdefault("checks", {})["options_vesum"] = {
            "status": "REVIEW" if missing else "PASS",
            "unattested": missing,
            "detail": "A lookup miss needs language disposition; letters, morphemes and intentionally wrong spellings are not silently approved."
            if missing
            else None,
        }
    report["option_analyses"] = {
        w: {form: analyses[form] for form in (w, w.capitalize(), w.upper()) if analyses.get(form)} for w in words
    }
    report["option_lookup_misses"] = [w for w, found in report["option_analyses"].items() if not found]
    report["source_tree_sha256"] = hashlib.sha256(
        json.dumps(sorted({(r["slug"], r["source_sha256"]) for r in rows})).encode()
    ).hexdigest()
    report["audit_program_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit every a1-v1 activity with the applicable Method 1 rules. JSON results include each source unit and option analysis. Dictionary misses require a language disposition; this command does not prove semantic uniqueness.",
        epilog="Outputs: JSON on stdout. Exit 0: no structural findings; exit 1: structural findings, including empty dropdowns; exit 2: invalid arguments. No curriculum file is written.",
    )
    parser.add_argument("--summary", action="store_true", help="Omit per-unit details and word analyses from stdout")
    args = parser.parse_args()
    report = audit()
    output = (
        {k: v for k, v in report.items() if k not in {"rows", "option_words", "option_analyses", "rendered_rows"}}
        if args.summary
        else report
    )
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 1 if report["findings"] or report["rendered_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
