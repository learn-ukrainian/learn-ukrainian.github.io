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
from typing import Any, Optional, Union

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
    explanation: Optional[str] = None


@dataclass
class QuizActivity:
    type: str = "quiz"
    title: str = ""
    items: list[QuizItem] = field(default_factory=list)


@dataclass
class SelectItem:
    question: str
    options: list[QuizOption]
    min_correct: Optional[int] = None
    explanation: Optional[str] = None


@dataclass
class SelectActivity:
    type: str = "select"
    title: str = ""
    items: list[SelectItem] = field(default_factory=list)


@dataclass
class TrueFalseItem:
    statement: str
    correct: bool
    explanation: Optional[str] = None


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
    explanation: Optional[str] = None


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
    explanation: Optional[str] = None


@dataclass
class TranslateActivity:
    type: str = "translate"
    title: str = ""
    items: list[TranslateItem] = field(default_factory=list)


@dataclass
class AnagramItem:
    scrambled: str
    answer: str
    hint: Optional[str] = None


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
    """C1-HIST: Structured source criticism using the 5-question method."""
    type: str = "source-evaluation"
    title: str = ""
    instruction: str = ""
    source_text: str = ""
    source_metadata: Optional[SourceMetadata] = None
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
    """C1-HIST: Contested historiographical interpretations."""
    type: str = "debate"
    title: str = ""
    instruction: str = ""
    debate_question: str = ""
    historical_context: str = ""
    positions: list[DebatePosition] = field(default_factory=list)
    analysis_tasks: list[str] = field(default_factory=list)
    model_analysis: str = ""


# Type alias
Activity = Union[
    QuizActivity, SelectActivity, TrueFalseActivity, FillInActivity,
    ClozeActivity, MatchUpActivity, GroupSortActivity, UnjumbleActivity,
    ErrorCorrectionActivity, MarkTheWordsActivity,
    TranslateActivity, AnagramActivity, ReadingActivity,
    EssayResponseActivity, CriticalAnalysisActivity,
    ComparativeStudyActivity, AuthorialIntentActivity,
    SourceEvaluationActivity, DebateActivity,
    EtymologyTraceActivity, GrammarIdentifyActivity
]


