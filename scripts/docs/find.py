"""One query surface for documents, data stores and resources (#9412).

``find(query)`` answers "where is X, is it current and what replaced it, where is it
implemented?" in one call, from four sources read at request time, with no persisted index:

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
4. **Code identifiers**: one ``git grep --cached`` over tracked code and configuration
   files (``code_readable``: CODE_ROOTS and root files, never a privacy-excluded path)
   whose lines are used only as identifiers - definitions, CLI subcommands and flags,
   configuration keys and ids, headings, quoted UPPER_SNAKE codes - and file summaries
   (comment and docstring lines among the first HEADER_LINES), never as prose. It is
   skipped with ``family`` and when the catalogue is invalid.

Query words: stopwords are dropped; intent words ("current", "replaced", "retired",
"implemented", ...) are not search terms beside other words, and a status question
ranks every lifecycle alike. A one-character word beside longer words is matched in
names, the catalogue and the phrase only (``coverage.name_only_terms``), which is a
complete search. A token typed as an identifier (``check_russian_shadow``, ``1-02``)
is also matched as a unit (``compounds``).

Ranking: catalogue matches first; then, by match band (whole phrase in a name,
whole phrase in text, every word, then the share of the query's rarity-weighted
words), typed identifiers held, lifecycle (current, then draft or unclassified, historical,
superseded; backup-like copies last), and path order. A word in a path name counts 1,
in one code identifier unit SYMBOL_WEIGHT, in text 1/2, each times its rarity over
documents and code together. Every hit carries its family, status, replacement and
the family's query hint, and every superseded hit is followed by its replacement
(match ``replacement``). The result states its coverage and says ``incomplete``
with a reason when a budget or a failed search worker cut the search short, so a
cutoff is never reported as "no source". ``limit`` and ``budget_seconds`` are validated before any
search starts (``FindError``, a ValueError).

The CLI is ``python -m scripts.docs.find``; the Monitor API mirrors it at
``GET /api/knowledge/find``.
"""
from __future__ import annotations

import argparse
import functools
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
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from scripts.docs import catalogue as cat

MAX_QUERY_CHARS = 200
DEFAULT_LIMIT = 20
MAX_LIMIT = 200
MAX_TERMS = 12
MAX_FAMILY_MATCHES = 5
MAX_ENTRYPOINTS_PER_FAMILY = 3
MAX_PRODUCERS_PER_STORE = 3
EXCERPT_CHARS = 200
EXCERPT_LINES_PER_FILE = 10
RERANK_POOL = 150  # content candidates whose matching lines are read to rank and quote them
PASSAGE_LINES_PER_FILE = 60  # matching lines read per pool file to find its best passage
PASSAGE_SPAN = 4  # consecutive lines that count as one passage (a paragraph or a table row with its neighbours)
CATALOGUE_WEIGHT = 1.0  # a word in a family's keywords, id or entry-point topic (curated, read before body text)
TEXT_WEIGHT = 0.4  # a word anywhere in a document's text (a bag), before its BM25 length factor
CODE_BAG_WEIGHT = 0.3  # a word anywhere among a code file's identifier units (a bag, weakest code evidence)
NAME_COVER_BONUS = 0.25  # every word of the file name (without its extension) is a query word
MIN_RARITY = 0.1  # the rarity weight floor: a word in most files still counts a little
PROCESS_CODE_BOOST = 1.3  # code evidence for a process question ("what stops ...", "where do we check ...")
UNIT_WEIGHT = 0.6  # a word in a code file's summary, or beside another query word in one short passage of text
INTENT_NAME_BONUS = 0.25  # an intent word ("deprecated", "old") in a path name: the folder says what is asked
RECORD_SHARE = 0.5  # a lifecycle line must hold at least this rarity-weighted share of a status question
LONG_LINE = 1000  # a matching line longer than this (a one-line data dump) is no evidence of proximity
DEFAULT_BUDGET_SECONDS = 10.0
MAX_BUDGET_SECONDS = 120.0
GREP_OUTPUT_CAP = 16 * 1024 * 1024
EXCERPT_OUTPUT_CAP = 32 * 1024 * 1024
CODE_OUTPUT_CAP = 32 * 1024 * 1024
LIFECYCLE_RANK = {'active': 0, None: 0, 'draft': 1, 'residual': 1, 'archive': 2, 'superseded': 3}
BACKUP_RANK = 4
LIFECYCLE_PENALTY = 0.03  # relevance a file gives up per lifecycle step (historical: 0.06, backup: 0.12)
STATUS_WORDS = {'active': 'current', 'archive': 'historical', 'superseded': 'superseded', 'draft': 'draft',
                'residual': 'unclassified', None: 'uncatalogued'}
BACKUP_SUFFIXES = ('.backup', '.bak', '.orig', '.truncated', '.old', '.tmp', '~')
# Words that carry no locating signal in a question ("where is the list of ..."): the standard
# English function-word list (NLTK's, which also holds the contraction fragments re, ve, ll, ...),
# question fillers a reader types around the subject, and Ukrainian function words.
STOPWORDS = frozenset({
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
    'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these',
    'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've',
    'y', 'would', 'could', 'may', 'might', 'must', 'shall',
    'per', 'instead', 'get', 'find', 'look', 'use', 'used', 'using', 'ever', 'also', 'anything',
    'something', 'someone', 'anyone', 'actually', 'like', 'thing', 'things', 'happen', 'happens', 'way',
    'every', 'whether',
    'і', 'й', 'та', 'в', 'у', 'на', 'з', 'із', 'до', 'що', 'як', 'де', 'чи', 'це', 'для', 'про',
})
# Words that state what a question asks, not what it is about: "is X still current, what replaced
# it?" (status) and "where is X implemented?" (process). Beside other words they are not search
# terms (every second document says "replaced" or "implemented"); a status question instead
# turns off the lifecycle demotion, because the superseded or historical thing is its subject.
STATUS_INTENT = frozenset({'current', 'currently', 'replaced', 'replace', 'replaces', 'replacement',
                           'retired', 'retire', 'deprecated', 'superseded', 'supersedes', 'obsolete',
                           'outdated', 'old', 'anymore', 'abandoned', 'still'})
PROCESS_INTENT = frozenset({'implemented', 'implement', 'implements', 'implementation', 'computed',
                            'handled'})
# A question word with one of these verbs asks where something is done ("what stops ...", "where do
# we check ..."); the verbs stay search terms. Matched in any inflection (stops, checked, deleting).
# Verbs that are also common nouns (record, store, build, limit) are left out.
QUESTION_WORDS = frozenset({'what', 'which', 'where', 'how'})
PROCESS_VERBS = frozenset({'check', 'enforce', 'refuse', 'reject', 'prevent', 'stop', 'block', 'delete', 'remove',
                           'clean', 'catch', 'detect', 'decide', 'schedule', 'validate', 'verify', 'measure',
                           'generate', 'parse', 'compute', 'guard', 'lint', 'reap', 'pick', 'select', 'launch',
                           'resolve', 'retry', 'kill', 'refresh'})
# Words that record a lifecycle state on a line: a registry row ("| dec-003 | ... | superseded | Cap
# review fix rounds at 4 |"), a banner ("REFERENCE ONLY", "Status: Deferred") or a configuration
# comment ("the subscription backing the glm lane is retired"). For a status question, such a line
# holding query words is the record that answers it (``lifecycle_record``).
LIFECYCLE_MARKER = re.compile(
    r'\b(?:supersed\w*|retire[ds]?|retirement|deprecat\w*|archived|obsolete|legacy|historical|parked|shelved'
    r'|deferred|abandoned|killed|rejected|proposed|accepted|frozen|discontinued|unsupported|stopped'
    r'|no longer|reference only|do not use|replaced by|moved to)\b')
