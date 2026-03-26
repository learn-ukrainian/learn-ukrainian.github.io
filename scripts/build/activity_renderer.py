"""Activity YAML → React JSX transformer.

Converts structured activity YAML (intermediate format from activity-v2.schema)
into React component JSX strings for MDX rendering.

Each activity type maps to a specific React component in starlight/src/components/.
The YAML uses an intermediate format — this module transforms it to match the
exact React component prop interfaces.

Issue: #1043
"""

from __future__ import annotations

import json
from typing import Any


def render_activity_to_jsx(activity: dict) -> str:
    """Convert an activity YAML dict to React component JSX string.

    Args:
        activity: Parsed YAML dict matching activity-v2.schema.json

    Returns:
        JSX string ready for insertion into MDX content.
        On unknown type, returns an HTML comment with the type name.
    """
    activity_type = activity.get("type", "")
    renderer = _RENDERERS.get(activity_type)
    if not renderer:
        return f"<!-- Unknown activity type: {activity_type} -->"
    return renderer(activity)


def get_required_imports(activities: list[dict]) -> list[str]:
    """Return deduplicated import statements for the activity types used.

    Args:
        activities: List of activity dicts (inline + workbook combined)

    Returns:
        List of import statement strings, sorted alphabetically.
    """
    seen: set[str] = set()
    imports: list[str] = []

    for act in activities:
        activity_type = act.get("type", "")
        component = _TYPE_TO_COMPONENT.get(activity_type)
        if component and component not in seen:
            seen.add(component)
            imports.append(
                f"import {component} from '@site/src/components/{component}';"
            )

    return sorted(imports)


# ---------------------------------------------------------------------------
# Type → Component name mapping
# ---------------------------------------------------------------------------

