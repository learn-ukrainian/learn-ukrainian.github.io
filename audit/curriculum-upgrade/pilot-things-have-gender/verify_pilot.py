#!/usr/bin/env python
"""Orchestrator-owned checker for the curriculum-upgrade Phase 0 pilot:
a1/things-have-gender split into three 60-minute lessons under the parallel
level `a1-v2`.

Baseline = the original module files at a PINNED commit (never the working
tree, never a movable branch). Exit code 1 on any BLOCKING failure.

Layout: original stays untouched at curriculum/l2-uk-en/a1/things-have-gender/;
the split lives at curriculum/l2-uk-en/a1-v2/things-have-gender/.

Usage (from the dispatch worktree root):
    /home/ops/learn-ukrainian/.venv/bin/python audit/curriculum-upgrade/pilot-things-have-gender/verify_pilot.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path.cwd()
ORIG = "curriculum/l2-uk-en/a1/things-have-gender"
V2 = "curriculum/l2-uk-en/a1-v2/things-have-gender"
LESSONS = ROOT / V2
HTML = ROOT / "docs/poc/poc-lesson-split-things-have-gender.html"
TEMPLATE = ROOT / "docs/poc/poc-lesson-split-design.html"
TEMPLATE_SHA = "935c9b632b89b0b4bc3dd124bced27743a93b3dba7a924b8ece5ff28d01a91b6"
BASE_COMMIT = "7829e74b6031cdcc4ef69895b5f42e0643569e44"          # pinned; drift is a blocking failure
BASELINE_SHA = {                          # sha256 of the four original files at BASE_COMMIT
    "module.md": "e7b6d74c6767227586f7058397dd8dd45a9a106b185f9fea7b32f3d2f05bc18e",
    "activities.yaml": "0477b01f2299d315e38c79f7e7ddc9125eccaf14fde1435d0d87a80b5fccbd1e",
    "vocabulary.yaml": "ec6b64f523001386cc63c48ab9aef6dcd9a5e54db702dd23f87b47d2fb87cd0f",
    "resources.yaml": "55dd714d7183bcb86125a743d3da4b088e1a019f0f86ebe8fc0e5c4ef4fc735c",
}
# original sections -> lesson that must carry them (intro = text before the first '## ')
SECTION_TO_LESSON = {"__intro__": 1, "Діалоги": 1, "Він, вона, воно": 1, "Предмети навколо": 2,
                     "Підсумок": 3, "Імена, пастки й самоперевірка": 3}
EXPECTED_EXEMPT = {"act-9", "act-w5"}     # 4-item profession-form quiz; 5-item plan gender diagnostic
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

report: dict = {"blocking": [], "warnings": [], "facts": {}}


def block(msg: str) -> None:
    report["blocking"].append(msg)


def warn(msg: str) -> None:
    report["warnings"].append(msg)


# ---------------------------------------------------------------- text utils
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


def html_to_text(h: str) -> str:
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    h = h.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#x27;", "'").replace("&#39;", "'")
    return norm_text(h)


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
    """orig ⊆ new structurally: dict keys must exist with contained values; lists are
    superset-by-element (each orig element contained in some new element); scalars equal
    modulo stress marks."""
    if isinstance(orig, dict):
        return isinstance(new, dict) and all(k in new and contains(v, new[k]) for k, v in orig.items())
    if isinstance(orig, list):
        return isinstance(new, list) and all(any(contains(o, n) for n in new) for o in orig)
    if isinstance(orig, str):
        return isinstance(new, str) and norm_md(orig) == norm_md(new)
    return orig == new


def missing_stress(text: str, allow: set[str]) -> list[str]:
    """Cyrillic tokens (NFC) with >=2 vowels and no combining acute."""
    bad = []
    for tok in re.findall(rf"[{CYR}'’{ACUTE}]+", nfc(text)):
        if ACUTE in tok:
            continue
        if len(re.findall(r"[аеєиіїоуюяАЕЄИІЇОУЮЯ]", tok)) >= 2 and strip_acute(tok).lower() not in allow:
            bad.append(tok)
    return bad


def git_show(path: str) -> str:
    return subprocess.run(["git", "show", f"{BASE_COMMIT}:{path}"], check=True,
                          capture_output=True, text=True).stdout


# ---------------------------------------------------------------- main
def main() -> int:
    # baseline pinned + hash-verified
    try:
        base = {n: git_show(f"{ORIG}/{n}") for n in BASELINE_SHA}
    except subprocess.CalledProcessError as e:
        block(f"cannot read baseline at {BASE_COMMIT}: {e.stderr.strip()}")
        return finish()
    for n, s in BASELINE_SHA.items():
        got = hashlib.sha256(base[n].encode("utf-8")).hexdigest()
        if got != s:
            block(f"baseline {n} at {BASE_COMMIT} hash {got[:12]} != pinned {s[:12]}")
    base_md, base_acts = base["module.md"], yaml.safe_load(base["activities.yaml"])
    base_vocab = yaml.safe_load(base["vocabulary.yaml"])
    base_secs = sections(base_md)
    base_paras_by_lesson: dict[int, list[str]] = {1: [], 2: [], 3: []}
    for title, body in base_secs.items():
        if title not in SECTION_TO_LESSON:
            block(f"baseline section {title!r} has no lesson mapping (checker config)")
            continue
        base_paras_by_lesson[SECTION_TO_LESSON[title]] += [p for p in paragraphs(body) if len(p.split()) >= 8]
    n_long = sum(len(v) for v in base_paras_by_lesson.values())
    report["facts"]["baseline"] = {"commit": BASE_COMMIT, "prose_tokens": len(strip_comments(base_md).split()),
                                   "long_paragraphs": n_long, "activities": {k: len(v) for k, v in base_acts.items()},
                                   "vocab": len(base_vocab)}

    # protected paths untouched (vs pinned commit) + template hash
    diff = subprocess.run(["git", "diff", "--name-only", BASE_COMMIT, "--", "scripts", "site", "starlight", ".github",
                           "curriculum/l2-uk-en/plans", ORIG], capture_output=True, text=True).stdout.split()
    if diff:
        block(f"protected paths modified: {diff}")
    if not TEMPLATE.exists():
        block("template copy missing at docs/poc/poc-lesson-split-design.html")
    elif hashlib.sha256(TEMPLATE.read_bytes()).hexdigest() != TEMPLATE_SHA:
        block("template copy hash differs from the approved template")
    tracked = subprocess.run(["git", "ls-files", "audit/curriculum-upgrade"], capture_output=True, text=True).stdout.split()
    gen = [p for p in tracked if p.endswith(".json") or p.endswith(".png")]
    if gen:
        block(f"generated evidence must stay untracked: {gen[:5]}")

    # lessons.yaml — fixed contract
    ly_path = LESSONS / "lessons.yaml"
    if not ly_path.exists():
        block(f"{V2}/lessons.yaml missing")
        return finish()
    ly = yaml.safe_load(ly_path.read_text(encoding="utf-8")) or {}
    lessons = ly.get("lessons") or []
    if [L.get("n") for L in lessons] != [1, 2, 3]:
        block(f"lessons must be exactly n=1,2,3 in order; got {[L.get('n') for L in lessons]}")
    if ly.get("closes_module") != 3:
        block(f"closes_module must be 3; got {ly.get('closes_module')!r}")
    exempt = {e.get("id"): (e.get("reason") or "").strip() for e in (ly.get("items_min_exempt") or [])}
    if set(exempt) != EXPECTED_EXEMPT or any(not r for r in exempt.values()):
        block(f"items_min_exempt must be exactly {sorted(EXPECTED_EXEMPT)} with non-empty reasons; got {exempt}")
    provenance = ly.get("provenance") or []

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
        d = LESSONS / f"lesson-{n}"
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
        if prose_tokens < 550:
            block(f"lesson {n}: prose tokens {prose_tokens} < 550 minimum")
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

    # attribution
    for path in list(LESSONS.rglob("*")) + [HTML]:
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".html"} or path.name == "resources.yaml":
            continue
        for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if NAME_RE.search(line) and not ATTR_RE.search(line):
                block(f"unattributed reference-name hit {path.relative_to(ROOT)}:{ln}: {line.strip()[:80]}")

    # render coverage: every long paragraph of every lesson, every activity leaf string >=3 chars,
    # every lemma, every resource title, three lesson screens
    if not HTML.exists():
        block("rendered HTML missing")
    else:
        h = HTML.read_text(encoding="utf-8")
        text = html_to_text(h)
        miss_p = [p for n, t in lesson_md_raw.items() for p in paragraphs(t)
                  if len(p.split()) >= 8 and md_to_text(p) not in text]
        if miss_p:
            block(f"rendered HTML lacks {len(miss_p)} lesson paragraphs, e.g. {md_to_text(miss_p[0])[:70]!r}")
        miss_s = []
        for aid, (n, _, act) in new_acts.items():
            for s in leaves({k: v for k, v in act.items() if k in LIST_FIELDS or k in ("title", "instruction")}):
                if isinstance(s, str) and len(s) >= 3 and norm_text(s) not in text:
                    miss_s.append((aid, s))
        if miss_s:
            block(f"rendered HTML lacks {len(miss_s)} activity strings, e.g. {miss_s[:3]}")
        miss_v = [e.get("lemma") for v in lesson_vocab.values() for e in v if norm_text(str(e.get("lemma"))) not in text]
        if miss_v:
            block(f"rendered HTML lacks vocabulary lemmas: {miss_v[:10]}")
        miss_r = [r.get("title") for v in lesson_res.values() for r in v if norm_text(str(r.get("title"))) not in text]
        if miss_r:
            block(f"rendered HTML lacks resource titles: {miss_r[:5]}")
        for n in (1, 2, 3):
            if f'data-screen="l{n}"' not in h:
                block(f"rendered HTML has no screen button for lesson {n}")
        if 'data-screen="module"' not in h:
            block("rendered HTML has no module screen button")
    return finish()


def finish() -> int:
    out = Path(os.environ.get("VERIFY_OUT") or ROOT / "audit/curriculum-upgrade/pilot-things-have-gender/verify_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["facts"], ensure_ascii=False, indent=2))
    for w in report["warnings"]:
        print("WARN ", w)
    for b in report["blocking"]:
        print("BLOCK", b)
    status = "PASS" if not report["blocking"] else "FAIL"
    print(f"VERIFY_PILOT: {status} ({len(report['blocking'])} blocking, {len(report['warnings'])} warnings) -> {out}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
