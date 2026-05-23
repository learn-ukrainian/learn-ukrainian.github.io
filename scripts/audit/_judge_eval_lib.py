"""Shared Russianism-judge calibration helpers.

The Grok single-model harness and the multi-model matrix use the same
Antonenko-grounded prompt, PR #2006 gold loader, and sev2-tolerant scoring.
Keep this module free of provider-specific subprocess logic.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Ensure cross-package absolute imports (e.g. `scripts.verification.*`) resolve
# regardless of how this module is loaded. When the matrix runner is invoked
# as `python scripts/audit/judge_calibration_matrix.py`, Python sets
# `sys.path[0]` to `scripts/audit/`, so the absolute import
# `from scripts.verification.check_ru_morph import is_russian_pattern` inside
# `_russian_shadow_check` would raise `ModuleNotFoundError` without this
# shim — silently disabling the Russian-shadow morphology channel. See #2050.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB = PROJECT_ROOT / "data" / "sources.db"
VESUM_DB = PROJECT_ROOT / "data" / "vesum.db"
UA_GEC_ROOT = PROJECT_ROOT / "data" / "ua-gec"

PR_2006_REF = "origin/pr-2006"
CALIBRATION_BLOB = "eval/russianism/calibration-cases.jsonl"

CYRILLIC_TOKEN_RE = re.compile(r"[А-Яа-яҐґЄєІіЇї'’ʼ\-]+")

ANTONENKO_SOURCE = "antonenko-davydovych-yak-my-hovorymo"
# Marker words that empirically signal russianism-rule discussion inside an
# Antonenko-Davydovych prose chunk. Validated against the 169-chunk corpus
# (#2049 H3a narrowing): each marker fires on a high-precision subset of
# chunks (8 markers combined cover ~30-40% of chunks). "не слід" was
# considered but excluded — it fires on 97/169 chunks (57%), generic enough
# to be useless as a filter. See `docs/best-practices/audit-standards.md`
# for the calibration cell metrics that motivated this narrowing.
ANTONENKO_PROSE_MARKERS = (
    "правильно",
    "неправильно",
    "не варто",
    "не вживайте",
    "натомість",
    "калька",
    "русизм",
    "російською",
)
UA_GEC_RELEVANT_TAGS = ("F/Calque", "F/Style", "F/Collocation", "G/Case", "G/Gender")
UA_GEC_ANN_RE = re.compile(r"\{([^{}=]*?)=>([^{}]*?):::error_type=([^}]+)\}")


def utc_timestamp() -> str:
    """Return a stable UTC timestamp for artifact metadata."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def pull_calibration_cases(
    *,
    ref: str | None = None,
    blob: str = CALIBRATION_BLOB,
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    """Load the russianism calibration cases.

    Preference order:
    1. Working-tree file at ``project_root / blob`` — PR #2006 is merged
       (commit ``82afad7438`` on 2026-05-15) and the fixture lives on
       main, so the working tree is the canonical source of truth.
    2. Explicit git ref via ``ref=`` (for historical-replay calibrations
       against a specific commit / branch).
    3. Legacy fallback to ``PR_2006_REF`` (``origin/pr-2006``) if it
       still exists locally; pruned-branch path errors clearly.
    """
    text: str | None = None
    source_note: str = ""

    if ref is None:
        working_path = project_root / blob
        if working_path.exists():
            text = working_path.read_text(encoding="utf-8")
            source_note = f"working tree: {working_path}"

    if text is None:
        effective_ref = ref or PR_2006_REF
        proc = subprocess.run(
            ["git", "show", f"{effective_ref}:{blob}"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            sys.exit(
                f"ERROR: could not read {blob} from {effective_ref}.\n"
                f"git stderr: {proc.stderr.strip()}\n"
                f"Working-tree path also missing: {project_root / blob}\n"
                "If origin/pr-2006 has been pruned, refetch with:\n"
                "  git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'\n"
                "Or pass an explicit --ref to a current commit/branch."
            )
        text = proc.stdout
        source_note = f"git show {effective_ref}:{blob}"

    cases: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    if not cases:
        sys.exit(f"ERROR: {source_note} returned zero calibration cases.")
    return cases


def retrieve_antonenko(text: str, k: int = 8, *, db_path: Path = DB) -> list[dict[str, Any]]:
    """Find Antonenko entries whose headwords appear in ``text``.

    Ported from ``scripts/audit/russianism_judge.py`` on ``origin/pr-2006``.
    It grounds the judge prompt in canonical evidence from the local sources DB.
    """
    conn = sqlite3.connect(db_path)
    try:
        words = set(re.findall(r"[А-Яа-яҐґЄєІіЇї'’ʼ\-]+", text.lower()))
        if not words:
            return []
        placeholders = ",".join("?" * len(words))
        rows = conn.execute(
            f"""
            SELECT word, section, page, text
            FROM style_guide
            WHERE word_lower IN ({placeholders})
               OR EXISTS (
                   SELECT 1 FROM (
                       SELECT value FROM json_each(?)
                   ) t WHERE word_lower = t.value
               )
            LIMIT ?
            """,
            (*words, json.dumps(list(words), ensure_ascii=False), k),
        ).fetchall()
    finally:
        conn.close()

    return [
        {"headword": r[0], "section": r[1], "page": r[2], "text": (r[3] or "")[:600]}
        for r in rows
    ]


def _text_tokens(text: str, *, min_len: int = 3) -> list[str]:
    """Lowercased Cyrillic tokens of length >= ``min_len``, deduplicated, sorted."""
    return sorted({m for m in (t.lower() for t in CYRILLIC_TOKEN_RE.findall(text)) if len(m) >= min_len})


def _proper_noun_tokens(text: str) -> set[str]:
    """Lowercased tokens that appear capitalized in non-sentence-initial position.

    Used to exclude proper nouns from VESUM-unknown / Russian-shadow checks.
    ``Львова`` (Lviv-gen) is morphologically valid Ukrainian but absent from
    VESUM's common-form table, so a naive check creates fake Russianism
    candidates on clean travel prose.
    """
    proper_nouns: set[str] = set()
    sentence_boundary = True
    for match in re.finditer(r"\S+", text):
        token = match.group(0)
        cyrillic_match = CYRILLIC_TOKEN_RE.match(token)
        if cyrillic_match and cyrillic_match.group(0)[0].isupper() and not sentence_boundary:
            proper_nouns.add(cyrillic_match.group(0).lower())
        sentence_boundary = token[-1] in ".!?…"
    return proper_nouns


def _heritage_check(text: str, *, db_path: Path = DB) -> list[dict[str, Any]]:
    """Tokens with attestation in Grinchenko (1907) or ESUM etymology.

    Single-word attestation in pre-Soviet / etymological dictionaries is strong
    evidence that the form is canonical Ukrainian, NOT a Russianism.
    """
    tokens = _text_tokens(text)
    if not tokens:
        return []
    conn = sqlite3.connect(db_path)
    try:
        placeholders = ",".join("?" * len(tokens))
        grinchenko = {
            r[0].lower()
            for r in conn.execute(
                f"SELECT word FROM grinchenko WHERE lower(word) IN ({placeholders})",
                tokens,
            ).fetchall()
        }
        esum = {
            r[0].lower()
            for r in conn.execute(
                f"SELECT lemma FROM esum_etymology WHERE lower(lemma) IN ({placeholders})",
                tokens,
            ).fetchall()
        }
    finally:
        conn.close()
    attested = []
    for token in tokens:
        sources = []
        if token in grinchenko:
            sources.append("Grinchenko 1907")
        if token in esum:
            sources.append("ESUM etymology")
        if sources:
            attested.append({"token": token, "sources": sources})
    return attested


def _russian_shadow_check(text: str) -> dict[str, Any]:
    """Run pymorphy3-based Russian-shadow heuristic over Cyrillic tokens.

    Returns ``{"available": bool, "triggered_tokens": [{token, ru_lemma, confidence}]}``.
    ``check_ru_morph.is_russian_pattern`` short-circuits on VESUM hits, so this
    only fires on tokens that are NOT valid Ukrainian forms AND look Russian.
    Proper nouns are excluded to avoid flagging place/person names.
    """
    try:
        from scripts.verification.check_ru_morph import is_russian_pattern
    except ImportError as exc:
        # Silent-disable is the existing contract (the channel renders as
        # "(pymorphy3 unavailable in this environment)" in the prompt),
        # but the failure must be visible in CLI output so missing/broken
        # installs do not bias future calibration runs.
        print(
            f"[_judge_eval_lib._russian_shadow_check] ImportError: {exc}; "
            "channel will render as 'pymorphy3 unavailable'. Fix sys.path "
            "or install pymorphy3 to restore the russian_shadow signal.",
            file=sys.stderr,
        )
        return {"available": False, "triggered_tokens": []}
    proper_nouns = _proper_noun_tokens(text)
    triggered = []
    for token in _text_tokens(text):
        if token in proper_nouns:
            continue
        try:
            result = is_russian_pattern(token)
        except Exception:
            continue
        if result.get("matches_russian"):
            triggered.append(
                {
                    "token": token,
                    "ru_lemma": result.get("russian_lemma"),
                    "confidence": round(float(result.get("confidence", 0.0)), 2),
                }
            )
    return {"available": True, "triggered_tokens": triggered}


def _vesum_unknown(text: str, *, db_path: Path = VESUM_DB) -> list[str]:
    """Cyrillic tokens NOT present in VESUM as a known word_form.

    Proper nouns are excluded — place and person names are typically absent
    from VESUM's common-form table even when morphologically valid Ukrainian.
    """
    tokens = _text_tokens(text)
    if not tokens:
        return []
    if not db_path.exists():
        return []
    proper_nouns = _proper_noun_tokens(text)
    candidate_tokens = [t for t in tokens if t not in proper_nouns]
    if not candidate_tokens:
        return []
    conn = sqlite3.connect(db_path)
    try:
        placeholders = ",".join("?" * len(candidate_tokens))
        known = {
            r[0]
            for r in conn.execute(
                f"SELECT DISTINCT word_form FROM forms WHERE word_form IN ({placeholders})",
                candidate_tokens,
            ).fetchall()
        }
    finally:
        conn.close()
    return sorted(set(candidate_tokens) - known)


def _substantive_tokens(text: str, *, min_len: int = 4) -> list[str]:
    """Lowercased Cyrillic tokens of length >= ``min_len``, deduplicated and
    sorted. Skips short function words so prefix scans stay tight."""
    return sorted({t for t in (m.lower() for m in CYRILLIC_TOKEN_RE.findall(text)) if len(t) >= min_len})


def _antonenko_fulltext_search(
    text: str,
    k: int = 4,
    *,
    db_path: Path = DB,
    snippet_chars: int = 200,
) -> list[dict[str, Any]]:
    """Search the full-text Antonenko corpus (169 page chunks) for phrases
    overlapping with the input text. Complements the 342 keyed headwords
    in ``style_guide``: many calques and register rules are discussed in
    the prose body but never lifted into a structured headword entry.

    Two-step retrieval (#2049 H3a narrowing):

    1. **Narrowed query** — token prefixes AND ``ANTONENKO_PROSE_MARKERS``.
       Returns only chunks that contain BOTH a token-overlap AND at least
       one russianism-discussion marker word. High precision: the H2
       calibration measured 0 prose-chunk citations because the prefix-OR
       FTS was too broad (matched on tangential tokens like ``тижні``);
       requiring a marker word ensures the chunk is actually discussing
       a rule, not just incidentally containing the same token.

    2. **Fallback query** — token prefixes only (the pre-H3a behavior).
       Activated when the narrowed query returns zero hits, so we never
       lose recall relative to H2; the cost is the marker filter is
       skipped on those cases. Each hit carries ``marker_narrowed: bool``
       so downstream consumers can see whether the filter fired.

    Strategy: tokenize input → drop tokens <4 chars (Ukrainian function
    words) → prefix-truncate at 5 chars (handle inflection) → FTS5 query
    against ``textbooks_fts`` restricted to ``source_file =
    antonenko-davydovych-yak-my-hovorymo``. Returns up to ``k`` hits
    ordered by FTS5 default ranking, with snippets centered on the first
    matched substring.
    """
    tokens = _substantive_tokens(text)
    if not tokens:
        return []
    prefixes = sorted({t[:5] for t in tokens if len(t) >= 5})
    if not prefixes:
        return []

    prefix_or = " OR ".join(f'"{p}"*' for p in prefixes)
    marker_or = " OR ".join(f'"{m}"' for m in ANTONENKO_PROSE_MARKERS)
    narrowed_query = f"({prefix_or}) AND ({marker_or})"

    def _run_query(fts_query: str) -> list[tuple[str, str]]:
        conn = sqlite3.connect(db_path)
        try:
            return conn.execute(
                """
                SELECT t.title, t.text
                FROM textbooks_fts f
                JOIN textbooks t ON t.id = f.rowid
                WHERE f.textbooks_fts MATCH ?
                  AND t.source_file = ?
                LIMIT ?
                """,
                (fts_query, ANTONENKO_SOURCE, k * 4),  # over-fetch then snippet-rank
            ).fetchall()
        finally:
            conn.close()

    marker_narrowed = True
    try:
        rows = _run_query(narrowed_query)
    except sqlite3.OperationalError:
        return []
    if not rows:
        # Fallback: token prefixes only. Preserves H2-level recall when no
        # chunk has both token overlap AND a russianism marker.
        marker_narrowed = False
        try:
            rows = _run_query(prefix_or)
        except sqlite3.OperationalError:
            return []
        if not rows:
            return []

    hits: list[dict[str, Any]] = []
    for title, chunk_text in rows:
        chunk_lower = chunk_text.lower()
        best_pos = None
        best_token = None
        for tok in tokens:
            pos = chunk_lower.find(tok[:5])
            if pos >= 0 and (best_pos is None or pos < best_pos):
                best_pos = pos
                best_token = tok
        if best_pos is None:
            continue
        start = max(0, best_pos - snippet_chars // 4)
        snippet = chunk_text[start:start + snippet_chars].strip().replace("\n", " ")
        # extract page number from title like "Antonenko-Davydovych «Як ми говоримо», p. 142"
        page_match = re.search(r"p\.\s*(\d+)", title or "")
        hits.append({
            "page": int(page_match.group(1)) if page_match else None,
            "matched_token": best_token,
            "snippet": snippet,
            "marker_narrowed": marker_narrowed,
        })
        if len(hits) >= k:
            break
    return hits


_UA_GEC_INDEX: list[tuple[frozenset[str], str, str, str]] | None = None


def _ua_gec_load_index(*, root: Path = UA_GEC_ROOT) -> list[tuple[frozenset[str], str, str, str]]:
    """Lazy-build an in-memory index of UA-GEC annotation triples.

    Scans every ``*.ann`` file under ``{gec-only,gec-fluency}/{train,test}/annotated/``,
    extracts ``{ERROR=>CORRECT:::error_type=TAG}`` triples, keeps only the
    russianism-adjacent tags in :data:`UA_GEC_RELEVANT_TAGS`, and stores
    them as ``(error_token_set, error_str, correct_str, tag)`` tuples.

    Skipped: empty-error insertions (``error_str == ""``) — those carry no
    token signal for retrieval and would match every input. The index is
    built once per process; subsequent calls return the cached list.
    """
    global _UA_GEC_INDEX
    if _UA_GEC_INDEX is not None:
        return _UA_GEC_INDEX
    if not root.exists():
        _UA_GEC_INDEX = []
        return _UA_GEC_INDEX
    index: list[tuple[frozenset[str], str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    relevant = set(UA_GEC_RELEVANT_TAGS)
    for ann_path in root.glob("data/gec-*/*/annotated/*.ann"):
        try:
            content = ann_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in UA_GEC_ANN_RE.finditer(content):
            error_str = match.group(1).strip()
            correct_str = match.group(2).strip()
            tag = match.group(3).strip()
            if tag not in relevant or not error_str:
                continue
            key = (error_str, correct_str, tag)
            if key in seen:
                continue
            seen.add(key)
            error_tokens = frozenset(
                t.lower() for t in CYRILLIC_TOKEN_RE.findall(error_str) if len(t) >= 3
            )
            if not error_tokens:
                continue
            index.append((error_tokens, error_str, correct_str, tag))
    _UA_GEC_INDEX = index
    return _UA_GEC_INDEX


def _ua_gec_calque_search(
    text: str,
    k: int = 4,
    *,
    min_overlap: int = 2,
) -> list[dict[str, Any]]:
    """Find UA-GEC annotation triples whose error tokens overlap the input.

    Returns up to ``k`` triples ranked by overlap count. ``min_overlap``
    defaults to 2 so single-token false positives (one frequent word
    matching half the corpus) are suppressed. For single-token UA-GEC
    errors, the threshold is relaxed to 1 (single-token annotations are
    rare and tend to be high-precision substitutions like
    ``повістку → порядок``).

    UA-GEC is the Grammarly Ukraine team's gold-standard learner-error
    corpus (MIT-licensed). Tags retrieved: F/Calque, F/Style,
    F/Collocation, G/Case, G/Gender — the russianism-adjacent error
    classes per ``UA_GEC_RELEVANT_TAGS``.
    """
    input_tokens = {t.lower() for t in CYRILLIC_TOKEN_RE.findall(text) if len(t) >= 3}
    if not input_tokens:
        return []
    index = _ua_gec_load_index()
    scored: list[tuple[int, tuple[frozenset[str], str, str, str]]] = []
    for entry in index:
        error_tokens = entry[0]
        overlap = len(error_tokens & input_tokens)
        effective_min = 1 if len(error_tokens) == 1 else min_overlap
        if overlap >= effective_min:
            scored.append((overlap, entry))
    scored.sort(key=lambda item: (-item[0], item[1][3], item[1][1]))
    return [
        {
            "error": entry[1],
            "correct": entry[2],
            "tag": entry[3],
            "overlap": overlap,
        }
        for overlap, entry in scored[:k]
    ]


def retrieve_evidence(text: str) -> dict[str, Any]:
    """Aggregate all evidence signals for one judge prompt.

    Combines Antonenko-Davydovych structured headwords (style_guide table)
    AND full-book prose chunks (textbooks table), Grinchenko/ESUM token
    attestation (heritage defense), pymorphy3 Russian-shadow morphology
    detection, VESUM-unknown token enumeration, and UA-GEC professional-
    annotator calque/style/collocation triples.
    """
    return {
        "antonenko": retrieve_antonenko(text),
        "antonenko_fulltext": _antonenko_fulltext_search(text),
        "heritage_attested": _heritage_check(text),
        "russian_shadow": _russian_shadow_check(text),
        "vesum_unknown_tokens": _vesum_unknown(text),
        "ua_gec_calques": _ua_gec_calque_search(text),
    }


def retrieve_ua_gec(text: str, k: int = 8, *, db_path: Path = DB) -> list[dict[str, Any]]:
    """Find UA-GEC error pairs matching words in ``text``.

    Searches the ``ua_gec_errors`` FTS5 table for error→correction triples
    whose ``error`` substring overlaps any word in the input. UA-GEC is
    Grammarly UA's MIT-licensed human-annotated learner-error corpus
    (8,937 rows filtered to russianism-relevant tags: F/Calque, F/Collocation,
    G/Case, G/Gender). Densest evidence source for phraseological and
    register calques that don't have Antonenko-Davydovych headword entries.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        words = set(re.findall(r"[А-Яа-яҐґЄєІіЇї'’ʼ\-]+", text.lower()))
        if not words:
            return []

        query_parts = []
        for word in words:
            if len(word) >= 3:
                # Escape double quotes for FTS5
                safe_word = word.replace('"', '""')
                query_parts.append(f'"{safe_word}"')

        if not query_parts:
            return []

        fts_query = " OR ".join(query_parts)
        rows = conn.execute(
            """
            SELECT m.error, m.correct, m.error_type, m.doc_id
            FROM ua_gec_errors_fts f
            JOIN ua_gec_errors m ON f.rowid = m.id
            WHERE f.error MATCH ?
            ORDER BY f.rank
            LIMIT ?
            """,
            (fts_query, k),
        ).fetchall()
    except sqlite3.OperationalError:
        # ua_gec_errors table may not yet exist on every checkout (e.g.
        # before this PR's ingest landed); fail soft.
        return []
    finally:
        conn.close()

    return [
        {"error": r["error"], "correct": r["correct"], "type": r["error_type"], "doc_id": r["doc_id"]}
        for r in rows
    ]


def build_judge_prompt(
    target_text: str,
    antonenko_entries: list[dict[str, Any]],
    ua_gec_entries: list[dict[str, Any]] | None = None,
) -> str:
    """Universal Russianism-judge prompt, identical across model families.

    Preserved at main as the production baseline. The H1 evidence-rich variant
    documented in ``audit/2026-05-17-judge-calibration-h1/COMPARISON.md`` was
    falsified on the current 12-case calibration set (recall collapsed because
    the evidence catalog couldn't anchor 14 of 16 sev>=2 flags). The
    ``retrieve_evidence`` helper below is preserved for H2c use (typed
    calibration set authoring + per-channel coverage metrics).

    The optional ``ua_gec_entries`` parameter renders human-annotated UA-GEC
    error→correction pairs as additional evidence. Backward-compatible: when
    omitted or None, the prompt body is byte-identical to the 2-argument form.
    """
    evidence = ""
    if antonenko_entries:
        evidence += (
            "## Relevant Antonenko-Davydovych entries "
            "(potentially applicable rules):\n\n"
        )
        for i, entry in enumerate(antonenko_entries[:8], 1):
            evidence += f"### Antonenko Rule {i}: {entry['headword']}\n{entry['text']}\n\n"

    if ua_gec_entries:
        evidence += "## UA-GEC human-annotated error pairs matching text:\n\n"
        for entry in ua_gec_entries[:8]:
            evidence += (
                f"- Error: \"{entry['error']}\" → Correction: "
                f"\"{entry['correct']}\" (Type: {entry['type']})\n"
            )
        evidence += "\n"

    if not evidence:
        evidence = (
            "(No directly-keyed Antonenko entries or UA-GEC pairs found for words in this text. "
            "Apply general knowledge of Ukrainian register and Russianism patterns.)\n"
        )

    return f"""You are an expert Ukrainian-language proofreader specializing in identifying Russianisms (русизми), calques (кальки), Surzhyk (суржик), and unnatural Ukrainian phrasing.
Your primary authorities are Антоненко-Давидович «Як ми говоримо» and UA-GEC (Ukrainian Grammatical Error Corpus, Grammarly UA, MIT-licensed).

## Text to evaluate

```
{target_text}
```

{evidence}

## Your task

Identify EVERY Russianism, calque, Surzhyk, or unnatural Ukrainian construction in the text above. For each issue:

- Quote the exact problematic phrase
- Cite the relevant authority (Antonenko rule by headword or UA-GEC pattern) or general principle
- Provide the correct Ukrainian alternative
- Severity: 1=minor (debatable), 2=clear Russianism, 3=blatant calque or borrowing

If the text is genuinely clean Ukrainian with NO Russianisms, output `{{"verdict": "clean", "issues": []}}`.

Otherwise output JSON with this exact shape:

```json
{{
  "verdict": "issues_found",
  "issues": [
    {{"phrase": "...", "rule": "...", "correct": "...", "severity": 1-3}}
  ]
}}
```

Output ONLY the JSON object — no commentary, no markdown fences, no preamble."""


def _render_evidence_section(evidence: dict[str, Any]) -> str:
    """Render the six H2 evidence channels as Markdown sections."""
    sections: list[str] = []

    ant_kw = evidence.get("antonenko") or []
    if ant_kw:
        sections.append(
            "### Antonenko-Davydovych — keyed headword entries (style_guide table)\n"
            "These are the 342 structured entries. Each is a canonical rule.\n\n"
            + "\n".join(
                f"- **{e['headword']}** (p.{e['page']}): {e['text'][:400]}"
                for e in ant_kw[:6]
            )
        )
    else:
        sections.append("### Antonenko-Davydovych — keyed headword entries\n(no headword hits)")

    ant_ft = evidence.get("antonenko_fulltext") or []
    if ant_ft:
        # Hits are uniformly marker-narrowed or uniformly fallback (the
        # search function makes that choice once per call). Read the flag
        # off the first hit; missing/legacy hits without the flag default
        # to non-narrowed for back-compatible rendering.
        narrowed = bool(ant_ft[0].get("marker_narrowed", False))
        if narrowed:
            preamble = (
                "**Narrowed retrieval (H3a):** every chunk below contains both "
                "a token-overlap with the target text AND a russianism-discussion "
                "marker word (`правильно`, `неправильно`, `не варто`, `не вживайте`, "
                "`натомість`, `калька`, `русизм`, `російською`) — i.e. the chunk is "
                "discussing a specific rule, not just incidentally sharing a token. "
                "These are higher-precision cites than the H2 prefix-only retrieval."
            )
        else:
            preamble = (
                "**Fallback retrieval:** the H3a marker-narrowed query returned zero "
                "chunks for this text, so we fell back to the H2 prefix-only matcher. "
                "Chunks below share a token-prefix with the target but may be "
                "discussing an unrelated rule — verify before citing."
            )
        sections.append(
            "### Antonenko-Davydovych — full-book prose hits (textbooks table, 169 page chunks)\n"
            "Complements the 342 headwords above. May surface register rules and discussion absent from the keyed index.\n\n"
            f"{preamble}\n\n"
            + "\n".join(
                f"- p.{h['page']} (matched on `{h['matched_token']}`): {h['snippet']}"
                for h in ant_ft[:4]
            )
        )
    else:
        sections.append("### Antonenko-Davydovych — full-book prose hits\n(no prose hits)")

    heritage = evidence.get("heritage_attested") or []
    if heritage:
        sections.append(
            "### Heritage attestation (Grinchenko 1907 + ESUM etymology)\n"
            "Single-word attestation in pre-Soviet / etymological dictionaries is strong "
            "evidence that the form is canonical Ukrainian, **not** a Russianism. Do not "
            "flag attested forms below as Russianisms without overriding evidence.\n\n"
            + "\n".join(
                f"- `{e['token']}` — attested in: {', '.join(e['sources'])}"
                for e in heritage[:12]
            )
        )
    else:
        sections.append("### Heritage attestation\n(no Grinchenko/ESUM attestations)")

    rs = evidence.get("russian_shadow") or {}
    rs_tokens = rs.get("triggered_tokens") if rs.get("available") else None
    if rs_tokens:
        sections.append(
            "### Russian-shadow morphology hits (pymorphy3, fires only on non-VESUM tokens)\n"
            + "\n".join(
                f"- `{t['token']}` → ru lemma `{t['ru_lemma']}` (confidence {t['confidence']})"
                for t in rs_tokens[:8]
            )
        )
    elif rs.get("available"):
        sections.append("### Russian-shadow morphology hits\n(no Russian-pattern tokens)")
    else:
        sections.append("### Russian-shadow morphology hits\n(pymorphy3 unavailable in this environment)")

    vu = evidence.get("vesum_unknown_tokens") or []
    if vu:
        sections.append(
            "### VESUM-unknown Cyrillic tokens (not in 6.7M form table; proper nouns filtered)\n"
            + ", ".join(f"`{t}`" for t in vu[:20])
        )
    else:
        sections.append("### VESUM-unknown Cyrillic tokens\n(every Cyrillic token is a known Ukrainian form)")

    ua_gec = evidence.get("ua_gec_calques") or []
    if ua_gec:
        sections.append(
            "### UA-GEC corpus — professionally-annotated learner errors (~7K triples across F/Calque, F/Style, F/Collocation, G/Case, G/Gender)\n"
            "Source: Grammarly Ukraine team, MIT-licensed gold-standard error-correction corpus.\n"
            "**Interpretation rules:**\n"
            "- `F/Calque` and `F/Collocation` hits are **strong** evidence of a russianism / unnatural pairing.\n"
            "- `F/Style` hits are **weaker** — they often record stylistic preferences (e.g. an annotator may prefer `Добрий день` over the equally-correct canonical greeting `Доброго дня!`). Do **not** flag a phrase as a Russianism on F/Style evidence alone unless the substitution is also supported by Antonenko or your independent knowledge.\n"
            "- `G/Case` and `G/Gender` hits indicate Russian-pattern grammar, but require that the target text actually contains the exact `error` form (or a close inflection) — verify before citing.\n\n"
            + "\n".join(
                f"- [{h['tag']}] `{h['error']}` → `{h['correct']}` (overlap={h['overlap']})"
                for h in ua_gec[:6]
            )
        )
    else:
        sections.append("### UA-GEC corpus matches\n(no overlapping annotation triples)")

    return "\n\n".join(sections)


def build_judge_prompt_h2(target_text: str, evidence: dict[str, Any]) -> str:
    """H2 evidence-rich judge prompt with cite-or-forbid + UA-GEC + Antonenko prose.

    Differences vs ``build_judge_prompt`` (baseline preserved on
    ``main``/``grok_judge_calibration.py``):

    1. Six evidence channels (was: only Antonenko headwords).
    2. Cite-or-forbid: every issue must include ``evidence_type`` ∈
       ``{antonenko_headword, antonenko_prose, ua_gec_calque,
       vesum_unknown, russian_shadow, general_principle}`` and a
       ``evidence_quote`` field naming the specific source.
    3. ``general_principle`` is allowed but reserved for cases the
       judge can defend without retrieval evidence — encourages the
       model to mark uncertain calls explicitly.
    4. Canonical-greeting protection: explicit instruction not to flag
       ``Доброго дня!``, ``Добрий день!``, ``Як ваші справи?``,
       ``будь ласка``, ``дякую`` as Russianisms (preserves the H1
       FP fix even when UA-GEC F/Style fuzzes a greeting hit).
    """
    evidence_block = _render_evidence_section(evidence)

    return f"""You are an expert Ukrainian-language proofreader specializing in Russianisms (русизми), calques (кальки), Surzhyk (суржик), and unnatural Ukrainian phrasing.

## Default verdict: CLEAN

Modern Ukrainian has many regional, colloquial, and stylistic variants that are NOT Russianisms. Default to `clean` and flag only when you have concrete, citeable evidence.

The following forms are **canonical Ukrainian** and must NEVER be flagged as Russianisms regardless of any retrieved evidence below:

- Greetings: `Доброго дня!`, `Добрий день!`, `Доброго ранку!`, `Добрий вечір!`, `Привіт!`
- Polite formulas: `Як ваші справи?`, `Будь ласка`, `Дякую`, `Перепрошую`
- Standard pronoun forms in their normal grammatical roles: `вас`, `вам`, `вами`, `усе`, `гаразд`

If a UA-GEC F/Style entry below substitutes one of these, treat it as a stylistic preference of the annotator and ignore it.

## Text to evaluate

```
{target_text}
```

## Retrieved evidence (six channels)

{evidence_block}

## Your task

Identify Russianisms, calques, Surzhyk, or unnatural Ukrainian only when you can cite specific evidence. Apply the **cite-or-forbid rule**: every issue must reference one concrete evidence anchor.

For each issue:

- `phrase` — exact problematic substring from the target text (must appear literally).
- `correct` — the natural Ukrainian alternative.
- `severity` — 1=minor/debatable, 2=clear Russianism, 3=blatant calque or borrowing.
- `evidence_type` — one of: `antonenko_headword`, `antonenko_prose`, `ua_gec_calque`, `vesum_unknown`, `russian_shadow`, `general_principle`.
- `evidence_quote` — short fragment naming the source (headword + page, prose-page snippet, UA-GEC `error→correct` pair, VESUM-unknown token, or a one-sentence general principle).

If you cite `general_principle`, you are stating that no retrieved evidence directly supports the flag and you are calling it on your own judgment. Use sparingly.

If the text is genuinely clean Ukrainian with NO Russianisms, output `{{"verdict": "clean", "issues": []}}`.

Otherwise output JSON with this exact shape:

```json
{{
  "verdict": "issues_found",
  "issues": [
    {{"phrase": "...", "correct": "...", "severity": 1-3, "evidence_type": "antonenko_headword|antonenko_prose|ua_gec_calque|vesum_unknown|russian_shadow|general_principle", "evidence_quote": "..."}}
  ]
}}
```

Output ONLY the JSON object — no commentary, no markdown fences, no preamble."""


def parse_json_verdict(raw_content: str, *, duration_s: float = 0.0) -> dict[str, Any]:
    """Parse a judge response into the verdict shape used by scoring."""
    match = re.search(r"\{.*\}", raw_content or "", re.DOTALL)
    if not match:
        return {
            "verdict": "judge_error",
            "raw": (raw_content or "")[:500],
            "duration_s": duration_s,
            "note": "no JSON object in response",
        }
    try:
        verdict = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return {
            "verdict": "json_parse_error",
            "raw": match.group(0)[:500],
            "error": str(exc),
            "duration_s": duration_s,
        }
    if isinstance(verdict, dict):
        verdict["_duration_s"] = duration_s
        return verdict
    return {
        "verdict": "json_parse_error",
        "raw": match.group(0)[:500],
        "error": "parsed JSON was not an object",
        "duration_s": duration_s,
    }


def score_case(verdict: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    """Score one case with PR #2006's sev2-tolerant approximation.

    Case-level accuracy is clean-vs-issues. Precision/recall/F1 count only
    severity >= 2 flags, so debatable severity-1 flags do not dominate routing.
    """
    expected_clean = bool(gold.get("expected_clean"))
    judged_clean = verdict.get("verdict") == "clean"
    case_acc = expected_clean == judged_clean

    issues = verdict.get("issues") or []
    sev2_plus_judge = sum(
        1
        for item in issues
        if isinstance(item, dict)
        and isinstance(item.get("severity"), int)
        and item["severity"] >= 2
    )
    expected_flags_n = len(gold.get("expected_flags") or [])

    if expected_clean:
        tp = 0
        fp = sev2_plus_judge
        fn = 0
    else:
        tp = min(sev2_plus_judge, expected_flags_n)
        fn = max(0, expected_flags_n - sev2_plus_judge)
        fp = max(0, sev2_plus_judge - expected_flags_n)

    return {
        "case_acc": case_acc,
        "judged_clean": judged_clean,
        "expected_clean": expected_clean,
        "judge_sev2_plus_count": sev2_plus_judge,
        "expected_flags_count": expected_flags_n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def aggregate(scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-case scores into precision, recall, F1, and case accuracy."""
    tp = sum(int(s["tp"]) for s in scores)
    fp = sum(int(s["fp"]) for s in scores)
    fn = sum(int(s["fn"]) for s in scores)
    n = len(scores)
    case_acc = sum(1 for s in scores if s["case_acc"]) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    rounded_case_acc = round(case_acc, 4)
    return {
        "n": n,
        "case_accuracy": rounded_case_acc,
        "case_acc": rounded_case_acc,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def judgment_row_from_case(
    *,
    case: dict[str, Any],
    model: str,
    verdict: dict[str, Any],
    score: dict[str, Any],
) -> dict[str, Any]:
    """Build the legacy judgment row written by ``grok_judge_calibration.py``."""
    return {
        "prompt_id": case["prompt_id"],
        "model": model,
        "verdict": verdict.get("verdict"),
        "judge_sev2_plus_count": score["judge_sev2_plus_count"],
        "expected_flags_count": score["expected_flags_count"],
        "case_acc": score["case_acc"],
        "duration_s": round(float(verdict.get("_duration_s", verdict.get("duration_s", 0.0))), 2),
        "raw": verdict,
    }


def render_grok_report(
    *,
    model: str,
    agg: dict[str, Any],
    judgments_path: Path,
    calibration_blob: str = CALIBRATION_BLOB,
    ref: str = PR_2006_REF,
) -> str:
    """Render the legacy single-model Grok report body."""
    report_lines = [
        f"# Grok 4.3 Russianism judge calibration — {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "",
        f"Model: `{model}` via Hermes OAuth (`api.x.ai/v1`)",
        f"Cases: {agg['n']} (from `{calibration_blob}` on `{ref}`)",
        "",
        "## Aggregate",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Case accuracy | **{agg['case_accuracy']*100:.1f}%** |",
        f"| Precision (sev≥2) | {agg['precision']*100:.1f}% |",
        f"| Recall (sev≥2) | {agg['recall']*100:.1f}% |",
        f"| **F1 (sev≥2)** | **{agg['f1']*100:.1f}%** |",
        f"| tp / fp / fn | {agg['tp']} / {agg['fp']} / {agg['fn']} |",
        "",
        "## Reference leaderboard (2026-05-15, n=12)",
        "",
        "| Judge | F1 | Precision | Recall | Case acc |",
        "|---|---:|---:|---:|---:|",
        "| claude-opus-4-7 | 86% | 79% | 94% | 100% |",
        "| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |",
        "| gpt-5.5 | 78% | 90% | 69% | 83% |",
        f"| **{model}** | **{agg['f1']*100:.0f}%** | **{agg['precision']*100:.0f}%** | **{agg['recall']*100:.0f}%** | **{agg['case_accuracy']*100:.0f}%** |",
        "",
        f"Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `{ref}` for the prior 3 judges.",
        "",
        "## Per-case breakdown",
        "",
        "| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |",
        "|---|---|---|:---:|---:|---:|",
    ]
    with judgments_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            expected = "clean" if row["expected_flags_count"] == 0 else "issues"
            mark = "✓" if row["case_acc"] else "✗"
            report_lines.append(
                f"| `{row['prompt_id']}` | {expected} | {row['verdict']} | {mark} | "
                f"{row['judge_sev2_plus_count']} | {row['duration_s']:.1f} |"
            )
    return "\n".join(report_lines) + "\n"