_TYPE_TO_COMPONENT: dict[str, str] = {
    "quiz": "Quiz",
    "fill-in": "FillIn",
    "match-up": "MatchUp",
    "group-sort": "GroupSort",
    "true-false": "TrueFalse",
    "error-correction": "ErrorCorrection",
    "anagram": "Anagram",
    "translate": "Translate",
    "unjumble": "Unjumble",
    "cloze": "Cloze",
    "select": "Select",
    "grammar-identify": "GrammarIdentify",
    "observe": "Observe",
    "classify": "Classify",
    "mark-the-words": "MarkTheWords",
    "highlight-morphemes": "HighlightMorphemes",
    "image-to-letter": "ImageToLetter",
    "letter-grid": "LetterGrid",
    "watch-and-repeat": "WatchAndRepeat",
    "odd-one-out": "OddOneOut",
    "divide-words": "DivideWords",
    "count-syllables": "CountSyllables",
    "pick-syllables": "PickSyllables",
    "phrase-table": "PhraseTable",
    "critical-analysis": "CriticalAnalysis",
    "essay-response": "EssayResponse",
    "source-evaluation": "SourceEvaluation",
    "reading": "ReadingActivity",
    "comparative-study": "ComparativeStudy",
    "authorial-intent": "AuthorialIntent",
    "debate": "Debate",
    "etymology-trace": "EtymologyTrace",
    "translation-critique": "TranslationCritique",
    "transcription": "Transcription",
    "paleography-analysis": "PaleographyAnalysis",
    "dialect-comparison": "DialectComparison",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _j(value: Any) -> str:
    """JSON-encode a value for JSX embedding."""
    return json.dumps(value, ensure_ascii=False)


def _prop(name: str, value: Any) -> str:
    """Build a JSX prop string. Strings become {\"...\"}, others become {json}."""
    if isinstance(value, str):
        return f' {name}={{{_j(value)}}}'
    return f' {name}={{{_j(value)}}}'


def _opt_prop(name: str, value: Any | None, default: Any = None) -> str:
    """Build optional prop — returns empty string if value is None/default."""
    if value is None or value == default:
        return ""
    return _prop(name, value)


def _component(name: str, props: str) -> str:
    """Build a self-closing JSX component with client:only directive."""
    return f'<{name} client:only="react"{props} />'


# ---------------------------------------------------------------------------
# Core activity renderers
# ---------------------------------------------------------------------------

def _render_quiz(act: dict) -> str:
    """quiz → <Quiz questions={[...]} instruction="..." />

    YAML items have {question, options[], correct(index)} format.
    React expects {question, options[{text, correct}]} format.
    """
    questions = []
    for item in act.get("items", []):
        correct_idx = item.get("correct", 0)
        options = [
            {"text": opt, "correct": i == correct_idx}
            for i, opt in enumerate(item.get("options", []))
        ]
        q: dict[str, Any] = {"question": item.get("question", ""), "options": options}
        questions.append(q)

    props = _prop("questions", questions)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Quiz", props)


def _render_fill_in(act: dict) -> str:
    """fill-in → <FillIn items={[...]} instruction="..." />

    YAML: {sentence, answer, options?}
    React: same structure.
    """
    items = []
    for item in act.get("items", []):
        entry: dict[str, Any] = {
            "sentence": item.get("sentence", ""),
            "answer": item.get("answer", ""),
        }
        if item.get("options"):
            entry["options"] = item["options"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("FillIn", props)


def _render_match_up(act: dict) -> str:
    """match-up → <MatchUp pairs={[...]} instruction="..." />"""
    pairs = [
        {"left": p.get("left", ""), "right": p.get("right", "")}
        for p in act.get("pairs", [])
    ]
    props = _prop("pairs", pairs)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("MatchUp", props)


def _render_group_sort(act: dict) -> str:
    """group-sort → <GroupSort groups={{...}} instruction="..." />

    YAML: groups[{label, items[]}]
    React: groups is {label: items[]} dict.
    """
    groups = {}
    for g in act.get("groups", []):
        groups[g.get("label", "")] = g.get("items", [])

    props = _prop("groups", groups)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("GroupSort", props)


def _render_true_false(act: dict) -> str:
    """true-false → <TrueFalse items={[...]} instruction="..." />

    YAML: {statement, correct(bool), explanation?}
    React: {statement, isTrue, explanation?}
    """
    items = []
    for item in act.get("items", []):
        entry: dict[str, Any] = {
            "statement": item.get("statement", ""),
            "isTrue": bool(item.get("correct", False)),
        }
        if item.get("explanation"):
            entry["explanation"] = item["explanation"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("TrueFalse", props)


def _render_error_correction(act: dict) -> str:
    """error-correction → <ErrorCorrection> children (renders per-item).

    React ErrorCorrection uses children, but the wrapper also accepts structured
    items. We render as individual ErrorCorrectionItems with all props.
    Actually, looking at the component, it uses children. We'll render as
    a wrapper with JSON data prop for the items.
    """
    # ErrorCorrection takes children — we pass items as JSON for the generator
    items = []
    for item in act.get("items", []):
        entry = {
            "sentence": item.get("sentence", ""),
            "errorWord": item.get("error", ""),
            "correctForm": item.get("correction", ""),
            "options": item.get("options", []),
            "explanation": item.get("explanation", ""),
        }
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("ErrorCorrection", props)


def _render_anagram(act: dict) -> str:
    """anagram → <Anagram items={[...]} instruction="..." />

    YAML: {letters[], answer, hint?}
    React AnagramItem: {scrambled(string, space-separated), answer, hint?}
    """
    items = []
    for item in act.get("items", []):
        letters = item.get("letters", [])
        entry: dict[str, Any] = {
            "scrambled": " ".join(letters),
            "answer": item.get("answer", ""),
        }
        if item.get("hint"):
            entry["hint"] = item["hint"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Anagram", props)


def _render_translate(act: dict) -> str:
    """translate → <Translate questions={[...]} instruction="..." />

    YAML: items[{source, answer?, alternatives?, options[{text, correct}]?}]
    React GeneratorTranslateQuestion: {source, options[{text, correct}]}
    """
    questions = []
    for item in act.get("items", []):
        options = item.get("options", [])
        if not options and item.get("answer"):
            # Build options from answer + alternatives
            correct = item["answer"]
            alts = item.get("alternatives", [])
            options = [{"text": correct, "correct": True}]
            for alt in alts:
                options.append({"text": alt, "correct": False})
        q: dict[str, Any] = {
            "source": item.get("source", ""),
            "options": options,
        }
        if item.get("explanation"):
            q["explanation"] = item["explanation"]
        questions.append(q)

    props = _prop("questions", questions)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Translate", props)


def _render_unjumble(act: dict) -> str:
    """unjumble → <Unjumble items={[...]} instruction="..." />

    YAML: {words[], correct_order[], hint?}
    React UnjumbleItem: {words(string, slash-separated), answer(string), hint?}
    """
    items = []
    for item in act.get("items", []):
        words = item.get("words", [])
        correct = item.get("correct_order", [])
        entry: dict[str, Any] = {
            "words": " / ".join(words),
            "answer": " ".join(correct),
        }
        if item.get("hint"):
            entry["hint"] = item["hint"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Unjumble", props)


def _render_cloze(act: dict) -> str:
    """cloze → <Cloze passage="..." blanks={[...]} instruction="..." />

    YAML: {text, blanks[{id, answer, options[]}]?, options[]?}
    React: {passage, blanks[{index, options[], answer}]}
    """
    text = act.get("text", "")
    blanks = []
    for b in act.get("blanks", []):
        blanks.append({
            "index": b.get("id", 0),
            "options": b.get("options", []),
            "answer": b.get("answer", ""),
        })

    props = _prop("passage", text)
    if blanks:
        props += _prop("blanks", blanks)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Cloze", props)


def _render_select(act: dict) -> str:
    """select → <Select questions={[...]} instruction="..." />

    YAML: items[{question, options[{text, correct}]}]
    React GeneratorSelectQuestion: {question, options[{text, correct}]}
    """
    questions = []
    for item in act.get("items", []):
        q: dict[str, Any] = {
            "question": item.get("question", ""),
            "options": item.get("options", []),
        }
        if item.get("explanation"):
            q["explanation"] = item["explanation"]
        questions.append(q)

    props = _prop("questions", questions)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Select", props)


def _render_grammar_identify(act: dict) -> str:
    """grammar-identify → <GrammarIdentify title="..." items={[...]} />

    YAML: {word, task, options[]?, answer?}
    React GrammarItem: {text, form, answer}
    """
    items = []
    for item in act.get("items", []):
        items.append({
            "text": item.get("word", ""),
            "form": item.get("task", ""),
            "answer": item.get("answer", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("items", items)
    return _component("GrammarIdentify", props)


def _render_observe(act: dict) -> str:
    """observe → <Observe> children

    React Observe wraps children. We use the ObserveActivity sub-component
    which takes examples[] and prompt directly.
    """
    examples = act.get("examples", [])
    prompt = act.get("prompt", "")

    # ObserveActivity is a named export, but the default export (Observe)
    # wraps children. We'll render with examples/prompt as data props.
    props = _prop("examples", examples)
    props += _opt_prop("prompt", prompt)
    return _component("Observe", props)


def _render_classify(act: dict) -> str:
    """classify → <Classify categories={[...]} instruction="..." />

    YAML: {categories[{label, symbol_hint?, items[]}]}
    React ClassifyCategory: {label, symbolHint?, items[]}
    """
    categories = []
    for cat in act.get("categories", []):
        entry: dict[str, Any] = {
            "label": cat.get("label", ""),
            "items": cat.get("items", []),
        }
        if cat.get("symbol_hint"):
            entry["symbolHint"] = cat["symbol_hint"]
        categories.append(entry)

    props = _prop("categories", categories)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("Classify", props)


def _render_mark_the_words(act: dict) -> str:
    """mark-the-words → <MarkTheWords> children

    React MarkTheWords expects children. We pass data as props.
    """
    props = _prop("text", act.get("text", ""))
    props += _prop("targetWords", act.get("target_words", []))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _opt_prop("criteria", act.get("criteria"))
    return _component("MarkTheWords", props)


def _render_highlight_morphemes(act: dict) -> str:
    """highlight-morphemes → <HighlightMorphemes> children

    React expects children. We pass items as data props.
    """
    items = []
    for item in act.get("items", []):
        morphemes = [
            {"text": m.get("text", ""), "type": m.get("type", "")}
            for m in item.get("morphemes", [])
        ]
        items.append({
            "word": item.get("word", ""),
            "morphemes": morphemes,
        })

    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("HighlightMorphemes", props)


def _render_image_to_letter(act: dict) -> str:
    """image-to-letter → <ImageToLetter items={[...]} />

    YAML: {image, letter, options?}
    React ImageToLetterItem: {emoji, answer, distractors[]}
    """
    items = []
    for item in act.get("items", []):
        entry: dict[str, Any] = {
            "emoji": item.get("image", ""),
            "answer": item.get("letter", ""),
            "distractors": item.get("options", []),
        }
        if item.get("note"):
            entry["note"] = item["note"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("title", act.get("instruction"))
    return _component("ImageToLetter", props)


def _render_letter_grid(act: dict) -> str:
    """letter-grid → <LetterGrid letters={[...]} />

    YAML and React use same field names: {upper, lower, name?, emoji?, key_word?}
    """
    letters = []
    for entry in act.get("letters", []):
        item: dict[str, Any] = {
            "upper": entry.get("upper", ""),
            "lower": entry.get("lower", ""),
        }
        for field in ("emoji", "key_word", "note", "sound_type"):
            if entry.get(field):
                item[field] = entry[field]
        letters.append(item)

    props = _prop("letters", letters)
    props += _opt_prop("title", act.get("instruction"))
    return _component("LetterGrid", props)


def _render_watch_and_repeat(act: dict) -> str:
    """watch-and-repeat → <WatchAndRepeat items={[...]} />

    YAML: items[{video, letter?, word?, note?}]
    React WatchAndRepeatItem: {video, letter?, word?, note?}
    """
    items = []
    for item in act.get("items", []):
        entry = {"video": item.get("video", "")}
        if item.get("letter"):
            entry["letter"] = item["letter"]
        if item.get("word"):
            entry["word"] = item["word"]
        if item.get("note"):
            entry["note"] = item["note"]
        items.append(entry)

    props = _prop("items", items)
    props += _opt_prop("title", act.get("instruction"))
    return _component("WatchAndRepeat", props)


def _render_odd_one_out(act: dict) -> str:
    """odd-one-out → <OddOneOut items={[...]} />"""
    items = []
    for item in act.get("items", []):
        entry = {
            "words": item.get("words", []),
            "correct": item.get("correct", 0),
            "explanation": item.get("explanation", ""),
        }
        items.append(entry)
    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("OddOneOut", props)


def _render_divide_words(act: dict) -> str:
    """divide-words → <DivideWords items={[...]} />"""
    items = []
    for item in act.get("items", []):
        entry = {"word": item.get("word", ""), "answer": item.get("answer", "")}
        if item.get("hint"):
            entry["hint"] = item["hint"]
        items.append(entry)
    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    return _component("DivideWords", props)


def _render_count_syllables(act: dict) -> str:
    """count-syllables → <CountSyllables items={[...]} />"""
    items = []
    for item in act.get("items", []):
        entry = {"word": item.get("word", ""), "correct": item.get("correct", 1)}
        if item.get("translation"):
            entry["translation"] = item["translation"]
        items.append(entry)
    props = _prop("items", items)
    props += _opt_prop("instruction", act.get("instruction"))
    if act.get("maxCount"):
        props += f' maxCount={{{act["maxCount"]}}}'
    return _component("CountSyllables", props)


def _render_pick_syllables(act: dict) -> str:
    """pick-syllables → <PickSyllables syllables={[...]} correctIndices={[...]} />"""
    props = _prop("syllables", act.get("syllables", []))
    props += _prop("correctIndices", act.get("correctIndices", []))
    props += f' category="{act.get("category", "закриті")}"'
    props += _opt_prop("instruction", act.get("instruction"))
    props += _opt_prop("explanation", act.get("explanation"))
    return _component("PickSyllables", props)


def _render_phrase_table(act: dict) -> str:
    """phrase-table → <PhraseTable groups={[...]} />

    YAML: groups[{label, phrases[str|{phrase, context?, emoji?}]}]
    React PhraseGroup: {function(=label), phrases[{phrase, context?, emoji?}]}
    """
    groups = []
    for g in act.get("groups", []):
        phrases = []
        for p in g.get("phrases", []):
            if isinstance(p, str):
                phrases.append({"phrase": p})
            else:
                phrases.append({
                    "phrase": p.get("phrase", ""),
                    "context": p.get("context"),
                    "emoji": p.get("emoji"),
                })
        groups.append({
            "function": g.get("label", ""),
            "phrases": phrases,
        })

    props = _prop("groups", groups)
    props += _opt_prop("title", act.get("instruction"))
    return _component("PhraseTable", props)


# ---------------------------------------------------------------------------
# Seminar activity renderers
# ---------------------------------------------------------------------------

def _render_critical_analysis(act: dict) -> str:
    """critical-analysis → <CriticalAnalysis title="..." ... />"""
    props = _prop("title", act.get("instruction", act.get("prompt", "")))
    props += _opt_prop("targetText", act.get("target_text"))
    props += _opt_prop("questions", act.get("questions"))
    props += _opt_prop("modelAnswers", act.get("model_answers"))
    return _component("CriticalAnalysis", props)


def _render_essay_response(act: dict) -> str:
    """essay-response → <EssayResponse title="..." prompt="..." ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("prompt", act.get("prompt", ""))
    props += _opt_prop("modelAnswer", act.get("model_answer"))

    # Convert rubric list to string if present
    rubric = act.get("rubric") or act.get("evaluation_criteria")
    if rubric and isinstance(rubric, list):
        if rubric and isinstance(rubric[0], dict):
            # Rubric with criteria/description/points
            rubric_lines = []
            for r in rubric:
                rubric_lines.append(
                    f"- {r.get('criteria', '')}: {r.get('description', '')}"
                )
            props += _prop("rubric", "\n".join(rubric_lines))
        else:
            props += _prop("rubric", "\n".join(f"- {c}" for c in rubric))

    return _component("EssayResponse", props)


def _render_source_evaluation(act: dict) -> str:
    """source-evaluation → <SourceEvaluation ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("sourceText", act.get("source_text", ""))

    metadata = act.get("source_metadata")
    if metadata:
        props += _prop("sourceMetadata", metadata)

    props += _opt_prop("evaluationCriteria", act.get("criteria"))
    props += _opt_prop("guidingQuestions", act.get("guiding_questions"))
    props += _opt_prop("modelEvaluation", act.get("model_evaluation"))
    return _component("SourceEvaluation", props)


def _render_reading(act: dict) -> str:
    """reading → <ReadingActivity title="..." tasks={[...]} ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _opt_prop("text", act.get("passage"))
    props += _opt_prop("source", act.get("source"))
    props += _prop("tasks", act.get("questions", []))
    return _component("ReadingActivity", props)


def _render_comparative_study(act: dict) -> str:
    """comparative-study → <ComparativeStudy ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _opt_prop("itemsToCompare", act.get("items_to_compare"))
    props += _opt_prop("criteria", act.get("criteria"))
    props += _opt_prop("prompt", act.get("prompt"))
    props += _opt_prop("modelAnswer", act.get("model_answer"))
    return _component("ComparativeStudy", props)


def _render_authorial_intent(act: dict) -> str:
    """authorial-intent → <AuthorialIntent ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("excerpt", act.get("excerpt", ""))
    props += _prop("questions", act.get("questions", []))
    props += _prop("modelAnswer", act.get("model_answer", ""))
    return _component("AuthorialIntent", props)


def _render_debate(act: dict) -> str:
    """debate → <Debate ... />

    YAML positions: [{label, arguments[]}]
    React Position: [{name, proponents, argument, evidence?, weaknesses?}]
    """
    positions = []
    for p in act.get("positions", []):
        args = p.get("arguments", [])
        positions.append({
            "name": p.get("label", ""),
            "proponents": "",
            "argument": "\n".join(args) if args else "",
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("debateQuestion", act.get("debate_question", ""))
    props += _prop("positions", positions)
    props += _opt_prop("analysisTasks", act.get("analysis_tasks"))
    return _component("Debate", props)


def _render_etymology_trace(act: dict) -> str:
    """etymology-trace → <EtymologyTrace ... />

    YAML stages: [{period, form, notes?}]
    React EtymologyItem: [{word, modern, evolution}]
    """
    items = []
    for stage in act.get("stages", []):
        items.append({
            "word": stage.get("period", ""),
            "modern": stage.get("form", ""),
            "evolution": stage.get("notes", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("items", items)
    return _component("EtymologyTrace", props)


def _render_translation_critique(act: dict) -> str:
    """translation-critique → <TranslationCritique ... />

    YAML translations: [{text, quality?, translator?, accuracy_score?, notes?}]
    React Translation: [{translator, text, accuracyScore, notes}]
    """
    translations = []
    for t in act.get("translations", []):
        translations.append({
            "translator": t.get("translator", ""),
            "text": t.get("text", ""),
            "accuracyScore": t.get("accuracy_score", 0),
            "notes": t.get("notes", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("original", act.get("original", ""))
    props += _prop("translations", translations)
    props += _opt_prop("focusPoints", act.get("focus_points"))
    return _component("TranslationCritique", props)


def _render_transcription(act: dict) -> str:
    """transcription → <Transcription ... />"""
    props = _prop("title", act.get("instruction", ""))
    props += _prop("original", act.get("original", ""))
    props += _prop("answer", act.get("answer", ""))
    props += _opt_prop("hints", act.get("hints"))
    return _component("Transcription", props)


def _render_paleography_analysis(act: dict) -> str:
    """paleography-analysis → <PaleographyAnalysis ... />

    YAML hotspots: [{x, y, label, explanation?}]
    React Hotspot: [{x, y, label, explanation}]
    """
    hotspots = []
    for h in act.get("hotspots", []):
        hotspots.append({
            "x": h.get("x", 0),
            "y": h.get("y", 0),
            "label": h.get("label", ""),
            "explanation": h.get("explanation", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _prop("imageUrl", act.get("image_url", ""))
    props += _prop("hotspots", hotspots)
    return _component("PaleographyAnalysis", props)


def _render_dialect_comparison(act: dict) -> str:
    """dialect-comparison → <DialectComparison ... />

    YAML features: [{feature, variant_a, variant_b, explanation?}]
    React Feature: [{featureName, valueA, valueB, explanation}]
    """
    features = []
    for f in act.get("features", []):
        features.append({
            "featureName": f.get("feature", ""),
            "valueA": f.get("variant_a", ""),
            "valueB": f.get("variant_b", ""),
            "explanation": f.get("explanation", ""),
        })

    props = _prop("title", act.get("instruction", ""))
    props += _opt_prop("instruction", act.get("instruction"))
    props += _prop("textA", act.get("text_a", ""))
    props += _prop("textB", act.get("text_b", ""))
    props += _opt_prop("labelA", act.get("label_a"))
    props += _opt_prop("labelB", act.get("label_b"))
    props += _prop("features", features)
    return _component("DialectComparison", props)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_RENDERERS: dict[str, Any] = {
    # Core types
    "quiz": _render_quiz,
    "fill-in": _render_fill_in,
    "match-up": _render_match_up,
    "group-sort": _render_group_sort,
    "true-false": _render_true_false,
    "error-correction": _render_error_correction,
    "anagram": _render_anagram,
    "translate": _render_translate,
    "unjumble": _render_unjumble,
    "cloze": _render_cloze,
    "select": _render_select,
    "grammar-identify": _render_grammar_identify,
    "observe": _render_observe,
    "classify": _render_classify,
    "mark-the-words": _render_mark_the_words,
    "highlight-morphemes": _render_highlight_morphemes,
    "image-to-letter": _render_image_to_letter,
    "letter-grid": _render_letter_grid,
    "watch-and-repeat": _render_watch_and_repeat,
    "odd-one-out": _render_odd_one_out,
    "divide-words": _render_divide_words,
    "count-syllables": _render_count_syllables,
    "pick-syllables": _render_pick_syllables,
    "phrase-table": _render_phrase_table,
    # Seminar types
    "critical-analysis": _render_critical_analysis,
    "essay-response": _render_essay_response,
    "source-evaluation": _render_source_evaluation,
    "reading": _render_reading,
    "comparative-study": _render_comparative_study,
    "authorial-intent": _render_authorial_intent,
    "debate": _render_debate,
    "etymology-trace": _render_etymology_trace,
    "translation-critique": _render_translation_critique,
    "transcription": _render_transcription,
    "paleography-analysis": _render_paleography_analysis,
    "dialect-comparison": _render_dialect_comparison,
}
