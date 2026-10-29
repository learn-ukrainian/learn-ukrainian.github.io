"""Run the ordered Method 1 audit using existing V7 and fresh structural rules."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from functools import cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from scripts.build.activity_renderer import (
    group_sort_group_name,
    order_correct_indices,
    quiz_correct_indices,
    unjumble_tokens,
)
from scripts.build.activity_validator import _check_group_sort, _check_match_up
from scripts.build.fresh.draft_schema import _alias_conflicts
from scripts.build.fresh.runner import _normal_letters, _structural_activity_error
from scripts.verification.vesum import _resolve_vesum_db_path, verify_words

TOKEN = re.compile(r"[А-Яа-яІіЇїЄєҐґ]+(?:['’ʼ`][А-Яа-яІіЇїЄєҐґ]+)*")
COMPONENTS = re.compile(
    r"<(Quiz|FillIn|Translate|TrueFalse|MatchUp|GroupSort|Order|Unjumble|ErrorCorrection|CountSyllables|DivideWords|OddOneOut|WatchAndRepeat)\b(.*?)/>",
    re.S,
)
JSON_PROP = re.compile(r"(\w+)=\{JSON\.parse\(`((?:\\.|[^`])*)`\)\}")
TYPE_COMPONENT = dict(
    zip(
        (
            "quiz",
            "fill-in",
            "translate",
            "true-false",
            "match-up",
            "group-sort",
            "order",
            "unjumble",
            "error-correction",
            "count-syllables",
            "divide-words",
            "odd-one-out",
            "watch-and-repeat",
        ),
        (
            "Quiz",
            "FillIn",
            "Translate",
            "TrueFalse",
            "MatchUp",
            "GroupSort",
            "Order",
            "Unjumble",
            "ErrorCorrection",
            "CountSyllables",
            "DivideWords",
            "OddOneOut",
            "WatchAndRepeat",
        ),
        strict=True,
    )
)


def decode_template(raw: str) -> str:
    """Decode only escapes produced by the renderer's template literal emitter."""

    def replace(match):
        value = match.group(1)
        if value not in {"\\", "`", "$"} or (value == "$" and raw[match.end() : match.end() + 1] != "{"):
            raise ValueError("unrecognized template escape")
        return value

    return re.sub(r"\\(.)", replace, raw, flags=re.S)


def check_unjumble(value: dict) -> tuple[list[str], str | None]:
    tokens = unjumble_tokens(value)
    answer = value.get("answer")
    if answer is None and isinstance(value.get("correct_order"), list):
        answer = " ".join(value["correct_order"])
    if not isinstance(answer, str) or not answer.strip():
        return tokens, "missing or invalid answer"
    error = _structural_activity_error({"items": [{"words": tokens, "answer": answer}]}, "unjumble", {})
    tile_words = [tuple(_normal_letters(w) for w in tile.split()) for tile in tokens]
    answer_words = tuple(_normal_letters(w) for w in answer.split())
    if any(not tile or any(not word for word in tile) for tile in tile_words):
        return tokens, "empty tile or word"
    if Counter(word for tile in tile_words for word in tile) != Counter(answer_words):
        return tokens, "word token multiset mismatch"
    counts = Counter(tile_words)
    tiles = tuple(counts)

    @cache
    def fits(position: int, remaining: tuple[int, ...]) -> bool:
        if position == len(answer_words):
            return not any(remaining)
        for i, tile in enumerate(tiles):
            if remaining[i] and answer_words[position : position + len(tile)] == tile:
                next_counts = list(remaining)
                next_counts[i] -= 1
                if fits(position + len(tile), tuple(next_counts)):
                    return True
        return False

    if not fits(0, tuple(counts[tile] for tile in tiles)):
        return tokens, "complete tiles cannot form answer in order"
    return tokens, error


def lexical_candidates(kind: str, value: dict, item: object, options: object) -> list:
    if kind in {"match-up", "MatchUp"}:
        return [value.get("left", ""), value.get("right", "")]
    if kind in {"group-sort", "GroupSort", "order", "Order"}:
        return [item]
    if kind in {"unjumble", "Unjumble"}:
        try:
            return unjumble_tokens(value)
        except (KeyError, TypeError, ValueError):
            return []
    if kind in {
        "count-syllables",
        "CountSyllables",
        "divide-words",
        "DivideWords",
        "watch-and-repeat",
        "WatchAndRepeat",
    }:
        return [value.get("word", "")]
    result = list(options) if isinstance(options, list) else []
    if kind in {"error-correction", "ErrorCorrection"}:
        result.append(value.get("correction", value.get("answer", value.get("correctForm", ""))))
    return result


