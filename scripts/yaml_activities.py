#!/usr/bin/env python3
"""
Shared YAML Activity Parser

Single source of truth for parsing YAML activity files.
Used by both the MDX generator and the YAML validator.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

import yaml

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QuizOption:
    text: str
    correct: bool


@dataclass
class QuizItem:
    question: str
    options: list[QuizOption]
    explanation: str | None = None


@dataclass
class QuizActivity:
    type: str = "quiz"
    title: str = ""
    items: list[QuizItem] = field(default_factory=list)


@dataclass
class SelectItem:
    question: str
    options: list[QuizOption]
    min_correct: int | None = None
    explanation: str | None = None


@dataclass
class SelectActivity:
    type: str = "select"
    title: str = ""
    items: list[SelectItem] = field(default_factory=list)


@dataclass
class TrueFalseItem:
    statement: str
    correct: bool
    explanation: str | None = None


@dataclass
class TrueFalseActivity:
    type: str = "true-false"
    title: str = ""
    items: list[TrueFalseItem] = field(default_factory=list)


@dataclass
class FillInItem:
    sentence: str
    answer: str
    options: list[str]
    explanation: str | None = None


@dataclass
class FillInActivity:
    type: str = "fill-in"
    title: str = ""
    items: list[FillInItem] = field(default_factory=list)


@dataclass
class ClozeBlank:
    id: int
    answer: str
    options: list[str]


@dataclass
class ClozeActivity:
    type: str = "cloze"
    title: str = ""
    passage: str = ""
    blanks: list[ClozeBlank] = field(default_factory=list)


@dataclass
class MatchPair:
    left: str
    right: str


@dataclass
class MatchUpActivity:
    type: str = "match-up"
    title: str = ""
    pairs: list[MatchPair] = field(default_factory=list)


@dataclass
class GroupSortGroup:
    name: str
    items: list[str]


@dataclass
class GroupSortActivity:
    type: str = "group-sort"
    title: str = ""
    groups: list[GroupSortGroup] = field(default_factory=list)


@dataclass
class UnjumbleItem:
    words: list[str]
    answer: str


@dataclass
class UnjumbleActivity:
    type: str = "unjumble"
    title: str = ""
    items: list[UnjumbleItem] = field(default_factory=list)


@dataclass
class ErrorCorrectionItem:
    sentence: str
    error: str
    answer: str
    options: list[str]
    explanation: str


@dataclass
class ErrorCorrectionActivity:
    type: str = "error-correction"
    title: str = ""
    items: list[ErrorCorrectionItem] = field(default_factory=list)


@dataclass
class MarkTheWordsActivity:
    type: str = "mark-the-words"
    title: str = ""
    instruction: str = ""
    text: str = ""
    answers: list[str] = field(default_factory=list)


@dataclass
class TranslateOption:
    text: str
    correct: bool


@dataclass
class TranslateItem:
    source: str
    options: list[TranslateOption]
    explanation: str | None = None


@dataclass
class TranslateActivity:
    type: str = "translate"
    title: str = ""
    items: list[TranslateItem] = field(default_factory=list)


@dataclass
class AnagramItem:
    scrambled: str
    answer: str
    hint: str | None = None


@dataclass
class AnagramActivity:
    type: str = "anagram"
    title: str = ""
    items: list[AnagramItem] = field(default_factory=list)


@dataclass
class EtymologyItem:
    word: str
    modern: str
    evolution: str


@dataclass
class EtymologyTraceActivity:
    type: str = "etymology-trace"
    title: str = ""
    instruction: str = ""
    items: list[EtymologyItem] = field(default_factory=list)


@dataclass
class GrammarIdentifyItem:
    text: str
    form: str
    answer: str


@dataclass
class GrammarIdentifyActivity:
    type: str = "grammar-identify"
    title: str = ""
    instruction: str = ""
    items: list[GrammarIdentifyItem] = field(default_factory=list)


@dataclass
class TranscriptionActivity:
    """OES/RUTH: Transcribe archaic script into modern Cyrillic."""
    type: str = "transcription"
    title: str = ""
    instruction: str = ""  # Context about the script (e.g., Glagolitic, Ustav)
    original: str = ""     # Archaic text (or image URL)
    answer: str = ""       # Modern Cyrillic equivalent
    hints: list[str] = field(default_factory=list)  # Optional hints


@dataclass
class PaleographyHotspot:
    x: float  # X coordinate (percentage 0-100)
    y: float  # Y coordinate (percentage 0-100)
    label: str  # Feature name
    explanation: str  # Why this feature matters


@dataclass
class PaleographyAnalysisActivity:
    """OES/RUTH: Identify visual features of manuscripts via hotspots."""
    type: str = "paleography-analysis"
    title: str = ""
    instruction: str = ""
    image_url: str = ""  # URL to manuscript image
    hotspots: list[PaleographyHotspot] = field(default_factory=list)
    options: list[str] = field(default_factory=list)  # Possible feature terms


@dataclass
class DialectFeature:
    feature_name: str
    value_a: str
    value_b: str
    explanation: str


@dataclass
class DialectComparisonActivity:
    """OES/RUTH: Side-by-side comparison of regional dialect features."""
    type: str = "dialect-comparison"
    title: str = ""
    instruction: str = ""
    text_a: str = ""  # First dialect text (e.g., Kyiv)
    text_b: str = ""  # Second dialect text (e.g., Novgorod)
    label_a: str = ""  # Label for text A
    label_b: str = ""  # Label for text B
    features: list[DialectFeature] = field(default_factory=list)


@dataclass
class TranslationItem:
    translator: str
    text: str
    accuracy_score: int  # 1-10
    notes: str


@dataclass
class TranslationCritiqueActivity:
    """OES/RUTH: Evaluate and critique modern translations of archaic texts."""
    type: str = "translation-critique"
    title: str = ""
    instruction: str = ""
    original: str = ""  # Original OES/RUTH text
    translations: list[TranslationItem] = field(default_factory=list)
    focus_points: list[str] = field(default_factory=list)  # Key words often mistranslated


@dataclass
class ReadingActivity:
    type: str = "reading"
    title: str = ""
    id: str = ""  # REQUIRED: Unique identifier for linking (Issue #425)
    text: str = ""  # Primary source text for analysis (LIT)
    context: str = ""
    source: str = ""  # Attribution (e.g., 'Тарас Шевченко (1845)')
    resource: dict = field(default_factory=dict)  # Legacy: for external resources
    tasks: list[str] = field(default_factory=list)


@dataclass
class EssayResponseActivity:
    type: str = "essay-response"
    title: str = ""
    source_reading: str = ""  # Links to reading activity id (Issue #425)
    prompt: str = ""
    min_words: int = 0
    model_answer: str = ""
    rubric: list = field(default_factory=list)


@dataclass
class CriticalAnalysisActivity:
    type: str = "critical-analysis"
    title: str = ""
    source_reading: str = ""  # Links to reading activity id (Issue #425)
    target_text: str = ""  # Specific excerpt for analysis
    context: str = ""
    question: str = ""
    questions: list[str] = field(default_factory=list)  # Multiple questions
    model_answer: str = ""
    model_answers: list[str] = field(default_factory=list)  # Multiple answers


@dataclass
class ComparativeStudyActivity:
    type: str = "comparative-study"
    title: str = ""
    source_reading: str = ""  # Links to reading activity id (Issue #425)
    items_to_compare: list[str] = field(default_factory=list)
    criteria: list[str] = field(default_factory=list)
    source_a: str = ""  # Legacy
    source_b: str = ""  # Legacy
    task: str = ""
    prompt: str = ""
    model_answer: str = ""


@dataclass
class AuthorialIntentActivity:
    type: str = "authorial-intent"
    title: str = ""
    source_reading: str = ""  # Links to reading activity id (Issue #425)
    excerpt: str = ""
    questions: list[str] = field(default_factory=list)
    model_answer: str = ""


@dataclass
class SourceMetadata:
    """Metadata for a historical source."""
    author: str = ""
    date: str = ""
    type: str = ""  # chronicle, memoir, official, propaganda, academic
    context: str = ""


@dataclass
class SourceEvaluationActivity:
    """ISTORIO: Structured source criticism using the 5-question method."""
    type: str = "source-evaluation"
    title: str = ""
    instruction: str = ""
    source_text: str = ""
    source_metadata: SourceMetadata | None = None
    evaluation_criteria: list[str] = field(default_factory=list)  # authorship, date_and_context, etc.
    guiding_questions: list[str] = field(default_factory=list)
    model_evaluation: str = ""


@dataclass
class DebatePosition:
    """A single position in a historiographical debate."""
    name: str = ""
    proponents: str = ""
    argument: str = ""
    evidence: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)


@dataclass
class DebateActivity:
    """ISTORIO: Contested historiographical interpretations."""
    type: str = "debate"
    title: str = ""
    instruction: str = ""
    debate_question: str = ""
    historical_context: str = ""
    positions: list[DebatePosition] = field(default_factory=list)
    analysis_tasks: list[str] = field(default_factory=list)
    model_analysis: str = ""


# ---------------------------------------------------------------------------
# Pre-literacy activity types (A1 Cyrillic modules)
# ---------------------------------------------------------------------------

@dataclass
class ClassifyCategory:
    label: str
    items: list[str]


@dataclass
class ClassifyActivity:
    type: str = "classify"
    title: str = ""
    instruction: str = ""
    categories: list[ClassifyCategory] = field(default_factory=list)


@dataclass
class ImageToLetterItem:
    emoji: str
    answer: str
    distractors: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class ImageToLetterActivity:
    type: str = "image-to-letter"
    title: str = ""
    instruction: str = ""
    items: list[ImageToLetterItem] = field(default_factory=list)


@dataclass
class WatchAndRepeatItem:
    video: str
    letter: str = ""
    word: str = ""
    note: str = ""


@dataclass
class WatchAndRepeatActivity:
    type: str = "watch-and-repeat"
    title: str = ""
    instruction: str = ""
    items: list[WatchAndRepeatItem] = field(default_factory=list)


@dataclass
class ObserveActivity:
    type: str = "observe"
    title: str = ""
    instruction: str = ""
    examples: list[str] = field(default_factory=list)
    prompt: str = ""


@dataclass
class OrderActivity:
    type: str = "order"
    title: str = ""
    instruction: str = ""
    items: list[str] = field(default_factory=list)
    correct_order: list[int] = field(default_factory=list)


@dataclass
class CountSyllablesItem:
    word: str
    correct: int
    translation: str | None = None


@dataclass
class CountSyllablesActivity:
    type: str = "count-syllables"
    title: str = ""
    instruction: str = ""
    items: list[CountSyllablesItem] = field(default_factory=list)
    max_count: int | None = None


@dataclass
class DivideWordsItem:
    word: str
    answer: str
    hint: str | None = None


@dataclass
class DivideWordsActivity:
    type: str = "divide-words"
    title: str = ""
    instruction: str = ""
    items: list[DivideWordsItem] = field(default_factory=list)


@dataclass
class HighlightMorphemeItem:
    word: str
    morpheme: str
    type: str = "unknown"


@dataclass
class HighlightMorphemesActivity:
    type: str = "highlight-morphemes"
    title: str = ""
    instruction: str = ""
    text: str = ""
    morphemes: list[HighlightMorphemeItem] = field(default_factory=list)


@dataclass
class LetterGridActivity:
    type: str = "letter-grid"
    title: str = ""
    instruction: str = ""
    letters: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class OddOneOutItem:
    words: list[str]
    correct: int
    explanation: str


@dataclass
class OddOneOutActivity:
    type: str = "odd-one-out"
    title: str = ""
    instruction: str = ""
    items: list[OddOneOutItem] = field(default_factory=list)


@dataclass
class PickSyllablesActivity:
    type: str = "pick-syllables"
    title: str = ""
    instruction: str = ""
    syllables: list[str] = field(default_factory=list)
    correct_indices: list[int] = field(default_factory=list)
    category: str = ""
    explanation: str = ""


# Type alias
Activity = Union[  # noqa: UP007
    QuizActivity, SelectActivity, TrueFalseActivity, FillInActivity,
    ClozeActivity, MatchUpActivity, GroupSortActivity, UnjumbleActivity,
    ErrorCorrectionActivity, MarkTheWordsActivity,
    TranslateActivity, AnagramActivity, ReadingActivity,
    EssayResponseActivity, CriticalAnalysisActivity,
    ComparativeStudyActivity, AuthorialIntentActivity,
    SourceEvaluationActivity, DebateActivity,
    EtymologyTraceActivity, GrammarIdentifyActivity,
    ClassifyActivity, ImageToLetterActivity, WatchAndRepeatActivity,
    ObserveActivity, OrderActivity, CountSyllablesActivity,
    DivideWordsActivity, HighlightMorphemesActivity, LetterGridActivity,
    OddOneOutActivity, PickSyllablesActivity,
]


@dataclass
class ValidationError:
    path: str
    message: str
    activity_type: str | None = None
    activity_title: str | None = None
    severity: str = "error"


@dataclass
class ValidationResult:
    ok: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(self, path: str, message: str, **kwargs):
        self.errors.append(ValidationError(path=path, message=message, severity="error", **kwargs))
        self.ok = False

    def add_warning(self, path: str, message: str, **kwargs):
        self.warnings.append(ValidationError(path=path, message=message, severity="warning", **kwargs))


class ActivityParser:
    def __init__(self, schemas_dir: Path | None = None):
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent.parent / "schemas"
        self.schemas_dir = schemas_dir
        self._schema_cache: dict[str, dict] = {}

    def parse(self, yaml_path: str | Path) -> list[Activity]:
        yaml_path = Path(yaml_path)
        with open(yaml_path, encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
        if raw_data is None:
            return []
        # V2 format: dict with inline/workbook lists
        if isinstance(raw_data, dict) and ('inline' in raw_data or 'workbook' in raw_data):
            merged = []
            for section in ('inline', 'workbook'):
                section_data = raw_data.get(section, [])
                if isinstance(section_data, list):
                    merged.extend(section_data)
            raw_data = merged
        elif isinstance(raw_data, dict) and 'activities' in raw_data:
            raw_data = raw_data['activities']
        if not isinstance(raw_data, list):
            raise ValueError(f"Expected list of activities, got {type(raw_data)}")
        activities = []
        for i, item in enumerate(raw_data):
            try:
                activity = self._parse_activity(item)
                activities.append(activity)
            except Exception as e:
                raise ValueError(f"Failed to parse {self._activity_context(i, item)}: {e}") from e
        return activities

    def _activity_context(self, index: int, data: Any) -> str:
        if not isinstance(data, dict):
            return f"activity {index} (non-dict {type(data).__name__})"
        parts = [f"activity {index}"]
        if data.get('id'):
            parts.append(f"id={data['id']!r}")
        parts.append(f"type={data.get('type', 'unknown')!r}")
        return " ".join(parts)

    def _parse_activity(self, data: dict) -> Activity:
        if not isinstance(data, dict):
            raise TypeError(f"activity must be a dict, got {type(data).__name__}")
        activity_type = data.get('type')
        parsers = {
            'quiz': self._parse_quiz,
            'select': self._parse_select,
            'true-false': self._parse_true_false,
            'fill-in': self._parse_fill_in,
            'cloze': self._parse_cloze,
            'match-up': self._parse_match_up,
            'group-sort': self._parse_group_sort,
            'unjumble': self._parse_unjumble,
            'error-correction': self._parse_error_correction,
            'mark-the-words': self._parse_mark_the_words,
            'translate': self._parse_translate,
            'anagram': self._parse_anagram,
            'reading': self._parse_reading,
            'essay-response': self._parse_essay_response,
            'critical-analysis': self._parse_critical_analysis,
            'comparative-study': self._parse_comparative_study,
            'authorial-intent': self._parse_authorial_intent,
            'source-evaluation': self._parse_source_evaluation,
            'debate': self._parse_debate,
            'etymology-trace': self._parse_etymology_trace,
            'grammar-identify': self._parse_grammar_identify,
            'transcription': self._parse_transcription,
            'paleography-analysis': self._parse_paleography_analysis,
            'dialect-comparison': self._parse_dialect_comparison,
            'translation-critique': self._parse_translation_critique,
            'classify': self._parse_classify,
            'image-to-letter': self._parse_image_to_letter,
            'watch-and-repeat': self._parse_watch_and_repeat,
            'observe': self._parse_observe,
            'order': self._parse_order,
            'count-syllables': self._parse_count_syllables,
            'divide-words': self._parse_divide_words,
            'highlight-morphemes': self._parse_highlight_morphemes,
            'letter-grid': self._parse_letter_grid,
            'odd-one-out': self._parse_odd_one_out,
            'pick-syllables': self._parse_pick_syllables,
        }
        parser = parsers.get(activity_type)
        if not parser:
            raise ValueError(f"unknown activity type {activity_type!r}")
        activity = parser(data)
        activity.id = data.get('id', '')
        return activity

    def _parse_quiz(self, data: dict) -> QuizActivity:
        items = []
        for item_data in data.get('items', []):
            raw_options = item_data.get('options', [])
            correct_answer = item_data.get('answer')
            correct_index = item_data.get('correct')  # V2: integer index
            options = []
            for i, opt in enumerate(raw_options):
                if isinstance(opt, str):
                    # V2: correct is integer index; V1: match by answer string
                    # Use type() not isinstance() — bool is subclass of int in Python
                    is_correct = i == correct_index if type(correct_index) is int else opt == correct_answer
                    options.append(QuizOption(text=opt, correct=is_correct))
                else:
                    options.append(QuizOption(text=opt['text'], correct=opt.get('correct', False)))
            question = item_data.get('question') or item_data.get('prompt', '')
            items.append(QuizItem(question=question, options=options, explanation=item_data.get('explanation')))
        return QuizActivity(title=data.get('title', ''), items=items)

    def _parse_select(self, data: dict) -> SelectActivity:
        items = []
        for item_data in data.get('items', []):
            raw_options = item_data.get('options', [])
            correct_answer = item_data.get('answer')
            options = []
            for opt in raw_options:
                if isinstance(opt, str):
                    is_correct = (opt in correct_answer) if isinstance(correct_answer, list) else (opt == correct_answer)
                    options.append(QuizOption(text=opt, correct=is_correct))
                else:
                    options.append(QuizOption(text=opt['text'], correct=opt.get('correct', False)))
            question = item_data.get('question') or item_data.get('prompt', '')
            items.append(SelectItem(question=question, options=options, min_correct=item_data.get('min_correct'), explanation=item_data.get('explanation')))
        return SelectActivity(title=data.get('title', ''), items=items)

    def _parse_true_false(self, data: dict) -> TrueFalseActivity:
        items = []
        for item_data in data.get('items', []):
            statement = item_data.get('statement') or item_data.get('question', '')
            correct = item_data.get('correct')
            if correct is None:
                correct = item_data.get('answer', False)
            items.append(TrueFalseItem(statement=statement, correct=correct, explanation=item_data.get('explanation')))
        return TrueFalseActivity(title=data.get('title', ''), items=items)

    def _parse_fill_in(self, data: dict) -> FillInActivity:
        items = []
        for item_data in data.get('items', []):
            sentence = item_data.get('sentence') or item_data.get('prompt', '')
            items.append(FillInItem(sentence=sentence, answer=item_data['answer'], options=item_data.get('options', []), explanation=item_data.get('explanation')))
        return FillInActivity(title=data.get('title', ''), items=items)

    def _parse_cloze(self, data: dict) -> ClozeActivity:
        passage = data.get('passage', '')
        explicit_blanks = data.get('blanks', [])

        # If explicit blanks are provided, use them
        if explicit_blanks:
            blanks = [ClozeBlank(id=b['id'], answer=b['answer'], options=b.get('options', [])) for b in explicit_blanks]
        else:
            # Parse inline format: {option1|option2|option3} where first option is correct
            blanks = []
            blank_id = 0
            for match in re.finditer(r'\{([^}]+)\}', passage):
                options_str = match.group(1)
                options = [opt.strip() for opt in options_str.split('|')]
                if options:
                    # First option is the correct answer
                    answer = options[0]
                    blanks.append(ClozeBlank(id=blank_id, answer=answer, options=options))
                    blank_id += 1

        return ClozeActivity(title=data.get('title', ''), passage=passage, blanks=blanks)

    def _parse_match_up(self, data: dict) -> MatchUpActivity:
        pairs = [MatchPair(left=p['left'], right=p['right']) for p in data.get('pairs', [])]
        return MatchUpActivity(title=data.get('title', ''), pairs=pairs)

    def _parse_group_sort(self, data: dict) -> GroupSortActivity:
        groups = [GroupSortGroup(name=g.get('name', g.get('label', '')), items=g.get('items', [])) for g in data.get('groups', [])]
        return GroupSortActivity(title=data.get('title', ''), groups=groups)

    def _parse_unjumble(self, data: dict) -> UnjumbleActivity:
        items = []
        for item_index, item_data in enumerate(data.get('items', [])):
            words = self._unjumble_words(item_data, item_index)
            items.append(UnjumbleItem(words=words, answer=item_data['answer']))
        return UnjumbleActivity(title=data.get('title', ''), items=items)

    def _unjumble_words(self, item_data: dict, item_index: int) -> list[str]:
        for field_name in ('words', 'jumbled', 'prompt', 'scrambled'):
            if field_name in item_data:
                return self._tokens_from_unjumble_field(item_data[field_name], field_name, item_index)
        raise KeyError(f"unjumble item {item_index} missing one of: words, jumbled, prompt, scrambled")

    def _tokens_from_unjumble_field(self, value: Any, field_name: str, item_index: int) -> list[str]:
        if isinstance(value, list):
            return [str(token) for token in value]
        if isinstance(value, str):
            separator = '/' if '/' in value else None
            return [token.strip() for token in value.split(separator) if token.strip()]
        raise TypeError(
            f"unjumble item {item_index} field {field_name!r} must be str or list, "
            f"got {type(value).__name__}"
        )

    def _parse_error_correction(self, data: dict) -> ErrorCorrectionActivity:
        items = [ErrorCorrectionItem(
            sentence=i['sentence'],
            error=i['error'],
            answer=i.get('answer') or i.get('correction', ''),
            options=i.get('options', []),
            explanation=i.get('explanation', ''),
        ) for i in data.get('items', [])]
        return ErrorCorrectionActivity(title=data.get('title', ''), items=items)

    def _parse_mark_the_words(self, data: dict) -> MarkTheWordsActivity:
        # Support both old and new field names for backwards compatibility
        raw_text = data.get('passage') or data.get('text', '')
        correct_words = data.get('correct_words') or data.get('answers', [])

        # Robust extraction from various markdown formats
        extracted_answers = []

        def replace_match(match):
            word = match.group(1).strip()
            if word:
                extracted_answers.append(word)
            return word

        # 1. Handle [word](correct) or [word](wrong)
        clean_text = re.sub(r'\[([^\]]+)\]\(correct\)', replace_match, raw_text)
        clean_text = re.sub(r'\[([^\]]+)\]\(wrong\)', r'\1', clean_text)

        # 2. Handle **word** (bold) - treat as correct
        clean_text = re.sub(r'\*\*([^*]+)\*\*', replace_match, clean_text)

        # 3. Handle *word* (italics) - treat as correct
        clean_text = re.sub(r'\*([^*]+)\*', replace_match, clean_text)

        # 4. Handle [word] (legacy brackets) - treat as correct
        clean_text = re.sub(r'\[([^\]]+)\]', replace_match, clean_text)

        # If explicit answers provided, we prefer them (legacy), otherwise use extracted
        if not correct_words:
            # Filter out duplicates and empty strings
            seen = set()
            correct_words = [x for x in extracted_answers if not (x in seen or seen.add(x))]

        return MarkTheWordsActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            text=clean_text,
            answers=correct_words
        )

    def _parse_translate(self, data: dict) -> TranslateActivity:
        items = [TranslateItem(source=i['source'], options=[TranslateOption(text=o['text'], correct=o.get('correct', False)) for o in i.get('options', [])], explanation=i.get('explanation')) for i in data.get('items', [])]
        return TranslateActivity(title=data.get('title', ''), items=items)

    def _parse_anagram(self, data: dict) -> AnagramActivity:
        items = []
        for i in data.get('items', []):
            # Support V2 schema ('letters' array) and legacy ('scrambled' string).
            # If neither key is present, KeyError propagates with activity context.
            if 'letters' in i:
                scrambled = ' '.join(str(ch) for ch in i['letters'])
            elif 'scrambled' in i:
                scrambled = i['scrambled']
            else:
                raise KeyError(f"Anagram item missing both 'letters' and 'scrambled': {list(i.keys())}")
            items.append(AnagramItem(scrambled=scrambled, answer=i['answer'], hint=i.get('hint')))
        return AnagramActivity(title=data.get('title', ''), items=items)

    def _parse_reading(self, data: dict) -> ReadingActivity:
        # LIT reading activities use inline text; others use external resources
        return ReadingActivity(
            title=data.get('title', ''),
            id=data.get('id', ''),  # Issue #425: Required for linking
            text=data.get('text', ''),  # LIT: inline primary source
            source=data.get('source', ''),  # Attribution
            context=data.get('context', ''),
            resource=data.get('resource', {}),
            tasks=data.get('tasks', [])
        )

    def _parse_essay_response(self, data: dict) -> EssayResponseActivity:
        return EssayResponseActivity(
            title=data.get('title', ''),
            source_reading=data.get('source_reading', ''),  # Issue #425: Link to reading
            prompt=data.get('prompt', ''),
            min_words=data.get('min_words', 0),
            model_answer=data.get('model_answer', ''),
            rubric=data.get('rubric', [])
        )

    def _parse_critical_analysis(self, data: dict) -> CriticalAnalysisActivity:
        return CriticalAnalysisActivity(
            title=data.get('title', ''),
            source_reading=data.get('source_reading', ''),  # Issue #425: Link to reading
            target_text=data.get('target_text', ''),
            context=data.get('context', ''),
            question=data.get('question', ''),
            questions=data.get('questions', []),
            model_answer=data.get('model_answer', ''),
            model_answers=data.get('model_answers', [])
        )

    def _parse_comparative_study(self, data: dict) -> ComparativeStudyActivity:
        return ComparativeStudyActivity(
            title=data.get('title', ''),
            source_reading=data.get('source_reading', ''),  # Issue #425
            items_to_compare=data.get('items_to_compare', []),
            criteria=data.get('criteria', []),
            source_a=data.get('source_a', ''),
            source_b=data.get('source_b', ''),
            task=data.get('task', ''),
            prompt=data.get('prompt', ''),
            model_answer=data.get('model_answer', '')
        )

    def _parse_authorial_intent(self, data: dict) -> AuthorialIntentActivity:
        return AuthorialIntentActivity(
            title=data.get('title', ''),
            source_reading=data.get('source_reading', ''),  # Issue #425
            excerpt=data.get('text_excerpt', ''),
            questions=[data.get('prompt', '')] if data.get('prompt') else [],
            model_answer=data.get('model_answer', '')
        )

    def _parse_source_evaluation(self, data: dict) -> SourceEvaluationActivity:
        """Parse source-evaluation activity (ISTORIO)."""
        metadata_raw = data.get('source_metadata', {})
        metadata = None
        if metadata_raw:
            metadata = SourceMetadata(
                author=metadata_raw.get('author', ''),
                date=metadata_raw.get('date', ''),
                type=metadata_raw.get('type', ''),
                context=metadata_raw.get('context', '')
            )
        return SourceEvaluationActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            source_text=data.get('source_text', ''),
            source_metadata=metadata,
            evaluation_criteria=data.get('evaluation_criteria', []),
            guiding_questions=data.get('guiding_questions', []),
            model_evaluation=data.get('model_evaluation', '')
        )

    def _parse_debate(self, data: dict) -> DebateActivity:
        """Parse debate activity (ISTORIO)."""
        positions = []
        for pos_data in data.get('positions', []):
            positions.append(DebatePosition(
                name=pos_data.get('name', ''),
                proponents=pos_data.get('proponents', ''),
                argument=pos_data.get('argument', ''),
                evidence=pos_data.get('evidence', []),
                weaknesses=pos_data.get('weaknesses', [])
            ))
        return DebateActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            debate_question=data.get('debate_question', ''),
            historical_context=data.get('historical_context', ''),
            positions=positions,
            analysis_tasks=data.get('analysis_tasks', []),
            model_analysis=data.get('model_analysis', '')
        )

    def _parse_etymology_trace(self, data: dict) -> EtymologyTraceActivity:
        items = []
        for item_data in data.get('items', []):
            items.append(EtymologyItem(
                word=item_data['word'],
                modern=item_data['modern'],
                evolution=item_data['evolution']
            ))
        return EtymologyTraceActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=items
        )

    def _parse_grammar_identify(self, data: dict) -> GrammarIdentifyActivity:
        items = []
        for item_data in data.get('items', []):
            items.append(GrammarIdentifyItem(
                text=item_data['text'],
                form=item_data['form'],
                answer=item_data['answer']
            ))
        return GrammarIdentifyActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=items
        )

    def _parse_transcription(self, data: dict) -> TranscriptionActivity:
        return TranscriptionActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            original=data.get('original', ''),
            answer=data.get('answer', ''),
            hints=data.get('hints', [])
        )

    def _parse_paleography_analysis(self, data: dict) -> PaleographyAnalysisActivity:
        hotspots = []
        for h in data.get('hotspots', []):
            hotspots.append(PaleographyHotspot(
                x=h.get('x', 0),
                y=h.get('y', 0),
                label=h.get('label', ''),
                explanation=h.get('explanation', '')
            ))
        return PaleographyAnalysisActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            image_url=data.get('image_url', ''),
            hotspots=hotspots,
            options=data.get('options', [])
        )

    def _parse_dialect_comparison(self, data: dict) -> DialectComparisonActivity:
        features = []
        for f in data.get('features', []):
            features.append(DialectFeature(
                feature_name=f.get('feature_name', ''),
                value_a=f.get('value_a', ''),
                value_b=f.get('value_b', ''),
                explanation=f.get('explanation', '')
            ))
        return DialectComparisonActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            text_a=data.get('text_a', ''),
            text_b=data.get('text_b', ''),
            label_a=data.get('label_a', ''),
            label_b=data.get('label_b', ''),
            features=features
        )

    def _parse_translation_critique(self, data: dict) -> TranslationCritiqueActivity:
        translations = []
        for t in data.get('translations', []):
            translations.append(TranslationItem(
                translator=t.get('translator', ''),
                text=t.get('text', ''),
                accuracy_score=t.get('accuracy_score', 0),
                notes=t.get('notes', '')
            ))
        return TranslationCritiqueActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            original=data.get('original', ''),
            translations=translations,
            focus_points=data.get('focus_points', [])
        )

    # ------------------------------------------------------------------
    # Pre-literacy activity parsers
    # ------------------------------------------------------------------

    def _parse_classify(self, data: dict) -> ClassifyActivity:
        cats = []
        for c in data.get('categories', []):
            cats.append(ClassifyCategory(
                label=c.get('label', ''),
                items=c.get('items', []),
            ))
        return ClassifyActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            categories=cats,
        )

    def _parse_image_to_letter(self, data: dict) -> ImageToLetterActivity:
        items = []
        for i in data.get('items', []):
            items.append(ImageToLetterItem(
                emoji=i.get('emoji', ''),
                answer=i.get('answer', ''),
                distractors=i.get('distractors', []),
                note=i.get('note', ''),
            ))
        return ImageToLetterActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=items,
        )

    def _parse_watch_and_repeat(self, data: dict) -> WatchAndRepeatActivity:
        items = []
        for i in data.get('items', []):
            items.append(WatchAndRepeatItem(
                video=i.get('video', ''),
                letter=i.get('letter', ''),
                word=i.get('word', ''),
                note=i.get('note', ''),
            ))
        return WatchAndRepeatActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=items,
        )

    def _parse_observe(self, data: dict) -> ObserveActivity:
        raw_examples = data.get('examples')
        if not isinstance(raw_examples, list) or not raw_examples:
            raise ValueError("observe requires non-empty examples list")
        examples = [
            str(item.get('text', '')) if isinstance(item, dict) else str(item)
            for item in raw_examples
        ]
        if not all(example.strip() for example in examples):
            raise ValueError("observe examples must be non-empty strings")
        prompt = data.get('prompt')
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("observe requires non-empty prompt")
        return ObserveActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            examples=examples,
            prompt=prompt,
        )

    def _parse_order(self, data: dict) -> OrderActivity:
        items = data.get('items')
        correct_order = data.get('correct_order')
        if not isinstance(items, list) or not items:
            raise ValueError("order requires non-empty items list")
        if not isinstance(correct_order, list) or not correct_order:
            raise ValueError("order requires non-empty correct_order list")
        if not all(isinstance(index, int) for index in correct_order):
            raise TypeError("order correct_order must contain integers")
        if any(index < 0 or index >= len(items) for index in correct_order):
            raise ValueError("order correct_order index out of range")
        return OrderActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=[str(item) for item in items],
            correct_order=correct_order,
        )

    def _parse_count_syllables(self, data: dict) -> CountSyllablesActivity:
        items = []
        for item in data.get('items', []):
            if 'word' not in item or 'correct' not in item:
                raise KeyError("count-syllables item requires word and correct")
            if not isinstance(item['correct'], int):
                raise TypeError("count-syllables item correct must be an integer")
            items.append(CountSyllablesItem(
                word=str(item['word']),
                correct=item['correct'],
                translation=str(item['translation']) if item.get('translation') else None,
            ))
        if not items:
            raise ValueError("count-syllables requires non-empty items list")
        max_count = data.get('maxCount')
        if max_count is not None and not isinstance(max_count, int):
            raise TypeError("count-syllables maxCount must be an integer")
        return CountSyllablesActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=items,
            max_count=max_count,
        )

    def _parse_divide_words(self, data: dict) -> DivideWordsActivity:
        items = []
        for item in data.get('items', []):
            if 'word' not in item or 'answer' not in item:
                raise KeyError("divide-words item requires word and answer")
            items.append(DivideWordsItem(
                word=str(item['word']),
                answer=str(item['answer']),
                hint=str(item['hint']) if item.get('hint') else None,
            ))
        if not items:
            raise ValueError("divide-words requires non-empty items list")
        return DivideWordsActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=items,
        )

    def _parse_highlight_morphemes(self, data: dict) -> HighlightMorphemesActivity:
        items = data.get('items', [])
        text = data.get('text', '')
        morphemes = []
        for item in items:
            word = str(item.get('word', '')).strip()
            if not word:
                raise ValueError("highlight-morphemes item requires word")
            raw_morphemes = item.get('morphemes', [])
            if isinstance(raw_morphemes, list) and raw_morphemes:
                for raw in raw_morphemes:
                    if isinstance(raw, dict):
                        morpheme = str(raw.get('morpheme') or raw.get('text') or '').strip()
                        mtype = str(raw.get('type', 'unknown'))
                    else:
                        morpheme = str(raw).strip()
                        mtype = 'unknown'
                    if not morpheme:
                        raise ValueError("highlight-morphemes morpheme must be non-empty")
                    morphemes.append(HighlightMorphemeItem(word=word, morpheme=morpheme, type=mtype))
            elif item.get('morpheme'):
                morphemes.append(HighlightMorphemeItem(
                    word=word,
                    morpheme=str(item['morpheme']),
                    type=str(item.get('type', 'unknown')),
                ))
            else:
                raise ValueError("highlight-morphemes item requires morphemes")
        if not morphemes:
            raise ValueError("highlight-morphemes requires non-empty items list")
        if not text:
            text = " ".join(item.word for item in morphemes)
        return HighlightMorphemesActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            text=str(text),
            morphemes=morphemes,
        )

    def _parse_letter_grid(self, data: dict) -> LetterGridActivity:
        letters = data.get('letters')
        if not isinstance(letters, list) or not letters:
            raise ValueError("letter-grid requires non-empty letters list")
        normalized = []
        for letter in letters:
            if not isinstance(letter, dict):
                raise TypeError("letter-grid letters must be dictionaries")
            required = ('upper', 'lower', 'emoji', 'key_word')
            missing = [key for key in required if not letter.get(key)]
            if missing:
                raise KeyError(f"letter-grid letter missing required fields: {missing}")
            normalized.append({key: letter[key] for key in letter if key in {'upper', 'lower', 'emoji', 'key_word', 'note', 'sound_type'}})
        return LetterGridActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            letters=normalized,
        )

    def _parse_odd_one_out(self, data: dict) -> OddOneOutActivity:
        items = []
        for item in data.get('items', []):
            if not isinstance(item.get('words'), list) or not item['words']:
                raise ValueError("odd-one-out item requires non-empty words list")
            correct = item.get('correct')
            if not isinstance(correct, int):
                raise TypeError("odd-one-out item correct must be an integer")
            if correct < 0 or correct >= len(item['words']):
                raise ValueError("odd-one-out item correct index out of range")
            explanation = item.get('explanation')
            if not isinstance(explanation, str) or not explanation.strip():
                raise ValueError("odd-one-out item requires explanation")
            items.append(OddOneOutItem(
                words=[str(word) for word in item['words']],
                correct=correct,
                explanation=explanation,
            ))
        if not items:
            raise ValueError("odd-one-out requires non-empty items list")
        return OddOneOutActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            items=items,
        )

    def _parse_pick_syllables(self, data: dict) -> PickSyllablesActivity:
        syllables = data.get('syllables')
        correct_indices = data.get('correctIndices')
        category = data.get('category')
        if not isinstance(syllables, list) or not syllables:
            raise ValueError("pick-syllables requires non-empty syllables list")
        if not isinstance(correct_indices, list) or not correct_indices:
            raise ValueError("pick-syllables requires non-empty correctIndices list")
        if not all(isinstance(index, int) for index in correct_indices):
            raise TypeError("pick-syllables correctIndices must contain integers")
        if any(index < 0 or index >= len(syllables) for index in correct_indices):
            raise ValueError("pick-syllables correctIndices index out of range")
        if not isinstance(category, str) or not category.strip():
            raise ValueError("pick-syllables requires non-empty category")
        return PickSyllablesActivity(
            title=data.get('title', ''),
            instruction=data.get('instruction', ''),
            syllables=[str(syllable) for syllable in syllables],
            correct_indices=correct_indices,
            category=category,
            explanation=str(data.get('explanation', '')),
        )

    def _escape_jsx(self, text: str) -> str:
        """Escapes characters that break JSX parsing when used as a string literal attribute."""
        if not text:
            return ""
        if not isinstance(text, str):
            return str(text)
        # Escape characters that break JSX string attributes (", \, and backticks)
        # Also escape newlines to keep the attribute on a single line in generated code
        res = text.replace('\\', '\\\\').replace('"', '&quot;').replace('\n', '\\n').replace('\r', '')
        return res

    def _dump_safe_json(self, data: Any) -> str:
        """Dumps JSON safely for inclusion in a JSX template literal (backticks)."""
        import datetime
        def json_serial(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError (f"Type {type(obj)} not serializable")

        s = json.dumps(data, ensure_ascii=False, default=json_serial)
        # Escape backslashes first to avoid double escaping other chars
        s = s.replace('\\', '\\\\')
        # Escape backticks for template literals
        s = s.replace('`', '\\`')
        # Escape $ to avoid template interpolation
        s = s.replace('${', '\\${')
        return s

    def to_mdx(self, activities: list[Activity], is_ukrainian_forced: bool = False) -> str:
        mdx_parts = []
        for activity in activities:
            mdx = self._activity_to_mdx(activity, is_ukrainian_forced)
            if mdx:
                mdx_parts.append(mdx)
        return '\n\n'.join(mdx_parts)

    def _activity_to_mdx(self, activity: Activity, is_ukrainian_forced: bool = False) -> str:
        if isinstance(activity, QuizActivity):
            return self._quiz_to_mdx(activity)
        if isinstance(activity, SelectActivity):
            return self._select_to_mdx(activity)
        if isinstance(activity, TrueFalseActivity):
            return self._true_false_to_mdx(activity)
        if isinstance(activity, FillInActivity):
            return self._fill_in_to_mdx(activity)
        if isinstance(activity, ClozeActivity):
            return self._cloze_to_mdx(activity)
        if isinstance(activity, MatchUpActivity):
            return self._match_up_to_mdx(activity)
        if isinstance(activity, GroupSortActivity):
            return self._group_sort_to_mdx(activity)
        if isinstance(activity, UnjumbleActivity):
            return self._unjumble_to_mdx(activity)
        if isinstance(activity, ErrorCorrectionActivity):
            return self._error_correction_to_mdx(activity)
        if isinstance(activity, MarkTheWordsActivity):
            return self._mark_the_words_to_mdx(activity)
        if isinstance(activity, TranslateActivity):
            return self._translate_to_mdx(activity)
        if isinstance(activity, AnagramActivity):
            return self._anagram_to_mdx(activity)
        if isinstance(activity, ReadingActivity):
            return self._reading_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, EssayResponseActivity):
            return self._essay_response_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, CriticalAnalysisActivity):
            return self._critical_analysis_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, ComparativeStudyActivity):
            return self._comparative_study_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, AuthorialIntentActivity):
            return self._authorial_intent_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, SourceEvaluationActivity):
            return self._source_evaluation_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, DebateActivity):
            return self._debate_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, EtymologyTraceActivity):
            return self._etymology_trace_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, GrammarIdentifyActivity):
            return self._grammar_identify_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, TranscriptionActivity):
            return self._transcription_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, PaleographyAnalysisActivity):
            return self._paleography_analysis_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, DialectComparisonActivity):
            return self._dialect_comparison_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, TranslationCritiqueActivity):
            return self._translation_critique_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, ClassifyActivity):
            return self._classify_to_mdx(activity)
        if isinstance(activity, ImageToLetterActivity):
            return self._image_to_letter_to_mdx(activity)
        if isinstance(activity, WatchAndRepeatActivity):
            return self._watch_and_repeat_to_mdx(activity)
        if isinstance(activity, ObserveActivity):
            return self._observe_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, OrderActivity):
            return self._order_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, CountSyllablesActivity):
            return self._count_syllables_to_mdx(activity)
        if isinstance(activity, DivideWordsActivity):
            return self._divide_words_to_mdx(activity)
        if isinstance(activity, HighlightMorphemesActivity):
            return self._highlight_morphemes_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, LetterGridActivity):
            return self._letter_grid_to_mdx(activity)
        if isinstance(activity, OddOneOutActivity):
            return self._odd_one_out_to_mdx(activity)
        if isinstance(activity, PickSyllablesActivity):
            return self._pick_syllables_to_mdx(activity)
        activity_type = getattr(activity, 'type', '')
        if activity_type == 'quiz':
            return self._quiz_to_mdx(activity)
        if activity_type == 'select':
            return self._select_to_mdx(activity)
        if activity_type == 'true-false':
            return self._true_false_to_mdx(activity)
        if activity_type == 'fill-in':
            return self._fill_in_to_mdx(activity)
        if activity_type == 'cloze':
            return self._cloze_to_mdx(activity)
        if activity_type == 'match-up':
            return self._match_up_to_mdx(activity)
        if activity_type == 'group-sort':
            return self._group_sort_to_mdx(activity)
        if activity_type == 'unjumble':
            return self._unjumble_to_mdx(activity)
        if activity_type == 'error-correction':
            return self._error_correction_to_mdx(activity)
        if activity_type == 'mark-the-words':
            return self._mark_the_words_to_mdx(activity)
        if activity_type == 'translate':
            return self._translate_to_mdx(activity)
        if activity_type == 'anagram':
            return self._anagram_to_mdx(activity)
        if activity_type == 'reading':
            return self._reading_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'essay-response':
            return self._essay_response_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'critical-analysis':
            return self._critical_analysis_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'comparative-study':
            return self._comparative_study_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'authorial-intent':
            return self._authorial_intent_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'source-evaluation':
            return self._source_evaluation_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'debate':
            return self._debate_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'etymology-trace':
            return self._etymology_trace_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'grammar-identify':
            return self._grammar_identify_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'transcription':
            return self._transcription_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'paleography-analysis':
            return self._paleography_analysis_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'dialect-comparison':
            return self._dialect_comparison_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'translation-critique':
            return self._translation_critique_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'classify':
            return self._classify_to_mdx(activity)
        if activity_type == 'image-to-letter':
            return self._image_to_letter_to_mdx(activity)
        if activity_type == 'watch-and-repeat':
            return self._watch_and_repeat_to_mdx(activity)
        if activity_type == 'observe':
            return self._observe_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'order':
            return self._order_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'count-syllables':
            return self._count_syllables_to_mdx(activity)
        if activity_type == 'divide-words':
            return self._divide_words_to_mdx(activity)
        if activity_type == 'highlight-morphemes':
            return self._highlight_morphemes_to_mdx(activity, is_ukrainian_forced)
        if activity_type == 'letter-grid':
            return self._letter_grid_to_mdx(activity)
        if activity_type == 'odd-one-out':
            return self._odd_one_out_to_mdx(activity)
        if activity_type == 'pick-syllables':
            return self._pick_syllables_to_mdx(activity)
        return ''

    def _quiz_to_mdx(self, activity: QuizActivity) -> str:
        items = [{'question': str(i.question), 'options': [{'text': str(o.text), 'correct': o.correct} for o in i.options], 'explanation': str(i.explanation) if i.explanation else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Quiz client:only='react' questions={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _select_to_mdx(self, activity: SelectActivity) -> str:
        items = [{'question': str(i.question), 'options': [{'text': str(o.text), 'correct': o.correct} for o in i.options], 'explanation': str(i.explanation) if i.explanation else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Select client:only='react' questions={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _true_false_to_mdx(self, activity: TrueFalseActivity) -> str:
        items = [{'statement': str(i.statement), 'isTrue': i.correct, 'explanation': str(i.explanation) if i.explanation else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<TrueFalse client:only='react' items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _fill_in_to_mdx(self, activity: FillInActivity) -> str:
        items = [{'sentence': str(i.sentence), 'answer': str(i.answer), 'options': [str(opt) for opt in i.options]} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<FillIn client:only='react' items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _cloze_to_mdx(self, activity: ClozeActivity) -> str:
        passage = activity.passage
        # Transform {content} placeholders to [___:N] markers if blanks are provided
        if activity.blanks:
            new_passage = ""
            last_pos = 0
            blank_idx = 0
            # Find all { ... } blocks
            for match in re.finditer(r'\{[^}]+\}', passage):
                new_passage += passage[last_pos:match.start()]
                new_passage += f"[___:{blank_idx}]"
                last_pos = match.end()
                blank_idx += 1
            new_passage += passage[last_pos:]

            # Use transformed passage if we found markers, otherwise trust original
            if blank_idx > 0:
                passage = new_passage

        blanks = [{'index': i, 'answer': str(b.answer), 'options': [str(opt) for opt in b.options]} for i, b in enumerate(activity.blanks)]
        return f"### {self._escape_jsx(activity.title)}\n\n<Cloze client:only='react' passage={{{json.dumps(str(passage), ensure_ascii=False)}}} blanks={{JSON.parse(`{self._dump_safe_json(blanks)}`)}} />"

    def _match_up_to_mdx(self, activity: MatchUpActivity) -> str:
        pairs = [{'left': str(p.left), 'right': str(p.right)} for p in activity.pairs]
        return f"### {self._escape_jsx(activity.title)}\n\n<MatchUp client:only='react' pairs={{JSON.parse(`{self._dump_safe_json(pairs)}`)}} />"

    def _group_sort_to_mdx(self, activity: GroupSortActivity) -> str:
        groups = {g.name: g.items for g in activity.groups}
        return f"### {self._escape_jsx(activity.title)}\n\n<GroupSort client:only='react' groups={{JSON.parse(`{self._dump_safe_json(groups)}`)}} />"

    def _unjumble_to_mdx(self, activity: UnjumbleActivity) -> str:
        items = [{'jumbled': ' / '.join(str(w) for w in i.words), 'answer': str(i.answer)} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Unjumble client:only='react' items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _error_correction_to_mdx(self, activity: ErrorCorrectionActivity) -> str:
        items = []
        for i in activity.items:
            opts = self._dump_safe_json([str(opt) for opt in i.options])
            items.append(f'  <ErrorCorrectionItem sentence="{self._escape_jsx(str(i.sentence))}" errorWord="{self._escape_jsx(str(i.error))}" correctForm="{self._escape_jsx(str(i.answer))}" options={{JSON.parse(`{opts}`)}} explanation="{self._escape_jsx(str(i.explanation))}" />')
        return f"### {self._escape_jsx(activity.title)}\n\n<ErrorCorrection client:only='react'>\n{chr(10).join(items)}\n</ErrorCorrection>"

    def _mark_the_words_to_mdx(self, activity: MarkTheWordsActivity) -> str:
        ans = self._dump_safe_json([w for word in activity.answers for w in (str(word).split() if ' ' in str(word) else [str(word)])])
        return f"### {self._escape_jsx(activity.title)}\n\n<MarkTheWords client:only='react'>\n  <MarkTheWordsActivity instruction=\"{self._escape_jsx(str(activity.instruction))}\" text=\"{self._escape_jsx(str(activity.text))}\" correctWords={{JSON.parse(`{ans}`)}} />\n</MarkTheWords>"

    def _translate_to_mdx(self, activity: TranslateActivity) -> str:
        items = [{'source': str(i.source), 'options': [{'text': str(o.text), 'correct': o.correct} for o in i.options]} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Translate client:only='react' questions={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _anagram_to_mdx(self, activity: AnagramActivity) -> str:
        items = [{'scrambled': str(i.scrambled), 'answer': str(i.answer), 'hint': str(i.hint) if i.hint else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Anagram client:only='react' items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _essay_response_to_mdx(self, activity: EssayResponseActivity, is_ukrainian_forced: bool = False) -> str:
        rubric_md = ""
        rows = []
        if activity.rubric:
            for r in activity.rubric:
                if isinstance(r, dict):
                    rows.append(f"| {r.get('criteria', '')} | {r.get('description', '')} | {r.get('points', 0)} |")
                elif isinstance(r, str):
                    rows.append(f"| {r} | | |")
        if is_ukrainian_forced:
            if rows:
                rubric_md = "\n\n#### Критерії оцінювання\n\n| Критерій | Опис | Бали |\n|---|---|---|\n" + "\n".join(rows)
        else:
            if rows:
                rubric_md = "\n\n#### Rubric\n\n| Criteria | Description | Points |\n|---|---|---|\n" + "\n".join(rows)
        # Using self._dump_safe_json for complex props might be safer than json.dumps inside {}
        # But here we are passing strings directly, not parsing JSON inside
        # Wait, the original code used json.dumps inside {}
        # prompt={{{json.dumps(activity.prompt)}}}
        # This puts "string" inside {}, resulting in prompt={"string"} which is valid JSX
        # So we don't need _dump_safe_json here, but we DO need to NOT escape quotes inside content
        # json.dumps does escaping correctly for a JS string literal.
        return f"### {self._escape_jsx(activity.title)}\n\n<EssayResponse client:only='react' title=\"{self._escape_jsx(activity.title)}\" prompt={{{json.dumps(activity.prompt, ensure_ascii=False)}}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}} rubric={{{json.dumps(rubric_md, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _reading_to_mdx(self, activity: ReadingActivity, is_ukrainian_forced: bool = False) -> str:
        tasks = self._dump_safe_json(activity.tasks)
        resource = self._dump_safe_json(activity.resource) if activity.resource else '{}'
        # Seminar mode uses text/source; legacy uses context/resource
        text_prop = f' text={{{json.dumps(activity.text, ensure_ascii=False)}}}' if activity.text else ''
        source_prop = f' source={{{json.dumps(activity.source, ensure_ascii=False)}}}' if activity.source else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<ReadingActivity client:only='react' title=\"{self._escape_jsx(activity.title)}\" context=\"{self._escape_jsx(activity.context)}\"{text_prop}{source_prop} resource={{JSON.parse(`{resource}`)}} tasks={{JSON.parse(`{tasks}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _critical_analysis_to_mdx(self, activity: CriticalAnalysisActivity, is_ukrainian_forced: bool = False) -> str:
        # Seminar mode uses targetText/questions/modelAnswers; legacy uses context/question/modelAnswer
        target_text_prop = f' targetText={{{json.dumps(activity.target_text, ensure_ascii=False)}}}' if activity.target_text else ''
        questions_prop = f' questions={{JSON.parse(`{self._dump_safe_json(activity.questions)}`)}}' if activity.questions else ''
        model_answers_prop = f' modelAnswers={{JSON.parse(`{self._dump_safe_json(activity.model_answers)}`)}}' if activity.model_answers else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<CriticalAnalysis client:only='react' title=\"{self._escape_jsx(activity.title)}\" context={{{json.dumps(activity.context, ensure_ascii=False)}}} question={{{json.dumps(activity.question, ensure_ascii=False)}}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}}{target_text_prop}{questions_prop}{model_answers_prop} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _comparative_study_to_mdx(self, activity: ComparativeStudyActivity, is_ukrainian_forced: bool = False) -> str:
        # Seminar mode uses itemsToCompare/criteria/prompt; legacy uses sourceA/sourceB/task
        items_prop = f' itemsToCompare={{JSON.parse(`{self._dump_safe_json(activity.items_to_compare)}`)}}' if activity.items_to_compare else ''
        criteria_prop = f' criteria={{JSON.parse(`{self._dump_safe_json(activity.criteria)}`)}}' if activity.criteria else ''
        prompt_prop = f' prompt={{{json.dumps(activity.prompt, ensure_ascii=False)}}}' if activity.prompt else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<ComparativeStudy client:only='react' title=\"{self._escape_jsx(activity.title)}\" content={{{json.dumps(activity.source_a, ensure_ascii=False)}}} task={{{json.dumps(activity.task, ensure_ascii=False)}}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}}{items_prop}{criteria_prop}{prompt_prop} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _authorial_intent_to_mdx(self, activity: AuthorialIntentActivity, is_ukrainian_forced: bool = False) -> str:
        questions = self._dump_safe_json(activity.questions)
        return f"### {self._escape_jsx(activity.title)}\n\n<AuthorialIntent client:only='react' title=\"{self._escape_jsx(activity.title)}\" excerpt={{{json.dumps(activity.excerpt, ensure_ascii=False)}}} questions={{JSON.parse(`{questions}`)}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _source_evaluation_to_mdx(self, activity: SourceEvaluationActivity, is_ukrainian_forced: bool = False) -> str:
        """Convert source-evaluation activity to SourceEvaluation component (ISTORIO)."""
        # Build sourceMetadata object
        metadata_dict = {}
        if activity.source_metadata:
            if activity.source_metadata.author:
                metadata_dict['author'] = activity.source_metadata.author
            if activity.source_metadata.date:
                metadata_dict['date'] = activity.source_metadata.date
            if activity.source_metadata.type:
                metadata_dict['type'] = activity.source_metadata.type
            if activity.source_metadata.context:
                metadata_dict['context'] = activity.source_metadata.context

        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        metadata_prop = f' sourceMetadata={{JSON.parse(`{self._dump_safe_json(metadata_dict)}`)}}' if metadata_dict else ''
        criteria_prop = f' evaluationCriteria={{JSON.parse(`{self._dump_safe_json(activity.evaluation_criteria)}`)}}' if activity.evaluation_criteria else ''
        questions_prop = f' guidingQuestions={{JSON.parse(`{self._dump_safe_json(activity.guiding_questions)}`)}}' if activity.guiding_questions else ''

        return f"### {self._escape_jsx(activity.title)}\n\n<SourceEvaluation client:only='react' title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} sourceText={{{json.dumps(activity.source_text, ensure_ascii=False)}}}{metadata_prop}{criteria_prop}{questions_prop} modelEvaluation={{{json.dumps(activity.model_evaluation, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _debate_to_mdx(self, activity: DebateActivity, is_ukrainian_forced: bool = False) -> str:
        """Convert debate activity to Debate component (ISTORIO)."""
        # Build positions array
        positions_data = []
        for pos in activity.positions:
            pos_dict = {
                'name': pos.name,
                'proponents': pos.proponents,
                'argument': pos.argument
            }
            if pos.evidence:
                pos_dict['evidence'] = pos.evidence
            if pos.weaknesses:
                pos_dict['weaknesses'] = pos.weaknesses
            positions_data.append(pos_dict)

        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        context_prop = f' historicalContext={{{json.dumps(activity.historical_context, ensure_ascii=False)}}}' if activity.historical_context else ''
        tasks_prop = f' analysisTasks={{JSON.parse(`{self._dump_safe_json(activity.analysis_tasks)}`)}}' if activity.analysis_tasks else ''

        return f"### {self._escape_jsx(activity.title)}\n\n<Debate client:only='react' title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} debateQuestion={{{json.dumps(activity.debate_question, ensure_ascii=False)}}}{context_prop} positions={{JSON.parse(`{self._dump_safe_json(positions_data)}`)}}{tasks_prop} modelAnalysis={{{json.dumps(activity.model_analysis, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _etymology_trace_to_mdx(self, activity: EtymologyTraceActivity, is_ukrainian_forced: bool = False) -> str:
        items = [{'word': str(i.word), 'modern': str(i.modern), 'evolution': str(i.evolution)} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<EtymologyTrace client:only='react' title=\"{self._escape_jsx(activity.title)}\" items={{JSON.parse(`{self._dump_safe_json(items)}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _grammar_identify_to_mdx(self, activity: GrammarIdentifyActivity, is_ukrainian_forced: bool = False) -> str:
        items = [{'text': str(i.text), 'form': str(i.form), 'answer': str(i.answer)} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<GrammarIdentify client:only='react' title=\"{self._escape_jsx(activity.title)}\" items={{JSON.parse(`{self._dump_safe_json(items)}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _transcription_to_mdx(self, activity: TranscriptionActivity, is_ukrainian_forced: bool = False) -> str:
        hints = self._dump_safe_json(activity.hints) if activity.hints else '[]'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<Transcription client:only='react' title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} original={{{json.dumps(activity.original, ensure_ascii=False)}}} answer={{{json.dumps(activity.answer, ensure_ascii=False)}}} hints={{JSON.parse(`{hints}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _paleography_analysis_to_mdx(self, activity: PaleographyAnalysisActivity, is_ukrainian_forced: bool = False) -> str:
        hotspots = [{'x': h.x, 'y': h.y, 'label': h.label, 'explanation': h.explanation} for h in activity.hotspots]
        options = self._dump_safe_json(activity.options) if activity.options else '[]'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<PaleographyAnalysis client:only='react' title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} imageUrl={{{json.dumps(activity.image_url, ensure_ascii=False)}}} hotspots={{JSON.parse(`{self._dump_safe_json(hotspots)}`)}} options={{JSON.parse(`{options}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _dialect_comparison_to_mdx(self, activity: DialectComparisonActivity, is_ukrainian_forced: bool = False) -> str:
        features = [{'featureName': f.feature_name, 'valueA': f.value_a, 'valueB': f.value_b, 'explanation': f.explanation} for f in activity.features]
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        label_a_prop = f' labelA={{{json.dumps(activity.label_a, ensure_ascii=False)}}}' if activity.label_a else ''
        label_b_prop = f' labelB={{{json.dumps(activity.label_b, ensure_ascii=False)}}}' if activity.label_b else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<DialectComparison client:only='react' title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} textA={{{json.dumps(activity.text_a, ensure_ascii=False)}}} textB={{{json.dumps(activity.text_b, ensure_ascii=False)}}}{label_a_prop}{label_b_prop} features={{JSON.parse(`{self._dump_safe_json(features)}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _translation_critique_to_mdx(self, activity: TranslationCritiqueActivity, is_ukrainian_forced: bool = False) -> str:
        translations = [{'translator': t.translator, 'text': t.text, 'accuracyScore': t.accuracy_score, 'notes': t.notes} for t in activity.translations]
        focus_points = self._dump_safe_json(activity.focus_points) if activity.focus_points else '[]'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<TranslationCritique client:only='react' title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} original={{{json.dumps(activity.original, ensure_ascii=False)}}} translations={{JSON.parse(`{self._dump_safe_json(translations)}`)}} focusPoints={{JSON.parse(`{focus_points}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    # ------------------------------------------------------------------
    # Pre-literacy activity renderers
    # ------------------------------------------------------------------

    def _classify_to_mdx(self, activity: ClassifyActivity) -> str:
        cats = [{'label': c.label, 'items': c.items} for c in activity.categories]
        props = f'categories={{JSON.parse(`{self._dump_safe_json(cats)}`)}}'
        if activity.title:
            props += f' title="{self._escape_jsx(activity.title)}"'
        if activity.instruction:
            props += f' instruction="{self._escape_jsx(activity.instruction)}"'
        heading = activity.title or 'Classify'
        return f"### {self._escape_jsx(heading)}\n\n<Classify client:only='react' {props} />"

    def _image_to_letter_to_mdx(self, activity: ImageToLetterActivity) -> str:
        items = [{'emoji': i.emoji, 'answer': i.answer, 'distractors': i.distractors} for i in activity.items]
        props = f'items={{JSON.parse(`{self._dump_safe_json(items)}`)}}'
        if activity.title:
            props += f' title="{self._escape_jsx(activity.title)}"'
        heading = activity.title or 'Image to Letter'
        return f"### {self._escape_jsx(heading)}\n\n<ImageToLetter client:only='react' {props} />"

    def _watch_and_repeat_to_mdx(self, activity: WatchAndRepeatActivity) -> str:
        items = []
        for i in activity.items:
            entry: dict[str, str] = {'video': i.video}
            if i.letter:
                entry['letter'] = i.letter
            if i.word:
                entry['word'] = i.word
            if i.note:
                entry['note'] = i.note
            items.append(entry)
        props = f'items={{JSON.parse(`{self._dump_safe_json(items)}`)}}'
        if activity.title:
            props += f' title="{self._escape_jsx(activity.title)}"'
        heading = activity.title or 'Watch and Repeat'
        return f"### {self._escape_jsx(heading)}\n\n<WatchAndRepeat client:only='react' {props} />"

    def _observe_to_mdx(self, activity: ObserveActivity, is_ukrainian_forced: bool = False) -> str:
        heading = activity.title or activity.instruction or 'Observe'
        props = (
            f"examples={{JSON.parse(`{self._dump_safe_json(activity.examples)}`)}} "
            f"prompt={{{json.dumps(activity.prompt, ensure_ascii=False)}}} "
            f"isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}"
        )
        return f"### {self._escape_jsx(heading)}\n\n<Observe client:only='react' {props} />"

    def _order_to_mdx(self, activity: OrderActivity, is_ukrainian_forced: bool = False) -> str:
        heading = activity.title or activity.instruction or 'Order'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return (
            f"### {self._escape_jsx(heading)}\n\n"
            f"<Order client:only='react' items={{JSON.parse(`{self._dump_safe_json(activity.items)}`)}} "
            f"correct_order={{JSON.parse(`{self._dump_safe_json(activity.correct_order)}`)}}"
            f"{instruction_prop} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"
        )

    def _count_syllables_to_mdx(self, activity: CountSyllablesActivity) -> str:
        heading = activity.title or activity.instruction or 'Count Syllables'
        items = []
        for item in activity.items:
            payload: dict[str, Any] = {'word': item.word, 'correct': item.correct}
            if item.translation:
                payload['translation'] = item.translation
            items.append(payload)
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        max_prop = f' maxCount={{{activity.max_count}}}' if activity.max_count is not None else ''
        return f"### {self._escape_jsx(heading)}\n\n<CountSyllables client:only='react'{instruction_prop} items={{JSON.parse(`{self._dump_safe_json(items)}`)}}{max_prop} />"

    def _divide_words_to_mdx(self, activity: DivideWordsActivity) -> str:
        heading = activity.title or activity.instruction or 'Divide Words'
        items = []
        for item in activity.items:
            payload = {'word': item.word, 'answer': item.answer}
            if item.hint:
                payload['hint'] = item.hint
            items.append(payload)
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(heading)}\n\n<DivideWords client:only='react'{instruction_prop} items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _highlight_morphemes_to_mdx(self, activity: HighlightMorphemesActivity, is_ukrainian_forced: bool = False) -> str:
        heading = activity.title or activity.instruction or 'Highlight Morphemes'
        morphemes = [
            {'word': item.word, 'morpheme': item.morpheme, 'type': item.type}
            for item in activity.morphemes
        ]
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return (
            f"### {self._escape_jsx(heading)}\n\n"
            f"<HighlightMorphemes client:only='react' isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}>\n"
            f"  <HighlightMorphemesActivity{instruction_prop} text={{{json.dumps(activity.text, ensure_ascii=False)}}} "
            f"morphemes={{JSON.parse(`{self._dump_safe_json(morphemes)}`)}} "
            f"isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />\n"
            f"</HighlightMorphemes>"
        )

    def _letter_grid_to_mdx(self, activity: LetterGridActivity) -> str:
        heading = activity.title or 'Letter Grid'
        title_prop = f' title="{self._escape_jsx(activity.title)}"' if activity.title else ''
        return f"### {self._escape_jsx(heading)}\n\n<LetterGrid client:only='react' letters={{JSON.parse(`{self._dump_safe_json(activity.letters)}`)}}{title_prop} />"

    def _odd_one_out_to_mdx(self, activity: OddOneOutActivity) -> str:
        heading = activity.title or activity.instruction or 'Odd One Out'
        items = [
            {'words': item.words, 'correct': item.correct, 'explanation': item.explanation}
            for item in activity.items
        ]
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(heading)}\n\n<OddOneOut client:only='react'{instruction_prop} items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _pick_syllables_to_mdx(self, activity: PickSyllablesActivity) -> str:
        heading = activity.title or activity.instruction or 'Pick Syllables'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        explanation_prop = f' explanation={{{json.dumps(activity.explanation, ensure_ascii=False)}}}' if activity.explanation else ''
        return (
            f"### {self._escape_jsx(heading)}\n\n"
            f"<PickSyllables client:only='react'{instruction_prop} "
            f"syllables={{JSON.parse(`{self._dump_safe_json(activity.syllables)}`)}} "
            f"correctIndices={{JSON.parse(`{self._dump_safe_json(activity.correct_indices)}`)}} "
            f"category={{{json.dumps(activity.category, ensure_ascii=False)}}}{explanation_prop} />"
        )
