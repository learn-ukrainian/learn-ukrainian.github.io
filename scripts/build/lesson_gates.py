"""Deterministic lesson quality gates ported from the pinned Phase 0 checker.

No writer, network, plan rewrite, or wiki coverage runs here. Stress correctness
uses the same offline ULIF oracle as the stress annotator and fails closed.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

MAX_UNVERIFIED_STRESS = 10
MAX_UNVERIFIED_LEMMAS = 5

ALLOWED = {
    "both": {"divide-words", "count-syllables", "pick-syllables", "unjumble", "order", "odd-one-out",
             "observe", "phrase-table", "match-up", "group-sort", "quiz", "true-false", "fill-in"},
    "inline_only": {"image-to-letter", "letter-grid", "watch-and-repeat"},
    "workbook_only": {"anagram", "error-correction", "translate"},
}
LIST_FIELDS = ("items", "questions", "pairs", "sentences", "words", "statements", "groups")
NAME_RE = re.compile(r"анна|anna|ulp|ohoiko|огойко", re.I)
ATTR_RE = re.compile(r"цит\.|цитата|за:|джерело|quoted from|source:|цитуємо", re.I)
ACUTE = "́"
CYR = "А-ЩЬЮЯҐЄІЇа-щьюяґєії"

def nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t)


def strip_acute(t: str) -> str:
    return nfc(unicodedata.normalize("NFD", t).replace(ACUTE, ""))


def strip_comments(t: str) -> str:
    return re.sub(r"<!--.*?-->", "", t, flags=re.S)


def norm_md(t: str) -> str:
    """Markdown-to-markdown comparison: only stress marks and whitespace may differ. Case preserved."""
    return re.sub(r"\s+", " ", strip_acute(t)).strip()


def md_to_text(t: str) -> str:
    """Approximate what a browser shows for a Markdown fragment."""
    t = strip_comments(t)
    t = re.sub(r"^\s*:::\w*.*$", " ", t, flags=re.M)          # admonition markers
    t = re.sub(r"^\s*```.*$", " ", t, flags=re.M)               # fence lines incl. language label
    t = re.sub(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", " ", t, flags=re.M)  # table separator rows
    t = re.sub(r"^\s{0,3}#{1,6}\s+", " ", t, flags=re.M)        # heading hashes
    t = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", " ", t, flags=re.M)  # list markers
    t = re.sub(r"^\s*>\s?", " ", t, flags=re.M)                 # blockquotes
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)             # links/images -> text
    t = re.sub(r"[*_`|]", " ", t)
    return norm_text(t)


def norm_text(t: str) -> str:
    return re.sub(r"\s+", " ", strip_acute(t)).strip()


def sections(md: str) -> dict[str, str]:
    """Return {section_title: body} with '__intro__' for text before the first '## '."""
    out: dict[str, str] = {}
    cur = "__intro__"
    buf: list[str] = []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            out[cur] = "\n".join(buf)
            cur = re.sub(r"^[^\w«]*", "", strip_acute(m.group(1))).strip()  # drop leading emoji
            buf = []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf)
    return out


def paragraphs(t: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", strip_comments(t)) if p.strip()]


def leaves(obj) -> list:
    if isinstance(obj, dict):
        return [x for v in obj.values() for x in leaves(v)]
    if isinstance(obj, list):
        return [x for v in obj for x in leaves(v)]
    return [obj]


def contains(orig, new) -> bool:
    """orig ⊆ new structurally with multiplicity: dict keys must exist with contained values;
    each orig list element must match a DISTINCT new element; scalars equal modulo stress
    marks and with the same type (True is not 1)."""
    if isinstance(orig, dict):
        return isinstance(new, dict) and all(k in new and contains(v, new[k]) for k, v in orig.items())
    if isinstance(orig, list):
        if not isinstance(new, list) or len(orig) > len(new):
            return False
        cand = [[i for i, n in enumerate(new) if contains(o, n)] for o in orig]

        def match(k: int, used: frozenset) -> bool:   # complete one-to-one assignment (backtracking)
            if k == len(cand):
                return True
            return any(match(k + 1, used | {i}) for i in cand[k] if i not in used)
        return match(0, frozenset())
    if isinstance(orig, str):
        return isinstance(new, str) and norm_md(orig) == norm_md(new)
    return type(orig) is type(new) and orig == new


def first_text(x) -> str | None:
    if isinstance(x, str):
        return norm_md(x).lower()
    if isinstance(x, dict):
        for v in x.values():
            if isinstance(v, str) and v.strip():
                return norm_md(v).lower()
    return None


def contradictions(obj, path="") -> list[str]:
    """Within any list, two elements with the same primary text are contradictory
    (same option twice with different answers, same word in two groups, duplicated items)."""
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += contradictions(v, f"{path}.{k}")
        return out
    if isinstance(obj, list):
        seen: dict[str, int] = {}
        for i, e in enumerate(obj):
            t = first_text(e)
            if t:
                seen[t] = seen.get(t, 0) + 1
            out += contradictions(e, f"{path}[{i}]")
        out += [f"{path}: '{t}' appears {c}x in one list" for t, c in seen.items() if c > 1]
        # groups: the same item in two groups
        if obj and all(isinstance(g, dict) and isinstance(g.get("items"), list) for g in obj):
            allitems: dict[str, int] = {}
            for g in obj:
                for it in g["items"]:
                    t = first_text(it)
                    if t:
                        allitems[t] = allitems.get(t, 0) + 1
            out += [f"{path}: item '{t}' sits in {c} groups" for t, c in allitems.items() if c > 1]
    return out


def learner_text(md: str) -> str:
    """Drop what the learner never reads as words: comments, code, link destinations, raw URLs."""
    t = strip_comments(md)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`\n]*`", " ", t)
    t = re.sub(r"\]\([^)]*\)", "]", t)
    t = re.sub(r"https?://\S+", " ", t)
    return t


def missing_stress(text: str, allow: set[str]) -> list[str]:
    """Cyrillic tokens (NFC) with >=2 vowels and no combining acute, in learner-facing text."""
    bad = []
    for tok in re.findall(rf"[{CYR}'’{ACUTE}]+", nfc(learner_text(text))):
        if ACUTE in tok:
            continue
        tok = tok.strip("'’")
        if tok and len(re.findall(r"[аеєиіїоуюяАЕЄИІЇОУЮЯ]", tok)) >= 2 and strip_acute(tok).lower() not in allow:
            bad.append(tok)
    return bad


def _acute_positions(form: str) -> list[int]:
    out, i = [], 0
    for ch in unicodedata.normalize("NFD", form):
        if ch == ACUTE:
            out.append(i - 1)
        else:
            i += 1
    return out


def wrong_stress(text: str, allow: set[str], proper: set[str] = frozenset()) -> list[str]:
    """Marked forms whose acute is not on a vowel the stress dictionary accepts.
    Uses the repo oracle (scripts.verification.stress, ULIF-derived); forms the dictionary
    does not know are skipped here (they must be declared in unverified_stress)."""
    try:
        from scripts.verification.stress import verify_stress  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("stress oracle unavailable") from e
    out: list[str] = []
    seen: set[str] = set()
    for tok in re.findall(rf"[{CYR}'{ACUTE}]+", nfc(text).replace("''", "'").replace("’", "'")):
        if ACUTE not in tok or tok in seen:
            continue
        seen.add(tok)
        tok = tok.strip("'’")
        bare = strip_acute(tok)
        if not tok or bare.lower() in allow:
            continue
        forms: list[str] = []
        # proper names (declared in lessons.yaml: proper_names, or capitalised vocabulary lemmas) are looked
        # up with their case first (Марко́); everything else lowercase first, so sentence-initial common words
        # (Стіна́, Мене́) never inherit a homograph's reading (Сті́на, Ме́не).
        order = [bare, bare.lower()] if (bare in proper and bare[:1].isupper()) else [bare.lower(), bare]
        for q in order:
            r = verify_stress(q)
            if r.get("status") in ("ok", "ambiguous") and r.get("matches"):
                forms = [nfc(m["stressed_form"]) for m in r["matches"]]
                break
        if not forms:
            out.append(f"{tok}: undeclared unverified stress")
            continue
        allowed: set[int] = set()
        for f in forms:
            allowed.update(_acute_positions(f))
        mine = _acute_positions(tok)
        if len(mine) != 1 or mine[0] not in allowed:
            out.append(f"{tok}→{'/'.join(forms)}")
    return sorted(out)


def _run_lesson_gates(module_dir: Path, source_dir: Path, plan: dict,
                     rendered: dict[str, str] | None = None) -> dict:
    """Validate the complete lesson set; cross-lesson invariants always apply.

    ``rendered`` maps lesson numbers and ``index`` to assembled MDX.
    Absent render evidence is a blocking failure, never a deferred pass.
    """
    report = {"blocking": [], "warnings": [], "facts": {}}
    block = report["blocking"].append
    warn = report["warnings"].append
    try:
        ly = yaml.safe_load((module_dir / "lessons.yaml").read_text()) or {}
        lessons = ly.get("lessons") or []
        from scripts.build.lesson_map import validate_lesson_map
        validate_lesson_map(ly)
        base = {name: (source_dir / name).read_text() for name in
                ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")}
        if not lessons or [L.get("n") for L in lessons] != list(range(1, len(lessons) + 1)):
            raise ValueError("lessons must be nonempty and consecutively numbered")
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        return {"passed": False, "diagnostics": [str(exc)], **report}
    section_to_lesson = {strip_acute(str(s)): L["n"] for L in lessons for s in L.get("sections", [])}
    section_to_lesson["__intro__"] = 1
    if ly.get("closes_module") != len(lessons):
        block("closes_module must name the last lesson")
    last_md = module_dir / f"lesson-{len(lessons)}" / "module.md"
    if last_md.is_file():
        from scripts.build.lesson_assembler import (
            _normalize_a1_example_fences,
            _normalize_a1_module_close,
        )
        last_text = _normalize_a1_module_close(
            _normalize_a1_example_fences(last_md.read_text(encoding="utf-8"))
        )
        if "Підсумок модуля" not in last_text and "Module summary" not in last_text:
            block("last lesson must close with Підсумок модуля — Module summary (not Module completion)")
    exempt = {e.get("id"): e.get("reason") for e in ly.get("items_min_exempt", [])}
    if any(not reason for reason in exempt.values()):
        block("item exemptions require reasons")
    provenance = ly.get("provenance") or []
    for L in lessons:
        if not L.get("title") or L.get("minutes") != 60 or not isinstance(L.get("word_target"), int) or L["word_target"] < 550:
            block(f"lesson {L.get('n')}: title, 60 minutes and word_target >=550 required")
        target = L.get("activities", {})
        if target.get("inline") != [4, 6] or target.get("workbook") != [6, 9] or target.get("total", 0) < 10:
            block(f"lesson {L.get('n')}: invalid activity targets")
    base_md, base_acts = base["module.md"], yaml.safe_load(base["activities.yaml"])
    base_vocab = yaml.safe_load(base["vocabulary.yaml"])
    base_secs = sections(base_md)
    base_paras_by_lesson: dict[int, list[str]] = {L["n"]: [] for L in lessons}
    for title, body in base_secs.items():
        if title not in section_to_lesson:
            block(f"baseline section {title!r} has no lesson mapping (checker config)")
            continue
        base_paras_by_lesson[section_to_lesson[title]] += [p for p in paragraphs(body) if len(p.split()) >= 8]
    n_long = sum(len(v) for v in base_paras_by_lesson.values())
    report["facts"]["baseline"] = {"commit": ly.get("source_commit"), "prose_tokens": len(strip_comments(base_md).split()),
                                   "long_paragraphs": n_long, "activities": {k: len(v) for k, v in base_acts.items()},
                                   "vocab": len(base_vocab)}

    all_ids: list[str] = []
    all_lemmas: list[str] = []
    per_lesson: dict[int, dict] = {}
    lesson_md_clean: dict[int, str] = {}
    lesson_md_raw: dict[int, str] = {}
    new_acts: dict[str, tuple[int, str, dict]] = {}   # id -> (lesson, placement, activity)
    lesson_vocab: dict[int, list] = {}
    lesson_res: dict[int, list] = {}
    for L in lessons:
        n = L.get("n")
        d = module_dir / f"lesson-{n}"
        files = {k: d / f"{k}.{ext}" for k, ext in (("module", "md"), ("activities", "yaml"),
                                                     ("vocabulary", "yaml"), ("resources", "yaml"))}
        missing = [k for k, p in files.items() if not p.exists()]
        if missing:
            block(f"lesson {n}: missing files {missing}")
            continue
        md = files["module"].read_text(encoding="utf-8")
        acts = yaml.safe_load(files["activities"].read_text(encoding="utf-8")) or {}
        vocab = yaml.safe_load(files["vocabulary"].read_text(encoding="utf-8")) or []
        res = yaml.safe_load(files["resources"].read_text(encoding="utf-8")) or []
        lesson_md_raw[n], lesson_md_clean[n] = md, strip_comments(md)
        lesson_vocab[n], lesson_res[n] = vocab, res
        prose_tokens = len(lesson_md_clean[n].split())
        narrator_surface = "\n".join(line for line in strip_comments(md).splitlines()
                                      if not line.lstrip().startswith(">"))
        if re.search(r"Привіт[!,.]?\s+Я\s+", strip_acute(narrator_surface), re.I):
            block(f"lesson {n}: named narrator opener is forbidden")
        if not isinstance(acts, dict) or "inline" not in acts or "workbook" not in acts:
            block(f"lesson {n}: activities.yaml must be a mapping with 'inline' and 'workbook' lists")
            acts = {"inline": [], "workbook": []}
        inline, workbook = acts.get("inline") or [], acts.get("workbook") or []
        inline_ids = [a.get("id") for a in inline]
        # every ## section of the lesson carries >=1 injection; injections == inline ids
        secs = sections(md)
        for title, body in secs.items():
            if title != "__intro__" and "INJECT_ACTIVITY" not in body:
                block(f"lesson {n}: section «{title}» has no INJECT_ACTIVITY")
        inject_ids = re.findall(r"<!--\s*INJECT_ACTIVITY:\s*([\w-]+)\s*-->", md)
        if sorted(inject_ids) != sorted(i for i in inline_ids if i) or len(inject_ids) != len(set(inject_ids)):
            block(f"lesson {n}: INJECT ids {sorted(inject_ids)} != inline ids {sorted(inline_ids)} (or duplicates)")
        if not 4 <= len(inline) <= 6:
            block(f"lesson {n}: inline count {len(inline)} outside 4–6")
        if not 6 <= len(workbook) <= 9:
            block(f"lesson {n}: workbook count {len(workbook)} outside 6–9")
        if len(inline) + len(workbook) < 10:
            block(f"lesson {n}: total activities {len(inline)+len(workbook)} < 10")
        minimum_words = max(550, L["word_target"])
        if prose_tokens < minimum_words:
            block(f"lesson {n}: prose tokens {prose_tokens} < {minimum_words} minimum")
        for placement, lst in (("inline", inline), ("workbook", workbook)):
            for a in lst:
                aid, typ = a.get("id"), a.get("type")
                if not aid:
                    block(f"lesson {n}: activity without id in {placement}: {str(a)[:60]}")
                    continue
                all_ids.append(aid)
                new_acts[aid] = (n, placement, a)
                if typ in ALLOWED["inline_only"] and placement != "inline":
                    block(f"lesson {n}: {aid} type {typ} is inline-only")
                elif typ in ALLOWED["workbook_only"] and placement != "workbook":
                    block(f"lesson {n}: {aid} type {typ} is workbook-only")
                elif typ not in ALLOWED["both"] | ALLOWED["inline_only"] | ALLOWED["workbook_only"]:
                    block(f"lesson {n}: {aid} type {typ} not in the A1 allowlist")
                # item minimum: count elements of the first list field; groups count their inner items
                cnt = None
                for f in LIST_FIELDS:
                    if isinstance(a.get(f), list):
                        cnt = sum(len(g.get("items", [])) for g in a[f]) if f == "groups" else len(a[f])
                        break
                if cnt is None:
                    block(f"lesson {n}: {aid} has no list payload ({'/'.join(LIST_FIELDS)})")
                elif cnt < 6 and aid not in exempt:
                    block(f"lesson {n}: {aid} has {cnt} items < 6 and is not exempt")
                if not (a.get("instruction") or a.get("title")):
                    block(f"lesson {n}: {aid} has no instruction/title")
                for c in contradictions({k: v for k, v in a.items() if k in LIST_FIELDS}, aid):
                    block(f"lesson {n}: contradictory payload in {c}")
        lemmas = [norm_md(str(e.get("lemma", ""))).lower() for e in vocab]
        all_lemmas += lemmas
        if len(lemmas) < 12:
            block(f"lesson {n}: vocabulary has {len(lemmas)} entries < 12")
        for e in vocab:
            if not all(e.get(k) for k in ("lemma", "translation", "pos", "usage")):
                block(f"lesson {n}: vocabulary entry incomplete: {e.get('lemma')}")
        if not res:
            block(f"lesson {n}: resources.yaml empty (P4)")
        for r in res:
            if not (r.get("title") and (r.get("url") or r.get("chunk_id") or r.get("source"))):
                block(f"lesson {n}: resource lacks title + url/chunk_id/source: {r}")
        # per-lesson unverified lists + limits
        u_stress = [str(w) for w in (L.get("unverified_stress") or [])]
        u_lem = [str(w) for w in (L.get("unverified_lemmas") or [])]
        if len(u_stress) > MAX_UNVERIFIED_STRESS:
            block(f"lesson {n}: {len(u_stress)} unverified stresses > {MAX_UNVERIFIED_STRESS} (stop rule)")
        if len(u_lem) > MAX_UNVERIFIED_LEMMAS:
            block(f"lesson {n}: {len(u_lem)} unverified lemmas > {MAX_UNVERIFIED_LEMMAS} (stop rule)")
        allow = {strip_acute(w).lower() for w in u_stress}
        # stress CORRECTNESS: every marked form must match a dictionary reading (not just carry a mark)
        proper = {strip_acute(str(w)) for w in (ly.get("proper_names") or [])} | {strip_acute(str(e.get("lemma", ""))) for e in vocab if str(e.get("lemma", ""))[:1].isupper()}
        try:
            wrong = wrong_stress(learner_text(lesson_md_clean[n]) + "\n" + "\n".join(str(x) for x in leaves(acts) + leaves(vocab) if isinstance(x, str)), allow, proper)
        except Exception as exc:
            block(f"lesson {n}: stress oracle unavailable: {type(exc).__name__}")
            wrong = []
        if wrong:
            block(f"lesson {n}: {len(wrong)} stressed forms contradict the stress dictionary: {wrong[:15]}")
        bad = sorted(set(missing_stress(lesson_md_clean[n], allow)
                         + missing_stress("\n".join(str(x) for x in leaves(acts) if isinstance(x, str)), allow)
                         + missing_stress("\n".join(str(x) for x in leaves(vocab) if isinstance(x, str)), allow)))
        if bad:
            block(f"lesson {n}: {len(bad)} multi-syllable words without stress mark (not in unverified_stress): {bad[:20]}")
        est = prose_tokens / 60 + 2.5 * len(inline) + 3 * len(workbook) + 8
        per_lesson[n] = {"prose_tokens": prose_tokens, "inline": len(inline), "workbook": len(workbook),
                         "vocab": len(lemmas), "resources": len(res), "unverified_stress": len(u_stress),
                         "unverified_lemmas": len(u_lem), "est_minutes": round(est)}
        if not 45 <= est <= 75:
            warn(f"lesson {n}: pacing estimate {est:.0f} min outside 45–75 (heuristic)")
    report["facts"]["lessons"] = per_lesson

    # cross-lesson invariants
    dup = sorted({i for i in all_ids if all_ids.count(i) > 1})
    if dup:
        block(f"duplicate activity ids across lessons: {dup}")
    base_lemmas = sorted(norm_md(str(e.get("lemma", ""))).lower() for e in base_vocab)
    if sorted(all_lemmas) != base_lemmas:
        block("vocabulary multiset != baseline 48: "
              f"missing={sorted(set(base_lemmas)-set(all_lemmas))} extra={sorted(set(all_lemmas)-set(base_lemmas))} "
              f"dups={sorted({l for l in all_lemmas if all_lemmas.count(l) > 1})}")
    total = sum(v["prose_tokens"] for v in per_lesson.values())
    report["facts"]["total_prose_tokens"] = total
    if total < 2000:
        block(f"total prose tokens {total} < 2000")

    # prose preservation: verbatim (modulo stress), exactly once overall, in the mapped lesson, comments excluded
    hay = {n: norm_md(t) for n, t in lesson_md_clean.items()}
    lost, misplaced, dupd = [], [], []
    for n, paras in base_paras_by_lesson.items():
        for p in paras:
            key = norm_md(p)
            counts = {m: hay[m].count(key) for m in hay}
            tot = sum(counts.values())
            if tot == 0:
                lost.append(p)
            elif tot > 1:
                dupd.append(p)
            elif counts.get(n, 0) != 1:
                misplaced.append((p, n, [m for m, c in counts.items() if c]))
    report["facts"]["preservation"] = {"long_paragraphs": n_long, "lost": len(lost), "duplicated": len(dupd), "misplaced": len(misplaced)}
    for p in lost[:5]:
        block(f"original paragraph not preserved verbatim: {p[:70]!r}")
    if len(lost) > 5:
        block(f"... and {len(lost)-5} more lost paragraphs")
    for p in dupd[:3]:
        block(f"original paragraph appears more than once: {p[:60]!r}")
    for p, n, where in misplaced[:3]:
        block(f"original paragraph belongs to lesson {n} but is in {where}: {p[:60]!r}")

    # original activity preservation via provenance (structured containment, exact ids, lesson ownership)
    prov = {(p.get("placement"), p.get("index")): p for p in provenance}
    originals = [("inline", i, a) for i, a in enumerate(base_acts.get("inline", []))] + \
                [("workbook", i, a) for i, a in enumerate(base_acts.get("workbook", []))]
    for placement, i, a in originals:
        p = prov.get((placement, i))
        expected_id = a.get("id") if placement == "inline" else f"act-w{i+1}"
        if not p:
            block(f"provenance missing for original {placement}[{i}] ({expected_id})")
            continue
        if p.get("new_id") != expected_id:
            block(f"original {placement}[{i}] must keep id {expected_id}; provenance says {p.get('new_id')}")
        na = new_acts.get(expected_id)
        if not na:
            block(f"original {expected_id} not found in any lesson")
            continue
        n, _, act = na
        if p.get("lesson") != n:
            block(f"provenance says {expected_id} in lesson {p.get('lesson')} but it lives in lesson {n}")
        if act.get("type") != a.get("type"):
            block(f"{expected_id}: type {a.get('type')} became {act.get('type')}")
        payload = {k: v for k, v in a.items() if k in LIST_FIELDS}
        if not payload:
            block(f"{expected_id}: original has no list payload to compare (checker config)")
        elif not contains(payload, {k: act.get(k) for k in payload}):
            block(f"{expected_id}: original items/answers/groups not preserved structurally")


    # Exemptions cannot be invented for new writer activities.
    original_ids = {a.get("id") for a in base_acts.get("inline", [])} | {
        f"act-w{i + 1}" for i, _ in enumerate(base_acts.get("workbook", []))}
    if not set(exempt) <= original_ids:
        block("item exemptions may name only preserved original activities")
    if len(provenance) != len(originals) or len(prov) != len(provenance):
        block("provenance must cover every original exactly once")
    # Allocation records first introduction once; a later lesson may use prior vocabulary.
    for path in module_dir.glob("lesson-*/*"):
        if path.name not in {"module.md", "activities.yaml", "vocabulary.yaml"}:
            continue
        for line in path.read_text().splitlines():
            if NAME_RE.search(line) and not ATTR_RE.search(line):
                block(f"unattributed reference-name hit in {path.name}")
    for n, md in lesson_md_raw.items():
        try:
            from scripts.build.linear_pipeline import (
                _advisory_immersion_pct,
                _component_density_gate,
                _l2_exposure_floor_gate,
                _long_uk_ceiling_gate,
            )
            a1_plan = {**plan, "level": "a1"}
            # The vocabulary tab is part of each lesson's learner-facing surface.
            surface = md + "\n" + "\n".join(
                f"- **{e['lemma']}** — {e['translation']}" for e in lesson_vocab[n])
            immersion = {
                "ratio_advisory": _advisory_immersion_pct(surface, a1_plan),
                "l2_exposure_floor": _l2_exposure_floor_gate(surface, a1_plan),
                "long_uk_ceiling": _long_uk_ceiling_gate(surface, a1_plan),
                "component_density": _component_density_gate(surface, a1_plan),
            }
            report["facts"].setdefault("immersion", {})[n] = immersion
            for name, result in immersion.items():
                if not result["passed"]:
                    block(f"lesson {n}: {name} failed: {result}")
        except Exception as exc:
            block(f"lesson {n}: immersion gate unavailable: {type(exc).__name__}")
        page = (rendered or {}).get(str(n), (rendered or {}).get(f"{n}.mdx", ""))
        if not page:
            block(f"lesson {n}: render coverage missing")
            continue
        # Parse serialized props as well as Markdown: escaped strings must remain
        # represented on the published surface (e.g. OddOneOut choices).
        decoded = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), page)
        decoded = decoded.replace('\\"', '"').replace("\\n", " ")
        visible = norm_text(md_to_text(decoded))
        literal_text = norm_text(strip_comments(decoded))
        if len(re.findall(r"<TabItem\s", strip_comments(page))) != 4:
            block(f"lesson {n}: render must have four learner tabs")
        for para in paragraphs(md):
            if len(para.split()) < 8:
                continue
            if para.lstrip().startswith(">") and "<DialogueBox" in page:
                # DialogueBox serializes speaker and spoken text as separate props.
                chunks = [re.sub(r"^>\s*", "", line) for line in para.splitlines() if line.strip()]
                missing = False
                for chunk in chunks:
                    speaker, sep, spoken = chunk.partition(":")
                    for value in (speaker, spoken) if sep else (chunk,):
                        if md_to_text(value) not in literal_text:
                            missing = True
                if not missing:
                    continue
            if md_to_text(para) not in visible:
                block(f"lesson {n}: render lacks lesson paragraph: {md_to_text(para)[:100]!r}")
        for aid, (owner, _, act) in new_acts.items():
            if owner != n:
                continue
            for value in leaves({k: v for k, v in act.items() if k in LIST_FIELDS or k in ("title", "instruction")}):
                if isinstance(value, str) and len(value) >= 3 and norm_text(value) not in literal_text:
                    block(f"lesson {n}: render lacks activity string from {aid}: {value!r}")
        for entry in lesson_vocab[n]:
            if norm_text(str(entry["lemma"])) not in visible:
                block(f"lesson {n}: render lacks vocabulary lemma")
        for resource in lesson_res[n]:
            if norm_text(str(resource["title"])) not in visible:
                block(f"lesson {n}: render lacks resource title")
    landing = (rendered or {}).get("index", (rendered or {}).get("index.mdx", ""))
    if not landing:
        block("module landing render missing")
    else:
        landing_text = norm_text(strip_comments(landing).replace('\\"', '"'))
        if len(re.findall(r"<TabItem\s", strip_comments(landing))) != 4:
            block("module landing must have four learner tabs")
        for lemma in base_lemmas:
            if lemma not in landing_text.lower():
                block("module landing lacks vocabulary union entry")
        for n, entries in lesson_res.items():
            if f"/{n}/" not in landing:
                block(f"module landing lacks lesson {n} link")
            for entry in entries:
                if norm_text(str(entry["title"])) not in landing_text:
                    block("module landing lacks resource union entry")
        for aid, (_, placement, activity) in new_acts.items():
            if placement == "workbook":
                for value in leaves({k: v for k, v in activity.items()
                                     if k in LIST_FIELDS or k in ("title", "instruction")}):
                    if isinstance(value, str) and len(value) >= 3 and norm_text(value) not in landing_text:
                        block(f"module landing lacks workbook union string from {aid}")
    return {"passed": not report["blocking"], "diagnostics": report["blocking"], **report}


def run_lesson_gates(module_dir: Path, source_dir: Path, plan: dict,
                     rendered: dict[str, str] | None = None) -> dict:
    """Fail closed on invalid artifacts as well as semantic gate failures."""
    try:
        return _run_lesson_gates(module_dir, source_dir, plan, rendered)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, yaml.YAMLError) as exc:
        diagnostics = [f"invalid lesson artifacts: {type(exc).__name__}: {exc}"]
        return {"passed": False, "diagnostics": diagnostics, "blocking": diagnostics,
                "warnings": [], "facts": {}}
