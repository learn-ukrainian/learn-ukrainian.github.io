"""Lexical Sandbox: VESUM-validated word bank for content generation.

Builds a verified vocabulary sandbox from a plan's vocabulary_hints and
module grammar constraints. Every Ukrainian word in the sandbox is:
1. VESUM-verified (exists in the morphological dictionary)
2. Constraint-filtered (only forms allowed at this module level)
3. Enriched with inflection tables showing all legal forms
4. Supplemented with RAG textbook example sentences

Issue: #755
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Reuse constraint definitions from morphological validator
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit.checks.morphological_validator import (
    _CASE_LABELS,
    GrammarConstraint,
    _get_constraints,
)
from rag_batch_verify import vesum_batch_lookup

# ---------------------------------------------------------------------------
# VESUM form generation
# ---------------------------------------------------------------------------

def _extract_ukr_word(hint: str) -> str:
    """Extract Ukrainian word from a vocabulary hint string.

    Handles formats like:
    - "новий (new) — Collocations: ..."
    - "собака"
    - "великий (big/grand)"
    """
    # Take text before first parenthesis or dash
    word = re.split(r'\s*[(\u2014—–-]', hint, maxsplit=1)[0].strip()
    # If still has non-Cyrillic, extract first Cyrillic token
    if word and not re.match(r'^[А-ЯҐЄІЇа-яґєіїʼ\'\u0301]+$', word):
        match = re.search(r'[А-ЯҐЄІЇа-яґєіїʼ\'\u0301]+', word)
        return match.group() if match else word
    return word


_GENDER_LABELS = {"m": "masculine", "f": "feminine", "n": "neuter", "p": "plural"}
_POS_LABELS = {"noun": "Noun", "adj": "Adjective", "verb": "Verb", "adv": "Adverb",
               "numr": "Numeral", "pron": "Pronoun", "prep": "Preposition",
               "conj": "Conjunction", "part": "Particle", "intj": "Interjection"}


def _extract_gender(tags: str) -> str | None:
    """Extract gender from VESUM tags."""
    for g in ("m", "f", "n", "p"):
        if f":{g}:" in tags or tags.endswith(f":{g}"):
            return g
    return None


def _extract_case(tags: str) -> str | None:
    """Extract case code from VESUM tags."""
    for case in _CASE_LABELS:
        if case in tags:
            return case
    return None


def _form_allowed(tags: str, constraints: GrammarConstraint) -> bool:
    """Check if a specific VESUM form is allowed under constraints."""
    # Verb check
    if tags.startswith("verb:"):
        if constraints.no_verbs:
            return False
        if constraints.no_imperatives and "impr" in tags:
            return False
        if constraints.present_only:
            for blocked in ("past", "futr"):
                if f":{blocked}" in tags:
                    return False
        return True

    # Case check for nouns/adjectives
    case = _extract_case(tags)
    if case:
        if constraints.nominative_only and case not in ("v_naz", "v_kly"):
            return False
        if constraints.no_accusative and case == "v_zna":
            return False

    return True


def _get_all_forms(lemma: str, batch_size: int = 500) -> list[dict]:
    """Get all inflected forms of a lemma from VESUM.

    Searches for the lemma in the forms table and returns all entries
    that share the same lemma.
    """
    from rag_batch_verify import get_vesum_conn
    conn = get_vesum_conn()
    rows = conn.execute(
        "SELECT word_form, lemma, pos, tags FROM forms WHERE lemma = ?",
        (lemma,)
    ).fetchall()
    return [{"word_form": r["word_form"], "lemma": r["lemma"],
             "pos": r["pos"], "tags": r["tags"]} for r in rows]


# ---------------------------------------------------------------------------
# Common function words (always available in sandbox)
# ---------------------------------------------------------------------------

COMMON_WORDS = [
    # Pronouns
    "я", "ти", "він", "вона", "воно", "ми", "ви", "вони",
    # Demonstratives
    "це", "той", "та", "те", "ті", "цей", "ця",
    # Common particles/adverbs
    "так", "ні", "не", "дуже", "тут", "там", "ось",
    "також", "ще", "вже", "теж", "тільки",
    # Conjunctions
    "і", "а", "але", "або", "що", "як", "бо",
    # Prepositions
    "в", "у", "на", "з", "до", "для", "по",
    # Question words
    "хто", "що", "де", "коли", "чому", "як", "який", "яка", "яке", "які",
    # Common nouns always needed
    "людина", "слово", "мова", "день", "час",
]


def _collect_candidates(plan: dict, extra_words: list[str] | None = None) -> list[str]:
    """Collect all candidate words from plan vocabulary_hints and extras.

    Returns deduplicated list preserving insertion order.
    """
    candidates: list[str] = list(COMMON_WORDS)

    vocab_hints = plan.get("vocabulary_hints", {})
    if isinstance(vocab_hints, dict):
        for _category, words in vocab_hints.items():
            if isinstance(words, list):
                for w in words:
                    candidates.append(_extract_ukr_word(w) if isinstance(w, str) else w)
            elif isinstance(words, str):
                candidates.append(_extract_ukr_word(words))
    elif isinstance(vocab_hints, list):
        for item in vocab_hints:
            if isinstance(item, str):
                candidates.append(_extract_ukr_word(item))
            elif isinstance(item, dict):
                word = item.get("word") or item.get("uk") or item.get("lemma", "")
                if word:
                    candidates.append(word)

    if extra_words:
        candidates.extend(extra_words)

    return list(dict.fromkeys(w.strip() for w in candidates if w.strip()))


def _select_primary_match(
    word_lower: str, matches: list[dict], is_common: bool
) -> dict:
    """Select the best VESUM match for a word based on POS preference."""
    if is_common:
        non_noun = [m for m in matches if m["pos"] not in ("noun",)]
        return non_noun[0] if non_noun else matches[0]
    if word_lower.endswith(("ти", "тися", "тись")):
        verb_matches = [m for m in matches if m["pos"] == "verb"]
        return verb_matches[0] if verb_matches else matches[0]
    return matches[0]


# ---------------------------------------------------------------------------
# Sandbox builder
# ---------------------------------------------------------------------------

def build_sandbox(
    track: str,
    module_num: int,
    plan: dict,
    extra_words: list[str] | None = None,
    max_examples: int = 8,
) -> str:
    """Build a Lexical Sandbox markdown document.

    Args:
        track: Track code (e.g., "a1", "b1")
        module_num: Module sequence number
        plan: Plan dict with vocabulary_hints, keywords, etc.
        extra_words: Additional words from Pass 1 resource request
        max_examples: Max RAG example sentences to include

    Returns:
        Markdown string with verified vocabulary tables and examples.
    """
    constraints = _get_constraints(track, module_num)

    # 1. Collect all candidate words
    candidates = _collect_candidates(plan, extra_words)
    if not candidates:
        return ""

    # 2. VESUM batch lookup
    lookup_words = [w.lower() for w in candidates]
    vesum_results = vesum_batch_lookup(lookup_words)

    # 3. For each found word, get all forms and filter by constraints
    sections: dict[str, list[dict]] = {
        "nouns": [], "adjectives": [], "verbs": [], "other": []
    }
    verified_lemmas: set[tuple[str, str]] = set()

    common_lower = {w.lower() for w in COMMON_WORDS}

    for word in candidates:
        word_lower = word.lower()
        matches = vesum_results.get(word_lower, [])
        if not matches:
            continue

        is_common = word_lower in common_lower
        primary = _select_primary_match(word_lower, matches, is_common)
        lemma = primary["lemma"]
        pos = primary["pos"]

        # Track (lemma, pos) pairs to allow same-form different-POS entries
        lemma_key = (lemma, pos)
        if lemma_key in verified_lemmas:
            continue
        verified_lemmas.add(lemma_key)

        if is_common and pos not in ("adj", "noun"):
            # For function words (adv, conj, prep, part): just the word itself
            allowed_forms = [{"word_form": word, "tags": primary["tags"],
                              "lemma": lemma, "pos": pos}]
        else:
            # For plan vocabulary: get all forms and filter by constraints
            all_forms = _get_all_forms(lemma)
            if not all_forms:
                all_forms = matches

            allowed_forms = [
                f for f in all_forms
                if _form_allowed(f["tags"], constraints)
                and ":long" not in f["tags"]
                and ":rare" not in f["tags"]
                and ":arch" not in f["tags"]
                and ":short" not in f["tags"]
                and ":pasv" not in f["tags"]
            ]

        if not allowed_forms:
            continue

        entry = {
            "lemma": lemma,
            "pos": pos,
            "original": word,
            "forms": allowed_forms,
        }

        if pos == "noun":
            sections["nouns"].append(entry)
        elif pos == "adj":
            sections["adjectives"].append(entry)
        elif pos == "verb":
            sections["verbs"].append(entry)
        else:
            sections["other"].append(entry)

    # 4. RAG textbook examples
    # Extract just lemma strings for textbook search
    lemma_strings = {lemma for lemma, _ in verified_lemmas}
    examples = _fetch_textbook_examples(
        lemma_strings, track, module_num, constraints, max_examples)

    # 5. Build markdown
    return _format_sandbox(
        track, module_num, constraints, sections, examples, candidates, vesum_results)


def _fetch_textbook_examples(
    lemmas: set[str],
    track: str,
    module_num: int,
    constraints: GrammarConstraint,
    max_examples: int,
) -> list[dict]:
    """Fetch and filter textbook examples from RAG."""
    examples = []
    try:
        from rag.query import search_text
    except ImportError:
        return examples

    # Search for sentences containing our verified lemmas
    search_terms = list(lemmas)[:5]
    for term in search_terms:
        if len(examples) >= max_examples:
            break
        try:
            results = search_text(term, limit=3)
            for r in results:
                if len(examples) >= max_examples:
                    break
                text = r.get("text", "")
                source = r.get("source", "unknown")
                # Only include proper sentences (has punctuation, reasonable length)
                has_punct = any(c in text for c in '.!?')
                cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
                if 20 < len(text) < 150 and has_punct and cyrillic_count > 10:
                    examples.append({
                        "text": text.strip(),
                        "source": source,
                        "search_term": term,
                    })
        except Exception:
            continue

    return examples


def _describe_constraints(constraints: GrammarConstraint) -> list[str]:
    """Return human-readable descriptions of active grammar constraints."""
    forbidden = []
    if constraints.no_verbs:
        forbidden.append("ALL verbs")
    if constraints.no_imperatives:
        forbidden.append("imperative forms")
    if constraints.nominative_only:
        forbidden.append("oblique cases (only nominative/vocative)")
    if constraints.no_accusative:
        forbidden.append("accusative case")
    if constraints.present_only:
        forbidden.append("past/future tense (only present/infinitive)")
    return forbidden


def _prioritize_verb_forms(forms: list[dict], max_forms: int = 15) -> list[str]:
    """Order verb forms by priority: imperative > present > infinitive > rest.

    Prevents truncation from cutting critical forms.
    """
    impr = sorted(set(f["word_form"] for f in forms if "impr" in f["tags"]))
    pres = sorted(set(
        f["word_form"] for f in forms
        if "pres" in f["tags"] and "impr" not in f["tags"]))
    inf = sorted(set(f["word_form"] for f in forms if "inf" in f["tags"]))
    other = sorted(set(
        f["word_form"] for f in forms
        if "impr" not in f["tags"] and "pres" not in f["tags"]
        and "inf" not in f["tags"]))

    seen: set[str] = set()
    ordered: list[str] = []
    for form in impr + pres + inf + other:
        if form not in seen:
            seen.add(form)
            ordered.append(form)
    return ordered[:max_forms]


def _format_sandbox(
    track: str,
    module_num: int,
    constraints: GrammarConstraint,
    sections: dict[str, list[dict]],
    examples: list[dict],
    candidates: list[str],
    vesum_results: dict,
) -> str:
    """Format the Lexical Sandbox as markdown."""
    lines = []
    lines.append(f"## Lexical Sandbox for M{module_num}")
    lines.append("")

    # Constraint summary
    forbidden = _describe_constraints(constraints)
    if forbidden:
        lines.append(f"**FORBIDDEN at M{module_num}:** {', '.join(forbidden)}")
        lines.append("")

    # Not found words
    not_found = [w for w in candidates if not vesum_results.get(w.lower())]
    if not_found:
        lines.append(f"**NOT IN VESUM (do not use):** {', '.join(not_found)}")
        lines.append("")

    # Nouns
    if sections["nouns"]:
        lines.append("### Nouns")
        lines.append("")
        lines.append("| Lemma | Gender | Allowed Forms |")
        lines.append("|-------|--------|---------------|")
        for entry in sections["nouns"]:
            gender = _extract_gender(entry["forms"][0]["tags"]) if entry["forms"] else "?"
            gender_label = _GENDER_LABELS.get(gender, gender or "?")
            forms = sorted(set(f["word_form"] for f in entry["forms"]))
            forms_str = ", ".join(forms[:8])
            lines.append(f"| {entry['lemma']} | {gender_label} | {forms_str} |")
        lines.append("")

    # Adjectives
    if sections["adjectives"]:
        lines.append("### Adjectives")
        lines.append("")
        if constraints.nominative_only:
            lines.append("| Lemma | Masculine | Feminine | Neuter | Plural |")
            lines.append("|-------|-----------|----------|--------|--------|")
            for entry in sections["adjectives"]:
                forms_by_gender = {"m": "—", "f": "—", "n": "—", "p": "—"}
                for f in entry["forms"]:
                    g = _extract_gender(f["tags"])
                    case = _extract_case(f["tags"])
                    if g and case in ("v_naz", None):
                        forms_by_gender[g] = f["word_form"]
                lines.append(
                    f"| {entry['lemma']} | {forms_by_gender['m']} | "
                    f"{forms_by_gender['f']} | {forms_by_gender['n']} | "
                    f"{forms_by_gender['p']} |"
                )
        else:
            lines.append("| Lemma | Allowed Forms |")
            lines.append("|-------|---------------|")
            for entry in sections["adjectives"]:
                forms = sorted(set(f["word_form"] for f in entry["forms"]))
                lines.append(f"| {entry['lemma']} | {', '.join(forms[:12])} |")
        lines.append("")

    # Verbs
    if sections["verbs"]:
        lines.append("### Verbs")
        lines.append("")
        lines.append("| Lemma | Aspect | Allowed Forms |")
        lines.append("|-------|--------|---------------|")
        for entry in sections["verbs"]:
            aspect = "imperf" if "imperf" in entry["forms"][0]["tags"] else "perf"
            ordered = _prioritize_verb_forms(entry["forms"])
            lines.append(f"| {entry['lemma']} | {aspect} | {', '.join(ordered[:15])} |")
        lines.append("")

    # Other POS
    if sections["other"]:
        lines.append("### Other Words")
        lines.append("")
        for entry in sections["other"]:
            pos_label = _POS_LABELS.get(entry["pos"], entry["pos"])
            lines.append(f"- **{entry['lemma']}** ({pos_label})")
        lines.append("")

    # Textbook examples
    if examples:
        lines.append("### Verified Example Sentences (from textbooks)")
        lines.append("")
        for ex in examples:
            lines.append(f"- {ex['text']}")
            lines.append(f"  *Source: {ex['source']}*")
        lines.append("")

    # Level-wide grammar warnings (beyond module-specific morphological constraints)
    # The sandbox shows all VESUM forms allowed by module constraints, but the
    # audit also enforces broader level-wide grammar rules from GRAMMAR_CONSTRAINTS.
    base_track = track.split("-")[0] if "-" in track else track
    if base_track == "a1":
        lines.append("### ⚠️ Level-Wide Grammar Rules (A1)")
        lines.append("")
        lines.append("Even though forms are listed above, the A1 audit enforces these rules on your **prose**:")
        lines.append("- **DATIVE CASE FORBIDDEN**: Do NOT use мені, тобі, йому, їй, нам, вам, їм or -ові/-еві dative noun endings in your text")
        lines.append("- **INSTRUMENTAL CASE FORBIDDEN**: Do NOT use з + instrumental (мною, тобою, ним, нею) or за/під/над + instrumental")
        lines.append("- **Max 10 words per Ukrainian sentence**, max 1 clause")
        lines.append("- **No subordinate clauses** (який, що, коли, бо, щоб as conjunctions)")
        lines.append("")

    # Instructions for LLM
    lines.append("### Usage Rules")
    lines.append("")
    lines.append("- **MANDATORY**: Every Ukrainian word in your output MUST appear in the tables above")
    lines.append("- You may use any allowed form listed for each lemma")
    lines.append("- You may use the verified example sentences directly or as templates")
    lines.append("- Do NOT invent Ukrainian words outside this sandbox — use English instead")
    lines.append("- English text is unrestricted — use freely for explanations")
    lines.append("- Memorized chunks (до побачення, як справи, etc.) are always allowed")
    lines.append("- Common function words (це, так, ні, він, вона, воно, вони, я, ти, ми, ви) are always allowed")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pass 1 resource request parser
# ---------------------------------------------------------------------------

def parse_resource_request(raw_output: str) -> dict | None:
    """Parse Gemini's Pass 1 JSON resource request.

    Looks for JSON between ===RESOURCE_REQUEST_START=== and ===RESOURCE_REQUEST_END===
    delimiters, or tries to parse the entire output as JSON.
    """
    # Try delimited extraction first
    start_marker = "===RESOURCE_REQUEST_START==="
    end_marker = "===RESOURCE_REQUEST_END==="
    if start_marker in raw_output and end_marker in raw_output:
        start = raw_output.index(start_marker) + len(start_marker)
        end = raw_output.index(end_marker)
        json_str = raw_output[start:end].strip()
    else:
        # Try to find JSON block in output
        json_match = re.search(r'```json\s*(.*?)\s*```', raw_output, re.DOTALL)
        json_str = json_match.group(1) if json_match else raw_output.strip()

    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse resource request JSON: %s", e)
        return None


def extract_words_from_request(request: dict) -> list[str]:
    """Extract all unique words from a parsed resource request."""
    words = []
    vocab = request.get("requested_vocabulary", {})
    if isinstance(vocab, dict):
        for _category, word_list in vocab.items():
            if isinstance(word_list, list):
                words.extend(word_list)
    elif isinstance(vocab, list):
        words.extend(vocab)

    phrases = request.get("requested_phrases", [])
    for phrase in phrases:
        if isinstance(phrase, str):
            # Extract Ukrainian words from phrases
            ukr_words = re.findall(r'[А-ЯҐЄІЇа-яґєіїʼ\'\u0301]+', phrase)
            words.extend(ukr_words)

    return list(dict.fromkeys(w.strip() for w in words if w.strip()))


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import yaml

    if len(sys.argv) < 3:
        print("Usage: lexical_sandbox.py <track> <module_num> [plan.yaml]")
        sys.exit(1)

    track = sys.argv[1]
    module_num = int(sys.argv[2])

    if len(sys.argv) > 3:
        plan_path = Path(sys.argv[3])
        with open(plan_path) as f:
            plan = yaml.safe_load(f)
    else:
        # Try to load from curriculum
        from batch_gemini_config import get_module_index
        idx = get_module_index(track)
        slug = idx["num_to_slug"].get(module_num, "")
        base = track.split("-")[0]
        plan_path = Path(f"curriculum/l2-uk-en/plans/{base}/{slug}.yaml")
        if plan_path.exists():
            with open(plan_path) as f:
                plan = yaml.safe_load(f)
        else:
            plan = {"vocabulary_hints": []}

    sandbox = build_sandbox(track, module_num, plan)
    print(sandbox)
