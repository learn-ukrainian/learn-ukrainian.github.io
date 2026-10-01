"""One query surface for documents, data stores and resources (#9412).

``find(query)`` answers "where is X and is it current?" in one call, from three
sources read at request time, with no persisted index:

1. **Catalogue** (``docs/knowledge/catalogue.yaml``): query words against each
   entry's keywords, id, entry-point topics and paths, store names and purpose.
   A strong match returns the family's entry points, or a data store with its
   query hint and producers (stores cannot be grepped).
2. **Tracked names**: query words against every path in Git's index outside the
   docs inventory's privacy exclusions (names only; no body is read).
3. **Tracked text**: ``git grep --cached`` over the paths that PR 1's
   ``body_readable`` gate admits (content-searchable families only). Pathnames
   are never protocol or shell text: the search names roots with ``:(literal)``
   pathspecs and drops every unreadable path with ``:(exclude,literal)``; every
   result is checked against the gate again before it is used.

Ranking: catalogue matches first; then, by match band (whole phrase in a name,
whole phrase in text, every word, then the share of the query's rarity-weighted
words), lifecycle (current, then draft or unclassified, historical, superseded;
backup-like copies last), and path order. Every hit carries its family, status,
replacement and the family's query hint. The result states its coverage and
says ``incomplete`` with a reason when a budget, a failed search worker or a
one-character word not searched alone cut the search short, so a cutoff is never
reported as "no source". ``limit`` and ``budget_seconds`` are validated before any
search starts (``FindError``, a ValueError).

The CLI is ``python -m scripts.docs.find``; the Monitor API mirrors it at
``GET /api/knowledge/find``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import threading
import time
import unicodedata
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from scripts.docs import catalogue as cat

MAX_QUERY_CHARS = 200
DEFAULT_LIMIT = 20
MAX_LIMIT = 200
MAX_TERMS = 8
MAX_FAMILY_MATCHES = 5
MAX_ENTRYPOINTS_PER_FAMILY = 3
MAX_PRODUCERS_PER_STORE = 3
EXCERPT_CHARS = 200
EXCERPT_LINES_PER_FILE = 10
RERANK_POOL = 60  # content candidates whose matching lines are read to rank and quote them
LONG_LINE = 1000  # a matching line longer than this (a one-line data dump) is no evidence of proximity
DEFAULT_BUDGET_SECONDS = 10.0
MAX_BUDGET_SECONDS = 120.0
GREP_OUTPUT_CAP = 16 * 1024 * 1024
EXCERPT_OUTPUT_CAP = 32 * 1024 * 1024
LIFECYCLE_RANK = {'active': 0, None: 0, 'draft': 1, 'residual': 1, 'archive': 2, 'superseded': 3}
BACKUP_RANK = 4
STATUS_WORDS = {'active': 'current', 'archive': 'historical', 'superseded': 'superseded', 'draft': 'draft',
                'residual': 'unclassified', None: 'uncatalogued'}
BACKUP_SUFFIXES = ('.backup', '.bak', '.orig', '.truncated', '.old', '.tmp', '~')
# Words that carry no locating signal in a question ("where is the list of ...").
STOPWORDS = frozenset({
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can', 'do', 'does', 'for', 'from', 'how', 'i', 'in',
    'is', 'it', 'its', 'me', 'my', 'of', 'on', 'or', 'our', 'the', 'this', 'that', 'to', 'what', 'when',
    'where', 'which', 'who', 'why', 'with', 'we', 'you', 'still', 'per', 'about', 'has', 'have', 'into',
    'there', 'their', 'they', 'these', 'those', 'was', 'were', 'will', 'would', 'should', 'could', 'not',
    'no', 'if', 'so', 'than', 'then', 'any', 'all', 'get', 'find', 'look',
    'і', 'й', 'та', 'в', 'у', 'на', 'з', 'із', 'до', 'що', 'як', 'де', 'чи', 'це', 'для', 'про',
})
# Separators between words. Apostrophes stay inside words (Ukrainian п'ять, пʼять).
SEPARATORS = re.compile(r"[\s_\-./\\:,;()\[\]{}<>\"`|+*?!@#=&%^~$]+")


FAMILY_ID_PATTERN = r'^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$'


class FindError(ValueError):
    """A request ``find`` cannot answer (bad query, limit, budget or family); ``code`` names the rule."""

    def __init__(self, code: str, message: str):
        super().__init__(f'{code}: {message}')
        self.code = code
        self.message = message


LIMIT_MESSAGE = f'limit must be a whole number between 1 and {MAX_LIMIT}'
BUDGET_MESSAGE = f'budget must be a finite number of seconds greater than 0 and at most {MAX_BUDGET_SECONDS:g}'


def checked_limit(limit: object) -> int:
    """``limit`` when it is an int (not a bool) in 1..MAX_LIMIT; FindError('limit') otherwise."""
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise FindError('limit', LIMIT_MESSAGE)
    return limit


INTEGER_TEXT = re.compile(r'[0-9]{1,6}')


def limit_from_text(text: str) -> int:
    """A limit typed as text (CLI argument, query string) as an int in 1..MAX_LIMIT.

    Only ASCII digits are a whole number: a sign, a decimal point, an exponent,
    whitespace or an empty value is FindError('limit') with the fixed message, before
    any conversion, so the CLI and the Monitor API accept exactly the same texts.
    """
    if not INTEGER_TEXT.fullmatch(text):
        raise FindError('limit', LIMIT_MESSAGE)
    return checked_limit(int(text))


def checked_budget(budget: object) -> float:
    """``budget`` in seconds as a float when it is an int or float (not a bool) in (0, MAX_BUDGET_SECONDS].

    The range test runs before any conversion, so NaN, infinities, huge ints and huge
    floats are rejected here and never reach a timer. FindError('budget') otherwise.
    """
    if type(budget) not in (int, float) or not 0 < budget <= MAX_BUDGET_SECONDS:
        raise FindError('budget', BUDGET_MESSAGE)
    return float(budget)


# ---------------------------------------------------------------- text normalisation

def normalise(text: str) -> str:
    """NFC, then Unicode case folding (no stemming)."""
    return unicodedata.normalize('NFC', text).casefold()


def words(text: str) -> list[str]:
    return [w for w in SEPARATORS.split(normalise(text)) if w]


def clean_query(raw: str) -> str:
    """NFC, every non-printable character (controls, line separators, format characters) as a space,
    whitespace collapsed, capped at MAX_QUERY_CHARS."""
    text = unicodedata.normalize('NFC', raw)
    text = ''.join(c if c.isprintable() else ' ' for c in text)
    return ' '.join(text.split())[:MAX_QUERY_CHARS].strip()


def query_terms(query: str) -> list[str]:
    """Distinct query words without stopwords (all words when only stopwords remain), at most MAX_TERMS."""
    found = list(dict.fromkeys(words(query)))
    kept = [w for w in found if w not in STOPWORDS]
    return (kept or found)[:MAX_TERMS]


def escape_excerpt(text: str) -> str:
    """Every non-printable character as a visible escape, so an excerpt is one safe line."""
    out = []
    for char in text:
        if char.isprintable():
            out.append(char)
        elif ord(char) < 0x100:
            out.append(f'\\x{ord(char):02x}')
        elif ord(char) < 0x10000:
            out.append('\\u' + f'{ord(char):04x}')
        else:
            out.append(f'\\U{ord(char):08x}')
    return ''.join(out)


def _prefix_hits(terms: list[str], field_words: list[str]) -> set[str]:
    return {t for t in terms if any(w.startswith(t) for w in field_words)}


def _contains_words(haystack: list[str], needle: list[str], *, prefix_last: bool = True) -> bool:
    """``needle`` occurs as consecutive words in ``haystack``; with ``prefix_last`` its last word
    may be a prefix of the haystack word (a query's last word typed short)."""
    if not needle or len(needle) > len(haystack):
        return False
    last = needle[-1]
    for i in range(len(haystack) - len(needle) + 1):
        word = haystack[i + len(needle) - 1]
        if haystack[i:i + len(needle) - 1] == needle[:-1] and (word.startswith(last) if prefix_last else word == last):
            return True
    return False


def is_backup_like(path: str) -> bool:
    return path.endswith(BACKUP_SUFFIXES)


# ---------------------------------------------------------------- catalogue state

@dataclass
class State:
    """The validated catalogue and the Git index it was checked against (one request's view)."""
    repo: Path
    catalogue: dict | None
    report: cat.Report
    files: dict[str, cat.IndexEntry]
    load_error: str | None = None
    by_id: dict[str, dict] = field(default_factory=dict)

    def lifecycle_of(self, path: str) -> tuple[str | None, str | None]:
        """(family id, lifecycle) for a path in the denominator; (None, None) outside it."""
        return self.report.resolved.get(path, (None, None))

    def superseded_by(self, path: str, family: str | None, lifecycle: str | None) -> str | None:
        if lifecycle != 'superseded' or family is None:
            return None
        entry = self.by_id.get(family, {})
        for override in entry.get('overrides', []):
            if override['path'] == path:
                return override.get('superseded_by')
        return entry.get('superseded_by')


_STATE_CACHE: OrderedDict[str, State] = OrderedDict()
_STATE_CACHE_SIZE = 4
_STATE_LOCK = threading.Lock()


def load_state(repo: Path) -> State:
    """Validate the catalogue against the index; memoised in memory by the exact inputs.

    The memo key hashes every index record, the catalogue, the schema and the two owner
    registries, so any change to them is a fresh validation. Nothing is written to disk.
    """
    files = cat.index_entries(repo)
    digest = hashlib.sha256()
    for path, entry in files.items():
        digest.update(f'{entry.mode} {entry.oid}\t'.encode() + path.encode('utf-8') + b'\0')
    raw: dict[str, bytes] = {}
    for rel in (cat.CATALOGUE_PATH, cat.SCHEMA_PATH):
        try:
            raw[rel] = (repo / rel).read_bytes()[:cat.MAX_CATALOGUE_BYTES + 1]
        except OSError:
            raw[rel] = b''
        digest.update(rel.encode() + b'\0' + hashlib.sha256(raw[rel]).digest())
    for rel, _ in cat.OWNER_SOURCES:
        digest.update(rel.encode() + b'\0' + files[rel].oid.encode() if rel in files else b'-')
    key = f'{repo}\0{digest.hexdigest()}'
    with _STATE_LOCK:
        if key in _STATE_CACHE:
            _STATE_CACHE.move_to_end(key)
            return _STATE_CACHE[key]
    state = _build_state(repo, files, raw)
    with _STATE_LOCK:
        _STATE_CACHE[key] = state
        while len(_STATE_CACHE) > _STATE_CACHE_SIZE:
            _STATE_CACHE.popitem(last=False)
    return state


def _build_state(repo: Path, files: dict[str, cat.IndexEntry], raw: dict[str, bytes]) -> State:
    try:
        catalogue = cat.parse(raw[cat.CATALOGUE_PATH])
        schema = json.loads(raw[cat.SCHEMA_PATH].decode('utf-8'))
        owners = cat.owner_keys(repo)
    except (cat.CatalogueLoadError, ValueError, OSError, subprocess.SubprocessError) as exc:
        return State(repo, None, cat.Report(), files, load_error=f'{type(exc).__name__}: {str(exc)[:200]}')
    report = cat.validate(catalogue, schema, list(files), owners)
    if not report.schema_ok:
        return State(repo, None, report, files, load_error='catalogue fails schema validation')
    return State(repo, catalogue, report, files, by_id={e['id']: e for e in catalogue['entries']})


# ---------------------------------------------------------------- Git search (the only body reader)

@dataclass
class GitRun:
    stdout: bytes
    outcome: str  # ok | no_match | timeout | output_budget | error
    detail: str = ''  # for error: the exception type when the runner itself failed


def _git_grep(repo: Path, args: list[str], deadline: float, cap: int) -> GitRun:
    """Run one ``git grep --cached`` with a wall-clock deadline and an output cap.

    ``args`` are options, ``-e`` patterns and pathspecs built by ``_search_args``;
    the subprocess gets no shell and no stdin. Exit status 1 is "no match".
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return GitRun(b'', 'timeout')
    env = {**os.environ, 'LC_ALL': 'C', 'GIT_TERMINAL_PROMPT': '0'}
    killed = threading.Event()
    proc: subprocess.Popen | None = None

    def kill() -> None:
        killed.set()
        if proc is not None:
            proc.kill()
    # Everything that can fail is built before the process exists or runs inside the try,
    # so no failure (including a BaseException) leaves a search running or unreaped.
    timer = threading.Timer(remaining, kill)
    chunks, size, over = [], 0, False
    try:
        proc = subprocess.Popen(['git', '-C', str(repo), '--no-pager', 'grep', '--cached', *args],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
        timer.start()
        while chunk := proc.stdout.read1(1 << 16):
            size += len(chunk)
            if size > cap:
                over = True
                proc.kill()
                break
            chunks.append(chunk)
    except BaseException:
        if proc is not None:
            proc.kill()  # never leave a search running behind a failure
        raise
    finally:
        timer.cancel()
        if proc is not None:
            try:
                proc.stdout.close()
            finally:
                status = proc.wait(timeout=5)
    if over:
        return GitRun(b''.join(chunks), 'output_budget')
    if killed.is_set():
        return GitRun(b'', 'timeout')
    if status == 1:
        return GitRun(b'', 'no_match')
    return GitRun(b''.join(chunks), 'ok' if status == 0 else 'error')


def _total_grep(repo: Path, args: list[str], deadline: float, cap: int) -> GitRun:
    """``_git_grep`` for a worker thread: any exception becomes an ``error`` run, never a traceback.

    The caller reports an ``error`` run as an incomplete search with its reason.
    """
    try:
        return _git_grep(repo, args, deadline, cap)
    except Exception as exc:  # deliberate: a worker failure is a typed incomplete result
        return GitRun(b'', 'error', type(exc).__name__)


def _variants(pattern: str) -> list[str]:
    """Case and normalisation forms git must try for a pattern git cannot case-fold itself.

    ASCII patterns use ``-i``. Git's ``-i`` is locale-dependent for other text, so a
    non-ASCII pattern is searched case-sensitively as its NFC original, lower, upper and
    title forms (plus NFD forms); every candidate line is re-checked with ``casefold``.
    """
    forms = {pattern, pattern.lower(), pattern.upper(), pattern.title(), pattern.capitalize()}
    forms |= {unicodedata.normalize('NFD', f) for f in forms}
    return sorted(forms)


def _files_args(pattern: str, pathspecs: list[str]) -> list[str]:
    """Files holding ``pattern`` as a fixed string: ``-i`` for ASCII, explicit forms otherwise."""
    args = ['--no-color', '-I', '-F', '--null', '-l']
    if pattern.isascii():
        args += ['-i', '-e', pattern]
    else:
        for form in _variants(pattern):
            args += ['-e', form]
    return [*args, '--', *pathspecs]


ERE_SPECIAL = frozenset('\\.[](){}*+?|^$')


def ere_escape(text: str) -> str:
    """``text`` as a POSIX extended regular expression that matches exactly itself."""
    return ''.join('\\' + c if c in ERE_SPECIAL else c for c in text)


def _line_args(patterns: list[str], pathspecs: list[str], per_file: int) -> list[str]:
    """Matching lines for any of ``patterns``, as ONE escaped ERE alternation.

    Several ``-e`` patterns with ``-n`` take tens of seconds on a large file (measured:
    31.8 s for two fixed strings on a 20 MB YAML, 0.45 s as one alternation), so line
    reads always use a single pattern. ``-i`` folds ASCII; non-ASCII patterns contribute
    their explicit case and normalisation forms; byte matching under LC_ALL=C.
    """
    forms = [form for pattern in patterns for form in ([pattern] if pattern.isascii() else _variants(pattern))]
    alternation = '|'.join(ere_escape(form) for form in dict.fromkeys(forms))
    return ['--no-color', '-I', '-E', '-i', '--null', '-n', '-m', str(per_file), '-e', alternation, '--', *pathspecs]


def _pathspecs(state: State, family: str | None) -> tuple[list[str], set[str]]:
    """Pathspecs that reach exactly the body-readable paths, and that readable set."""
    readable = {p for p in state.report.resolved if cat.body_readable(state.report, p)
                and (family is None or state.report.resolved[p][0] == family)}
    if family is not None:
        return [f':(literal){p}' for p in sorted(readable)], readable
    excluded = [p for p in state.files if cat.under_roots(p) and p not in readable]
    return ([f':(literal){root}' for root in cat.TRACKED_ROOTS]
            + [f':(exclude,literal){p}' for p in excluded]), readable


# ---------------------------------------------------------------- the search

@dataclass
class Candidate:
    path: str
    name_terms: set[str] = field(default_factory=set)
    content_terms: set[str] = field(default_factory=set)
    phrase_in_name: bool = False
    phrase_in_content: bool = False
    line: int | None = None
    line_text: str | None = None
    line_terms: int = 0  # distinct query words on the best matching line (0 for a one-line dump)

    @property
    def in_content(self) -> bool:
        return bool(self.content_terms) or self.phrase_in_content


def find(query: str, limit: int = DEFAULT_LIMIT, *, family: str | None = None, repo: Path | None = None,
         budget_seconds: float = DEFAULT_BUDGET_SECONDS) -> dict:
    """Search the catalogue, tracked names and readable tracked text for ``query``.

    Raises FindError (a ValueError) before any search starts for a limit that is not an
    int in 1..MAX_LIMIT, a budget that is not a finite number in (0, MAX_BUDGET_SECONDS],
    an empty query or an unknown ``family``; every other condition (an invalid catalogue,
    a Git failure, a failed search worker, a budget cut) is reported inside the result's
    ``coverage`` as incomplete.
    """
    limit = checked_limit(limit)
    budget_seconds = checked_budget(budget_seconds)
    if not isinstance(query, str):
        raise FindError('query', 'the query must be text')
    started = time.monotonic()
    deadline = started + budget_seconds
    text = clean_query(query)
    terms = query_terms(text)
    if not terms:
        raise FindError('empty_query', 'the query has no searchable word')
    repo = cat.toplevel(repo or Path('.'))
    state = load_state(repo)
    if family is not None and (state.catalogue is None or family not in state.by_id):
        raise FindError('unknown_family', f'no catalogue family {family!r}')
    timings = {'catalogue_ms': round((time.monotonic() - started) * 1000)}
    reasons: list[str] = []
    if state.catalogue is None:
        reasons.append(f'catalogue_invalid: {state.load_error}')
    phrase = words(text)

    tick = time.monotonic()
    family_hits, matched_families = _catalogue_hits(state, terms, phrase, family)
    candidates = _name_candidates(state, terms, phrase, family)
    timings['names_ms'] = round((time.monotonic() - tick) * 1000)

    tick = time.monotonic()
    df, readable, content_complete = _content_candidates(state, terms, text, phrase, family, candidates, deadline,
                                                         reasons)
    timings['content_ms'] = round((time.monotonic() - tick) * 1000)

    weights = {t: math.log((len(readable) + 1) / (df.get(t, 0) + 1)) + 1 for t in terms}
    seen = {hit['path'] for hit in family_hits if hit.get('path')}
    ranked = sorted((c for c in candidates.values() if c.path not in seen),
                    key=lambda c: _rank_key(state, c, terms, weights))
    pool = ranked[:max(RERANK_POOL, 3 * limit)]
    tick = time.monotonic()
    excerpts_complete = _read_lines(state, [c for c in pool if c.in_content], terms, text, phrase, deadline)
    timings['excerpts_ms'] = round((time.monotonic() - tick) * 1000)
    pool.sort(key=lambda c: _rank_key(state, c, terms, weights))
    content_hits = [_candidate_hit(state, c, terms, phrase) for c in pool[:max(0, limit - len(family_hits))]]
    hits = (family_hits + content_hits)[:limit]
    timings['total_ms'] = round((time.monotonic() - started) * 1000)
    for rank, hit in enumerate(hits, 1):
        hit['rank'] = rank

    incomplete = bool(reasons) or not content_complete
    outcome = 'found' if hits else ('incomplete' if incomplete else 'no_match')
    return {
        'query': text, 'terms': terms, 'outcome': outcome, 'hits': hits,
        'candidates': len(candidates) + len(family_hits), 'families_matched': matched_families,
        'coverage': _coverage(state, family, readable, incomplete, reasons, excerpts_complete),
        'timings_ms': timings,
    }


def _coverage(state: State, family: str | None, readable: set[str], incomplete: bool, reasons: list[str],
              excerpts_complete: bool) -> dict:
    entries = state.catalogue['entries'] if state.catalogue else []
    families = [e for e in entries if e['kind'] != 'data_store' and (family is None or e['id'] == family)]
    owners = {state.report.resolved[p][0] for p in readable}
    return {
        'families_searched': sorted(e['id'] for e in families if e['id'] in owners),
        'families_skipped': sorted(e['id'] for e in families if e['id'] not in state.report.searchable_entries),
        'files_searched': len(readable),
        'uncovered_unsearched': len(state.report.uncovered),
        'catalogue_errors': len(state.report.errors),
        'data_stores_matched_by_catalogue_only': True,
        'incomplete': incomplete,
        'incomplete_reasons': reasons,
        'excerpts_complete': excerpts_complete,
    }


def _status(lifecycle: str | None) -> str:
    return STATUS_WORDS.get(lifecycle, lifecycle or 'uncatalogued')


def _query_hint(entry: dict | None) -> list[dict]:
    return [dict(q) for q in entry.get('query', [])] if entry else []


def _path_hit(state: State, path: str, match: str, **extra) -> dict:
    family, lifecycle = state.lifecycle_of(path)
    entry = state.by_id.get(family) if family else None
    hit = {'path': path, 'line': None, 'excerpt': None, 'match': match, 'family': family,
           'kind': entry['kind'] if entry else None, 'lifecycle': lifecycle, 'status': _status(lifecycle),
           'superseded_by': state.superseded_by(path, family, lifecycle), 'query': _query_hint(entry)}
    if is_backup_like(path):
        hit['backup_like'] = True
    hit.update(extra)
    return hit


def _lifecycle_rank(state: State, path: str) -> int:
    if is_backup_like(path):
        return BACKUP_RANK
    return LIFECYCLE_RANK.get(state.lifecycle_of(path)[1], 1)


def relevance(c: Candidate, terms: list[str], weights: dict[str, float]) -> float:
    """Field-weighted relevance in [0, 2]: a word in the path name counts twice a word in the text.

    Each query word contributes its rarity weight (idf over the searched files) times 1
    in the name or 1/2 in the text; the sum is divided by the total weight. The whole
    phrase adds 1 in the name or 1/2 in the text (1/4 when its only line is a one-line
    data dump longer than LONG_LINE characters).
    """
    total = sum(weights[t] for t in terms)
    score = sum(weights[t] * (1.0 if t in c.name_terms else 0.5 if t in c.content_terms else 0.0) for t in terms)
    score /= total
    if len(terms) > 1:
        if c.phrase_in_name:
            score += 1.0
        elif c.phrase_in_content:
            score += 0.25 if c.line_text is not None and len(c.line_text) > LONG_LINE else 0.5
    return score


def _rank_key(state: State, c: Candidate, terms: list[str], weights: dict[str, float]) -> tuple:
    """(tier, relevance band, lifecycle, name evidence, line evidence, relevance, path).

    Tier 0: the whole query in the path name (every word of it, or the phrase). Tier 1:
    the whole phrase in the text on a line that is not a one-line data dump (a one-word
    query: the word in the text). Tier 2: everything else, banded by ``relevance`` in
    quarter steps. Within a tier and band, lifecycle comes first (current ahead of draft
    or unclassified, historical, superseded and, last, backup-like copies), then words in
    the path name, then query words together on one short line; the exact relevance and
    the path break the remaining ties.
    """
    score = relevance(c, terms, weights)
    long_line = c.line_text is not None and len(c.line_text) > LONG_LINE
    if c.phrase_in_name or c.name_terms == set(terms):
        tier = 0
    elif (c.phrase_in_content or (len(terms) == 1 and c.content_terms)) and not long_line:
        tier = 1
    else:
        tier = 2
    name_weight = sum(weights[t] for t in c.name_terms)
    return (tier, -round(score * 4), _lifecycle_rank(state, c.path), -round(name_weight, 6), -c.line_terms,
            -round(score, 6), c.path)


def _candidate_hit(state: State, c: Candidate, terms: list[str], phrase: list[str]) -> dict:
    hit = _path_hit(state, c.path, 'content' if c.in_content else 'name',
                    matched=sorted(c.name_terms | c.content_terms))
    if c.line is not None:
        hit['line'] = c.line
        hit['excerpt'] = _excerpt(c.line_text, terms, phrase)
    return hit


# ---------------------------------------------------------------- step 1: catalogue

def _entry_fields(entry: dict) -> tuple[list[list[str]], list[str]]:
    strong = [words(k) for k in entry.get('keywords', [])]
    strong.append(words(entry['id']))
    strong += [words(e['topic']) for e in entry.get('entrypoints', [])]
    strong += [words(e['path']) for e in entry.get('entrypoints', [])]
    strong += [words(s) for s in entry.get('store', [])]
    strong += [words(p) for p in entry.get('producer', [])]
    weak = words(entry.get('purpose', '')) + words(entry.get('notes', ''))
    return strong, weak


def _catalogue_hits(state: State, terms: list[str], phrase: list[str], family: str | None) -> tuple[list[dict], list[str]]:
    if state.catalogue is None:
        return [], []
    scored = []
    for order, entry in enumerate(state.catalogue['entries']):
        if family is not None and entry['id'] != family:
            continue
        strong, weak = _entry_fields(entry)
        strong_terms = set().union(*(_prefix_hits(terms, f) for f in strong))
        weak_terms = _prefix_hits(terms, weak) - strong_terms
        keyword_in_query = [k for k in strong[:len(entry.get('keywords', [])) + 1]
                            if _contains_words(phrase, k, prefix_last=False)]
        phrase_in_field = any(_contains_words(f, phrase) for f in strong)
        complete = len(terms) > 1 and strong_terms == set(terms)
        if not (keyword_in_query or phrase_in_field or complete):
            continue
        weight = (2 * len(strong_terms) + len(weak_terms) + 3 * bool(phrase_in_field)
                  + max((len(k) for k in keyword_in_query), default=0))
        scored.append((-weight, LIFECYCLE_RANK.get(entry['lifecycle'], 1), order, entry))
    scored.sort(key=lambda item: item[:3])
    hits, matched = [], []
    for *_, entry in scored[:MAX_FAMILY_MATCHES]:
        matched.append(entry['id'])
        hits.extend(_entry_hits(state, entry, terms))
    return hits, matched


def _entry_hits(state: State, entry: dict, terms: list[str]) -> list[dict]:
    base = {'family': entry['id'], 'kind': entry['kind'], 'query': _query_hint(entry)}
    if entry['kind'] == 'data_store':
        store = {'path': entry['store'][0], 'line': None, 'excerpt': None, 'match': 'data_store',
                 'lifecycle': entry['lifecycle'], 'status': _status(entry['lifecycle']),
                 'superseded_by': entry.get('superseded_by'), 'stores': list(entry['store']),
                 'producer': list(entry['producer']), 'local_only': entry['local_only'],
                 'purpose': entry['purpose'], **base}
        producers = [_path_hit(state, p, 'producer', family=entry['id'], kind=entry['kind'], query=base['query'])
                     for p in entry['producer'][:MAX_PRODUCERS_PER_STORE]]
        points = [_path_hit(state, cat.strip_fragment(e['path']), 'entrypoint', topic=e['topic'])
                  for e in entry.get('entrypoints', [])[:MAX_ENTRYPOINTS_PER_FAMILY]]
        return [store, *producers, *points]
    points = entry.get('entrypoints', [])
    if not points:
        return [{'path': None, 'line': None, 'excerpt': None, 'match': 'family', 'lifecycle': entry['lifecycle'],
                 'status': _status(entry['lifecycle']), 'superseded_by': entry.get('superseded_by'),
                 'paths': list(entry['paths']), 'purpose': entry['purpose'], **base}]
    ranked = sorted(enumerate(points), key=lambda item: (-len(_prefix_hits(terms, words(item[1]['topic'])
                                                                           + words(item[1]['path']))), item[0]))
    return [_path_hit(state, cat.strip_fragment(point['path']), 'entrypoint', topic=point['topic'],
                      purpose=entry['purpose'])
            for _, point in ranked[:MAX_ENTRYPOINTS_PER_FAMILY]]


# ---------------------------------------------------------------- step 2: names

def _name_candidates(state: State, terms: list[str], phrase: list[str], family: str | None) -> dict[str, Candidate]:
    found: dict[str, Candidate] = {}
    for path in state.files:
        folded = normalise(path)
        if not any(t in folded for t in terms):
            continue  # cheap screen: a prefix of a path word is a substring of the path
        if cat.CONTROL_CHARS.search(path) or cat.is_excluded(path):
            continue
        if family is not None and state.report.resolved.get(path, (None,))[0] != family:
            continue
        path_words = words(path)
        hits = _prefix_hits(terms, path_words)
        if hits:
            found[path] = Candidate(path, name_terms=hits,
                                    phrase_in_name=len(phrase) > 1 and _contains_words(path_words, phrase))
    return found


# ---------------------------------------------------------------- step 3: tracked text

def _content_candidates(state: State, terms: list[str], text: str, phrase: list[str], family: str | None,
                        candidates: dict[str, Candidate], deadline: float,
                        reasons: list[str]) -> tuple[dict[str, int], set[str], bool]:
    """Per-term (and whole-phrase) file lists from git grep; returns (document frequency, readable, complete)."""
    if state.catalogue is None:
        return {}, set(), False
    pathspecs, readable = _pathspecs(state, family)
    if not readable:
        return {}, readable, True
    # A one-character word matches almost every file, so beside longer words it is not searched
    # alone (names, the catalogue and the whole phrase still are). That is reported, never
    # silent: the result is incomplete. A query of one-character words only is searched.
    searched = [t for t in terms if len(t) > 1] or terms
    skipped = [t for t in terms if t not in searched]
    if skipped:
        reasons.append(f"content_search_skipped: one-character word(s) {', '.join(map(repr, skipped))} not "
                       'searched alone in text')
    patterns = [(t, t) for t in searched]
    if len(phrase) > 1:
        patterns.append(('\0phrase', text))  # the cleaned query as typed: separators and all
    jobs = {key: _files_args(pattern, pathspecs) for key, pattern in patterns}
    with ThreadPoolExecutor(max_workers=min(4, len(jobs)) or 1) as pool:
        futures = {key: pool.submit(_total_grep, state.repo, args, deadline, GREP_OUTPUT_CAP)
                   for key, args in jobs.items()}
        runs = {key: future.result() for key, future in futures.items()}
    complete = True
    df: dict[str, int] = {}
    for key, run in runs.items():
        if run.outcome in ('timeout', 'output_budget', 'error'):
            complete = False
            detail = f' ({run.detail})' if run.detail else ''
            reasons.append(f'{run.outcome}: the search for {key.lstrip(chr(0))!r} did not finish{detail}')
            continue
        paths = [p.decode('utf-8', 'replace') for p in run.stdout.split(b'\0') if p]
        paths = [p for p in paths if p in readable]  # the gate again, whatever git returned
        if key != '\0phrase':
            df[key] = len(paths)
        for path in paths:
            candidate = candidates.setdefault(path, Candidate(path))
            if key == '\0phrase':
                candidate.phrase_in_content = True
            else:
                candidate.content_terms.add(key)
    return df, readable, complete


def _read_lines(state: State, pool: list[Candidate], terms: list[str], text: str, phrase: list[str],
               deadline: float) -> bool:
    """Read the matching lines of each content candidate (bounded) and keep its best line.

    Files holding the whole phrase are searched for the phrase alone, the rest for the
    words, so the quoted line is the most specific one. Returns False when a budget cut
    a read short (excerpts and line evidence are then partial; the hit list is not).
    """
    by_path = {c.path: c for c in pool if cat.body_readable(state.report, c.path)}
    if not by_path:
        return True
    # One-character words match almost every line, so they pick lines only when nothing longer exists.
    words_only = [t for t in terms if len(t) > 1] or terms
    jobs = []
    for phrase_files, patterns in ((True, [text]), (False, words_only)):
        paths = sorted(p for p, c in by_path.items() if c.phrase_in_content == phrase_files)
        if paths and patterns:
            jobs.append(_line_args(patterns, [f':(literal){p}' for p in paths], EXCERPT_LINES_PER_FILE))
    found: dict[str, list[tuple[int, str]]] = {}
    complete = True
    with ThreadPoolExecutor(max_workers=min(4, len(jobs)) or 1) as pool_runner:
        runs = list(pool_runner.map(lambda args: _total_grep(state.repo, args, deadline, EXCERPT_OUTPUT_CAP), jobs))
    for run in runs:
        if run.outcome not in ('ok', 'no_match'):
            complete = False
        for record in run.stdout.split(b'\n'):
            parts = record.split(b'\0', 2)
            if len(parts) != 3 or not parts[1].isdigit():
                continue
            path = parts[0].decode('utf-8', 'replace')
            if path in by_path:
                found.setdefault(path, []).append((int(parts[1]), parts[2].decode('utf-8', 'replace')))
    for path, lines in found.items():
        candidate = by_path[path]
        candidate.line, candidate.line_text = _best_line(lines, terms, normalise(text) if len(phrase) > 1 else '')
        folded = normalise(candidate.line_text)
        candidate.line_terms = (sum(t in folded for t in terms) if len(candidate.line_text) <= LONG_LINE else 0)
    return complete


def _best_line(found: list[tuple[int, str]], terms: list[str], phrase: str) -> tuple[int, str]:
    """The line holding the whole phrase, else the most query words; short lines before one-line dumps."""
    def score(item: tuple[int, str]) -> tuple:
        folded = normalise(item[1])
        has_phrase = bool(phrase) and phrase in folded
        return (not has_phrase, -sum(t in folded for t in terms), len(item[1]) > LONG_LINE, item[0])
    return min(found, key=score)


def _excerpt(text: str, terms: list[str], phrase: list[str]) -> str:
    text = text.rstrip('\r')
    folded = normalise(text)
    positions = [folded.find(t) for t in [' '.join(phrase), *terms] if t and folded.find(t) >= 0]
    start = 0
    if len(text) > EXCERPT_CHARS:
        # NFC + casefold can change lengths, so the position is approximate; centre on it.
        start = max(0, min(min(positions, default=0) - EXCERPT_CHARS // 4, len(text) - EXCERPT_CHARS))
    piece = text[start:start + EXCERPT_CHARS].strip()
    return escape_excerpt(('…' if start else '') + piece + ('…' if start + EXCERPT_CHARS < len(text) else ''))


# Failures that mean "the repository or Git could not be read" (callers map them to a typed error).
UNREADABLE = (OSError, subprocess.SubprocessError, UnicodeDecodeError)


# ---------------------------------------------------------------- CLI

def format_text(result: dict) -> str:
    cov = result['coverage']
    lines = [f"query {result['query']!r}: {result['outcome']}, {len(result['hits'])} hit(s) shown of "
             f"{result['candidates']} candidate(s); {cov['files_searched']} files searched in "
             f"{len(cov['families_searched'])} families; {len(cov['families_skipped'])} families not "
             f"content-searchable; {result['timings_ms']['total_ms']} ms"]
    if cov['incomplete']:
        lines.append('INCOMPLETE: ' + '; '.join(cov['incomplete_reasons'] or ['a budget cut the search short'])
                     + ' (absence of a hit is not evidence of absence)')
    for hit in result['hits']:
        where = cat.shown(hit['path']) if hit.get('path') else ', '.join(hit.get('paths', []))
        if hit.get('line'):
            where += f":{hit['line']}"
        status = hit['status'] + (f" -> {hit['superseded_by']}" if hit.get('superseded_by') else '')
        if hit.get('backup_like'):
            status += ', backup copy'
        lines.append(f"{hit['rank']:>3}. {where}  [{hit['match']}; {hit.get('family') or 'no family'}; {status}]")
        detail = hit.get('topic') or hit.get('excerpt')
        if detail:
            lines.append(f'     {escape_excerpt(detail)}')
        if hit['match'] in ('data_store', 'family') and hit.get('query'):
            lines.append('     query: ' + escape_excerpt('; '.join(f"{q['surface']}: {q['how']}" for q in hit['query'])))
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='python -m scripts.docs.find',
        description='Find where a document, data store or resource lives and whether it is current, in one query.\n'
                    'Use it before reporting "no source" or asking where something is; it searches the catalogue, '
                    'tracked file names and tracked text. Not a Ukrainian dictionary or corpus search: use the '
                    'sources MCP tools for language facts.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  .venv/bin/python -m scripts.docs.find "ULP 1-02"\n'
               '  .venv/bin/python -m scripts.docs.find "vesum database" --json\n'
               '  .venv/bin/python -m scripts.docs.find "teacher deck" --family practice-specs --limit 5\n'
               'Outputs: ranked hits on stdout (path, line, excerpt, family, status, replacement, query hint) and '
               'the search coverage; writes nothing and keeps no index.\n'
               'Exit codes: 0 at least one hit; 1 no hit in a complete search; 2 invalid arguments (a limit or budget '
               'out of range or not a number), an empty query '
               'or an unknown family; 3 unreadable repository; 4 internal error; 5 no hit and the search was '
               'incomplete (a budget or catalogue problem cut it short, so absence is not proven). Failures print a '
               'typed error (JSON with --json), never a traceback.\n'
               'Related: #9412; GET /api/knowledge/find (same search); docs/README.md; '
               'docs/knowledge/catalogue.yaml; scripts/docs/catalogue.py.')
    parser.add_argument('query', help='Words or a phrase to look for, e.g. "ULP 1-02" or "teacher deck rebuild"; '
                                      f'non-printable characters become spaces, at most {MAX_QUERY_CHARS} characters.')
    parser.add_argument('--limit', default=str(DEFAULT_LIMIT),
                        help=f'Maximum hits to return, 1..{MAX_LIMIT}, written as ASCII digits only (0-9): no '
                             f'sign, no spaces, no decimal point or exponent (default: {DEFAULT_LIMIT}).')
    parser.add_argument('--family', default=None,
                        help='Restrict the search to one catalogue family or store id, e.g. runbooks '
                             '(default: all).')
    parser.add_argument('--repo', type=Path, default=Path('.'),
                        help='Repository or worktree root (default: current directory).')
    parser.add_argument('--budget', default=str(DEFAULT_BUDGET_SECONDS),
                        help='Wall-clock budget in seconds for the text search, greater than 0 and at most '
                             f'{MAX_BUDGET_SECONDS:g} (default: {DEFAULT_BUDGET_SECONDS:g}); a cut-off search is '
                             'reported as incomplete.')
    parser.add_argument('--json', action='store_true', help='Print the full result as JSON (default: text).')
    args = parser.parse_args(argv)
    try:
        result = find(args.query, limit_from_text(args.limit), family=args.family, repo=args.repo,
                      budget_seconds=_cli_budget(args.budget))
    except FindError as exc:
        return _fail(args.json, 'invalid_request', exc.code, exc.message, 2)
    except UNREADABLE as exc:
        return _fail(args.json, 'unreadable', getattr(exc, 'code', type(exc).__name__), str(exc), 3)
    except Exception as exc:  # deliberate catch-all at the process boundary
        return _fail(args.json, 'internal_error', type(exc).__name__, str(exc), 4)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_text(result))
    return {'found': 0, 'no_match': 1, 'incomplete': 5}[result['outcome']]


def _cli_budget(text: str) -> float:
    """The --budget text as a float; FindError('budget') with the fixed message when it is not a number.

    ``find`` then rejects NaN, infinities and out-of-range values with the same message.
    """
    try:
        return float(text)
    except (ValueError, OverflowError):
        raise FindError('budget', BUDGET_MESSAGE) from None


def _fail(as_json: bool, kind: str, code: str, message: str, status: int) -> int:
    message = escape_excerpt(message[:500])
    if as_json:
        print(json.dumps({'error': {'kind': kind, 'code': code, 'message': message}}, sort_keys=True))
    else:
        print(f'Find could not run ({kind}): {code}: {message}')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