def matching_problems(slug: str, section: str, pairs: list) -> dict[int, list[str]]:
    valid = [(i, pair) for i, pair in enumerate(pairs) if isinstance(pair, dict)]
    problems = {i: ["pair entry is not a mapping"] for i, pair in enumerate(pairs) if not isinstance(pair, dict)}
    for issue in _check_match_up(slug, section, [pair for _, pair in valid]):
        problems.setdefault(valid[issue.item_index][0], []).append(issue.message)
    return problems


def rendered_audit(mods: list[str]) -> tuple[list[dict], dict, dict, list[dict]]:
    """Inspect the tracked learner payloads after parser coercions and deduplication."""
    result = []
    inventory = {}
    hashes = {}
    component_findings = []
    for slug in mods:
        page = ROOT / f"site/src/content/docs/a1-v1/{slug}.mdx"
        page_bytes = page.read_bytes()
        hashes[slug] = hashlib.sha256(page_bytes).hexdigest()
        text = page_bytes.decode("utf-8")
        inventory[slug] = []
        for ai, (kind, body) in enumerate(COMPONENTS.findall(text)):
            props = {name: json.loads(decode_template(raw)) for name, raw in JSON_PROP.findall(body)}
            items = props.get("items", props.get("questions", props.get("pairs", [])))
            if kind == "GroupSort":
                groups = props.get("groups")
                items = []
                problems = []
                if not isinstance(groups, dict):
                    problems.append("group payload is missing or not a mapping")
                else:
                    for label, entries in groups.items():
                        if not isinstance(entries, list):
                            problems.append(f"group {label!r} items are not a list")
                        else:
                            items.extend(entries)
                if problems:
                    component_findings.append(
                        {"location": f"{slug}/rendered/{ai}", "component": kind, "status": "FLAG", "problems": problems}
                    )
            if not isinstance(items, list):
                raise ValueError(f"{slug}/rendered/{ai}: invalid item payload")
            inventory[slug].append((kind, len(items)))
            match_problems = matching_problems(slug, "rendered", items) if kind == "MatchUp" else {}
            for ii, item in enumerate(items):
                problems = []
                value = item if isinstance(item, dict) else {}
                try:
                    if kind in {"Quiz", "Translate", "FillIn", "ErrorCorrection", "OddOneOut"}:
                        choices = value.get("words", []) if kind == "OddOneOut" else value.get("options", [])
                        if not isinstance(choices, list):
                            raise ValueError("options must be a list")
                    if kind in {"Quiz", "Translate"}:
                        quiz_correct_indices(value)
                    elif kind == "FillIn":
                        if not isinstance(value.get("answer"), str):
                            problems.append("missing or non-string rendered fill-in key")
                        elif not value.get("options"):
                            problems.append("empty options; reserved for dropdown gap")
                        elif value["options"].count(value["answer"]) != 1:
                            problems.append("rendered fill-in key missing or repeated")
                    elif kind == "TrueFalse" and type(value.get("isTrue")) is not bool:
                        problems.append("rendered truth key is not boolean")
                    elif kind == "MatchUp":
                        problems.extend(match_problems.get(ii, []))
                        if not all(isinstance(value.get(k), str) and value[k].strip() for k in ("left", "right")):
                            problems.append("empty matching side")
                    elif kind == "GroupSort":
                        if not isinstance(item, str) or not item:
                            problems.append("invalid group member")
                        elif items.count(item) > 1:
                            problems.append("duplicate group member")
                    elif kind == "Order":
                        indices = order_correct_indices(items, props["correct_order"])
                        error = _structural_activity_error({"items": items, "correct_order": indices}, "order", {})
                        if error and ii == 0:
                            problems.append(error)
                    elif kind == "Unjumble":
                        _, error = check_unjumble(value)
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
                        correction = value.get("correctForm")
                        if not isinstance(correction, str) or not correction.strip():
                            problems.append("missing rendered correction key")
                        if not isinstance(error, str) or not error.strip():
                            problems.append("missing rendered error span")
                        elif not isinstance(value.get("sentence"), str) or error not in value["sentence"]:
                            problems.append("rendered error span absent from sentence")
                        if value.get("options") and value.get("correctForm") not in value["options"]:
                            problems.append("rendered correction key absent from choices")
                    elif kind == "OddOneOut":
                        quiz_correct_indices({**value, "options": value["words"]})
                except (KeyError, TypeError, ValueError) as exc:
                    if kind != "Order" or ii == 0:
                        problems.append(str(exc))
                candidates = lexical_candidates(kind, value, item, value.get("options", value.get("words", [])))
                option_tokens = []
                for oi, opt in enumerate(candidates):
                    candidate = opt.get("text", "") if isinstance(opt, dict) else opt
                    candidate = candidate if isinstance(candidate, str) else ""
                    tokens = [
                        t.replace("’", "'").replace("ʼ", "'").replace("`", "'").casefold()
                        for t in TOKEN.findall(candidate.replace("\u0301", ""))
                    ]
                    option_tokens.append({"index": oi, "text": candidate, "tokens": tokens})
                result.append(
                    {
                        "location": f"{slug}/rendered/{ai}/{ii}",
                        "component": kind,
                        "status": "FLAG"
                        if problems
                        else "REVIEW"
                        if kind == "ErrorCorrection" and not value.get("options")
                        else "PASS",
                        "problems": problems,
                        "key_review": kind == "ErrorCorrection" and not value.get("options"),
                        "option_tokens": option_tokens,
                    }
                )
    return result, inventory, hashes, component_findings