# Numerals a reader writes as words ("four rounds") and a record as digits ("4 rounds"), both ways.
NUMERALS = dict(zip(['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                     'eleven', 'twelve'], map(str, range(13)), strict=True))
NUMERALS.update({digits: word for word, digits in NUMERALS.items()})
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


POSSESSIVE = re.compile(r"(?<=[a-z0-9])['\u2019]s$")


QUOTES = "'\u2019\u02bc"


def words(text: str) -> list[str]:
    """The folded words of ``text``: apostrophes stay inside a word (п'ять), quotes around it go, and
    an English possessive ("project's") is its noun."""
    found = (POSSESSIVE.sub('', w.strip(QUOTES)) for w in SEPARATORS.split(normalise(text)))
    return [w for w in found if w]


def clean_query(raw: str) -> str:
    """NFC, every non-printable character (controls, line separators, format characters) as a space,
    whitespace collapsed, capped at MAX_QUERY_CHARS."""
    text = unicodedata.normalize('NFC', raw)
    text = ''.join(c if c.isprintable() else ' ' for c in text)
    return ' '.join(text.split())[:MAX_QUERY_CHARS].strip()


def query_plan(query: str) -> tuple[list[str], list[str]]:
    """(search terms, intent words) of a query.

    Terms are the distinct query words without stopwords and, when other words remain, without
    intent words (STATUS_INTENT, PROCESS_INTENT) outside typed identifiers; at most MAX_TERMS, taken after both filters so
    a long question keeps its content words. When only stopwords or intent words remain, they
    are the terms (a query is never emptied).
    """
    found = list(dict.fromkeys(words(query)))
    kept = [w for w in found if w not in STOPWORDS] or found
    # A word inside a typed identifier (retired-model-9) is part of a name, never intent.
    named = {w for unit in compounds(query) for w in words(unit)}
    asks = (STATUS_INTENT | PROCESS_INTENT) - named
    content = [w for w in kept if w not in asks]
    intent = [w for w in kept if w in asks] if content else []
    return (content or kept)[:MAX_TERMS], intent


def query_terms(query: str) -> list[str]:
    """The search terms of ``query_plan``."""
    return query_plan(query)[0]


def compounds(text: str) -> list[str]:
    """The identifier-like tokens of a cleaned query: whitespace-separated tokens that join two or more
    words with ``_``, ``-``, ``.``, ``/`` or ``:`` (``check_russian_shadow``, ``gpt-6-astra``, ``1-02``,
    ``atlas.db``), folded, without surrounding punctuation; at most MAX_TERMS, never the whole query.

    A typed identifier is the most specific thing a query can say, so a file holding it as a unit
    (in its name, a code identifier or its text) ranks ahead of one holding its words apart.
    """
    found = []
    for token in text.split():
        token = normalise(token.strip('?!,;:\'"`()[]{}<>'))
        if len(words(token)) > 1 and token != normalise(text) and token not in found:
            found.append(token)
    return found[:MAX_TERMS]


MIN_PREFIX = 3  # a term this long or longer also meets the words it begins
MAX_PREFIX_EXTRA = 3  # how many characters a met word may add to the term or its stem
SHORT_ENDINGS = ('', 's', 'es', 'ed', 'ing', 'er', 'ers')
STEM_SUFFIXES = ('ations', 'ation', 'ments', 'ment', 'ions', 'ion', 'ing', 'ies', 'ed', 'es', 's')
MIN_STEM = 4
UNDOUBLED = re.compile(r'([b-df-hj-km-np-rtv-xz])\1$')  # a doubled final consonant other than l, s, z
VERB_NOUN_AL = re.compile(r'(?<=[svw])als?$')  # approval(s), removal, proposal, renewal: a verb's -al noun


@functools.lru_cache(maxsize=4096)
def stem(term: str) -> str:
    """``term`` without one suffix, when at least MIN_STEM letters remain; used as a word prefix.

    The suffixes are inflectional (ing, ed, es, s, ies) and the common derivational endings
    (ation, ion, ment and their plurals), longest first, so "parsing" meets "parse", "deletion"
    meets "delete", "enforcement" meets "enforce", "migration" meets "migrate" and "entries"
    meets "entry". A doubled final consonant left by ing or ed is undoubled (scanning, scan),
    as in Porter's stemmer; a double ``ss`` keeps its ``s`` (process, class). A verb's -al noun
    loses its -al (approval meets approve, removal meets remove, proposal meets propose).
    """
    if term.endswith('ss'):
        return term
    if (found := VERB_NOUN_AL.search(term)) and found.start() >= MIN_STEM:
        return term[:found.start()]
    for suffix in STEM_SUFFIXES:
        if term.endswith(suffix) and len(term) - len(suffix) >= MIN_STEM:
            base = term[:-len(suffix)]
            return base[:-1] if suffix in ('ing', 'ed') and UNDOUBLED.search(base) else base
    return term


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


def _prefix_hits(terms: Sequence[str], field_words: Sequence[str]) -> set[str]:
    """The terms that are a prefix of a field word, as typed or as their ``stem``; a numeral meets its
    word form and back ("4" and "four", ``NUMERALS``)."""
    joined = ' ' + ' '.join(field_words) + ' '
    if any(w in NUMERALS for w in field_words):
        joined += ' '.join(NUMERALS[w] for w in field_words if w in NUMERALS) + ' '
    return {t for t in terms if _term_pattern(t).search(joined)}


@functools.lru_cache(maxsize=4096)
def _term_pattern(term: str) -> re.Pattern:
    """A whole field word that ``term`` meets, in a space-joined word list.

    The word is the term or its ``stem`` followed by at most MAX_PREFIX_EXTRA more characters
    (parse, parser; deletion, deleted; pack, packed, never packages). A term shorter than
    MIN_PREFIX ("pr", "ci") meets only itself and its SHORT_ENDINGS inflections.
    """
    if len(term) < MIN_PREFIX:
        body = re.escape(term) + '(?:' + '|'.join(re.escape(e) for e in SHORT_ENDINGS) + ')'
    else:
        body = '(?:' + '|'.join(sorted({re.escape(term), re.escape(stem(term))}, key=len, reverse=True)) + ')'
        body += f'[^ ]{{0,{MAX_PREFIX_EXTRA}}}'
    return re.compile(f'(?<= ){body}(?= )')


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
    # Query-independent facts derived from the same index, built on first use and kept with the
    # state (so a long-lived API process reads them once per index): blob sizes, code summaries.
    derived: dict = field(default_factory=dict)
    derived_lock: threading.Lock = field(default_factory=threading.Lock)

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

    ``args`` are options, ``-e`` patterns and pathspecs built by ``_search_args``.
    Exit status 1 is "no match".
    """
    return _run_git(repo, ['grep', '--cached', *args], deadline, cap)


def _run_git(repo: Path, argv: list[str], deadline: float, cap: int) -> GitRun:
    """The one process starter: ``git <argv>`` with a wall-clock deadline and an output cap.

    The subprocess gets no shell and no stdin; it is killed at the deadline or when its
    output passes ``cap`` bytes, and always reaped. Exit status 1 is "no match".
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
        proc = subprocess.Popen(['git', '-C', str(repo), '--no-pager', *argv],
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


def _total_run(repo: Path, argv: list[str], deadline: float, cap: int) -> GitRun:
    """``_run_git`` that never raises: any exception becomes an ``error`` run."""
    try:
        return _run_git(repo, argv, deadline, cap)
    except Exception as exc:  # deliberate: a failure is a typed outcome, never a traceback
        return GitRun(b'', 'error', type(exc).__name__)


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


def _line_args(patterns: list[str], pathspecs: list[str], per_file: int | None) -> list[str]:
    """Matching lines for any of ``patterns``, as ONE escaped ERE alternation.

    Several ``-e`` patterns with ``-n`` take tens of seconds on a large file (measured:
    31.8 s for two fixed strings on a 20 MB YAML, 0.45 s as one alternation), so line
    reads always use a single pattern. ``-i`` folds ASCII; non-ASCII patterns contribute
    their explicit case and normalisation forms; byte matching under LC_ALL=C. ``per_file`` caps
    the lines read per file (None: every matching line).
    """
    forms = [form for pattern in patterns for form in ([pattern] if pattern.isascii() else _variants(pattern))]
    alternation = '|'.join(ere_escape(form) for form in dict.fromkeys(forms))
    cap = [] if per_file is None else ['-m', str(per_file)]
    return ['--no-color', '-I', '-E', '-i', '--null', '-n', *cap, '-e', alternation, '--', *pathspecs]


def _pathspecs(state: State, family: str | None) -> tuple[list[str], set[str]]:
    """Pathspecs that reach exactly the text-readable paths, and that readable set.

    The body-readable catalogued documents and, without a ``family`` filter, every
    ``prose_readable`` file outside the catalogued roots (named one by one).
    """
    readable = {p for p in state.report.resolved if cat.body_readable(state.report, p)
                and (family is None or state.report.resolved[p][0] == family)}
    if family is not None:
        return [f':(literal){p}' for p in sorted(readable)], readable
    prose = sorted(p for p in state.files if prose_readable(p))
    excluded = [p for p in state.files if cat.under_roots(p) and p not in readable]
    return ([f':(literal){root}' for root in cat.TRACKED_ROOTS] + [f':(literal){p}' for p in prose]
            + [f':(exclude,literal){p}' for p in excluded]), readable | set(prose)


# ---------------------------------------------------------------- authorities, sizes and code summaries

# A directory's README (or index) is the conventional authority for what the directory holds and
# whether it is still used. Inside the catalogued roots it is a document like any other; outside
# them (scripts/legacy/..., packages/..., tests/replay/...) its text is searched too.
README_NAME = re.compile(r'readme(?:\.[a-z]{2})?(?:\.(?:md|markdown|txt|rst))?', re.IGNORECASE)
INDEX_NAME = re.compile(r'(?:readme|index)(?:\.[a-z]{2})?(?:\.(?:md|markdown|txt|rst|ya?ml|json))?', re.IGNORECASE)


@functools.lru_cache(maxsize=1 << 16)
def prose_readable(path: str) -> bool:
    """Prose outside the catalogued roots whose text may be searched like a document.

    Any README (README, README.md, README.uk.md, ...) and every Markdown file that
    ``code_readable`` admits (rules, skills and phase prompts under the code roots, AGENTS.md at
    the root). The same privacy boundary as code: no inventory-excluded component, no control
    character, never a path inside the catalogued roots (those follow the catalogue's gate).
    """
    if cat.under_roots(path) or cat.CONTROL_CHARS.search(path) or cat.is_excluded(path):
        return False
    return bool(README_NAME.fullmatch(PurePosixPath(path).name)) or (_suffix(path) == '.md' and code_readable(path))


def text_readable(state: State, path: str) -> bool:
    """The privacy gate for text reads: a body-readable catalogued document or ``prose_readable`` prose."""
    return cat.body_readable(state.report, path) or prose_readable(path)


def _derived(state: State, key: str, build):
    """``state.derived[key]``, built once per state under its lock."""
    with state.derived_lock:
        if key not in state.derived:
            state.derived[key] = build()
        return state.derived[key]


def blob_sizes(state: State, deadline: float) -> dict[str, int]:
    """The size in bytes of every tracked blob that is text- or code-readable, from one bounded
    ``git ls-files --format`` (names and sizes only, no body is read).

    Kept with the state once read; a read that does not finish is not kept, and a path whose
    size is unknown counts at full weight (``length_factor`` 1).
    """
    with state.derived_lock:
        if 'sizes' in state.derived:
            return state.derived['sizes']
    run = _total_run(state.repo, ['ls-files', '-z', '--format=%(objectsize) %(path)'], deadline, CODE_OUTPUT_CAP)
    if run.outcome != 'ok':
        return {}
    sizes = {}
    for record in run.stdout.split(b'\0'):
        size, _, raw = record.partition(b' ')
        path = raw.decode('utf-8', 'replace')
        if size.isdigit() and path in state.files and (code_readable(path) or text_readable(state, path)):
            sizes[path] = int(size)
    with state.derived_lock:
        state.derived['sizes'] = sizes
    return sizes


# Binary presence of a word means more in a short file than in a long one (a long file holds most
# words somewhere). BM25's length normalisation with a term frequency of one, capped at 1 so a
# short file is never weighted above a word in its name: (k1 + 1) / (1 + k1 * (1 - b + b * dl / avgdl)).
BM25_K1 = 1.2
BM25_B = 0.75


def length_factor(size: int | None, average: float) -> float:
    """BM25 length normalisation in (0, 1] for a file of ``size`` bytes against the ``average`` size."""
    if not size or average <= 0:
        return 1.0
    return min(1.0, (BM25_K1 + 1) / (1 + BM25_K1 * (1 - BM25_B + BM25_B * size / average)))


def authority_files(state: State) -> dict[str, list[str]]:
    """Per catalogue family, the files that speak for it: its entry points, else its shallowest
    README or index files, else its only file. Data stores have none (their store speaks)."""
    def build() -> dict[str, list[str]]:
        members: dict[str, list[str]] = {}
        for path, (family, _) in state.report.resolved.items():
            members.setdefault(family, []).append(path)
        out = {}
        for entry in (state.catalogue or {}).get('entries', []):
            if entry['kind'] == 'data_store':
                continue
            points = [cat.strip_fragment(e['path']) for e in entry.get('entrypoints', [])]
            files = members.get(entry['id'], [])
            if not points:
                index = [p for p in files if INDEX_NAME.fullmatch(PurePosixPath(p).name)]
                depth = min((p.count('/') for p in index), default=0)
                points = sorted(p for p in index if p.count('/') == depth) or (files if len(files) == 1 else [])
            out[entry['id']] = points[:MAX_ENTRYPOINTS_PER_FAMILY]
        return out
    return _derived(state, 'authorities', build)


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
    symbol_terms: set[str] = field(default_factory=set)  # query words in ONE code identifier or header line
    compounds: set[str] = field(default_factory=set)  # typed identifiers held as a unit (name, code or text)
    defined: set[str] = field(default_factory=set)  # those held in the path name or a code identifier
    summary_terms: set[str] = field(default_factory=set)  # query words in a code file's summary (docstring, header)
    code_terms: set[str] = field(default_factory=set)  # query words over all of a code file's identifier units
    passage_terms: set[str] = field(default_factory=set)  # query words together in one short passage of text
    record_terms: set[str] = field(default_factory=set)  # query words on one line that records a lifecycle state
    catalogue_terms: set[str] = field(default_factory=set)  # in its family's keywords, id or its entry-point topic
    purpose_terms: set[str] = field(default_factory=set)  # in its family's purpose or notes
    authority: bool = False  # an entry point, README or index that speaks for its family or directory
    length: float = 1.0  # the BM25 length factor of its text (1 for a short file)
    store: dict | None = None  # the catalogue entry when this candidate is a data store (no tracked file)
    intent_in_name: int = 0  # intent words ("deprecated", "old") in its path name
    name_covered: bool = False  # every word of its file name is a query word

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
    terms, intent_words = query_plan(text)
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
    units = compounds(text)
    family_hits, matched_families = _catalogue_hits(state, terms, phrase, family)
    candidates = _name_candidates(state, terms, phrase, family, units)
    timings['names_ms'] = round((time.monotonic() - tick) * 1000)

    tick = time.monotonic()
    with ThreadPoolExecutor(max_workers=1) as code_runner:
        # Code identifiers are searched beside the text search; never with a --family filter or an
        # invalid catalogue (which reads no text at all).
        code = (code_runner.submit(_symbol_scan, state, terms, deadline, units)
                if family is None and state.catalogue is not None else None)
        df, readable, content_complete = _content_candidates(state, terms, text, phrase, family, candidates,
                                                             deadline, reasons, units)
        scan = code.result() if code is not None else SymbolScan()
    _merge_symbols(scan, candidates, reasons)
    _catalogue_evidence(state, terms, family, candidates, units)
    _mark_candidates(state, candidates, intent_words, deadline)
    timings['content_ms'] = round((time.monotonic() - tick) * 1000)

    status_question = any(w in STATUS_INTENT for w in intent_words)
    process = is_process_question(text, intent_words)
    # Rarity over everything searched: a word common in code identifiers is not rare because prose lacks it.
    searched = len(readable) + scan.files
    weights = {t: rarity(searched, df.get(t, 0) + scan.df.get(t, 0)) for t in terms}
    seen = {hit['path'] for hit in family_hits if hit.get('path')}
    rank_key = functools.partial(_rank_key, state, terms=terms, weights=weights, status_question=status_question,
                                 process=process)
    ranked = sorted((c for c in candidates.values() if c.path not in seen), key=rank_key)
    pool = ranked[:max(RERANK_POOL, 3 * limit)]
    # The files that speak for a catalogue family (its entry points, else its shallowest README or
    # index) are always read, whatever the ``limit``: what they say about their family is found
    # however weak its word evidence. For a status question every README or index is read too: the
    # record of a lifecycle (a decision index row, a directory README's status line) lives there.
    speakers = {p for paths in authority_files(state).values() for p in paths}
    pool += [c for c in ranked[len(pool):] if c.in_content and (c.path in speakers or (status_question and c.authority))]
    tick = time.monotonic()
    excerpts_complete = _read_lines(state, [c for c in pool if c.in_content], terms, text, phrase, deadline)
    timings['excerpts_ms'] = round((time.monotonic() - tick) * 1000)
    pool.sort(key=rank_key)
    content_hits = [_candidate_hit(state, c, terms, phrase) for c in pool[:limit]]
    hits = _with_replacements(state, family_hits + content_hits, terms)[:limit]
    if status_question:
        hits = _with_lifecycle_records(state, hits, terms, deadline)[:limit]
    timings['total_ms'] = round((time.monotonic() - started) * 1000)
    for rank, hit in enumerate(hits, 1):
        hit['rank'] = rank

    incomplete = bool(reasons) or not content_complete
    outcome = 'found' if hits else ('incomplete' if incomplete else 'no_match')
    return {
        'query': text, 'terms': terms, 'intent_words': intent_words, 'outcome': outcome, 'hits': hits,
        'candidates': len(candidates) + len(family_hits), 'families_matched': matched_families,
        'coverage': {**_coverage(state, family, readable, incomplete, reasons, excerpts_complete),
                     'code_files_searched': scan.files, 'name_only_terms': _name_only_terms(terms)},
        'timings_ms': timings,
    }


def _coverage(state: State, family: str | None, readable: set[str], incomplete: bool, reasons: list[str],
              excerpts_complete: bool) -> dict:
    entries = state.catalogue['entries'] if state.catalogue else []
    families = [e for e in entries if e['kind'] != 'data_store' and (family is None or e['id'] == family)]
    owners = {state.report.resolved[p][0] for p in readable if p in state.report.resolved}
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


def _lifecycle_rank(state: State, path: str, status_question: bool = False) -> int:
    """Current first, then draft or unclassified, historical, superseded; backup-like copies last.

    For a status question every lifecycle ranks alike (the superseded or historical thing is
    what is asked about, and its replacement follows it); backup-like copies stay last.
    """
    if is_backup_like(path):
        return BACKUP_RANK
    if status_question:
        return 0
    return LIFECYCLE_RANK.get(state.lifecycle_of(path)[1], 1)


def field_weight(c: Candidate, term: str, process: bool = False, record: bool = False) -> float:
    """How strongly ``c`` holds ``term``: its best field.

    1 in the path name; CATALOGUE_WEIGHT in its family's keywords, id or entry-point topic;
    SYMBOL_WEIGHT in one code identifier unit (a definition with its docstring); UNIT_WEIGHT in
    the file's summary (module docstring, header comments), with another query word in one
    short passage of text (PASSAGE_SPAN lines) or in its family's purpose; TEXT_WEIGHT times the
    BM25 length factor anywhere in its text, CODE_BAG_WEIGHT times it over all its code
    identifier units. For a process question (``is_process_question``) the three code fields
    count PROCESS_CODE_BOOST times as much (at most 1): the implementation is the answer. With
    ``record`` (a status question whose words ``c`` records on one lifecycle line, ``record_share``),
    a word on that line counts like a word in the name: the line is the record that answers it.
    """
    boost = PROCESS_CODE_BOOST if process else 1.0
    if term in c.name_terms or (record and term in c.record_terms):
        return 1.0
    if term in c.catalogue_terms:
        return CATALOGUE_WEIGHT
    if term in c.symbol_terms:
        return min(1.0, SYMBOL_WEIGHT * boost)
    if term in c.summary_terms:
        return min(1.0, UNIT_WEIGHT * boost)
    if term in c.passage_terms or term in c.purpose_terms:
        return UNIT_WEIGHT
    if term in c.content_terms:
        return TEXT_WEIGHT * c.length
    if term in c.code_terms:
        return min(1.0, CODE_BAG_WEIGHT * boost) * c.length
    return 0.0


def is_process_question(text: str, intent_words: Sequence[str]) -> bool:
    """A question about where something is done ("what stops ...", "where do we check ...",
    "where is X implemented?"): a process intent word, or a question word (what, which, where,
    how) with a PROCESS_VERBS verb in any inflection."""
    if any(w in PROCESS_INTENT for w in intent_words):
        return True
    found = words(text)
    return bool(found) and found[0] in QUESTION_WORDS and bool(_prefix_hits(sorted(PROCESS_VERBS), found))


def record_share(c: Candidate, terms: list[str], weights: dict[str, float]) -> float:
    """The rarity-weighted share of the query that ``c`` holds on one lifecycle line (``lifecycle_record``),
    or 0 below RECORD_SHARE: a record answers a status question only when it names most of what is
    asked about, not when a common word or two sit beside "legacy" or "historical"."""
    if not c.record_terms:
        return 0.0
    share = sum(weights[t] for t in c.record_terms) / sum(weights[t] for t in terms)
    return share if share >= RECORD_SHARE else 0.0


def rarity(searched: int, holding: int) -> float:
    """A word's rarity weight: BM25's Robertson-Sparck Jones idf, log((N - n + 0.5) / (n + 0.5)), floored
    at MIN_RARITY. A word in most searched files ("check", "data") carries almost no weight, so the
    rare words of a question decide its ranking."""
    holding = min(holding, searched)
    return max(MIN_RARITY, math.log((searched - holding + 0.5) / (holding + 0.5)))


def relevance(c: Candidate, terms: list[str], weights: dict[str, float], process: bool = False,
              status: bool = False) -> float:
    """Field-weighted relevance in [0, 2.25]: each query word's rarity weight (idf over the searched
    documents and code files) times its ``field_weight``, divided by the total weight.

    The whole phrase adds 1 in the name or 1/2 in the text (1/4 when its only line is a one-line
    data dump longer than LONG_LINE characters); an intent word in the path name ("deprecated",
    "old") adds INTENT_NAME_BONUS.
    """
    total = sum(weights[t] for t in terms)
    record = status and record_share(c, terms, weights) > 0
    score = sum(weights[t] * field_weight(c, t, process, record) for t in terms) / total
    if len(terms) > 1:
        if c.phrase_in_name:
            score += 1.0
        elif c.phrase_in_content:
            score += 0.25 if c.line_text is not None and len(c.line_text) > LONG_LINE else 0.5
    if c.intent_in_name:
        score += INTENT_NAME_BONUS
    if c.name_covered:
        score += NAME_COVER_BONUS
    return score


def _rank_key(state: State, c: Candidate, terms: list[str], weights: dict[str, float],
              status_question: bool = False, process: bool = False) -> tuple:
    """(tier, relevance band, typed identifiers held, lifecycle, name evidence, line evidence, relevance, path).

    Tier 0: the whole query in the path name (every word of it, or the phrase), or every word
    in the path name and one code identifier line together. Tier 1:
    the whole phrase in the text on a line that is not a one-line data dump (a one-word
    query: the word in the text). Tier 2: everything else. Within a tier, files are banded
    in quarter steps of ``relevance`` less LIFECYCLE_PENALTY per lifecycle step (current,
    draft or unclassified, historical, superseded, backup-like), so an older file with
    clearly better evidence still ranks first. Within a band, a file holding more of the
    query's typed identifiers (``compounds``) as a unit comes first: in its name or a code
    identifier (where it is defined), then anywhere (its text). Then lifecycle (alike for a
    status question), then a file that speaks for its family or directory (entry point,
    README, index, data store), then words in the path name, then query words together on one short line; the exact
    relevance and the path break the remaining ties.
    """
    score = relevance(c, terms, weights, process, status_question)
    long_line = c.line_text is not None and len(c.line_text) > LONG_LINE
    if c.phrase_in_name or (c.name_terms | c.symbol_terms | c.catalogue_terms) == set(terms):
        tier = 0
    elif (c.phrase_in_content or (len(terms) == 1 and c.content_terms)) and not long_line:
        tier = 1
    else:
        tier = 2
    name_weight = sum(weights[t] for t in c.name_terms)
    lifecycle = _lifecycle_rank(state, c.path, status_question)
    banded = score - LIFECYCLE_PENALTY * lifecycle
    record = round(record_share(c, terms, weights), 6) if status_question else 0
    return (tier, -round(banded * 4), -len(c.defined), -len(c.compounds | c.defined), -record, lifecycle,
            not c.authority, -round(name_weight, 6), -c.line_terms, -round(score, 6), c.path)


def _candidate_hit(state: State, c: Candidate, terms: list[str], phrase: list[str]) -> dict:
    matched = sorted(c.name_terms | c.content_terms | c.symbol_terms | c.summary_terms | c.code_terms
                     | c.catalogue_terms | c.purpose_terms | c.passage_terms | c.record_terms)
    if c.store is not None:
        return {**_entry_hits(state, c.store, terms)[0], 'matched': matched}
    match = ('content' if c.in_content else 'symbol' if c.symbol_terms or c.summary_terms
             else 'catalogue' if c.catalogue_terms or c.purpose_terms else 'name')
    hit = _path_hit(state, c.path, match, matched=matched)
    if c.line is not None:
        hit['line'] = c.line
        hit['excerpt'] = _excerpt(c.line_text, terms, phrase)
    return hit


def _with_replacements(state: State, hits: list[dict], terms: list[str]) -> list[dict]:
    """``hits`` with each superseded hit followed by its replacement, and no path twice.

    "Is X current, and what replaced it?" is answered by X's lifecycle record: the hit for X
    says superseded, and the next hit is the replacement itself (match ``replacement``,
    ``replaces`` naming X), unless the replacement already ranks above X.
    """
    out: list[dict] = []
    emitted: set[str] = set()

    def add(hit: dict) -> None:
        if hit.get('path') is None or hit['path'] not in emitted:
            out.append(hit)
            if hit.get('path'):
                emitted.add(hit['path'])
    for hit in hits:
        add(hit)
        target = hit.get('superseded_by')
        if not target:
            continue
        replaces = hit.get('path') or hit.get('family')
        if target.startswith('id:'):
            entry = state.by_id.get(target[3:])
            for replacement in (_entry_hits(state, entry, terms)[:1] if entry else []):
                add({**replacement, 'match': 'replacement', 'replaces': replaces})
        else:
            add(_path_hit(state, cat.strip_fragment(target), 'replacement', replaces=replaces))
    return out


# A path word that says the thing is historical (scripts/legacy/..., scripts-deprecated/, docs/archive/).
HISTORICAL_PATH_WORDS = frozenset({'legacy', 'deprecated', 'archive', 'archived', 'old', 'obsolete', 'historical',
                                   'retired', 'superseded'})
MIN_RECORD_NAME = 6  # a file name shorter than this ("a.md") names nothing in an index


def is_historical(hit: dict) -> bool:
    """A hit for a historical thing: catalogued historical or superseded, a backup-like copy, or a
    path whose words say so (``HISTORICAL_PATH_WORDS``)."""
    return (hit.get('lifecycle') in ('archive', 'superseded') or bool(hit.get('backup_like'))
            or bool(HISTORICAL_PATH_WORDS.intersection(words(hit['path']))))


def directory_indexes(state: State) -> dict[str, list[str]]:
    """Per directory, its text-readable README or index files (``INDEX_NAME``)."""
    def build() -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for path in state.files:
            if INDEX_NAME.fullmatch(PurePosixPath(path).name) and text_readable(state, path):
                out.setdefault(str(PurePosixPath(path).parent), []).append(path)
        return {d: sorted(paths) for d, paths in out.items()}
    return _derived(state, 'directory_indexes', build)


def lifecycle_authorities(state: State, path: str) -> tuple[list[str], list[str]]:
    """Where the lifecycle of ``path`` is recorded, besides the catalogue: (its family's authority
    files, which record it only when they name it; the README or index of its nearest owning
    directory below the top level, which governs everything in it). Never ``path`` itself and
    never an unreadable file."""
    family = state.lifecycle_of(path)[0]
    registries = [a for a in authority_files(state).get(family, []) if a != path and text_readable(state, a)]
    parents = PurePosixPath(path).parent.parts
    indexes = directory_indexes(state)
    for depth in range(len(parents), 1, -1):
        found = [i for i in indexes.get('/'.join(parents[:depth]), []) if i != path]
        if found:
            return registries, found[:1]
    return registries, []


def _with_lifecycle_records(state: State, hits: list[dict], terms: list[str], deadline: float) -> list[dict]:
    """``hits`` with each historical hit (``is_historical``) of a status question followed by the record
    of its lifecycle: the family authority that names it (a decision index, an ADR index, a ledger;
    one bounded ``git grep`` for the file names), else the README of its owning directory (match
    ``lifecycle_record``, ``records`` naming the hit, the naming line as excerpt). "Is X still used,
    what happened to it?" is answered by that record, not by X; no path appears twice.
    """
    plans: list[tuple[dict, list[str], list[str]]] = []
    for hit in hits:
        path = hit.get('path')
        if path and hit.get('match') != 'data_store' and is_historical(hit) \
                and not INDEX_NAME.fullmatch(PurePosixPath(path).name):
            plans.append((hit, *lifecycle_authorities(state, path)))
    names = {PurePosixPath(hit['path']).name for hit, registries, _ in plans if registries}
    names = sorted(n for n in names if len(n) >= MIN_RECORD_NAME)
    registries = sorted({r for _, rs, _ in plans for r in rs})
    naming: dict[tuple[str, str], tuple[int, str]] = {}
    if names and registries:
        run = _total_grep(state.repo, _line_args(names, [f':(literal){r}' for r in registries], None),
                          deadline, EXCERPT_OUTPUT_CAP)
        for record in run.stdout.split(b'\n'):
            parts = record.split(b'\0', 2)
            if len(parts) == 3 and parts[1].isdigit():
                where, line = parts[0].decode('utf-8', 'replace'), parts[2].decode('utf-8', 'replace')
                for name in names:
                    if name.casefold() in line.casefold():
                        naming.setdefault((where, name), (int(parts[1]), line))
    records: dict[str, tuple[str, int | None, str | None]] = {}
    for hit, rs, directory in plans:
        name = PurePosixPath(hit['path']).name
        named = [(r, naming[(r, name)]) for r in rs if (r, name) in naming]
        if named:
            records[hit['path']] = (named[0][0], *named[0][1])
        elif directory:
            records[hit['path']] = (directory[0], None, None)
    out: list[dict] = []
    emitted: set[str] = set()
    for hit in hits:
        if hit.get('path') in emitted:
            continue
        out.append(hit)
        if hit.get('path'):
            emitted.add(hit['path'])
        if hit.get('path') in records:
            where, line, text = records[hit['path']]
            if where not in emitted:
                extra = {'line': line, 'excerpt': _excerpt(text, terms, [])} if text is not None else {}
                out.append(_path_hit(state, where, 'lifecycle_record', records=hit['path'], **extra))
                emitted.add(where)
    return out


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


def _catalogue_evidence(state: State, terms: list[str], family: str | None,
                        candidates: dict[str, Candidate], units: Sequence[str] = ()) -> None:
    """Credit each family's catalogue words to the files that speak for it, and data stores to their store.

    The catalogue is curated metadata about a family, so it is read before body text: query words
    in a family's keywords or id (and, for one entry point, its topic) count at CATALOGUE_WEIGHT for
    each of its ``authority_files``; words in its purpose or notes count as text. A data store has
    no tracked file, so its store becomes a candidate of its own (rendered as a data_store hit).
    Every entry point, README or index that speaks for a family is marked ``authority``.
    """
    if state.catalogue is None:
        return
    authorities = authority_files(state)
    for entry in state.catalogue['entries']:
        if family is not None and entry['id'] != family:
            continue
        keys = [words(k) for k in entry.get('keywords', [])] + [words(entry['id'])]
        keys += [words(s) for s in entry.get('store', [])]
        strong = set().union(*(_prefix_hits(terms, k) for k in keys))
        weak = _prefix_hits(terms, words(entry.get('purpose', '')) + words(entry.get('notes', ''))) - strong
        if entry['kind'] == 'data_store':
            if strong or weak:
                store = entry['store'][0]
                candidate = candidates.setdefault(store, Candidate(store))
                candidate.catalogue_terms |= strong
                candidate.purpose_terms |= weak
                candidate.name_terms |= _prefix_hits(terms, words(store))
                candidate.defined |= {u for u in units if _contains_words(words(store), words(u))}
                candidate.store, candidate.authority = entry, True
            continue
        topics = {cat.strip_fragment(e['path']): words(e['topic']) for e in entry.get('entrypoints', [])}
        for path in authorities.get(entry['id'], []):
            if path not in state.files or cat.is_excluded(path) or cat.CONTROL_CHARS.search(path):
                continue
            own = strong | _prefix_hits(terms, topics.get(path, []))
            if own or weak or path in candidates:
                candidate = candidates.setdefault(path, Candidate(path))
                candidate.catalogue_terms |= own
                candidate.purpose_terms |= weak - own
                candidate.authority = True


def _average_sizes(state: State, sizes: dict[str, int]) -> tuple[float, float]:
    """The mean size of the text-readable files and of the other (code) files: BM25's avgdl per corpus."""
    text = [size for path, size in sizes.items() if text_readable(state, path)]
    code = [size for path, size in sizes.items() if not text_readable(state, path)]
    return (sum(text) / len(text) if text else 0.0, sum(code) / len(code) if code else 0.0)


def _mark_candidates(state: State, candidates: dict[str, Candidate], intent_words: list[str],
                     deadline: float) -> None:
    """Length factors, README authority and intent words in names, for every candidate."""
    sizes = blob_sizes(state, deadline)
    averages = _average_sizes(state, sizes)
    for path, c in candidates.items():
        c.length = length_factor(sizes.get(path), averages[not text_readable(state, path)])
        if README_NAME.fullmatch(PurePosixPath(path).name):
            c.authority = True
        if intent_words:
            c.intent_in_name = len(_prefix_hits(intent_words, words(path)))


# ---------------------------------------------------------------- step 2: names

GIT_FILE = re.compile(r'\.git[a-z]+')


def name_words(path: str) -> list[str]:
    """The words of a path that can say what it is about: every word except a README or index file
    name, which only says that the file describes its directory ("read" never meets README)."""
    name = PurePosixPath(path).name
    found = words(path)
    if INDEX_NAME.fullmatch(name):
        return found[:-len(words(name))]
    if GIT_FILE.fullmatch(name):  # .gitattributes is git's attributes file: "git" and "attributes"
        return [*found[:-1], 'git', found[-1][3:]]
    return found


def name_covered(path: str, terms: list[str]) -> bool:
    """Every word of the file name without its extension is a query word (as typed or stemmed):
    the query names the file itself (``.python-version`` for "python version pin"). Never a README
    or index file, whose name is not its subject."""
    name = PurePosixPath(path).name
    if INDEX_NAME.fullmatch(name):
        return False
    base = name.rsplit('.', 1)[0] if '.' in name[1:] else name
    base_words = words(base)
    return bool(base_words) and all(_prefix_hits(terms, [w]) for w in base_words)


def _name_candidates(state: State, terms: list[str], phrase: list[str], family: str | None,
                     units: list[str]) -> dict[str, Candidate]:
    found: dict[str, Candidate] = {}
    for path in state.files:
        folded = normalise(path)
        if not any(stem(t) in folded for t in terms):
            continue  # cheap screen: a prefix of a path word is a substring of the path
        if cat.CONTROL_CHARS.search(path) or cat.is_excluded(path):
            continue
        if family is not None and state.report.resolved.get(path, (None,))[0] != family:
            continue
        path_words = name_words(path)
        hits = _prefix_hits(terms, path_words)
        if hits:
            found[path] = Candidate(path, name_terms=hits,
                                    phrase_in_name=len(phrase) > 1 and _contains_words(path_words, phrase),
                                    defined={u for u in units if _contains_words(path_words, words(u))},
                                    name_covered=name_covered(path, terms))
    return found


# ---------------------------------------------------------------- step 3: tracked text

def _text_pattern(term: str) -> str:
    """What the text search looks for: the term's ``stem`` as a fixed string, so "regenerated" meets
    "regeneration" and "deletion" meets "deleted" (the stem keeps at least MIN_STEM letters)."""
    return stem(term)


def _name_only_terms(terms: list[str]) -> list[str]:
    """One-character terms beside longer terms: matched in names, the catalogue and the phrase, not in text."""
    return [t for t in terms if len(t) == 1] if any(len(t) > 1 for t in terms) else []


def _content_candidates(state: State, terms: list[str], text: str, phrase: list[str], family: str | None,
                        candidates: dict[str, Candidate], deadline: float, reasons: list[str],
                        units: Sequence[str] = ()) -> tuple[dict[str, int], set[str], bool]:
    """Per-term (whole-phrase, compound) file lists from git grep; returns (document frequency, readable, complete)."""
    if state.catalogue is None:
        return {}, set(), False
    pathspecs, readable = _pathspecs(state, family)
    if not readable:
        return {}, readable, True
    # A one-character word beside longer words is matched in names, the catalogue and the whole
    # phrase only (``_name_only_terms``, reported in the coverage): in text it occurs in almost
    # every file, so it carries no evidence and the lowest rarity weight. The search is complete.
    name_only = _name_only_terms(terms)
    patterns = [(t, _text_pattern(t)) for t in terms if t not in name_only]
    if len(phrase) > 1:
        patterns.append(('\0phrase', text))  # the cleaned query as typed: separators and all
    patterns += [(f'\0compound {unit}', unit) for unit in units]
    jobs = {key: _files_args(pattern, pathspecs) for key, pattern in patterns}
    with ThreadPoolExecutor(max_workers=min(4, len(jobs)) or 1) as pool:
        futures = {key: pool.submit(_total_grep, state.repo, args, deadline, GREP_OUTPUT_CAP)
                   for key, args in jobs.items()}
        runs = {key: future.result() for key, future in futures.items()}
    complete = True
    df: dict[str, int] = dict.fromkeys(name_only, len(readable))
    for key, run in runs.items():
        if run.outcome in ('timeout', 'output_budget', 'error'):
            complete = False
            detail = f' ({run.detail})' if run.detail else ''
            reasons.append(f'{run.outcome}: the search for {key.lstrip(chr(0))!r} did not finish{detail}')
            continue
        paths = [p.decode('utf-8', 'replace') for p in run.stdout.split(b'\0') if p]
        paths = [p for p in paths if p in readable]  # the gate again, whatever git returned
        if not key.startswith('\0'):
            df[key] = len(paths)
        for path in paths:
            candidate = candidates.setdefault(path, Candidate(path))
            if key == '\0phrase':
                candidate.phrase_in_content = True
            elif key.startswith('\0compound '):
                candidate.compounds.add(key.removeprefix('\0compound '))
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
    by_path = {c.path: c for c in pool if text_readable(state, c.path)}
    if not by_path:
        return True
    # One-character words match almost every line, so they pick lines only when nothing longer exists.
    words_only = [t for t in terms if len(t) > 1] or terms
    stems = list(dict.fromkeys(_text_pattern(t) for t in words_only))
    jobs = []
    for phrase_files, patterns, cap in ((True, [text], EXCERPT_LINES_PER_FILE), (False, stems, PASSAGE_LINES_PER_FILE)):
        paths = sorted(p for p, c in by_path.items() if c.phrase_in_content == phrase_files)
        if paths and patterns:
            jobs.append(_line_args(patterns, [f':(literal){p}' for p in paths], cap))
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
    echoes = catalogue_echoes(state)
    for path, lines in found.items():
        candidate = by_path[path]
        candidate.line, candidate.line_text = _best_line(lines, terms, normalise(text) if len(phrase) > 1 else '')
        folded = normalise(candidate.line_text)
        candidate.line_terms = (sum(t in folded for t in terms) if len(candidate.line_text) <= LONG_LINE else 0)
        candidate.passage_terms = best_passage(lines, terms)
        if path not in echoes:
            candidate.record_terms = lifecycle_record(lines, terms)
    return complete


def catalogue_echoes(state: State) -> set[str]:
    """The files that restate the catalogue's lifecycle records: the catalogue's own family (the
    catalogue, its census) and the documentation map whose family table is generated from it. Find
    reads the catalogue as structure (every hit carries its status and replacement), so their
    lifecycle lines are never a second record (``lifecycle_record``)."""
    def build() -> set[str]:
        own = state.lifecycle_of(cat.CATALOGUE_PATH)[0]
        return {p for p, (family, _) in state.report.resolved.items() if own and family == own} | {cat.README_PATH}
    return _derived(state, 'echoes', build)


def lifecycle_record(lines: list[tuple[int, str]], terms: list[str]) -> set[str]:
    """The most query words on one line that also records a lifecycle state (LIFECYCLE_MARKER): a
    registry row, a status banner or a configuration comment. At least two words (one word beside
    "superseded" is any sentence); lines longer than LONG_LINE (one-line data dumps) are no record."""
    best: set[str] = set()
    for _, text in lines:
        if len(text) <= LONG_LINE and LIFECYCLE_MARKER.search(normalise(text)):
            hits = _prefix_hits(terms, words(text))
            if len(hits) > len(best):
                best = hits
    return best if len(best) > 1 else set()


def best_passage(lines: list[tuple[int, str]], terms: list[str]) -> set[str]:
    """The most query words found together within PASSAGE_SPAN consecutive lines (whole words, as
    typed or stemmed); lines longer than LONG_LINE (one-line data dumps) are no passage."""
    hits = sorted((no, _prefix_hits(terms, words(text))) for no, text in lines if len(text) <= LONG_LINE)
    best: set[str] = set()
    for i, (start, _) in enumerate(hits):
        window = set().union(*(h for no, h in hits[i:] if no < start + PASSAGE_SPAN))
        if len(window) > len(best):
            best = window
    return best if len(best) > 1 else set()  # one word alone is text, not co-occurrence


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


# ---------------------------------------------------------------- step 4: code identifiers

# "Where is X implemented / checked / configured?" is answered by the code or configuration file
# that defines X, not by prose that mentions it. Code text is never searched as prose: only its
# identifiers count (definitions, CLI subcommands and flags, configuration keys and ids, Markdown
# headings, quoted UPPER_SNAKE codes) and its own summary (comment and docstring-opening lines
# among the first HEADER_LINES).
CODE_ROOTS = ('scripts', 'agents_extensions', '.githooks', '.github', '.mcp', 'packages', 'schemas', 'packaging')
INI_SUFFIXES = frozenset({'.service', '.timer', '.slice', '.socket', '.path', '.target', '.ini', '.cfg', '.conf'})
CONFIG_SUFFIXES = frozenset({'.yaml', '.yml', '.toml'}) | INI_SUFFIXES
CODE_SUFFIXES = frozenset({'.py', '.sh', '.bash', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.yaml', '.yml', '.toml',
                           '.md', ''}) | INI_SUFFIXES
HEADER_LINES = 20
MIN_CODE_PATTERN = 3
_PY = re.compile(r'''^\s*(?:async\s+)?(?:def|class)\s+(\w+)|^([A-Za-z_]\w*)\s*(?::[^=]*)?=(?!=)'''
                 r'''|\badd_parser\(\s*['"]([^'"]+)|\badd_argument\(\s*['"](-[^'"]+)'''
                 r'''|^\s*(?:[rRbBuU]{1,2})?(?:"""|\'\'\')(.+)''')
_SH = re.compile(r'^\s*(?:function\s+)?([A-Za-z_][\w:.-]*)\s*\(\)|^([A-Za-z_]\w*)=')
_JS = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?'
                 r'(?:function\*?|class|const|let|var|interface|type|enum)\s+([A-Za-z_$][\w$]*)')
_YAML = re.compile(r'''^\s*(?:-\s+)?['"]?([^'"#:\s{\[-][^'"#:]*?)['"]?\s*:(?:\s|$)'''
                   r'''|(?:^|[{,]|-)\s*(?:id|name)\s*:\s*['"]?([^'"#,}\s]+)''')
_TOML = re.compile(r'^\s*\[+([^\]]+)\]|^\s*([\w.-]+)\s*=')
_MD = re.compile(r'^#{1,6}\s+(.+)')
# INI-style configuration (systemd units, setup.cfg): a Description is the unit's own summary.
_INI = re.compile(r'^\s*Description\s*=\s*(.+)|^\s*\[([^\]]+)\]|^\s*([\w.-]+)\s*=')
INI_DESCRIPTION = re.compile(r'\s*Description\s*=')
SYMBOL_SHAPES = {'.py': _PY, '.sh': _SH, '.bash': _SH, '': _SH, '.js': _JS, '.mjs': _JS, '.cjs': _JS, '.ts': _JS,
                 '.tsx': _JS, '.yaml': _YAML, '.yml': _YAML, '.toml': _TOML, '.md': _MD,
                 **dict.fromkeys(INI_SUFFIXES, _INI)}
# Git's own pattern files (.gitattributes, .gitignore): every line is a path pattern and its attributes
# ("data/literary_texts/*.jsonl filter=lfs"), the record of how those paths are stored.
_GIT_PATTERNS = re.compile(r'^\s*([^#\s]\S*)(?:\s+(\S.*))?')
NAMED_SHAPES = {'.gitattributes': _GIT_PATTERNS, '.gitignore': _GIT_PATTERNS}
CAMEL = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')
HEADER_LINE = re.compile(r'''\s*(?:#|//|/\*|\*|--|<!--|[rRbBuU]{0,2}(?:"""|\'\'\'))''')
# A quoted UPPER_SNAKE literal names a typed code (an error, finding or event type) wherever it sits.
CODE_LITERAL = re.compile(r'''['"]([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)['"]''')
# CLI help and description text says in words what a command or flag does.
HELP_TEXT = re.compile(r'''\b(?:help|description)\s*=\s*[rRfFuU]{0,2}(?:'([^'\n]{3,})|"([^"\n]{3,}))''')
SUMMARY_LINES = 40  # the head of a code file read for its summary (docstring and comment lines)
DEFINITION = re.compile(r'\s*(?:export\s+)?(?:async\s+)?(?:def|class|function)\s')
DOCSTRING = re.compile(r'''\s*[rRbBuU]{0,2}(?:"""|\'\'\')''')
DOCSTRING_WINDOW = 12  # lines from a definition to its docstring (a long signature in between)
SYMBOL_WEIGHT = 0.75  # a word in one code identifier line: between the path name (1) and the text (1/2)


@functools.lru_cache(maxsize=1 << 16)
def _suffix(path: str) -> str:
    return PurePosixPath(path).suffix


@functools.lru_cache(maxsize=1 << 16)
def code_readable(path: str) -> bool:
    """The privacy boundary for code reads: a code or configuration file whose identifiers may be read.

    True for a path under CODE_ROOTS or at the repository root, with a CODE_SUFFIXES suffix
    (none for hooks and dotfiles), outside the catalogued document roots (searched as text
    instead), with no inventory-excluded component and no control character.
    """
    if cat.CONTROL_CHARS.search(path) or cat.is_excluded(path) or cat.under_roots(path):
        return False
    top, slash, _ = path.partition('/')
    return (not slash or top in CODE_ROOTS) and _suffix(path) in CODE_SUFFIXES


def symbol_text(path: str, line_no: int, line: str) -> str | None:
    """The identifier text a code line contributes, or None when the line is only a use.

    A definition, subcommand, flag, configuration key, id, heading or quoted UPPER_SNAKE code
    contributes its name; a comment or docstring-opening line among the first HEADER_LINES
    (the file's own summary) contributes all of its text. camelCase is split.
    """
    shape = NAMED_SHAPES.get(PurePosixPath(path).name) or SYMBOL_SHAPES.get(_suffix(path))
    found = shape.search(line) if shape else None
    names = [g for g in found.groups() if g] if found else []
    names += CODE_LITERAL.findall(line)
    names += [single or double for single, double in HELP_TEXT.findall(line)]
    if names:
        text = ' '.join(names)
    elif line_no <= HEADER_LINES and HEADER_LINE.match(line):
        text = line
    else:
        return None
    return CAMEL.sub(' ', text)


def _code_pathspecs(state: State) -> tuple[list[str], set[str]]:
    """Pathspecs that reach exactly the code-readable paths, and that readable set."""
    readable = {p for p in state.files if code_readable(p)}
    roots = [r for r in CODE_ROOTS if any(p.startswith(r + '/') for p in readable)]
    top_files = sorted(p for p in readable if '/' not in p)
    excluded = [p for p in state.files if p not in readable and any(p.startswith(r + '/') for r in roots)]
    return ([f':(literal){r}' for r in roots] + [f':(literal){p}' for p in top_files]
            + [f':(exclude,literal){p}' for p in excluded]), readable


def summary_lines(path: str, lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """The lines of a code file's head (``lines``: its first SUMMARY_LINES) that say what the file is.

    Program files (Python, shell, JavaScript, TypeScript, hooks): the header block before the
    first line of code - comment lines and, in Python, the module docstring (opening, body and
    closing); a comment further down is not the file's summary. Configuration (YAML, TOML, INI):
    comment lines anywhere in the head and an INI ``Description=``. Markdown: a front-matter
    ``description``, the first heading and the first paragraph after it. Never a ``#!`` line.
    """
    suffix = _suffix(path)
    if suffix == '.md':
        return _markdown_summary(lines)
    program = suffix not in CONFIG_SUFFIXES
    out: list[tuple[int, str]] = []
    closing = None  # the quote that closes the open module docstring
    for no, line in lines:
        if closing:
            out.append((no, line))
            if closing in line:
                closing = None
        elif suffix == '.py' and DOCSTRING.match(line) and not any(DOCSTRING.match(text) for _, text in out):
            quote = '"""' if '"""' in line else "'''"
            out.append((no, line))
            if quote not in line.split(quote, 1)[1]:
                closing = quote
        elif line.startswith('#!') or not line.strip():
            continue
        elif HEADER_LINE.match(line) or (suffix in INI_SUFFIXES and INI_DESCRIPTION.match(line)):
            out.append((no, line))
        elif program:
            break  # the first line of code ends the header
    return out


FRONT_MATTER_SUMMARY = re.compile(r'\s*(?:description|summary)\s*:\s*(.+)', re.IGNORECASE)


def _markdown_summary(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """A Markdown file's front-matter description, first heading and first paragraph after that heading."""
    out: list[tuple[int, str]] = []
    front = bool(lines) and lines[0][1].strip() == '---'
    heading = paragraph = False
    for index, (no, line) in enumerate(lines):
        text = line.strip()
        if front:
            if index and text == '---':
                front = False
            elif FRONT_MATTER_SUMMARY.match(line):
                out.append((no, line))
        elif not heading:
            if _MD.match(line):
                heading = True
                out.append((no, line))
        elif text.startswith(('```', '~~~', '#')) or (paragraph and not text):
            break  # a code fence, the next heading, or the blank line that ends the first paragraph
        elif text:
            paragraph = True
            out.append((no, line))
    return out


@dataclass
class CodeSummaries:
    """Per code file its summary lines, and an index from each summary word to the files holding it."""
    lines: dict[str, list[tuple[int, str]]] = field(default_factory=dict)
    index: dict[str, set[str]] = field(default_factory=dict)


def code_summaries(state: State, deadline: float) -> tuple[CodeSummaries, str | None]:
    """The summaries of every code-readable file: one ``git grep -m SUMMARY_LINES`` reads each file's head.

    Built once per state; a search that does not finish is returned with its reason and not kept.
    """
    with state.derived_lock:
        if 'summaries' in state.derived:
            return state.derived['summaries'], None
    pathspecs, readable = _code_pathspecs(state)
    if not readable:
        return CodeSummaries(), None
    args = ['--no-color', '-I', '--null', '-n', '-m', str(SUMMARY_LINES), '-e', '', '--', *pathspecs]
    run = _total_grep(state.repo, args, deadline, CODE_OUTPUT_CAP)
    if run.outcome not in ('ok', 'no_match'):
        detail = f' ({run.detail})' if run.detail else ''
        return CodeSummaries(), f'{run.outcome}: the code summary read did not finish{detail}'
    heads: dict[str, list[tuple[int, str]]] = {}
    for record in run.stdout.split(b'\n'):
        parts = record.split(b'\0', 2)
        if len(parts) == 3 and parts[1].isdigit():
            path = parts[0].decode('utf-8', 'replace')
            if path in readable:
                heads.setdefault(path, []).append((int(parts[1]), parts[2].decode('utf-8', 'replace')[:LONG_LINE]))
    found = CodeSummaries()
    for path, head in heads.items():
        if kept := summary_lines(path, head):
            found.lines[path] = kept
            for word in words(CAMEL.sub(' ', ' '.join(text for _, text in kept))):
                found.index.setdefault(word, set()).add(path)
    with state.derived_lock:
        state.derived['summaries'] = found
    return found, None


def _summary_hits(summaries: CodeSummaries, terms: list[str]) -> dict[str, set[str]]:
    """Per code file, the terms its summary holds as a word prefix (as typed or as their stem)."""
    hits: dict[str, set[str]] = {}
    for term in terms:
        prefixes = (term, stem(term))
        for word, paths in summaries.index.items():
            if word.startswith(prefixes):
                for path in paths:
                    hits.setdefault(path, set()).add(term)
    return hits


@dataclass
class SymbolScan:
    """What ``_symbol_scan`` found: per path its best identifier unit, and how the search went."""
    lines: dict[str, tuple[set[str], int, str]] = field(default_factory=dict)  # path -> (terms, line no, line)
    df: dict[str, int] = field(default_factory=dict)  # term -> code files holding it in an identifier line
    compounds: dict[str, set[str]] = field(default_factory=dict)  # path -> typed identifiers in an identifier line
    union: dict[str, set[str]] = field(default_factory=dict)  # path -> terms over all its identifier units
    summary: dict[str, tuple[set[str], int, str]] = field(default_factory=dict)  # path -> its summary's terms
    records: dict[str, set[str]] = field(default_factory=dict)  # path -> terms on a lifecycle line of its summary
    files: int = 0
    failure: str | None = None


def _symbol_scan(state: State, terms: list[str], deadline: float, units: Sequence[str] = ()) -> SymbolScan:
    """Code files whose identifiers or header hold query words.

    One ``git grep`` reads every code line holding a query word (or its stem); a line counts
    only when ``symbol_text`` finds an identifier in it, and a file's evidence is its ONE unit
    with the most query words (a line, or a definition with the docstring that opens within
    DOCSTRING_WINDOW lines of it), so words scattered over a large file's definitions never
    add up. Runs beside the text search (no shared state); ``_merge_symbols`` applies the result.
    """
    pathspecs, readable = _code_pathspecs(state)
    scan = SymbolScan(files=len(readable))
    if not readable:
        return scan
    # Words shorter than MIN_CODE_PATTERN occur on most code lines: they never select lines, but
    # still count on a line another query word selected (a query of short words only uses them).
    patterns = list(dict.fromkeys(stem(t) for t in terms if len(t) >= MIN_CODE_PATTERN)) or terms
    run = _total_grep(state.repo, _line_args(patterns, pathspecs, None), deadline, CODE_OUTPUT_CAP)
    if run.outcome in ('timeout', 'output_budget', 'error'):
        detail = f' ({run.detail})' if run.detail else ''
        scan.failure = f'{run.outcome}: the code identifier search did not finish{detail}'
    seen: dict[str, set[str]] = {}
    last_definition: dict[str, tuple[int, set[str]]] = {}  # git grep reports a file's lines in order
    for record in run.stdout.split(b'\n'):
        parts = record.split(b'\0', 2)
        if len(parts) != 3 or not parts[1].isdigit():
            continue
        path, line_no, line = parts[0].decode('utf-8', 'replace'), int(parts[1]), parts[2].decode('utf-8', 'replace')
        if path not in readable or len(line) > LONG_LINE:
            continue
        text = symbol_text(path, line_no, line)
        text_words = words(text) if text else []
        hits = _prefix_hits(terms, text_words)
        if held := {u for u in units if _contains_words(text_words, words(u))}:
            scan.compounds.setdefault(path, set()).update(held)
        for term in hits:
            seen.setdefault(term, set()).add(path)
        if hits and DEFINITION.match(line):
            last_definition[path] = (line_no, hits)
        elif hits and DOCSTRING.match(line) and path in last_definition:
            defined_at, defined = last_definition[path]
            if line_no - defined_at <= DOCSTRING_WINDOW:
                hits = hits | defined
        if hits and (path not in scan.lines or len(hits) > len(scan.lines[path][0])):
            scan.lines[path] = (hits, line_no, line)
        if hits:
            scan.union.setdefault(path, set()).update(hits)
    # The file's summary (its docstring or header comments) is one more unit: "what this file does",
    # in the words a reader uses. Its excerpt is the summary line holding the most query words.
    summaries, failure = code_summaries(state, deadline)
    scan.failure = scan.failure or failure
    for path, hits in _summary_hits(summaries, terms).items():
        for term in hits:
            seen.setdefault(term, set()).add(path)
        scan.union.setdefault(path, set()).update(hits)
        line_no, line = max(summaries.lines[path], key=lambda item: (
            len(_prefix_hits(terms, words(CAMEL.sub(' ', item[1])))), -item[0]))
        scan.summary[path] = (hits, line_no, line)
        if record := lifecycle_record(summaries.lines[path], terms):
            scan.records[path] = record
    scan.df = {term: len(paths) for term, paths in seen.items()}
    return scan


def _merge_symbols(scan: SymbolScan, candidates: dict[str, Candidate], reasons: list[str]) -> None:
    if scan.failure:
        reasons.append(scan.failure)
    for path, held in scan.compounds.items():
        candidates.setdefault(path, Candidate(path)).defined |= held
    for path, (hits, line_no, line) in scan.lines.items():
        candidate = candidates.setdefault(path, Candidate(path))
        candidate.symbol_terms = hits
        candidate.line, candidate.line_text = line_no, line
    for path, (hits, line_no, line) in scan.summary.items():
        candidate = candidates.setdefault(path, Candidate(path))
        candidate.summary_terms = hits
        if len(hits) > len(candidate.symbol_terms):  # quote the unit that holds the most query words
            candidate.line, candidate.line_text = line_no, line
    for path, hits in scan.union.items():
        candidates[path].code_terms = hits
    for path, hits in scan.records.items():
        candidates[path].record_terms = hits


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
        if hit.get('replaces'):
            status += f", replaces {cat.shown(hit['replaces'])}"
        if hit.get('records'):
            status += f", records the lifecycle of {cat.shown(hit['records'])}"
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
                    'Use it before reporting "no source" or asking where something is, whether it is still current '
                    'and what replaced it, or where a check or step is implemented; it searches the catalogue, '
                    'tracked file names, tracked text and the identifiers of tracked code and configuration. Not a Ukrainian dictionary or corpus search: use the '
                    'sources MCP tools for language facts.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  .venv/bin/python -m scripts.docs.find "ULP 1-02"\n'
               '  .venv/bin/python -m scripts.docs.find "vesum database" --json\n'
               '  .venv/bin/python -m scripts.docs.find "teacher deck" --family practice-specs --limit 5\n'
               '  .venv/bin/python -m scripts.docs.find "is gpt-6-astra still current"\n'
               '  .venv/bin/python -m scripts.docs.find "where is resolve-reviewer implemented"\n'
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