@dataclass
class ValidationError:
    path: str
    message: str
    activity_type: Optional[str] = None
    activity_title: Optional[str] = None
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
    def __init__(self, schemas_dir: Optional[Path] = None):
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent.parent / "schemas"
        self.schemas_dir = schemas_dir
        self._schema_cache: dict[str, dict] = {}

    def parse(self, yaml_path: Union[str, Path]) -> list[Activity]:
        yaml_path = Path(yaml_path)
        with open(yaml_path, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
        if raw_data is None: return []
        if isinstance(raw_data, dict) and 'activities' in raw_data:
            raw_data = raw_data['activities']
        if not isinstance(raw_data, list):
            raise ValueError(f"Expected list of activities, got {type(raw_data)}")
        activities = []
        for item in raw_data:
            activity = self._parse_activity(item)
            if activity: activities.append(activity)
        return activities

    def _parse_activity(self, data: dict) -> Optional[Activity]:
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
        }
        parser = parsers.get(activity_type)
        return parser(data) if parser else None

    def _parse_quiz(self, data: dict) -> QuizActivity:
        items = []
        for item_data in data.get('items', []):
            raw_options = item_data.get('options', [])
            correct_answer = item_data.get('answer')
            options = []
            for opt in raw_options:
                if isinstance(opt, str):
                    options.append(QuizOption(text=opt, correct=(opt == correct_answer)))
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
            if correct is None: correct = item_data.get('answer', False)
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
        groups = [GroupSortGroup(name=g['name'], items=g.get('items', [])) for g in data.get('groups', [])]
        return GroupSortActivity(title=data.get('title', ''), groups=groups)

    def _parse_unjumble(self, data: dict) -> UnjumbleActivity:
        items = []
        for item_data in data.get('items', []):
            words = item_data.get('words', [])
            if not words and 'jumbled' in item_data: words = [w.strip() for w in item_data['jumbled'].split('/')]
            if not words and 'prompt' in item_data: words = [w.strip() for w in item_data['prompt'].split('/')]
            if not words and 'scrambled' in item_data: words = [w.strip() for w in item_data['scrambled'].split('/')]
            items.append(UnjumbleItem(words=words, answer=item_data['answer']))
        return UnjumbleActivity(title=data.get('title', ''), items=items)

    def _parse_error_correction(self, data: dict) -> ErrorCorrectionActivity:
        items = [ErrorCorrectionItem(sentence=i['sentence'], error=i['error'], answer=i['answer'], options=i.get('options', []), explanation=i.get('explanation', '')) for i in data.get('items', [])]
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
        items = [AnagramItem(scrambled=i['scrambled'], answer=i['answer'], hint=i.get('hint')) for i in data.get('items', [])]
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
            excerpt=data.get('excerpt', ''),
            questions=data.get('questions', []),
            model_answer=data.get('model_answer', '')
        )

    def _parse_source_evaluation(self, data: dict) -> SourceEvaluationActivity:
        """Parse source-evaluation activity (C1-HIST)."""
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
        """Parse debate activity (C1-HIST)."""
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

    def _escape_jsx(self, text: str) -> str:
        """Escapes characters that break JSX parsing when used as a string literal attribute."""
        if not text: return ""
        if not isinstance(text, str): return str(text)
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
            raise TypeError ("Type %s not serializable" % type(obj))

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
            if mdx: mdx_parts.append(mdx)
        return '\n\n'.join(mdx_parts)

    def _activity_to_mdx(self, activity: Activity, is_ukrainian_forced: bool = False) -> str:
        if isinstance(activity, QuizActivity): return self._quiz_to_mdx(activity)
        if isinstance(activity, SelectActivity): return self._select_to_mdx(activity)
        if isinstance(activity, TrueFalseActivity): return self._true_false_to_mdx(activity)
        if isinstance(activity, FillInActivity): return self._fill_in_to_mdx(activity)
        if isinstance(activity, ClozeActivity): return self._cloze_to_mdx(activity)
        if isinstance(activity, MatchUpActivity): return self._match_up_to_mdx(activity)
        if isinstance(activity, GroupSortActivity): return self._group_sort_to_mdx(activity)
        if isinstance(activity, UnjumbleActivity): return self._unjumble_to_mdx(activity)
        if isinstance(activity, ErrorCorrectionActivity): return self._error_correction_to_mdx(activity)
        if isinstance(activity, MarkTheWordsActivity): return self._mark_the_words_to_mdx(activity)
        if isinstance(activity, TranslateActivity): return self._translate_to_mdx(activity)
        if isinstance(activity, AnagramActivity): return self._anagram_to_mdx(activity)
        if isinstance(activity, ReadingActivity): return self._reading_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, EssayResponseActivity): return self._essay_response_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, CriticalAnalysisActivity): return self._critical_analysis_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, ComparativeStudyActivity): return self._comparative_study_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, AuthorialIntentActivity): return self._authorial_intent_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, SourceEvaluationActivity): return self._source_evaluation_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, DebateActivity): return self._debate_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, EtymologyTraceActivity): return self._etymology_trace_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, GrammarIdentifyActivity): return self._grammar_identify_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, TranscriptionActivity): return self._transcription_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, PaleographyAnalysisActivity): return self._paleography_analysis_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, DialectComparisonActivity): return self._dialect_comparison_to_mdx(activity, is_ukrainian_forced)
        if isinstance(activity, TranslationCritiqueActivity): return self._translation_critique_to_mdx(activity, is_ukrainian_forced)
        return ''

    def _quiz_to_mdx(self, activity: QuizActivity) -> str:
        items = [{'question': str(i.question), 'options': [{'text': str(o.text), 'correct': o.correct} for o in i.options], 'explanation': str(i.explanation) if i.explanation else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Quiz questions={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _select_to_mdx(self, activity: SelectActivity) -> str:
        items = [{'question': str(i.question), 'options': [{'text': str(o.text), 'correct': o.correct} for o in i.options], 'explanation': str(i.explanation) if i.explanation else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Select questions={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _true_false_to_mdx(self, activity: TrueFalseActivity) -> str:
        items = [{'statement': str(i.statement), 'isTrue': i.correct, 'explanation': str(i.explanation) if i.explanation else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<TrueFalse items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _fill_in_to_mdx(self, activity: FillInActivity) -> str:
        items = [{'sentence': str(i.sentence), 'answer': str(i.answer), 'options': [str(opt) for opt in i.options]} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<FillIn items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

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
        return f"### {self._escape_jsx(activity.title)}\n\n<Cloze passage={{{json.dumps(str(passage), ensure_ascii=False)}}} blanks={{JSON.parse(`{self._dump_safe_json(blanks)}`)}} />"

    def _match_up_to_mdx(self, activity: MatchUpActivity) -> str:
        pairs = [{'left': str(p.left), 'right': str(p.right)} for p in activity.pairs]
        return f"### {self._escape_jsx(activity.title)}\n\n<MatchUp pairs={{JSON.parse(`{self._dump_safe_json(pairs)}`)}} />"

    def _group_sort_to_mdx(self, activity: GroupSortActivity) -> str:
        groups = {g.name: g.items for g in activity.groups}
        return f"### {self._escape_jsx(activity.title)}\n\n<GroupSort groups={{JSON.parse(`{self._dump_safe_json(groups)}`)}} />"

    def _unjumble_to_mdx(self, activity: UnjumbleActivity) -> str:
        items = [{'jumbled': ' / '.join(str(w) for w in i.words), 'answer': str(i.answer)} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Unjumble items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _error_correction_to_mdx(self, activity: ErrorCorrectionActivity) -> str:
        items = []
        for i in activity.items:
            opts = self._dump_safe_json([str(opt) for opt in i.options])
            items.append(f'  <ErrorCorrectionItem sentence="{self._escape_jsx(str(i.sentence))}" errorWord="{self._escape_jsx(str(i.error))}" correctForm="{self._escape_jsx(str(i.answer))}" options={{JSON.parse(`{opts}`)}} explanation="{self._escape_jsx(str(i.explanation))}" />')
        return f"### {self._escape_jsx(activity.title)}\n\n<ErrorCorrection>\n{chr(10).join(items)}\n</ErrorCorrection>"

    def _mark_the_words_to_mdx(self, activity: MarkTheWordsActivity) -> str:
        ans = self._dump_safe_json([w for word in activity.answers for w in (str(word).split() if ' ' in str(word) else [str(word)])])
        return f"### {self._escape_jsx(activity.title)}\n\n<MarkTheWords>\n  <MarkTheWordsActivity instruction=\"{self._escape_jsx(str(activity.instruction))}\" text=\"{self._escape_jsx(str(activity.text))}\" correctWords={{JSON.parse(`{ans}`)}} />\n</MarkTheWords>"

    def _translate_to_mdx(self, activity: TranslateActivity) -> str:
        items = [{'source': str(i.source), 'options': [{'text': str(o.text), 'correct': o.correct} for o in i.options]} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Translate questions={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

    def _anagram_to_mdx(self, activity: AnagramActivity) -> str:
        items = [{'scrambled': str(i.scrambled), 'answer': str(i.answer), 'hint': str(i.hint) if i.hint else ''} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<Anagram items={{JSON.parse(`{self._dump_safe_json(items)}`)}} />"

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
                rubric_md = f"\n\n#### Критерії оцінювання\n\n| Критерій | Опис | Бали |\n|---|---|---|\n" + "\n".join(rows)
        else:
            if rows:
                rubric_md = f"\n\n#### Rubric\n\n| Criteria | Description | Points |\n|---|---|---|\n" + "\n".join(rows)
        # Using self._dump_safe_json for complex props might be safer than json.dumps inside {}
        # But here we are passing strings directly, not parsing JSON inside
        # Wait, the original code used json.dumps inside {}
        # prompt={{{json.dumps(activity.prompt)}}}
        # This puts "string" inside {}, resulting in prompt={"string"} which is valid JSX
        # So we don't need _dump_safe_json here, but we DO need to NOT escape quotes inside content
        # json.dumps does escaping correctly for a JS string literal.
        return f"### {self._escape_jsx(activity.title)}\n\n<EssayResponse title=\"{self._escape_jsx(activity.title)}\" prompt={{{json.dumps(activity.prompt, ensure_ascii=False)}}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}} rubric={{{json.dumps(rubric_md, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _reading_to_mdx(self, activity: ReadingActivity, is_ukrainian_forced: bool = False) -> str:
        tasks = self._dump_safe_json(activity.tasks)
        resource = self._dump_safe_json(activity.resource) if activity.resource else '{}'
        # Seminar mode uses text/source; legacy uses context/resource
        text_prop = f' text={{{json.dumps(activity.text, ensure_ascii=False)}}}' if activity.text else ''
        source_prop = f' source={{{json.dumps(activity.source, ensure_ascii=False)}}}' if activity.source else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<ReadingActivity title=\"{self._escape_jsx(activity.title)}\" context=\"{self._escape_jsx(activity.context)}\"{text_prop}{source_prop} resource={{JSON.parse(`{resource}`)}} tasks={{JSON.parse(`{tasks}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _critical_analysis_to_mdx(self, activity: CriticalAnalysisActivity, is_ukrainian_forced: bool = False) -> str:
        # Seminar mode uses targetText/questions/modelAnswers; legacy uses context/question/modelAnswer
        target_text_prop = f' targetText={{{json.dumps(activity.target_text, ensure_ascii=False)}}}' if activity.target_text else ''
        questions_prop = f' questions={{JSON.parse(`{self._dump_safe_json(activity.questions)}`)}}' if activity.questions else ''
        model_answers_prop = f' modelAnswers={{JSON.parse(`{self._dump_safe_json(activity.model_answers)}`)}}' if activity.model_answers else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<CriticalAnalysis title=\"{self._escape_jsx(activity.title)}\" context={{{json.dumps(activity.context, ensure_ascii=False)}}} question={{{json.dumps(activity.question, ensure_ascii=False)}}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}}{target_text_prop}{questions_prop}{model_answers_prop} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _comparative_study_to_mdx(self, activity: ComparativeStudyActivity, is_ukrainian_forced: bool = False) -> str:
        # Seminar mode uses itemsToCompare/criteria/prompt; legacy uses sourceA/sourceB/task
        items_prop = f' itemsToCompare={{JSON.parse(`{self._dump_safe_json(activity.items_to_compare)}`)}}' if activity.items_to_compare else ''
        criteria_prop = f' criteria={{JSON.parse(`{self._dump_safe_json(activity.criteria)}`)}}' if activity.criteria else ''
        prompt_prop = f' prompt={{{json.dumps(activity.prompt, ensure_ascii=False)}}}' if activity.prompt else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<ComparativeStudy title=\"{self._escape_jsx(activity.title)}\" content={{{json.dumps(activity.source_a, ensure_ascii=False)}}} task={{{json.dumps(activity.task, ensure_ascii=False)}}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}}{items_prop}{criteria_prop}{prompt_prop} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _authorial_intent_to_mdx(self, activity: AuthorialIntentActivity, is_ukrainian_forced: bool = False) -> str:
        questions = self._dump_safe_json(activity.questions)
        return f"### {self._escape_jsx(activity.title)}\n\n<AuthorialIntent title=\"{self._escape_jsx(activity.title)}\" excerpt={{{json.dumps(activity.excerpt, ensure_ascii=False)}}} questions={{JSON.parse(`{questions}`)}} modelAnswer={{{json.dumps(activity.model_answer, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _source_evaluation_to_mdx(self, activity: SourceEvaluationActivity, is_ukrainian_forced: bool = False) -> str:
        """Convert source-evaluation activity to SourceEvaluation component (C1-HIST)."""
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

        return f"### {self._escape_jsx(activity.title)}\n\n<SourceEvaluation title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} sourceText={{{json.dumps(activity.source_text, ensure_ascii=False)}}}{metadata_prop}{criteria_prop}{questions_prop} modelEvaluation={{{json.dumps(activity.model_evaluation, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _debate_to_mdx(self, activity: DebateActivity, is_ukrainian_forced: bool = False) -> str:
        """Convert debate activity to Debate component (C1-HIST)."""
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

        return f"### {self._escape_jsx(activity.title)}\n\n<Debate title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} debateQuestion={{{json.dumps(activity.debate_question, ensure_ascii=False)}}}{context_prop} positions={{JSON.parse(`{self._dump_safe_json(positions_data)}`)}}{tasks_prop} modelAnalysis={{{json.dumps(activity.model_analysis, ensure_ascii=False)}}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _etymology_trace_to_mdx(self, activity: EtymologyTraceActivity, is_ukrainian_forced: bool = False) -> str:
        items = [{'word': str(i.word), 'modern': str(i.modern), 'evolution': str(i.evolution)} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<EtymologyTrace title=\"{self._escape_jsx(activity.title)}\" items={{JSON.parse(`{self._dump_safe_json(items)}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _grammar_identify_to_mdx(self, activity: GrammarIdentifyActivity, is_ukrainian_forced: bool = False) -> str:
        items = [{'text': str(i.text), 'form': str(i.form), 'answer': str(i.answer)} for i in activity.items]
        return f"### {self._escape_jsx(activity.title)}\n\n<GrammarIdentify title=\"{self._escape_jsx(activity.title)}\" items={{JSON.parse(`{self._dump_safe_json(items)}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _transcription_to_mdx(self, activity: TranscriptionActivity, is_ukrainian_forced: bool = False) -> str:
        hints = self._dump_safe_json(activity.hints) if activity.hints else '[]'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<Transcription title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} original={{{json.dumps(activity.original, ensure_ascii=False)}}} answer={{{json.dumps(activity.answer, ensure_ascii=False)}}} hints={{JSON.parse(`{hints}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _paleography_analysis_to_mdx(self, activity: PaleographyAnalysisActivity, is_ukrainian_forced: bool = False) -> str:
        hotspots = [{'x': h.x, 'y': h.y, 'label': h.label, 'explanation': h.explanation} for h in activity.hotspots]
        options = self._dump_safe_json(activity.options) if activity.options else '[]'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<PaleographyAnalysis title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} imageUrl={{{json.dumps(activity.image_url, ensure_ascii=False)}}} hotspots={{JSON.parse(`{self._dump_safe_json(hotspots)}`)}} options={{JSON.parse(`{options}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _dialect_comparison_to_mdx(self, activity: DialectComparisonActivity, is_ukrainian_forced: bool = False) -> str:
        features = [{'featureName': f.feature_name, 'valueA': f.value_a, 'valueB': f.value_b, 'explanation': f.explanation} for f in activity.features]
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        label_a_prop = f' labelA={{{json.dumps(activity.label_a, ensure_ascii=False)}}}' if activity.label_a else ''
        label_b_prop = f' labelB={{{json.dumps(activity.label_b, ensure_ascii=False)}}}' if activity.label_b else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<DialectComparison title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} textA={{{json.dumps(activity.text_a, ensure_ascii=False)}}} textB={{{json.dumps(activity.text_b, ensure_ascii=False)}}}{label_a_prop}{label_b_prop} features={{JSON.parse(`{self._dump_safe_json(features)}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"

    def _translation_critique_to_mdx(self, activity: TranslationCritiqueActivity, is_ukrainian_forced: bool = False) -> str:
        translations = [{'translator': t.translator, 'text': t.text, 'accuracyScore': t.accuracy_score, 'notes': t.notes} for t in activity.translations]
        focus_points = self._dump_safe_json(activity.focus_points) if activity.focus_points else '[]'
        instruction_prop = f' instruction={{{json.dumps(activity.instruction, ensure_ascii=False)}}}' if activity.instruction else ''
        return f"### {self._escape_jsx(activity.title)}\n\n<TranslationCritique title=\"{self._escape_jsx(activity.title)}\"{instruction_prop} original={{{json.dumps(activity.original, ensure_ascii=False)}}} translations={{JSON.parse(`{self._dump_safe_json(translations)}`)}} focusPoints={{JSON.parse(`{focus_points}`)}} isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}} />"