def audit() -> dict:
    manifest = (ROOT / "curriculum/l2-uk-en/curriculum.yaml").read_bytes()
    mods = yaml.safe_load(manifest)["levels"]["a1-v1"]["modules"]
    if not isinstance(mods, list) or len(mods) != 55 or len(set(mods)) != len(mods):
        raise ValueError("invalid module inventory: expected 55 unique modules")
    rows = []
    words = {}
    activities = []
    structural_findings = []
    source_hashes = {}

    def add_check(row, name, error=None):
        row["checks"][name] = {"status": "FLAG" if error else "PASS", "detail": error}

    for pos, slug in enumerate(mods, 1):
        path = ROOT / f"curriculum/l2-uk-en/a1-v1/{slug}/activities.yaml"
        source_bytes = path.read_bytes()
        source_hashes[slug] = hashlib.sha256(source_bytes).hexdigest()
        data = yaml.safe_load(source_bytes)
        if not isinstance(data, (list, dict)):
            raise ValueError(f"{slug}: invalid activity source")
        sections = [("root", data)] if isinstance(data, list) else data.items()
        for section, acts in sections:
            if not isinstance(acts, list):
                structural_findings.append(
                    {"location": f"{slug}/{section}", "detail": "section is not an activity list"}
                )
                continue
            for ai, act in enumerate(acts):
                if not isinstance(act, dict):
                    structural_findings.append(
                        {"location": f"{slug}/{section}/{ai}", "detail": "activity is not a mapping"}
                    )
                    continue
                typ = act.get("type")
                if not isinstance(typ, str):
                    typ = "<invalid>"
                ident = act.get("id", f"{section}-{ai}")
                activity_loc = f"{slug}/{section}/{ai}-{ident}"
                if typ not in TYPE_COMPONENT:
                    structural_findings.append(
                        {"location": activity_loc, "detail": f"unsupported activity type: {typ}"}
                    )
                if typ == "group-sort":
                    groups = act.get("groups", [])
                    if not isinstance(groups, list):
                        groups = []
                    units = []
                    group_problems = {}
                    for issue in _check_group_sort(slug, section, groups):
                        group_problems.setdefault(issue.item_index, []).append(issue.message)
                    names = []
                    members = []
                    for gi, group in enumerate(groups):
                        try:
                            name = group_sort_group_name(group, gi)
                            if name in names:
                                group_problems.setdefault(gi, []).append("duplicate group label")
                            names.append(name)
                        except (TypeError, ValueError):
                            pass
                        entries = group.get("items", []) if isinstance(group, dict) else []
                        if not isinstance(entries, list):
                            group_problems.setdefault(gi, []).append("invalid group items")
                            entries = []
                        if not entries:
                            group_problems.setdefault(gi, []).append("empty group")
                        for ii, member in enumerate(entries):
                            units.append((f"groups/{gi}/items/{ii}", member))
                            if isinstance(member, str):
                                members.append(member)
                    duplicates = {member for member, count in Counter(members).items() if count > 1}
                    for gi, problems in group_problems.items():
                        structural_findings.extend(
                            {"location": f"{activity_loc}/groups/{gi}", "detail": problem} for problem in problems
                        )
                elif typ == "match-up":
                    pairs = act.get("pairs", [])
                    units = [(f"pairs/{i}", value) for i, value in enumerate(pairs if isinstance(pairs, list) else [])]
                    match_problems = matching_problems(slug, section, pairs if isinstance(pairs, list) else [])
                else:
                    items = act.get("items", [])
                    units = [(f"items/{i}", value) for i, value in enumerate(items if isinstance(items, list) else [])]
                activities.append(
                    {
                        "module": pos,
                        "slug": slug,
                        "section": section,
                        "activity": ident,
                        "type": typ,
                        "units": len(units),
                    }
                )
                if not units:
                    structural_findings.append({"location": activity_loc, "detail": "zero units"})
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
                    loc = f"{activity_loc}/{unit}"
                    row = {
                        "module": pos,
                        "slug": slug,
                        "section": section,
                        "activity": ident,
                        "type": typ,
                        "unit": unit,
                        "location": loc,
                        "source_sha256": source_hashes[slug],
                        "key_review": typ == "error-correction" and isinstance(item, dict) and not item.get("options"),
                        "checks": {
                            k: {"status": "N/A"}
                            for k in ["key", "aliases", "multiset", "matching", "syllables", "options_vesum"]
                        },
                        "option_tokens": [],
                    }
                    value = item if isinstance(item, dict) else {}
                    aliases = []
                    try:
                        _alias_conflicts(aliases, typ, value, loc)
                    except (KeyError, TypeError, ValueError) as exc:
                        aliases.append(str(exc))
                    if typ == "true-false":
                        claims = [value[k] for k in ["correct", "answer", "is_true", "isTrue"] if k in value]
                        if len(claims) > 1 and any(type(v) is not bool or v != claims[0] for v in claims):
                            aliases.append("true/false alias conflict")
                    add_check(row, "aliases", str(aliases) if aliases else None)
                    options = value.get("options", [])
                    if typ == "odd-one-out":
                        options = value.get("words", [])
                    try:
                        if typ in {
                            "quiz",
                            "translate",
                            "fill-in",
                            "error-correction",
                            "odd-one-out",
                        } and not isinstance(options, list):
                            raise ValueError("options must be a list")
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
                            if (
                                not isinstance(correction, str)
                                or not correction.strip()
                                or not isinstance(error, str)
                                or not error.strip()
                                or not isinstance(value.get("sentence"), str)
                                or error not in value["sentence"]
                            ):
                                problem = "missing correction or error span"
                            elif options and correction not in options:
                                problem = "correction absent from options"
                            add_check(row, "key", problem)
                            if not problem and not options:
                                row["checks"]["key"] = {"status": "REVIEW", "detail": "reveal-only correction"}
                        elif typ == "order":
                            add_check(row, "key", order_error if unit == "items/0" else None)
                            add_check(row, "multiset", order_error if unit == "items/0" else None)
                        elif typ == "unjumble":
                            _, problem = check_unjumble(value)
                            add_check(row, "key", problem)
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
                            findings = match_problems.get(int(unit.split("/")[-1]), [])
                            add_check(row, "matching", "; ".join(findings) if findings else None)
                            add_check(
                                row,
                                "key",
                                None
                                if all(isinstance(value.get(k), str) and value[k].strip() for k in ("left", "right"))
                                else "empty matching side",
                            )
                        elif typ == "group-sort":
                            problem = None if isinstance(item, str) and item else "invalid group member"
                            if isinstance(item, str) and item in duplicates:
                                problem = "duplicate group member"
                            add_check(row, "key", problem)
                    except (KeyError, TypeError, ValueError) as exc:
                        add_check(row, "key", str(exc))
                    lexical_options = lexical_candidates(typ, value, item, options)
                    if lexical_options:
                        for oi, opt in enumerate(lexical_options):
                            text = opt.get("text", "") if isinstance(opt, dict) else opt
                            text = text if isinstance(text, str) else ""
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
        "snapshot": {"manifest_sha256": hashlib.sha256(manifest).hexdigest(), "source_sha256": source_hashes},
        "modules": len(mods),
        "activities": len(activities),
        "units": len(rows),
        "type_counts": dict(Counter(a["type"] for a in activities)),
        "rows": rows,
        "option_words": words,
        "findings": structural_findings
        + [
            {"location": r["location"], "type": r["type"], "check": k, "detail": v.get("detail")}
            for r in rows
            for k, v in r["checks"].items()
            if v["status"] == "FLAG"
        ],
    }
    report["rendered_rows"], rendered_inventory, mdx_hashes, component_findings = rendered_audit(mods)
    report["rendered_units"] = len(report["rendered_rows"])
    report["snapshot"]["mdx_sha256"] = mdx_hashes
    for slug in mods:
        source_activities = [a for a in activities if a["slug"] == slug]
        if not source_activities:
            report["findings"].append({"location": slug, "detail": "module has no activities"})
        raw_types = Counter(TYPE_COMPONENT.get(a["type"], a["type"]) for a in source_activities)
        rendered_types = Counter(kind for kind, _ in rendered_inventory[slug])
        raw_units = Counter()
        rendered_units = Counter()
        for activity in source_activities:
            raw_units[TYPE_COMPONENT.get(activity["type"], activity["type"])] += activity["units"]
        for kind, count in rendered_inventory[slug]:
            rendered_units[kind] += count
        for label, source, rendered in (
            ("activity count", len(source_activities), len(rendered_inventory[slug])),
            ("activity types", dict(raw_types), dict(rendered_types)),
            ("unit counts by type", dict(raw_units), dict(rendered_units)),
        ):
            if source != rendered:
                report["findings"].append(
                    {"location": slug, "detail": f"{label} mismatch", "source": source, "rendered": rendered}
                )
    report["rendered_findings"] = component_findings + [r for r in report["rendered_rows"] if r["problems"]]
    for row in report["rendered_rows"]:
        for option in row["option_tokens"]:
            for token in option["tokens"]:
                words.setdefault(token, []).append(
                    {"location": row["location"], "option": option["index"], "text": option["text"]}
                )
    surfaces = sorted(set(words) | {w.capitalize() for w in words} | {w.upper() for w in words})
    analyses = verify_words(surfaces)
    for row in rows + report["rendered_rows"]:
        if not any(option["tokens"] for option in row["option_tokens"]):
            row.setdefault("checks", {})["options_vesum"] = {"status": "N/A"}
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
    report["units_without_lexical_tokens"] = {
        "source": {
            typ: sum(r["type"] == typ and not any(o["tokens"] for o in r["option_tokens"]) for r in rows)
            for typ in TYPE_COMPONENT
        },
        "rendered": {
            kind: sum(
                r["component"] == kind and not any(o["tokens"] for o in r["option_tokens"])
                for r in report["rendered_rows"]
            )
            for kind in TYPE_COMPONENT.values()
        },
    }
    report["reveal_only_error_correction"] = {
        "source": sum(r["key_review"] for r in rows),
        "source_denominator": sum(r["type"] == "error-correction" for r in rows),
        "rendered": sum(r["key_review"] for r in report["rendered_rows"]),
        "rendered_denominator": sum(r["component"] == "ErrorCorrection" for r in report["rendered_rows"]),
    }
    report["finding_counts"] = {
        "source_issues": len(report["findings"]),
        "source_affected_rows": len({f["location"] for f in report["findings"]} & {r["location"] for r in rows}),
        "rendered_issues": sum(len(r["problems"]) for r in report["rendered_findings"]),
        "rendered_affected_rows": sum(bool(r["problems"]) for r in report["rendered_rows"]),
    }
    report["source_tree_sha256"] = hashlib.sha256(
        json.dumps(sorted({(r["slug"], r["source_sha256"]) for r in rows})).encode()
    ).hexdigest()
    report["audit_program_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    helper_paths = [
        "scripts/build/activity_renderer.py",
        "scripts/build/activity_validator.py",
        "scripts/build/fresh/draft_schema.py",
        "scripts/build/fresh/runner.py",
        "scripts/verification/vesum.py",
    ]
    report["snapshot"]["helper_sha256"] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in helper_paths}
    vesum_hash = hashlib.sha256()
    with _resolve_vesum_db_path().open("rb") as db:
        for chunk in iter(lambda: db.read(1024 * 1024), b""):
            vesum_hash.update(chunk)
    report["snapshot"]["vesum"] = {"identity": "VESUM SQLite", "sha256": vesum_hash.hexdigest()}
    return report


def main() -> int:
    class JsonArgumentParser(argparse.ArgumentParser):
        def error(self, message):
            print(json.dumps({"status": "ERROR", "error": "invalid arguments"}), file=sys.stderr)
            raise SystemExit(2)

    parser = JsonArgumentParser(
        description="Audit every a1-v1 activity with the applicable Method 1 rules. JSON results include each source unit and option analysis. Dictionary misses require a language disposition; this command does not prove semantic uniqueness.",
        epilog="Outputs: JSON on stdout. Exit 0: no structural findings; exit 1: structural findings, including empty dropdowns; exit 2: invalid inputs or tool failure (JSON ERROR on stderr). No curriculum file is written.",
    )
    parser.add_argument("--summary", action="store_true", help="Omit per-unit details and word analyses from stdout")
    args = parser.parse_args()
    try:
        report = audit()
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": type(exc).__name__}), file=sys.stderr)
        return 2
    output = (
        {k: v for k, v in report.items() if k not in {"rows", "option_words", "option_analyses", "rendered_rows"}}
        if args.summary
        else report
    )
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 1 if report["findings"] or report["rendered_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
