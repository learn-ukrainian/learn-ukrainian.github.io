"""Plan gates for the defects plan reviewers marked checkable (issue #9487).

The full-access plan reviews of A1 positions 1–3 recorded findings that a
script can decide; each cost a review round. These gates decide them from data
the validator already reads — the plan, the module pack (video models and
URLs, quote bytes), the level word store, the arc and the earlier plans — so a
plan with the defect fails before a reviewer is spent. C1–C6 come from the
first reviews, C7–C14 from the second, C15–C20 from the third, C21–C28 from the fourth.

  C1  a declared activity target unknown, introduced after its earliest linking step (else lesson end),
      or outside the lesson's allowed set (failure); dialogue target_grammar and legacy focus candidates (note)
  C2  two or more activities of one lesson carry the same focus text (failure)
  C3  a listening activity whose cited videos model exactly one target, so every item has
      the same key (failure)
  C4  in a letter-stage module, an incidental word none of whose word-store spellings can be
      read with the letters taught through its lesson (failure); a lemma that cannot be read
      while another of its forms can is a note
  C5  a teach-text clause that says a word id is heard, in a step citing no video whose
      models.words lists it (note)
  C6  core records of earlier positions that no recycled list of the module names (note)
  C7  a recap lesson declares no first-person story, or scores its comprehension on another
      host (failure)
  C8  in a recap lesson, an activity other than an unscored presentation is linked before a
      comprehension activity (failure)
  C9  an activity focus names a pack record that no step of its lesson cites as evidence (failure)
  C10 in a letter-stage module, a word a step introduces or uses that cannot be read with the letters taught so
      far and that no recording the lesson cites models (failure); a recycled word that is
      readable only through a recording the step itself does not cite (failure); a lemma that
      cannot be read while another form can (note)
  C11 an odd-one-out row drawn from a quote host without exactly one member differing in the
      stated feature (failure); a feature the gate cannot compute (note)
  C12 a quote host whose bytes carry a private-use code point, a non-Cyrillic symbol inside a
      transcription bracket, a web-address watermark or a word that is neither a word-store
      spelling nor a VESUM form (failure; quote_bytes.py)
  C13 a count-syllables activity whose targets all have the same syllable count (failure); the
      same when the count depends on a form the plan does not bind (note)
  C14 two video entries of one lesson whose pack records are the same recording (failure)
  C15 two adjacent steps of one lesson that display the same text, exercise or example record (failure); the
      same when the second step calls it a recall (note)
  C16 an incidental record named by no step, activity or dialogue of its lesson (note)
  C17 a lesson video whose printed Ресурси description carries pipeline wording, or names a step that does not
      cite the video (failure)
  C18 in a letter-stage module, a declared option with an untaught letter at the activity step (failure,
      no recording exemption); legacy fill-in/quiz focus candidates (note)
  C19 in a letter-stage module, an example sentence cited in a lesson that cannot read it (failure); one first
      cited later than the lesson that could read it (note)
  C20 a cited video that models words but binds no segment (failure)
  C21 non-printable learner_reads refs or absent word selectors (failure); declared learner print with
      untaught letters at the activity step (failure); legacy step/activity directives to the exact print of a record
      holding words with letters not taught by that step (failure); the same when the text says the teacher reads
      the instruction without naming its words and does not bound what the learner reads (note)
  C22 three or more choice activities of one lesson on the same two-member key set (failure); two (note)
  C23 a pick-syllables row that another syllable of the activity in a blanked slot turns into an attested word
      (failure; a note when the focus says the stems carry a cue); an anagram whose letters spell another attested
      word (note)
  C24 a rationale or job that says the lesson recycles a category of word records none of which it recycles (failure)
  C25 a practice step with no practice, need, dialogue or paradigm (failure)
  C26 a declared comprehension target (else a legacy focus W- id) the word store lacks (failure), or a word its quote and recording
      hosts do not hold (failure); the same when a host holds a transcription that may show it, or when the plan
      does not decide it: an ambiguous sentence, an unresolvable or sibling's host (note)
  C27 in a letter-stage module, a letter a step introduces that no recording the lesson cites models (failure); the
      same when the step records the teacher modelling that letter (note)
  C28 a word id a step's teach text names outside the lesson's inventory and the prior learner state (failure)

C29 (#9582) checks A1 core/incidental vocabulary against the words-only reference,
with typed exceptions and class-specific A1 closed-class attestations for inventory-absent words;
advisory until #9541 PR2 sets A1_REFERENCE_ENFORCEMENT to failure. Membership is spelling-based,
so unlabelled reference POS never rejects an inventory member.

Check 7 of #9487 is a learner-state fix (scripts/curriculum/learner_state/planned.py). Check 9 of the
second round is in pack-verify (scripts/curriculum/evidence/sources.py, Standard line numbering).

How exact each gate is:

Activities optionally declare ``targets``, ``options`` and ``learner_reads`` (#9541).
Presence (including an empty array) makes the corresponding field authoritative;
C1/C18/C21/C26 never infer that field from focus prose. Legacy absence keeps the
existing prose path until the PR2 migration. Required/forbidden option policy is
advisory in PR1. Each structured activity is checked at its earliest linking step,
otherwise at lesson end; options have no recording exemption.

- C1 fails unknown, out-of-set or later-introduced ``targets``, for scored and unscored
  types alike. Without ``targets``, focus candidates and dialogue ``target_grammar``
  stay notes with their evidence spans, as in #9487.
- C2 compares focus text after collapsing whitespace.
- C3 applies to an activity whose focus declares its item kind as ``kind: listening``.
  The keys such an activity can have are the targets its cited videos model
  (``models.letters`` and ``models.words`` in the pack; descriptions never establish
  models). One target in all means one key for every item. A cited video without models
  leaves the targets unknown, so the gate does not decide.
- C4 applies where the arc position carries letters (the rule 5 definition of a letter-stage
  module) and from the first lesson that has a taught letter; before it nothing is read,
  so every word is heard. The letters of a word are its Cyrillic letters; an apostrophe is
  not a letter. Incidental entries carry no forms, so the plan does not say which form is
  used: the gate fails only when no spelling of the record is readable.
- C5 is a note because "heard" is read from prose: a clause (split at punctuation and at
  then/before/after) that holds a hearing word (hear, heard, listen, …) and a word id. A
  clause such as "hear Т before reading W-101" would be misread, so a person confirms it;
  making it a failure needs a structured field, which is a plan-schema change.
- C6 is a note by design (#9487): recycling is a pedagogical choice the review makes.
- C7–C8, C11–C13 read the item kind and host an activity focus declares in the writer contract's
  own syntax (``kind: comprehension``, ``host: {kind: quote, ref: T-…}``, or "quote host refs
  T-…"); prose is never read for them. A recap's first-person story (A1 arc D4, plan schema §2b)
  is its dialogue block with exactly one speaker, the narrator: the plan has no other field for
  it. Its side-by-side English is a draft field (``dialogue.translation_en``) the plan cannot
  state. C7 and C8 apply to ``kind: recap`` lessons; a closing-shape (b) recap step is left to the
  plan review (rule 1b already flags that shape).
- C8: in D4 order the story is followed by its questions and then the production task. Every
  activity linked (steps in order, each practice list in order, then consolidation) before a
  comprehension activity must be an ``observe`` activity — the story's display or a recall.
- C9 reads pack ids (``T-``, ``X-``, ``EX-``, ``E-``, ``V-``, ``S-``, ``U-`` …) that exist in the pack,
  and compares them with the union of the lesson's step evidence: the writer receives a lesson's
  records through its steps (R-26), so a record only a focus names never reaches it.
- C10 applies where the arc position carries letters. The letters taught so far at a step are those
  of earlier positions and lessons plus the letters this lesson's steps introduce up to and including
  it. A word is decodable when its lemma is. When only another form of its record is, the plan does
  not bind which form the step uses, so that is a note; with no readable spelling it fails.
  The words of a step are its ``introduces.vocabulary`` and ``uses.vocabulary``.
  A recording is a video whose pack record lists the word in ``models.words``; the lesson cites it
  in ``videos`` or in a step's evidence.
- C11 applies to an ``odd-one-out`` activity, or one whose focus asks for the member that "differs"
  or is "odd", hosted on a quote. A row is a quote line of three or more words and nothing else.
  The feature is read from the focus: initial/first sound, initial/first letter or glyph, final/last letter,
  syllables (or vowel nuclei), letter count. Letters are compared case-folded. A sound is never read from a letter:
  word-initial я ю є ї are [й] and a vowel, щ is [шч], and a consonant's softness comes from the next letter
  (``_initial_sound``); a row with a word whose first sound the spelling does not decide (a cluster, a
  semi-softened consonant) is a note.
- C13 computes the key of every type whose key is a function of the target form alone: at A1 that is
  ``count-syllables`` (the number of vowel letters). Its targets are the word ids its focus names. A
  target's form is the one a cited quote host prints, else the forms its core entry teaches, else
  any form of the record, which makes the outcome a note.
- C12's quote hosts are the records an activity focus declares as its quote host and the quote
  records cited by a step whose ``needs`` holds ``quote`` (the records the preflight treats as
  printable quotes); the preflight runs the same checks on the same hosts (scripts/build/fresh/preflight.py). A
  quote is tokenised composed (NFC), so decomposed bytes are read as the words they spell. When VESUM cannot be
  read, the byte defects are still reported and the lookup is ``vesum_unavailable``: not_checked, and a failure
  under --strict unless the run declares an environment without VESUM (--not-checked-when-unavailable vesum).
- C14 compares a YouTube video by its id, any other URL without its fragment and trailing slash,
  together with ``models.segment``: two segments of one video are two recordings.
- C15 reads a step's displays two ways. A teach-text sentence (split at . ; ! ?) directs a display when
  "display" or "show" (imperative, participle or gerund — never "shows", whose subject is the record) comes
  before a T-/X-/EX- id of the pack and is not negated ("do not display"); and a step prints the text records it
  cites under ``needs: quote`` and the example records it cites under ``needs: example``, as the preflight does.
  Steps are fixed structure (plan schema §7 decision 1: which steps exist, their evidence and practice are
  binding), so a writer cannot merge the two displays: a repeat fails. A repeat the second step's teach text
  calls a recall (recall, again, already displayed, re-display) is a deliberate return and only a note.
- C16 is a note: an incidental word may be writer-optional (plan schema §4 lifts the inventory as a limit). A
  record is named by its W- id or by a spelling of it (lemma or a store form, case-folded, syllable hyphens
  removed) anywhere in the lesson's steps, activities and dialogue, in the bytes of a record the lesson
  displays (C15's displays, an activity's quote host or model, an example's sentence words), or in the
  models.words of a video it cites. A record cited only as grounding is not displayed, so its words do not count.
- C17 lints the description the assembler prints (scripts/build/fresh/assemble.py ``build_resursy_entries``:
  the plan's ``videos[].use``, else the pack record's ``use``, for every video the lesson's steps or videos
  cite). The pipeline wording is the wording the A1 plans and packs actually put there: ``segment:``, ``null``,
  ``driver-owned``, ``timecode``, ``timed (…) segment``, ``acoustic proof`` and record ids (R-27, W-081, T-040,
  G-a1-002). A step reference (``s3``) must name a step of the lesson that cites the video in its evidence.
- C18 reads the Ukrainian words (two or more letters) of a fill-in or quiz focus, from the first lesson that has a
  taught letter (before it nothing is read). A word a recording the lesson cites models (a store record in its
  models.words) is heard, so it passes. Any other word with an untaught letter is a note: the plan has no option
  field, so whether the word is printed option text, a key, a teacher's spoken translation or a word the focus says
  is never printed is not read from the prose. Without ``options`` these candidates stay notes.
  Declared options fail on every untaught letter at the activity step, without recording exemptions.
- C19 applies to example records (EX-) a step cites: the host is the first lesson citing one. The letters
  taught through a lesson are the arc's earlier positions plus this plan's introductions so far (as C4).
- C20 reads the pack: a video whose models.words is not empty and whose models.segment is null. A letter
  video may be a whole resource; a word or phrase model inside a whole episode needs the timed segment.
- C21 fails non-printable ``learner_reads`` refs, selections absent from exact print, and
  untaught letters in declared print at its step. Without the field, C21 reads the sentences that direct
  modelling or reading a record's exact print ("demonstrates the exact print
  in T-…", "models its exact printed source", "models the exact cited T-… forms"); "read the exact T-036 Ко-ло"
  names words of the record, not its print, so it is not read. The print is the record's printable text in the pack
  (quote, text, items_sample); every Cyrillic word of it must be readable with the letters taught by the step (as
  C10; an activity is taken at the step whose practice links it, else the lesson's last step). A recording does not
  help: the directive is about print. Each record is reported once per step. The plan bounds the learner-read print
  in the same text: a clause saying the learner reads named words ("the learner reads only мама") limits the scan
  to them, and words a clause says the teacher reads ("the teacher reads Прочитай") are not learner print unless a
  clause also says the learner reads them (teacher modelling does not remove the learner's decoding). A teacher
  clause reading the instruction or rubric without naming its words, with no learner bound, leaves the untaught
  words possibly the teacher's frame, so that is a note. The failure stands on the record's print, which the pack
  states; the prose only narrows it, and only where it names the words.
- C22 reads a declared key set, "keys Привіт and Добрий день", "keys О, У, И, А", "keys 1 and 2", in a quiz, fill-in,
  true-false, odd-one-out or pick-syllables focus. Two activities on one binary key set can be a recognition and a
  transfer (the plan reviews accepted repeated types with different operations), so two is a note; a third scores
  the same choice again, which is the defect the review found.
- C23 builds the completions of a pick-syllables focus: its rows are the source segmentations it prints (ма-ма,
  По-лі-на) and its blanked rows with a stated key (ма- __ -на has key ли); its syllables are every segment and every
  one-vowel token the focus prints, which is what the activity's one syllable list (writer contract: syllables and
  correctIndices) draws from. The slots are the blanked one, else the positions the focus names before
  "syllable"/"blank" (first, initial, second, middle, final, last), else every slot. A completion is a word-store
  spelling or a VESUM form, looked up in lower case, and capitalised too only when the row's word is a name. An
  anagram's other arrangements (targets of at most seven letters) are mostly rare inflected or archaic forms, so a
  hit is a note. Completions the word store attests are decided without VESUM; when VESUM cannot be read the rest
  are ``vesum_unavailable`` (not_checked, a failure under --strict unless the run declares an environment without
  VESUM).
- C24 reads a rationale or job sentence saying the lesson recycles word records "including" (or "such as") a list.
  Each English word of the list names a category when it equals the head word of store records' gloss_en ("sound",
  "letter"); function words and words describing records do not. A quoted Ukrainian word names its records. The
  claim fails when no record of the category is in the lesson's recycled list, inventory or step vocabulary.
- C25: a ``practice`` step whose practice list is empty and which has no needs, hosts no dialogue and carries no
  paradigm leaves the writer an empty section (steps are fixed structure, plan schema §7 decision 1).
- C26 gives every declared ``targets`` id (otherwise every W- id of a comprehension focus) exactly one outcome;
  the outcomes are a total mapping over the
  ids, so no id can pass unseen. An id the word store lacks fails. A word is held when a spelling of its record is a
  token of a resolvable host quote of the activity (also read with spaces removed, for letter-spaced print) or a
  resolvable host video models it; a held word has no finding. The activity's hosts are those declared outside
  sentences naming another activity: a sentence naming one ("as in b2 (host: {kind: dialogue})") declares that
  activity's host. An unheld word fails when it is named in a plain sentence and every host of the activity is a pack
  quote or a video with models (a note when a host holds a transcription that may show it). Otherwise the plan does
  not decide it, and it is a note quoting the sentence and the reason: the word is named only in a sentence with
  exclusion wording ("do not", "instead of" …, which may exclude it or something else) or naming another activity
  (whose items it may be about), or a host is a dialogue (drafted by the writer) or another unresolvable record, or
  the activity declares no host of its own, or a host is declared in a sentence naming another activity.
- C27 compares each letter a step introduces with the models.letters of every recording the lesson cites
  (case-folded); a teach-text sentence naming the teacher's model or pronunciation and the letter itself is a note.
- C28 compares the W- ids of each teach text with C1's allowed set (the lesson's inventory, its steps' vocabulary,
  earlier lessons and positions' introductions and the base layer); earlier incidentals are not in it.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from itertools import permutations
from pathlib import Path

import yaml

from scripts.practice.euphony_stem_engine import VOWELS as VOWEL_LETTERS

from ..arc.loader import ArcPosition
from . import a1_reference, codes, config, quote_bytes
from .cross import LevelPlans
from .mechanical import Gates, _names_letter, tokens_of
from .pack import Pack, WordStore
from .report import Outcome, Report
from .scope import CYRILLIC_LETTER_CLASS

_LETTER = re.compile(f"[{CYRILLIC_LETTER_CLASS}]")
_WORD_ID = re.compile(r"\bW-\d+\b")
_VIDEO_ID = re.compile(r"\bV-\d+\b")
_LISTENING_KIND = re.compile(r"\bkind:\s*listening\b")
_CLAUSE_BREAK = re.compile(r"[.;:,!?()]|\b(?:then|before|after)\b", re.IGNORECASE)
_HEARING = re.compile(r"\b(?:hear|hears|heard|hearing|listen|listens|listened|listening)\b", re.IGNORECASE)
_PACK_ID = re.compile(r"\b[A-Z][A-Z0-9]*-\d+\b")
_COMPREHENSION_KIND = re.compile(r"\bkind:\s*comprehension\b")
_HOST = quote_bytes.HOST
_QUOTE_HOST_REFS = quote_bytes.QUOTE_HOST_REFS
_ODD_ONE_OUT = re.compile(r"\bodd\b|\bdiffers?\s+from\b", re.IGNORECASE)
_ROW_WORD = f"[{CYRILLIC_LETTER_CLASS}]+(?:['’ʼ-][{CYRILLIC_LETTER_CLASS}]+)*"
_ROW = re.compile(rf"\s*{_ROW_WORD}(?:[\s,;]+{_ROW_WORD}){{2,}}[\s,;.]*")
_ROW_TOKEN = re.compile(_ROW_WORD)
_PRINT_TOKEN = re.compile(r"[^\W_]+(?:['’ʼ-][^\W_]+)*")
_PRINT_SENTENCE_BREAK = re.compile(r"[.!?…]+")
_SENTENCE_BREAK = re.compile(r"[.;!?](?=\s|$)")
#: The evidence span of a prose-read finding is its sentence, kept with its closing punctuation.
_SPAN_BREAK = re.compile(r"(?<=[.;!?])\s+")
#: A display directive: the imperative or participle of display/show (never "X shows Y", where X is the subject).
_DISPLAY = re.compile(r"\b(?:re-?)?(?:display|displayed|displaying|show|shown|showing)\b", re.IGNORECASE)
_NOT_DISPLAY = re.compile(r"\b(?:not|never)\s+(?:\w+\s+){0,2}?(?:re-?)?(?:display|show)", re.IGNORECASE)
_RECALL = re.compile(
    r"\brecall(?:s|ed|ing)?\b|\balready\s+(?:displayed|shown)\b|\bagain\b|\bre-?(?:display|show)", re.IGNORECASE
)
_DISPLAYABLE_ID = re.compile(r"\b(?:T|X|EX)-\d+\b")
_STEP_REF = re.compile(r"\bs\d+\b")
#: Pipeline wording a video description must not carry (C17): (pattern, what it is). Built from the
#: wording the A1 plans and packs actually put in `use` lines, not from a guess.
_PIPELINE_TOKENS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bsegment\s*:", re.IGNORECASE), "the YAML syntax of the pack field models.segment"),
    (re.compile(r"\bnull\b", re.IGNORECASE), "the YAML null literal"),
    (re.compile(r"\bdriver-owned\b", re.IGNORECASE), "fleet role wording"),
    (re.compile(r"\btimecodes?\b", re.IGNORECASE), "pack verification wording"),
    (re.compile(r"\btimed\s+(?:\w+\s+)?segments?\b", re.IGNORECASE), "pack field wording (models.segment)"),
    (re.compile(r"\bacoustic\s+proof\b", re.IGNORECASE), "verification wording"),
    (re.compile(r"\b(?:[A-Z][A-Z0-9]*-\d+|G-[a-z]\d+-\d+)\b"), "a record id"),
)
_CHOICE_TYPES = frozenset({"fill-in", "quiz"})
_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'"})
_YOUTUBE = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
#: C21: a directive to model or read a record's exact print ("demonstrates the exact print in T-…",
#: "models its exact printed source", "models the exact cited T-… forms"); "read the exact T-036 Ко-ло" names words.
_MODELED_PRINT = re.compile(r"\bexact\s+(?:print(?:ed)?|cited)\b", re.IGNORECASE)
#: C22: a declared key set, "keys Привіт and Добрий день", "keys О, У, И, А", "keys 1 and 2", "keys CV and VC".
_KEY_ITEM = rf"(?:[{CYRILLIC_LETTER_CLASS}]+(?:\s[{CYRILLIC_LETTER_CLASS}]+)?|\d+|[A-Z]{{1,3}})"
_KEY_SEPARATOR = r"\s*,\s*(?:and\s+)?|\s+and\s+|\s*/\s*"
_KEY_SET = re.compile(rf"\bkeys\s+({_KEY_ITEM}(?:(?:{_KEY_SEPARATOR}){_KEY_ITEM})+)(?![{CYRILLIC_LETTER_CLASS}\w])")
_KEY_SPLIT = re.compile(_KEY_SEPARATOR)
_KEYED_CHOICE_TYPES = frozenset({"quiz", "fill-in", "true-false", "odd-one-out", "pick-syllables"})
#: C23: a source segmentation or blanked row (ма-ма, По-лі-на, ма- __ -на, __ -ва) and the key a blanked row states.
_SYLLABLE_OR_BLANK = rf"(?:[{CYRILLIC_LETTER_CLASS}]+|_{{2,}})"
_SEGMENTED = re.compile(
    rf"(?<![{CYRILLIC_LETTER_CLASS}_]){_SYLLABLE_OR_BLANK}(?:[ \t]*-[ \t]*{_SYLLABLE_OR_BLANK})+(?![{CYRILLIC_LETTER_CLASS}_])"
)
_BLANK = re.compile(r"_{2,}")
_BLANK_KEY = re.compile(rf"\s+has\s+key\s+([{CYRILLIC_LETTER_CLASS}]+)")
_SLOT = r"(?:first|initial|second|middle|final|last)"
_SLOT_WORDS: tuple[tuple[re.Pattern[str], int | str], ...] = tuple(
    (
        re.compile(
            rf"\b(?:{word})\b(?:\s+(?:or|and)\s+{_SLOT})*\s+(?:missing\s+)?(?:syllables?|blanks?|slots?)\b"
            rf"|\b{_SLOT}\s+(?:or|and)\s+(?:{word})\s+(?:missing\s+)?(?:syllables?|blanks?|slots?)\b",
            re.IGNORECASE,
        ),
        index,
    )
    for word, index in (("first|initial", 0), ("second", 1), ("middle", "middle"), ("final|last", -1))
)
_CUE = re.compile(r"\b(?:gloss(?:es|ed)?|pictures?|pictured|images?|illustrations?|target cue)\b", re.IGNORECASE)
_LETTER_RUN = re.compile(f"[{CYRILLIC_LETTER_CLASS}]+")
#: An anagram of more letters has too many arrangements to look up; A1 anagram targets are short.
_ANAGRAM_MAX_LETTERS = 7
#: C24: a rationale or job sentence saying the lesson recycles word records "including" (or "such as") a list.
_RECYCLE_LIST = re.compile(
    r"\brecycl\w*\b[^.;]*?\b(?:words?|records?|vocabulary|lemmas?)\b[^.;]*?\b(?:including|such as)\s+(.+)",
    re.IGNORECASE,
)
_ENGLISH_WORD = re.compile(r"[A-Za-z]+")
_GLOSS_HEAD = re.compile(r"[(,;]")
#: Words of a recycle claim that name no category of records: words describing records, and function words
#: (the store glosses conjunctions and pronouns, so "and" would match і, та, а).
_META_TERMS = frozenset(
    {"word", "record", "form", "item", "term", "category", "lemma", "vocabulary", "label"}
    | {"and", "or", "the", "a", "an", "of", "for", "with", "to", "in", "on", "by", "as", "its", "their", "all"}
    | {"both", "other", "some", "such", "this", "that", "these", "those", "previously", "taught", "earlier"}
)
#: C26: exclusion wording in a focus sentence ("do not reuse those four words here"); its ids only note.
_EXCLUDING = re.compile(r"\b(?:do not|don't|never|exclude[sd]?|excluding|must not|instead of)\b", re.IGNORECASE)
_STRESS_MARKS = re.compile("[̀́]")
_ACTIVITY_REF = re.compile(r"\b[a-z]\d+\b")
_LETTER_SPACED = re.compile(
    rf"(?<![{CYRILLIC_LETTER_CLASS}])[{CYRILLIC_LETTER_CLASS}](?: [{CYRILLIC_LETTER_CLASS}])+(?![{CYRILLIC_LETTER_CLASS}])"
)
#: C27: a teach-text sentence recording the teacher's model of a letter (the letter must stand in the sentence).
_TEACHER_MODEL = re.compile(
    r"\bteacher\b[^.;]*\b(?:models?|modell?ing|pronounc\w*|demonstrat\w*)\b"
    r"|\b(?:models?|pronounc\w*|demonstrat\w*)\b[^.;]*\bteacher\b",
    re.IGNORECASE,
)
#: C21: a clause bounding what the learner reads ("the learner reads only мама") and one saying the teacher reads
#: (or says) words of the print; a teacher clause naming the instruction or rubric without its words is a frame.
_READING_CLAUSE = re.compile(r"[.;,!?]|\b(?:while|whereas|but|and then)\b", re.IGNORECASE)
_LEARNER_READS = re.compile(r"\b(?:learners?|students?|pupils?|children)\b.*?\bread(?:s|ing)?\b", re.IGNORECASE)
_TEACHER_READS = re.compile(r"\bteacher\b.*?\b(?:reads?|reading|says?|voices?)\b", re.IGNORECASE)
_FRAME_WORDING = re.compile(
    r"\b(?:instructions?|rubrics?|headings?|prompts?|task wording|frame words?)\b", re.IGNORECASE
)
#: C11: letters whose consonant has a soft pair (Ukrainian д т з с ц л н р дз); before я ю є ь і it is soft.
_SOFT_PAIRED = frozenset({"д", "т", "з", "с", "ц", "л", "н", "р", "дз"})
_HARD_VOWEL_LETTERS = frozenset("аоуеи")
_SOFTENING_LETTERS = frozenset("яюєьі")
_IOTATED = frozenset("яюєї")
_APOSTROPHE_CHARACTERS = frozenset("'’ʼ")


def _nfc(text: str) -> str:
    """Pack text as the gates tokenise it: composed, so a decomposed й or ї stays one letter."""
    return unicodedata.normalize("NFC", text)


def _initial_sound(word: str) -> str | None:
    """The first sound of a word where its spelling decides it, else None (C11).

    Word-initial я ю є ї spell two sounds, [й] and a vowel, and щ spells [шч] (5th-grade textbooks
    5-klas-ukrmova-zabolotnyi-2023_s0063, 5-klas-ukrmova-golub-2022_s0077); дж and дз at the start of a word are
    one sound. A consonant before а о у е и or an apostrophe is hard; a consonant with a soft pair before я ю є ь і
    is soft ([р′] in рік). The other cases (a cluster, whose first consonant may assimilate, and a consonant
    without a soft pair before я ю є ь і, which is semi-softened) are not computed."""
    text = _nfc(word).casefold()
    if not text or not _LETTER.match(text):
        return None
    first = text[0]
    if first in _IOTATED or first == "й":
        return "й"
    if first in VOWEL_LETTERS:
        return first
    if first == "щ":
        return "ш"
    unit = text[:2] if text[:2] in ("дж", "дз") else first
    following = text[len(unit) : len(unit) + 1]
    if following in _HARD_VOWEL_LETTERS or following in _APOSTROPHE_CHARACTERS:
        return unit
    if following in _SOFTENING_LETTERS and unit in _SOFT_PAIRED:
        return f"{unit}′"
    return None


def _span(text: str, token: str, pattern: re.Pattern[str]) -> str:
    """The evidence span of a prose-read finding: the sentence of text holding token, quoted («…»).

    The sentence is the one where pattern (the pattern that found token) matches token whole, never as a substring:
    W-201 is not found inside W-2010, nor ма inside мама."""
    sentence = next((part for part in _SPAN_BREAK.split(text) if token in pattern.findall(part)), text)
    return f"«{_normalized(sentence)}»"


def _reading_bounds(text: str) -> tuple[set[str] | None, set[str], bool]:
    """(the words a clause bounds the learner's reading to, or None; the words a clause says the teacher reads and
    no clause says the learner reads; whether a teacher clause reads the instruction or rubric without naming its
    words) for C21. Teacher modelling does not remove the learner's decoding: a word both read stays learner print."""
    learner: set[str] | None = None
    teacher: set[str] = set()
    frame = False
    for clause in _READING_CLAUSE.split(text or ""):
        words = {token.casefold() for token in _ROW_TOKEN.findall(clause)}
        if _LEARNER_READS.search(clause) and words:
            learner = (learner or set()) | words
        elif _TEACHER_READS.search(clause):
            teacher |= words
            frame = frame or (not words and bool(_FRAME_WORDING.search(clause)))
    return learner, teacher - (learner or set()), frame


def _vowel_count(text: str) -> int:
    return sum(1 for char in text.casefold() if char in VOWEL_LETTERS)


def _word_letters(text: str) -> list[str]:
    return [letter.casefold() for letter in _LETTER.findall(text)]


#: Odd-one-out features a focus can state and the gate can compute (C11): pattern, name, value of a word (None: the
#: gate does not compute it for that word).
_FEATURES: tuple[tuple[re.Pattern[str], str, Callable[[str], object]], ...] = (
    (re.compile(r"\b(?:initial|first)\s+sounds?\b", re.IGNORECASE), "initial sound", _initial_sound),
    (
        re.compile(r"\b(?:initial|first)\s+(?:glyph|letter)s?\b", re.IGNORECASE),
        "initial letter",
        lambda word: _word_letters(word)[0],
    ),
    (
        re.compile(r"\b(?:final|last)\s+(?:glyph|letter)s?\b", re.IGNORECASE),
        "final letter",
        lambda word: _word_letters(word)[-1],
    ),
    (re.compile(r"\bsyllables?\b|\bvowel nuclei\b", re.IGNORECASE), "syllable count", _vowel_count),
    (
        re.compile(r"\bletter count\b|\bnumber of letters\b|\blength\b", re.IGNORECASE),
        "letter count",
        lambda word: len(_word_letters(word)),
    ),
)

#: Activity types whose every item's key is a function of its target form alone (C13).
_COMPUTED_KEYS: dict[str, tuple[str, Callable[[str], object]]] = {"count-syllables": ("syllable count", _vowel_count)}


def _ids(pattern: re.Pattern[str], text: str) -> list[str]:
    """The ids pattern finds in text, in order, once each."""
    return list(dict.fromkeys(pattern.findall(text or "")))


def _normalized(text: str) -> str:
    return " ".join((text or "").split())


def _host(focus: str) -> tuple[str, str | None] | None:
    """The (kind, ref) host an activity focus declares, in the writer contract's syntax."""
    match = _HOST.search(focus)
    if match:
        return match.group(1), match.group(2)
    match = _QUOTE_HOST_REFS.search(focus)
    if match:
        return "quote", _ids(re.compile(r"T-\d+"), match.group(1))[0]
    return None


_quote_host_refs = quote_bytes.quote_host_refs


def _host_label(host: tuple[str, str | None]) -> str:
    """A declared host as a C26 message names it: its record id, or its kind when it names none ({kind: dialogue})."""
    kind, ref = host
    return ref or kind


@dataclass(frozen=True)
class _C26Context:
    """What C26 reads from one comprehension focus, shared by the outcome of each of its W- ids."""

    focus: str
    #: (sentence, why it is ambiguous: "" for a plain sentence) for each sentence of the focus.
    sentences: list[tuple[str, str]]
    #: The activity's own declared hosts, as a message names them.
    where: str
    #: Word ids the activity's resolvable recordings model.
    modelled: set[str]
    #: The text of the activity's resolvable quote hosts.
    quotes: list[str]
    #: Why the activity's host set does not decide a word it does not hold ([] when it does).
    host_gaps: list[str]


#: C26 outcome codes in report order, each with the ending of its message ({where}: the activity's own hosts; {gaps}:
#: why they do not decide a word they do not hold); the first two fail the run.
_C26_REPORTS: tuple[tuple[str, str], ...] = (
    (
        codes.COMPREHENSION_TARGET_UNKNOWN,
        ", which the level word store does not hold; a comprehension item asks about a word record, so name one the "
        "store holds",
    ),
    (
        codes.COMPREHENSION_TARGET_NOT_IN_HOST,
        ", which no host ({where}) prints or models; a comprehension item is answered from its host, so host it on a "
        "record that holds the word",
    ),
    (
        codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED,
        ", which no host ({where}) prints in spelling; a host holds a transcription, so the plan review confirms the "
        "host shows each word the items ask about",
    ),
    (
        codes.COMPREHENSION_TARGET_UNVERIFIED,
        ", whose presence in the host ({where}) is unverified{gaps}; whether this activity's items ask about the word, or what "
        "its host holds, is not read from the plan, so the plan review confirms every word the items ask about is in "
        "the host",
    ),
)
_C26_FAILURES = frozenset({codes.COMPREHENSION_TARGET_UNKNOWN, codes.COMPREHENSION_TARGET_NOT_IN_HOST})


def _linked(lesson: dict) -> list[tuple[int, int, str]]:
    """(step index, slot, activity id) in presentation order; consolidation counts as one more step."""
    steps = lesson["steps"]
    linked = [
        (index, slot, item) for index, step in enumerate(steps) for slot, item in enumerate(step.get("practice") or [])
    ]
    linked += [(len(steps), slot, item) for slot, item in enumerate(lesson.get("consolidation") or [])]
    return linked


def _shown_rows(rows: list[tuple[str, list[str]]]) -> str:
    shown = "; ".join(" ".join(words) for _ref, words in rows[:3])
    return shown + (f"; … {len(rows) - 3} more rows" if len(rows) > 3 else "")


def _video_key(url: str, segment: str | None) -> tuple[str, str | None]:
    match = _YOUTUBE.search(url)
    if match:
        return f"youtube:{match.group(1)}", segment
    return url.split("#", 1)[0].rstrip("/").casefold(), segment


def _displays(step: dict, displayable: set[str], printed: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    """(records the step displays, records its teach text calls a recall) for C15 and C16.

    A step displays a record when a teach-text sentence directs its display (display/show before the id,
    not negated) or when it cites the record under a need the preflight prints: a text record of a
    ``quote`` step, an example record of an ``example`` step (``printed`` maps the need to those ids)."""
    shown, recalled = set(), set()
    for sentence in _SENTENCE_BREAK.split(step.get("teach") or ""):
        refs = [ref for ref in _ids(_DISPLAYABLE_ID, sentence) if ref in displayable]
        directive = _DISPLAY.search(sentence)
        if directive and not _NOT_DISPLAY.search(sentence):
            first: dict[str, int] = {}  # each id's first whole occurrence (T-01 is not found inside T-010)
            for match in _DISPLAYABLE_ID.finditer(sentence):
                first.setdefault(match.group(0), match.start())
            shown |= {ref for ref in refs if first[ref] > directive.start()}
        if _RECALL.search(sentence):
            recalled |= set(refs)
    for need in step.get("needs") or []:
        shown |= {ref for ref in step.get("evidence") or [] if ref in printed.get(need, set())}
    return shown, recalled


def _strings(value: object) -> list[str]:
    """Every string inside a plan value (a mapping, list or scalar), in order."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return []


def _print_holds(text: str, spelling: str, *, exact: bool = False) -> bool:
    """Match a complete word or formula as a contiguous token run in printed text.

    Selectors preserve NFC spelling and case; word-record host matching folds case,
    apostrophes and syllable hyphens, and also accepts letter-spaced host print.
    Whitespace, including line wrapping, separates tokens without breaking a run;
    sentence-final punctuation breaks it. Non-NFC exact selectors are rejected.
    """
    if exact and _nfc(spelling) != spelling:
        return False
    normalize = (lambda value: value) if exact else _spelling
    # Latin text/numbers interrupt a run too; they cannot disappear between Cyrillic words.
    wanted = [normalize(token) for token in _PRINT_TOKEN.findall(_nfc(spelling))]
    if not wanted:
        return False
    text = _nfc(text)
    variants = (text,) if exact else (text, _LETTER_SPACED.sub(lambda match: match.group(0).replace(" ", ""), text))
    for variant in variants:
        for sentence in _PRINT_SENTENCE_BREAK.split(variant):
            tokens = [normalize(token) for token in _PRINT_TOKEN.findall(sentence)]
            if any(tokens[i : i + len(wanted)] == wanted for i in range(len(tokens) - len(wanted) + 1)):
                return True
    return False


def _spelling(text: str) -> str:
    """A spelling as C16 compares it: case-folded, one apostrophe, syllable hyphens removed."""
    return text.translate(_APOSTROPHES).casefold().replace("-", "")


@dataclass
class ReviewGates(Gates):
    pack: Pack = field(kw_only=True)
    #: --strict: a lookup the run could not make fails the run instead of being reported as not_checked.
    strict: bool = field(default=False, kw_only=True)
    #: --not-checked-when-unavailable vesum: the run declares an environment without VESUM (the CI runner), so an
    #: undecided lookup stays a not_checked line under --strict too, and says why.
    vesum_declared_unavailable: bool = field(default=False, kw_only=True)

    def fail(self, code: str, message: str, lesson: int | None, step: str | None = None) -> None:
        self.report.failures.append(Outcome(code, message, lesson, step))

    def lookup_unavailable(self, rule: str, detail: str) -> None:
        """VESUM could not be read: the gate's lookup outcome is unknown, never a pass.

        Outside --strict it is a not_checked line; --strict (plan-promote) needs every gate decided, so
        there it fails the run, unless the run declared an environment without VESUM. Findings the gate decided from
        local evidence are reported before this."""
        message = f"gate {rule} is undecided because VESUM is unavailable: {detail}"
        if self.vesum_declared_unavailable:
            message += " (declared by --not-checked-when-unavailable vesum)"
        outcome = Outcome(codes.VESUM_UNAVAILABLE, message)
        failing = self.strict and not self.vesum_declared_unavailable
        (self.report.failures if failing else self.report.not_checked).append(outcome)

    @staticmethod
    def _activity_step(lesson: dict, activity_id: str) -> str | None:
        """Earliest linking step, otherwise the lesson end, including unlinked activities."""
        return next(
            (step["id"] for step in lesson["steps"] if activity_id in (step.get("practice") or [])),
            lesson["steps"][-1]["id"] if lesson["steps"] else None,
        )

    # -- C1 -------------------------------------------------------------------

    def check_named_before_introduction(self) -> None:
        for index, lesson in enumerate(self.plan["lessons"]):
            steps = lesson["steps"]
            order = {step["id"]: position for position, step in enumerate(steps)}
            introduced_at: dict[str, int] = {}
            for position, step in enumerate(steps):
                for item in (step.get("introduces") or {}).get("vocabulary") or []:
                    introduced_at.setdefault(item, position)
            activities: dict[str, dict] = {}
            for activity in lesson.get("activities") or []:
                activities.setdefault(activity["id"], activity)  # a duplicate id is duplicate_activity_id (rule 6)

            sources: list[tuple[str, int, str]] = []  # (what names the ids, step position, text)
            dialogue = lesson.get("dialogue") or {}
            if dialogue.get("step") in order and dialogue.get("target_grammar"):
                sources.append(
                    (
                        f"the dialogue's target_grammar (dialogue step {dialogue['step']})",
                        order[dialogue["step"]],
                        dialogue["target_grammar"],
                    )
                )
            for position, step in enumerate(steps):
                for activity_id in step.get("practice") or []:
                    if activity_id in activities and "targets" not in activities[activity_id]:
                        sources.append(
                            (
                                f"activity {activity_id} focus (practice of step {step['id']})",
                                position,
                                activities[activity_id]["focus"],
                            )
                        )

            allowed: set[str] | None = None
            for activity in activities.values():
                if "targets" not in activity:
                    continue
                step_id = self._activity_step(lesson, activity["id"])
                position = order.get(step_id, len(steps))
                for item in activity["targets"]:
                    reason = None
                    if item not in self.store.records:
                        reason = "the level word store does not hold it"
                    elif introduced_at.get(item, -1) > position:
                        reason = f"step {steps[introduced_at[item]]['id']} introduces it later"
                    else:
                        if allowed is None:
                            allowed = self.allowed_ids(index, "C1")
                        if allowed is not None and item not in allowed:
                            reason = "it is outside the lesson's allowed set"
                    if reason:
                        self.fail(
                            codes.TARGET_NOT_AVAILABLE,
                            f"activity {activity['id']} targets {item}: {reason} (#9541 C1)",
                            lesson["n"],
                            step_id,
                        )
            for where, position, text in sources:
                later, unknown = [], []
                for item in _ids(_WORD_ID, text):
                    if item in introduced_at:
                        if introduced_at[item] > position:
                            later.append(
                                f"{item} (introduced by step {steps[introduced_at[item]]['id']}) in "
                                f"{_span(text, item, _WORD_ID)}"
                            )
                        continue
                    if allowed is None:
                        allowed = self.allowed_ids(index, "C1")
                        if allowed is None:
                            return
                    if item not in allowed:
                        unknown.append(f"{item} in {_span(text, item, _WORD_ID)}")
                step_id = steps[position]["id"]
                if later:
                    self.note(
                        codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED,
                        f"{where} names {'; '.join(later)}, which a later step of this lesson introduces; the text is "
                        "prose, so whether it presents or scores the word or keeps it out is not read from it, and the "
                        "plan review confirms a word is introduced at or before the step that presents or scores it "
                        "(#9487 C1)",
                        lesson["n"],
                        step_id,
                    )
                if unknown:
                    self.note(
                        codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED,
                        f"{where} names {'; '.join(unknown)}, which no step up to {step_id} introduces and which is "
                        "outside the lesson's allowed set (earlier lessons and positions, base layer, incidental, "
                        "recycled, dialogue names); the text is prose, so whether it presents or scores the word is not "
                        "read from it, and the plan review confirms (#9487 C1)",
                        lesson["n"],
                        step_id,
                    )

    # -- C2 -------------------------------------------------------------------

    def check_duplicate_focus(self) -> None:
        for lesson in self.plan["lessons"]:
            by_focus: dict[str, list[str]] = {}
            for activity in lesson.get("activities") or []:
                by_focus.setdefault(_normalized(activity["focus"]), []).append(activity["id"])
            for focus, activity_ids in by_focus.items():
                if len(activity_ids) > 1:
                    self.fail(
                        codes.DUPLICATE_ACTIVITY_FOCUS,
                        f"activities {', '.join(activity_ids)} carry the same focus text {focus[:80]!r}"
                        f"{'…' if len(focus) > 80 else ''}; each activity states its own operation (#9487 C2)",
                        lesson["n"],
                    )

    # -- C3 -------------------------------------------------------------------

    def check_listening_single_key(self) -> None:
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                if not _LISTENING_KIND.search(activity["focus"]):
                    continue
                videos = _ids(_VIDEO_ID, activity["focus"])
                if not videos or any(video not in self.pack.video_models for video in videos):
                    continue  # targets unknown: no cited video, or a cited video without models
                targets = {
                    *(f"letter {letter}" for video in videos for letter in self.pack.video_models[video].letters),
                    *(f"word {word}" for video in videos for word in self.pack.video_models[video].words),
                }
                if len(targets) == 1:
                    self.fail(
                        codes.LISTENING_QUIZ_SINGLE_KEY,
                        f"listening activity {activity['id']} cites {', '.join(videos)}, which together model "
                        f"only {next(iter(targets))}; every item has that one key (#9487 C3)",
                        lesson["n"],
                    )

    # -- C4 -------------------------------------------------------------------

    def check_incidental_decodable(self) -> None:
        lessons = [lesson for lesson in self.plan["lessons"] if lesson["inventory"]["vocabulary"]["incidental"]]
        if not lessons:
            return
        through = self.letter_state_or_skip("C4", True)
        if through is None:
            return  # not a letter-stage module, or its arc is unavailable (skipped above)
        for lesson in lessons:
            taught = through.get(lesson["n"], set())
            if not taught:
                continue  # before the first taught letter nothing is read
            for entry in lesson["inventory"]["vocabulary"]["incidental"]:
                record = self.store.records.get(entry["evidence"])
                spellings = [entry["lemma"], *(record.form_texts if record else ())]
                readable = [text for text in dict.fromkeys(spellings) if self._readable(text, taught)]
                if entry["lemma"] in readable:
                    continue
                untaught = sorted({letter for letter in self._letters(entry["lemma"]) if letter not in taught})
                if not readable:
                    self.fail(
                        codes.INCIDENTAL_NOT_DECODABLE,
                        f"incidental {entry['evidence']} ({entry['lemma']!r}) needs {', '.join(untaught)}, not taught "
                        f"through lesson {lesson['n']}, and no spelling of its word record is readable with the "
                        "taught letters (#9487 C4)",
                        lesson["n"],
                    )
                else:
                    self.note(
                        codes.INCIDENTAL_LEMMA_NOT_DECODABLE,
                        f"incidental lemma {entry['lemma']!r} ({entry['evidence']}) needs {', '.join(untaught)}, not "
                        f"taught through lesson {lesson['n']}; readable forms: {', '.join(readable)}; the plan does "
                        "not bind the form, so the plan review confirms it (#9487 C4)",
                        lesson["n"],
                    )

    @staticmethod
    def _letters(text: str) -> set[str]:
        return {letter.casefold() for letter in _LETTER.findall(text)}

    @classmethod
    def _readable(cls, text: str, taught: set[str]) -> bool:
        return cls._letters(text) <= taught

    # -- C5 -------------------------------------------------------------------

    def check_heard_words(self) -> None:
        for lesson in self.plan["lessons"]:
            for step in lesson["steps"]:
                heard = list(
                    dict.fromkeys(
                        item
                        for clause in _CLAUSE_BREAK.split(step.get("teach") or "")
                        if clause and _HEARING.search(clause)
                        for item in _ids(_WORD_ID, clause)
                    )
                )
                videos = [item for item in step.get("evidence") or [] if item.startswith("V-")]
                modelled = {
                    word
                    for video in videos
                    if video in self.pack.video_models
                    for word in self.pack.video_models[video].words
                }
                missing = [item for item in heard if item not in modelled]
                if missing:
                    self.note(
                        codes.HEARD_WORD_WITHOUT_VIDEO,
                        f"the teach text says {', '.join(missing)} {'is' if len(missing) == 1 else 'are'} heard, "
                        f"but no video the step cites ({', '.join(videos) or 'none'}) lists "
                        f"{'it' if len(missing) == 1 else 'them'} in models.words; the clause is read from prose, "
                        "so the plan review confirms it (#9487 C5)",
                        lesson["n"],
                        step["id"],
                    )

    # -- C6 -------------------------------------------------------------------

    def check_earlier_core_recycled(self) -> None:
        position = self.plan["arc_ref"]["position"]
        if position <= 1:
            return
        missing = [p for p in range(1, position) if p not in self.level_plans.by_position]
        if missing:
            self.skip("C6", "earlier arc positions " + ", ".join(map(str, missing)) + " have no plan file")
            return
        earlier: dict[str, int] = {}
        for prior in range(1, position):
            for lesson in self.level_plans.by_position[prior][1].get("lessons") or []:
                vocabulary = ((lesson or {}).get("inventory") or {}).get("vocabulary") or {}
                for entry in vocabulary.get("core") or []:
                    if isinstance(entry, dict) and isinstance(entry.get("evidence"), str):
                        earlier.setdefault(entry["evidence"], prior)
        recycled = {item for lesson in self.plan["lessons"] for item in lesson["inventory"]["vocabulary"]["recycled"]}
        absent = sorted(set(earlier) - recycled)
        if absent:
            listed = ", ".join(
                f"{item} {self.store.records[item].lemma!r} (position {earlier[item]})"
                if item in self.store.records
                else f"{item} (position {earlier[item]})"
                for item in absent
            )
            self.note(
                codes.EARLIER_CORE_NOT_RECYCLED,
                f"{len(absent)} of {len(earlier)} core records of earlier positions appear in no recycled list "
                f"of this module: {listed} (#9487 C6)",
                None,
            )

    # -- second round: C7–C14 ------------------------------------------------------------

    def _comprehension(self, lesson: dict) -> list[dict]:
        return [a for a in lesson.get("activities") or [] if _COMPREHENSION_KIND.search(a["focus"])]

    # -- C7 -------------------------------------------------------------------

    def check_recap_story(self) -> None:
        for lesson in self.plan["lessons"]:
            if lesson["kind"] != "recap":
                continue
            dialogue = lesson.get("dialogue")
            speakers = (dialogue or {}).get("speakers") or []
            if dialogue is None or len(speakers) != 1:
                found = "no dialogue block" if dialogue is None else f"a dialogue with {len(speakers)} speakers"
                self.fail(
                    codes.RECAP_STORY_MISSING,
                    f"the recap declares no first-person story: it has {found}; a recap is one short first-person "
                    "story side by side in Ukrainian and English, declared as a dialogue block with one speaker, "
                    "the narrator (A1 arc D4, plan schema §2b) (#9487 C7)",
                    lesson["n"],
                )
            comprehension = self._comprehension(lesson)
            if not comprehension:
                self.fail(
                    codes.RECAP_COMPREHENSION_NOT_ON_STORY,
                    "no activity of the recap declares kind: comprehension; the recap asks Ukrainian-only "
                    "questions about its story (A1 arc D4) (#9487 C7)",
                    lesson["n"],
                )
            for activity in comprehension:
                host = _host(activity["focus"])
                if host is None or host[0] != "dialogue":
                    declared = (
                        "no host" if host is None else f"host kind {host[0]}" + (f" ({host[1]})" if host[1] else "")
                    )
                    self.fail(
                        codes.RECAP_COMPREHENSION_NOT_ON_STORY,
                        f"comprehension activity {activity['id']} declares {declared}; a recap's scored comprehension "
                        "is hosted on its first-person story block (host: {kind: dialogue}) (#9487 C7)",
                        lesson["n"],
                    )

    # -- C8 -------------------------------------------------------------------

    def check_recap_order(self) -> None:
        for lesson in self.plan["lessons"]:
            if lesson["kind"] != "recap":
                continue
            activities = {a["id"]: a for a in reversed(lesson.get("activities") or [])}
            comprehension = {a["id"] for a in self._comprehension(lesson)}
            linked = _linked(lesson)
            for index, (step_index, _slot, activity_id) in enumerate(linked):
                if activity_id not in comprehension:
                    continue
                before = [
                    f"{item} ({activities[item]['type']})"
                    for _s, _t, item in linked[:index]
                    if item in activities and item not in comprehension and activities[item]["type"] != "observe"
                ]
                if before:
                    steps = lesson["steps"]
                    where = steps[step_index]["id"] if step_index < len(steps) else "consolidation"
                    self.fail(
                        codes.RECAP_COMPREHENSION_AFTER_PRODUCTION,
                        f"comprehension activity {activity_id} (linked in {where}) comes after "
                        f"{', '.join(dict.fromkeys(before))}; in a recap the story's questions come before the "
                        "production task, and only an unscored observe (the story's display or a recall) precedes "
                        "them (A1 arc D4) (#9487 C8)",
                        lesson["n"],
                        steps[step_index]["id"] if step_index < len(steps) else None,
                    )

    # -- C9 -------------------------------------------------------------------

    def check_focus_evidence(self) -> None:
        for lesson in self.plan["lessons"]:
            cited = {item for step in lesson["steps"] for item in step.get("evidence") or []}
            for activity in lesson.get("activities") or []:
                own = {activity.get("model"), *(activity.get("error_refs") or [])}
                missing = [
                    item
                    for item in _ids(_PACK_ID, activity["focus"])
                    if not item.startswith("W-") and item in self.pack.ids and item not in cited and item not in own
                ]
                if missing:
                    self.fail(
                        codes.FOCUS_EVIDENCE_NOT_IN_STEPS,
                        f"activity {activity['id']} focus names {', '.join(missing)}, which no step of this lesson "
                        "cites as evidence and which is not the activity's model or error_refs; the writer receives "
                        "only the records the lesson cites (R-26) (#9487 C9)",
                        lesson["n"],
                    )

    # -- C10 ------------------------------------------------------------------

    @cached_property
    def taught_before(self) -> dict[int, set[str]] | None:
        """Letters taught before each lesson starts, or None outside a letter stage."""
        through = self.taught_through
        if through is None:
            return None
        position = self.plan["arc_ref"]["position"]
        before = {letter.casefold() for e in self.arc or [] if e.position < position for letter in e.letters or []}
        state: dict[int, set[str]] = {}
        for lesson in self.plan["lessons"]:
            state[lesson["n"]] = set(before)
            before = set(through[lesson["n"]])
        return state

    def _modelled(self, video_ids: list[str]) -> set[str]:
        return {
            word
            for video in video_ids
            if video in self.pack.video_models
            for word in self.pack.video_models[video].words
        }

    def check_step_words_decodable(self) -> None:
        cyrillic = any(
            _LETTER.search(record.lemma)
            for lesson in self.plan["lessons"]
            for step in lesson["steps"]
            for key in ("introduces", "uses")
            for item in (step.get(key) or {}).get("vocabulary") or []
            if (record := self.store.records.get(item)) is not None
        )
        if self.letter_state_or_skip("C10", cyrillic) is None or self.taught_before is None:
            return
        for lesson in self.plan["lessons"]:
            lesson_videos = [video["evidence"] for video in lesson.get("videos") or []]
            lesson_videos += [
                item for step in lesson["steps"] for item in step.get("evidence") or [] if item.startswith("V-")
            ]
            lesson_modelled = self._modelled(lesson_videos)
            recycled = set(lesson["inventory"]["vocabulary"]["recycled"])
            taught = set(self.taught_before[lesson["n"]])
            for step in lesson["steps"]:
                taught |= {letter.casefold() for letter in (step.get("introduces") or {}).get("letters") or []}
                step_modelled = self._modelled([item for item in step.get("evidence") or [] if item.startswith("V-")])
                unreadable, in_print, lemma_only = [], [], []
                shown = (step.get("introduces") or {}).get("vocabulary") or []
                shown = list(dict.fromkeys([*shown, *((step.get("uses") or {}).get("vocabulary") or [])]))
                for item in shown:
                    record = self.store.records.get(item)
                    if record is None:
                        continue  # unknown_word_id (rule 3)
                    spellings = [record.lemma, *record.form_texts]
                    untaught = ", ".join(sorted(set(self._letters(record.lemma)) - taught))
                    readable = [text for text in dict.fromkeys(spellings) if self._readable(text, taught)]
                    if record.lemma in readable or item in step_modelled:
                        continue
                    if readable:
                        if item not in lesson_modelled:
                            lemma_only.append(
                                f"{item} {record.lemma!r} (needs {untaught}; readable: {', '.join(readable[:4])})"
                            )
                        continue
                    if item not in lesson_modelled:
                        unreadable.append(f"{item} {record.lemma!r} (needs {untaught})")
                    elif item in recycled:
                        in_print.append(f"{item} {record.lemma!r} (needs {untaught})")
                if unreadable:
                    self.fail(
                        codes.STEP_WORD_NOT_DECODABLE,
                        f"step {step['id']} introduces or uses {', '.join(unreadable)}: no spelling is readable with the letters "
                        "taught so far and no recording the lesson cites models it (#9487 C10)",
                        lesson["n"],
                        step["id"],
                    )
                if lemma_only:
                    self.note(
                        codes.STEP_WORD_LEMMA_NOT_DECODABLE,
                        f"step {step['id']} introduces or uses {', '.join(lemma_only)}: the lemma needs letters not taught so far "
                        "and no recording the lesson cites models it, while another form is readable; the plan does "
                        "not bind the form, so the plan review confirms it (#9487 C10)",
                        lesson["n"],
                        step["id"],
                    )
                if in_print:
                    self.fail(
                        codes.RECYCLED_WORD_NOT_DECODABLE_IN_PRINT,
                        f"step {step['id']} recycles {', '.join(in_print)}: not readable with the letters taught so "
                        "far, and the recording that models it is not cited by this step, so the step meets it in "
                        "print (#9487 C10)",
                        lesson["n"],
                        step["id"],
                    )

    # -- C11 ------------------------------------------------------------------

    def check_odd_one_out_rows(self) -> None:
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                focus = activity["focus"]
                if activity["type"] != "odd-one-out" and not _ODD_ONE_OUT.search(focus):
                    continue
                refs = [ref for ref in _quote_host_refs(focus) if ref in self.pack.quotes]
                rows = [
                    (ref, _ROW_TOKEN.findall(line))
                    for ref in refs
                    for line in _nfc(self.pack.quotes[ref]).splitlines()
                    if _ROW.fullmatch(line)
                ]
                if not rows:
                    continue
                feature = next((entry for entry in _FEATURES if entry[0].search(focus)), None)
                if feature is None:
                    self.note(
                        codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED,
                        f"activity {activity['id']} draws odd-one-out rows from {', '.join(refs)} "
                        f"({_shown_rows(rows)}), and its focus states no feature the "
                        "gate computes (initial or final letter, syllables, letter count); the plan review confirms "
                        "each row has exactly one odd member (#9487 C11)",
                        lesson["n"],
                    )
                    continue
                _pattern, name, value = feature
                for ref, words in rows:
                    values = [value(word) for word in words]
                    if None in values:
                        unknown = ", ".join(word for word, val in zip(words, values, strict=True) if val is None)
                        self.note(
                            codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED,
                            f"activity {activity['id']} row {' '.join(words)!r} of {ref}: the gate does not compute "
                            f"the {name} of {unknown} (a consonant cluster, or a semi-softened consonant), so the plan "
                            "review confirms the row has exactly one odd member (#9487 C11)",
                            lesson["n"],
                        )
                        continue
                    counts = Counter(values)
                    if len(counts) == 2 and min(counts.values()) == 1:
                        continue
                    shown = ", ".join(f"{word} ({val})" for word, val in zip(words, values, strict=True))
                    self.fail(
                        codes.ODD_ONE_OUT_ROW_INVALID,
                        f"activity {activity['id']} row {' '.join(words)!r} of {ref} does not have exactly one member "
                        f"differing in {name}: {shown} (#9487 C11)",
                        lesson["n"],
                    )

    # -- C12 ------------------------------------------------------------------

    def check_quote_host_bytes(self, lookup: Callable[[list[str]], set[str]] | None = None) -> None:
        hosts: dict[str, list[str]] = {}  # ref -> where it hosts
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                for ref in _quote_host_refs(activity["focus"]):
                    if ref in self.pack.quotes:
                        hosts.setdefault(ref, []).append(f"lesson {lesson['n']} {activity['id']}")
            for step in lesson["steps"]:
                if "quote" in (step.get("needs") or []):
                    for ref in step.get("evidence") or []:
                        if ref in self.pack.quotes:
                            hosts.setdefault(ref, []).append(f"lesson {lesson['n']} step {step['id']}")
        if not hosts:
            return
        for ref, where in hosts.items():
            for defect in quote_bytes.byte_defects(self.pack.quotes[ref]):
                self.fail(
                    _QUOTE_CODES[defect.kind],
                    f"quote host {ref} (hosting {', '.join(where)}) carries {defect.kind.replace('_', ' ')}: "
                    f"{defect.detail}; the engine prints quote bytes exactly (#9487 C12)",
                    None,
                )
        tokens = {ref: quote_bytes.word_tokens(self.pack.quotes[ref]) for ref in hosts}
        known = quote_bytes.known_spellings(
            text for record in self.store.records.values() for text in (record.lemma, *record.form_texts)
        )
        try:
            unknown = set(
                quote_bytes.unknown_words(
                    [token for ref_tokens in tokens.values() for token in ref_tokens],
                    known,
                    lookup or quote_bytes.vesum_lookup,
                )
            )
        except quote_bytes.VesumUnavailable as error:
            self.lookup_unavailable(
                "C12", f"quote-host words outside the word store are not looked up ({', '.join(hosts)}): {error}"
            )
            return
        for ref, ref_tokens in tokens.items():
            words = [token.surface for token in ref_tokens if token.surface in unknown]
            if words:
                self.fail(
                    codes.QUOTE_HOST_TOKEN_NOT_IN_VESUM,
                    f"quote host {ref} (hosting {', '.join(hosts[ref])}) prints {', '.join(map(repr, words))}, which "
                    "are neither word-store spellings nor VESUM forms: an OCR fragment, a split word, or a word VESUM "
                    "does not list (#9487 C12)",
                    None,
                )

    # -- C13 ------------------------------------------------------------------

    @cached_property
    def _core_forms(self) -> dict[str, set[str]]:
        """Word id -> the form tags core entries of this and earlier plans teach."""
        plans = [self.plan] + [
            self.level_plans.by_position[p][1]
            for p in range(1, self.plan["arc_ref"]["position"])
            if p in self.level_plans.by_position
        ]
        forms: dict[str, set[str]] = {}
        for plan in plans:
            for lesson in plan.get("lessons") or []:
                for entry in (((lesson or {}).get("inventory") or {}).get("vocabulary") or {}).get("core") or []:
                    if isinstance(entry, dict) and isinstance(entry.get("evidence"), str):
                        forms.setdefault(entry["evidence"], set()).update(entry.get("forms") or [])
        return forms

    def check_computed_key(self) -> None:
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                if activity["type"] not in _COMPUTED_KEYS:
                    continue
                name, key = _COMPUTED_KEYS[activity["type"]]
                targets = [item for item in _ids(_WORD_ID, activity["focus"]) if item in self.store.records]
                if not targets:
                    continue
                printed = {
                    token.casefold()
                    for ref in _ids(re.compile(r"\bT-\d+\b"), activity["focus"])
                    if ref in self.pack.quotes
                    for token in _ROW_TOKEN.findall(_nfc(self.pack.quotes[ref]))
                }
                bound, unbound = {}, {}
                for item in targets:
                    record = self.store.records[item]
                    spellings = [record.lemma, *record.form_texts]
                    source = [text for text in spellings if text.casefold() in printed]
                    taught = [text for tag, text in record.tagged_forms if tag in self._core_forms.get(item, set())]
                    if source or taught:
                        bound[item] = {key(text) for text in source or taught}
                    else:
                        unbound[item] = ({key(record.lemma)}, {key(text) for text in spellings})
                least = set().union(*bound.values(), *(lemma for lemma, _all in unbound.values()))
                most = set().union(*bound.values(), *(every for _lemma, every in unbound.values()))
                if len(most) == 1:
                    self.fail(
                        codes.COMPUTED_KEY_SINGLE_VALUE,
                        f"{activity['type']} activity {activity['id']} targets {', '.join(targets)}, whose {name} is "
                        f"{next(iter(most))} for every target, so every item has the same key (#9487 C13)",
                        lesson["n"],
                    )
                elif len(least) == 1:
                    self.note(
                        codes.COMPUTED_KEY_FORM_DEPENDENT,
                        f"{activity['type']} activity {activity['id']} targets {', '.join(targets)}: their bound forms "
                        f"and lemmas all have {name} {next(iter(least))}; another key needs a form the plan does not "
                        f"bind ({', '.join(unbound)}), so the plan review confirms the keys vary (#9487 C13)",
                        lesson["n"],
                    )

    # -- C14 ------------------------------------------------------------------

    def check_duplicate_videos(self) -> None:
        for lesson in self.plan["lessons"]:
            groups: dict[tuple[str, str | None], list[str]] = {}
            for entry in lesson.get("videos") or []:
                source = self.pack.video_sources.get(entry["evidence"])
                if source is not None:
                    groups.setdefault(_video_key(*source), []).append(entry["evidence"])
            for (identity, segment), video_ids in groups.items():
                if len(video_ids) > 1:
                    self.fail(
                        codes.DUPLICATE_LESSON_VIDEO,
                        f"video entries {', '.join(video_ids)} resolve to one recording ({identity}"
                        f"{', segment ' + segment if segment else ', whole video'}); the page would embed it "
                        f"{len(video_ids)} times (#9487 C14)",
                        lesson["n"],
                    )

    # -- third round: C15–C20 ------------------------------------------------------------

    # -- C15 ------------------------------------------------------------------

    @cached_property
    def _display_inputs(self) -> tuple[set[str], dict[str, set[str]]]:
        displayable = {ref for ref in self.pack.ids if _DISPLAYABLE_ID.fullmatch(ref)}
        return displayable, {"quote": set(self.pack.quotes), "example": set(self.pack.examples)}

    def check_adjacent_display(self) -> None:
        for lesson in self.plan["lessons"]:
            previous: tuple[str, set[str]] | None = None
            for step in lesson["steps"]:
                shown, recalled = _displays(step, *self._display_inputs)
                if previous is not None:
                    prior_id, prior_shown = previous
                    repeated = [ref for ref in sorted(prior_shown & shown) if ref not in recalled]
                    recall = sorted(prior_shown & shown & recalled)
                    if repeated:
                        self.fail(
                            codes.ADJACENT_STEP_SAME_DISPLAY,
                            f"steps {prior_id} and {step['id']} both display {', '.join(repeated)}; steps and their "
                            "evidence are binding (plan schema §7 decision 1), so the writer prints the same record "
                            "twice in a row; keep one display step and drop the directive from the other (#9487 C15)",
                            lesson["n"],
                            step["id"],
                        )
                    if recall:
                        self.note(
                            codes.ADJACENT_STEP_DISPLAY_RECALL,
                            f"steps {prior_id} and {step['id']} both display {', '.join(recall)}, and {step['id']} calls "
                            "it a recall; the plan review confirms the repeat is intended (#9487 C15)",
                            lesson["n"],
                            step["id"],
                        )
                previous = (step["id"], shown)

    # -- C16 ------------------------------------------------------------------

    def check_incidental_used(self) -> None:
        for lesson in self.plan["lessons"]:
            incidental = lesson["inventory"]["vocabulary"]["incidental"]
            if not incidental:
                continue
            named = _strings([lesson["steps"], lesson.get("activities"), lesson.get("dialogue")])
            shown = {ref for step in lesson["steps"] for ref in _displays(step, *self._display_inputs)[0]}
            for activity in lesson.get("activities") or []:
                shown |= {activity.get("model"), *_quote_host_refs(activity["focus"])}
            for item in shown:
                if item in self.pack.record_texts:
                    named.append(_nfc(self.pack.record_texts[item]))
                named += self.pack.examples.get(item, ("", ()))[1]
            videos = [entry["evidence"] for entry in lesson.get("videos") or []]
            videos += [item for step in lesson["steps"] for item in step.get("evidence") or [] if item.startswith("V-")]
            named += sorted(self._modelled(videos))
            text = "\n".join(named)
            ids = set(_ids(_WORD_ID, text))
            spellings = {_spelling(token) for token in _ROW_TOKEN.findall(text)}
            unused = []
            for entry in incidental:
                record = self.store.records.get(entry["evidence"])
                forms = {_spelling(form) for form in (entry["lemma"], *(record.form_texts if record else ()))}
                if entry["evidence"] not in ids and not forms & spellings:
                    unused.append(f"{entry['evidence']} {entry['lemma']!r}")
            if unused:
                self.note(
                    codes.INCIDENTAL_NOT_USED,
                    f"{len(unused)} incidental record{'s' if len(unused) > 1 else ''} named by no step, activity or "
                    f"dialogue of the lesson, nor in a record it displays or a recording it cites: {', '.join(unused)}; Словник lists every "
                    "incidental, so learners would get cards for words the lesson does not use (#9487 C16)",
                    lesson["n"],
                )

    # -- C17 ------------------------------------------------------------------

    def check_video_descriptions(self) -> None:
        for lesson in self.plan["lessons"]:
            steps = {step["id"]: step for step in lesson["steps"]}
            uses = {entry["evidence"]: entry.get("use") or "" for entry in lesson.get("videos") or []}
            cited = [
                item
                for step in lesson["steps"]
                for item in [*(step.get("evidence") or []), *(step.get("explains") or []), step.get("ref")]
                if isinstance(item, str) and item.startswith("V-")
            ]
            for video in dict.fromkeys([*cited, *uses]):
                description = uses.get(video) or self.pack.video_uses.get(video, "")
                source = "videos[].use" if uses.get(video) else "the pack record's use"
                found = [
                    f"{match.group(0)!r} ({what})"
                    for pattern, what in _PIPELINE_TOKENS
                    for match in [pattern.search(description)]
                    if match
                ]
                if found:
                    self.fail(
                        codes.VIDEO_USE_PIPELINE_TOKEN,
                        f"the Ресурси description of {video} ({source}: {description!r}) carries pipeline wording: "
                        f"{', '.join(found)}; the assembler prints it to the learner (#9487 C17)",
                        lesson["n"],
                    )
                wrong = [
                    ref
                    for ref in _ids(_STEP_REF, description)
                    if ref not in steps or video not in (steps[ref].get("evidence") or [])
                ]
                if wrong:
                    self.fail(
                        codes.VIDEO_USE_STEP_MISMATCH,
                        f"the Ресурси description of {video} ({source}) names step {', '.join(wrong)}, which "
                        f"{'does' if len(wrong) == 1 else 'do'} not cite {video} in its evidence (#9487 C17)",
                        lesson["n"],
                    )

    # -- C18 ------------------------------------------------------------------

    def check_choice_options_taught(self) -> None:
        lessons = [
            lesson
            for lesson in self.plan["lessons"]
            if any(
                "options" in activity
                or (
                    activity["type"] in _CHOICE_TYPES
                    and any(len(_word_letters(token)) >= 2 for token in _ROW_TOKEN.findall(activity["focus"]))
                )
                for activity in lesson.get("activities") or []
            )
        ]
        if not lessons or self.letter_state_or_skip("C18", True) is None:
            return  # no choice focus prints a word, or not a letter stage (or its arc is unavailable)
        for lesson in lessons:
            taught = self.taught_through[lesson["n"]]
            videos = [entry["evidence"] for entry in lesson.get("videos") or []]
            videos += [item for step in lesson["steps"] for item in step.get("evidence") or [] if item.startswith("V-")]
            modelled = self._modelled(videos)
            taught_at = self._taught_at_steps(lesson)
            for activity in lesson.get("activities") or []:
                if "options" in activity:
                    step_id = self._activity_step(lesson, activity["id"])
                    at = taught_at.get(step_id, taught)
                    missing = [option for option in activity["options"] if not self._readable(option, at)]
                    if missing:
                        self.fail(
                            codes.CHOICE_OPTION_NOT_DECODABLE,
                            f"activity {activity['id']} options {self._needs(missing, at)} need untaught "
                            f"letters at step {step_id}; recordings do not exempt print (#9541 C18)",
                            lesson["n"],
                            step_id,
                        )
                    continue
                if not taught or activity["type"] not in _CHOICE_TYPES:
                    continue
                focus = _nfc(activity["focus"])
                words = [
                    token
                    for token in dict.fromkeys(_ROW_TOKEN.findall(focus))
                    if len(_word_letters(token)) >= 2
                    and not self._readable(token, taught)
                    and not self.index.get(token.translate(_APOSTROPHES).casefold(), set()) & modelled
                ]
                if words:
                    self.note(
                        codes.CHOICE_OPTION_UNVERIFIED,
                        f"{activity['type']} activity {activity['id']} focus names "
                        f"{'; '.join(f'{self._needs([word], taught)} in {_span(focus, word, _ROW_TOKEN)}' for word in words)}: "
                        f"letters not taught through lesson {lesson['n']}, and no recording the lesson cites models "
                        "the word; the plan has no option field and the focus is prose, so whether the learner sees "
                        "the word as an option or key is not read from it, and the plan review confirms no printed "
                        "option needs an untaught letter (#9487 C18)",
                        lesson["n"],
                    )

    def _needs(self, words: list[str], taught: set[str]) -> str:
        return ", ".join(f"{word!r} (needs {', '.join(sorted(self._letters(word) - taught))})" for word in words)

    # -- C19 ------------------------------------------------------------------

    def check_sentence_decodability(self) -> None:
        hosts: dict[str, int] = {}
        for lesson in self.plan["lessons"]:
            for step in lesson["steps"]:
                for item in step.get("evidence") or []:
                    if item in self.pack.examples:
                        hosts.setdefault(item, lesson["n"])
        if not hosts or self.letter_state_or_skip("C19", True) is None or self.taught_before is None:
            return
        first_lesson = self.plan["lessons"][0]["n"]
        for item, host in hosts.items():
            text = self.pack.examples[item][0]
            letters = self._letters(text)
            missing = sorted(letters - self.taught_through[host])
            if missing:
                self.fail(
                    codes.SENTENCE_NOT_DECODABLE_AT_HOST,
                    f"example {item} ({text!r}) is cited in lesson {host} and needs {', '.join(missing)}, not taught "
                    "through that lesson (#9487 C19)",
                    host,
                )
                continue
            if letters <= self.taught_before[first_lesson]:
                earliest = "before this module"
            else:
                earliest = next(
                    (f"from lesson {n}" for n, taught in self.taught_through.items() if letters <= taught), None
                )
            if earliest is not None and earliest != f"from lesson {host}":
                self.note(
                    codes.SENTENCE_DECODABLE_EARLIER,
                    f"example {item} ({text!r}) is cited first in lesson {host} but is decodable {earliest}; the "
                    "plan review confirms the placement and any rationale tying it to this lesson's letters "
                    "(#9487 C19)",
                    host,
                )

    # -- C20 ------------------------------------------------------------------

    def check_word_model_segments(self) -> None:
        for lesson in self.plan["lessons"]:
            videos = [entry["evidence"] for entry in lesson.get("videos") or []]
            videos += [item for step in lesson["steps"] for item in step.get("evidence") or [] if item.startswith("V-")]
            for video in dict.fromkeys(videos):
                models = self.pack.video_models.get(video)
                if models is None or not models.words:
                    continue
                if models.segment is None:
                    self.fail(
                        codes.WORD_MODEL_WITHOUT_SEGMENT,
                        f"{video} models {', '.join(models.words)} (words or phrases, not a whole-resource letter) "
                        "but binds no models.segment, so the learner is sent to the whole recording; the pack binds "
                        "the timed segment that models them (#9487 C20)",
                        lesson["n"],
                    )

    # -- fourth round: C21–C28 -----------------------------------------------------------

    def _taught_at_steps(self, lesson: dict) -> dict[str, set[str]]:
        """Letters taught at each step of a letter-stage lesson: earlier lessons plus this lesson's steps so far."""
        taught = set((self.taught_before or {}).get(lesson["n"], set()))
        at: dict[str, set[str]] = {}
        for step in lesson["steps"]:
            taught |= {letter.casefold() for letter in (step.get("introduces") or {}).get("letters") or []}
            at[step["id"]] = set(taught)
        return at

    def _lesson_videos(self, lesson: dict) -> list[str]:
        videos = [entry["evidence"] for entry in lesson.get("videos") or []]
        videos += [item for step in lesson["steps"] for item in step.get("evidence") or [] if item.startswith("V-")]
        return list(dict.fromkeys(videos))

    # -- C21 ------------------------------------------------------------------

    def check_modeled_print_decodable(self) -> None:
        declared: list[tuple[dict, dict, str, list[str]]] = []
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                for selection in activity.get("learner_reads", []):
                    ref = selection if isinstance(selection, str) else selection["ref"]
                    step_id = self._activity_step(lesson, activity["id"])
                    if ref not in self.pack.record_texts:
                        self.fail(
                            codes.LEARNER_READ_REF_NOT_PRINTABLE,
                            f"activity {activity['id']} learner_reads {ref}: no printable pack text (#9541 C21)",
                            lesson["n"],
                            step_id,
                        )
                        continue
                    text = _STRESS_MARKS.sub("", _nfc(self.pack.record_texts[ref]))
                    words = _ROW_TOKEN.findall(text) if isinstance(selection, str) else selection["words"]
                    if isinstance(selection, dict):
                        for word in words:
                            if not _print_holds(text, word, exact=True):
                                self.fail(
                                    codes.LEARNER_READ_WORD_NOT_IN_PRINT,
                                    f"activity {activity['id']} learner_reads {ref}: {word!r} is not in its "
                                    "exact print (#9541 C21)",
                                    lesson["n"],
                                    step_id,
                                )
                    declared.append((lesson, activity, ref, words))
        directed = any(
            _MODELED_PRINT.search(text)
            for lesson in self.plan["lessons"]
            for text in [
                *(step.get("teach") or "" for step in lesson["steps"]),
                *(activity["focus"] for activity in lesson.get("activities", []) if "learner_reads" not in activity),
            ]
        )
        if not (directed or declared) or self.letter_state_or_skip("C21", True) is None or self.taught_before is None:
            return
        for lesson, activity, ref, words in declared:
            step_id = self._activity_step(lesson, activity["id"])
            taught = self._taught_at_steps(lesson).get(step_id, self.taught_through[lesson["n"]])
            missing = [word for word in words if not self._readable(word, taught)]
            if missing:
                self.fail(
                    codes.MODELED_PRINT_NOT_DECODABLE,
                    f"activity {activity['id']} learner_reads {ref}: {self._needs(missing, taught)} needs "
                    f"untaught letters at step {step_id} (#9541 C21)",
                    lesson["n"],
                    step_id,
                )
        for lesson in self.plan["lessons"]:
            taught_at = self._taught_at_steps(lesson)
            sources = [
                (f"step {step['id']} teach text", step["id"], step.get("teach") or "") for step in lesson["steps"]
            ]
            sources += [
                (f"activity {activity['id']} focus", self._activity_step(lesson, activity["id"]), activity["focus"])
                for activity in lesson.get("activities") or []
                if "learner_reads" not in activity
            ]
            reported: set[tuple[str, str]] = set()  # (step, record): an activity repeating its step's list adds nothing
            for where, step_id, text in sources:
                if step_id is None:
                    continue
                refs = [
                    ref
                    for sentence in _SENTENCE_BREAK.split(text)
                    if _MODELED_PRINT.search(sentence)
                    for ref in _ids(_DISPLAYABLE_ID, sentence)
                    if ref in self.pack.record_texts and (step_id, ref) not in reported
                ]
                reported |= {(step_id, ref) for ref in refs}
                taught = taught_at[step_id]
                learner, teacher, frame = _reading_bounds(text)
                found = []
                for ref in dict.fromkeys(refs):
                    words = [
                        token
                        for token in dict.fromkeys(_ROW_TOKEN.findall(_nfc(self.pack.record_texts[ref])))
                        if not self._readable(token, taught)
                        and (learner is None or token.casefold() in learner)
                        and token.casefold() not in teacher
                    ]
                    if words:
                        needs = sorted(set().union(*(self._letters(word) for word in words)) - taught)
                        shown = ", ".join(words[:5]) + (f", … {len(words) - 5} more" if len(words) > 5 else "")
                        found.append(f"{ref} ({shown}; needs {', '.join(needs)})")
                if found and frame and learner is None:
                    self.note(
                        codes.MODELED_PRINT_TEACHER_FRAME,
                        f"{where} directs modelling or reading the exact print of {'; '.join(found)}: letters not "
                        f"taught by step {step_id}; the text says the teacher reads the instruction without naming "
                        "its words or bounding what the learner reads, so the plan review confirms the untaught "
                        "words are the teacher-read frame (#9487 C21)",
                        lesson["n"],
                        step_id,
                    )
                elif found:
                    self.fail(
                        codes.MODELED_PRINT_NOT_DECODABLE,
                        f"{where} directs modelling or reading the exact print of {'; '.join(found)}: letters not "
                        f"taught by step {step_id}, so the learner reads untaught letters from print; limit the "
                        "modelled print to taught forms or keep the record explains-only (#9487 C21)",
                        lesson["n"],
                        step_id,
                    )

    # -- C22 ------------------------------------------------------------------

    def check_choice_key_sets(self) -> None:
        for lesson in self.plan["lessons"]:
            groups: dict[frozenset[str], list[str]] = {}
            for activity in lesson.get("activities") or []:
                if activity["type"] not in _KEYED_CHOICE_TYPES:
                    continue
                for match in _KEY_SET.finditer(activity["focus"]):
                    keys = frozenset(_normalized(item).casefold() for item in _KEY_SPLIT.split(match.group(1)))
                    if len(keys) == 2:
                        groups.setdefault(keys, [])
                        if activity["id"] not in groups[keys]:
                            groups[keys].append(activity["id"])
            for keys, activity_ids in groups.items():
                if len(activity_ids) < 2:
                    continue
                shown = " / ".join(sorted(keys))
                if len(activity_ids) >= 3:
                    self.fail(
                        codes.CHOICE_BINARY_KEYS_REPEATED,
                        f"choice activities {', '.join(activity_ids)} all declare the two keys {shown}: the lesson "
                        "scores one binary choice three or more times; give the repeats a different operation or "
                        "key set (#9487 C22)",
                        lesson["n"],
                    )
                else:
                    self.note(
                        codes.CHOICE_BINARY_KEYS_SHARED,
                        f"choice activities {', '.join(activity_ids)} both declare the two keys {shown}; the plan "
                        "review confirms their operations differ (#9487 C22)",
                        lesson["n"],
                    )

    # -- C23 ------------------------------------------------------------------

    def check_construction_distractors(self, lookup: Callable[[list[str]], set[str]] | None = None) -> None:
        candidates: list[tuple[dict, dict, list[tuple[str, str, str]]]] = []  # lesson, activity, (shown, made, key)
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                if activity["type"] == "pick-syllables":
                    made = _syllable_swaps(activity["focus"])
                elif activity["type"] == "anagram":
                    made = self._anagram_swaps(activity["focus"])
                else:
                    continue
                if made:
                    candidates.append((lesson, activity, made))
        if not candidates:
            return
        records = self.store.records.values()
        known = {_spelling(text) for record in records for text in (record.lemma, *record.form_texts)}
        # A completion is looked up as a common word; as a name too only when its target is a name (Павлик, Поліна),
        # so a surname or first name VESUM lists (Зиза, Коко) does not count against a common-word row.
        names = {_spelling(record.lemma) for record in records if record.lemma[:1].isupper()}
        variants = {
            variant
            for _l, _a, swaps in candidates
            for _s, made, key in swaps
            if made not in known
            for variant in ((made, made.capitalize()) if key in names else (made,))
        }
        # Completions the word store attests are decided from local evidence; an unreadable VESUM leaves only the
        # others undecided, which is reported after them.
        unavailable: quote_bytes.VesumUnavailable | None = None
        try:
            attested = (lookup or quote_bytes.vesum_lookup)(sorted(variants)) if variants else set()
        except quote_bytes.VesumUnavailable as error:
            attested, unavailable = set(), error
        attested = {word.casefold() for word in attested} | known
        for lesson, activity, swaps in candidates:
            hits = list(dict.fromkeys(f"{shown} → {made}" for shown, made, key in swaps if made in attested))
            if not hits:
                continue
            what = "row" if activity["type"] == "pick-syllables" else "letter set"
            if activity["type"] == "anagram":
                self.note(
                    codes.ANAGRAM_LETTERS_FORM_OTHER_WORD,
                    f"anagram activity {activity['id']}: the letters also spell {'; '.join(hits)}, VESUM or word-store "
                    "forms; most such arrangements are rare inflected or archaic forms no learner builds, so the plan "
                    "review confirms none is a word an A1 learner could build in its place (#9487 C23)",
                    lesson["n"],
                )
                continue
            if _CUE.search(activity["focus"]):
                self.note(
                    codes.CONSTRUCTION_DISTRACTOR_CUED,
                    f"{activity['type']} activity {activity['id']}: another completion of a {what} forms an attested "
                    f"word ({'; '.join(hits)}); the focus says the stems carry a cue, so the plan review confirms it "
                    "selects the key (#9487 C23)",
                    lesson["n"],
                )
                continue
            self.fail(
                codes.CONSTRUCTION_DISTRACTOR_FORMS_WORD,
                f"pick-syllables activity {activity['id']}: another syllable of the activity in a blanked slot forms a "
                f"word-store spelling or VESUM form ({'; '.join(hits)}), so a learner who builds that real word is "
                "marked wrong; cue each stem's target (gloss, picture) or use syllables that form no attested word "
                "(#9487 C23)",
                lesson["n"],
            )
        if unavailable is not None:
            self.lookup_unavailable(
                "C23",
                f"constructed completions outside the word store are not looked up ({len(variants)} spellings); "
                f"completions the word store attests are decided: {unavailable}",
            )

    def _anagram_swaps(self, focus: str) -> list[tuple[str, str, str]]:
        """(target, another arrangement of its letters, target) for each anagram target of the focus."""
        swaps = []
        for item in _ids(_WORD_ID, focus):
            record = self.store.records.get(item)
            if record is None:
                continue
            word = _spelling(record.lemma)
            if not _LETTER_RUN.fullmatch(word) or len(word) > _ANAGRAM_MAX_LETTERS:
                continue
            swaps += [
                (f"{item} {record.lemma}", "".join(order), word)
                for order in sorted(set(permutations(word)))
                if "".join(order) != word
            ]
        return swaps

    # -- C24 ------------------------------------------------------------------

    @cached_property
    def _gloss_heads(self) -> dict[str, set[str]]:
        """English gloss head word (case-folded) -> ids of the store records whose gloss_en starts with it."""
        heads: dict[str, set[str]] = {}
        for record in self.store.records.values():
            if record.gloss_en:
                head = _GLOSS_HEAD.split(record.gloss_en, 1)[0].strip(" ?!.").casefold()
                head = head.removeprefix("to ").removeprefix("a ").removeprefix("the ")
                heads.setdefault(head, set()).add(record.id)
        return heads

    def check_recycled_categories(self) -> None:
        for lesson in self.plan["lessons"]:
            vocabulary = lesson["inventory"]["vocabulary"]
            held = {entry["evidence"] for entry in vocabulary["core"] + vocabulary["incidental"]}
            held |= set(vocabulary["recycled"])
            for step in lesson["steps"]:
                for key in ("introduces", "uses"):
                    held |= set((step.get(key) or {}).get("vocabulary") or [])
            for field_name in ("rationale", "job"):
                for sentence in _SENTENCE_BREAK.split(lesson.get(field_name) or ""):
                    match = _RECYCLE_LIST.search(sentence)
                    if not match:
                        continue
                    claimed = match.group(1)
                    missing = []
                    for term in dict.fromkeys(_singular(word) for word in _ENGLISH_WORD.findall(claimed)):
                        records = self._gloss_heads.get(term, set())
                        if term in _META_TERMS or not records or records & held:
                            continue
                        missing.append(f"{term!r} ({', '.join(self._shown_records(records))})")
                    for token in tokens_of(claimed):
                        records = self.index.get(token, set())
                        if records and not records & held:
                            missing.append(f"«{token}» ({', '.join(self._shown_records(records))})")
                    if missing:
                        self.fail(
                            codes.RECYCLED_CATEGORY_NOT_IN_LIST,
                            f"the lesson {field_name} says it recycles {', '.join(missing)}, but none of those word "
                            "records is in the lesson's recycled list or inventory; correct the claim or recycle the "
                            "records (#9487 C24)",
                            lesson["n"],
                        )

    def _shown_records(self, ids: set[str]) -> list[str]:
        return [f"{item} {self.store.records[item].lemma}" for item in sorted(ids) if item in self.store.records]

    # -- C25 ------------------------------------------------------------------

    def check_practice_steps_have_content(self) -> None:
        for lesson in self.plan["lessons"]:
            dialogue_step = (lesson.get("dialogue") or {}).get("step")
            for step in lesson["steps"]:
                if step.get("kind") != "practice" or step.get("practice") or step.get("needs"):
                    continue
                if step.get("paradigm") or step["id"] == dialogue_step:
                    continue
                self.fail(
                    codes.PRACTICE_STEP_EMPTY,
                    f"practice step {step['id']} links no activity, needs no block (quote, example, video …), hosts "
                    "no dialogue and carries no paradigm; steps are fixed structure (plan schema §7 decision 1), so "
                    "the writer must produce an empty section; merge it into the step it prepares (#9487 C25)",
                    lesson["n"],
                    step["id"],
                )

    # -- C26 ------------------------------------------------------------------

    def check_comprehension_targets_in_host(self) -> None:
        for lesson in self.plan["lessons"]:
            for activity in self._comprehension(lesson):
                context = self._comprehension_context(lesson, activity)
                outcomes = (
                    {item: self._comprehension_target(item, context, structured=True) for item in activity["targets"]}
                    if "targets" in activity
                    else self._comprehension_target_outcomes(context)
                )
                gaps = "".join(f"; {gap}" for gap in context.host_gaps)
                for code, ending in _C26_REPORTS:
                    entries = [entry for item_code, entry in outcomes.values() if item_code == code]
                    if not entries:
                        continue
                    message = (
                        f"comprehension activity {activity['id']} names {'; '.join(entries)}"
                        f"{ending.format(where=context.where, gaps=gaps)} (#9487 C26)"
                    )
                    if code in _C26_FAILURES:
                        self.fail(code, message, lesson["n"])
                    else:
                        self.note(code, message, lesson["n"])

    def _comprehension_context(self, lesson: dict, activity: dict) -> _C26Context:
        """What C26 reads from a comprehension activity's focus: its sentences, its own hosts and what they hold."""
        focus = activity["focus"]
        others = {item["id"] for item in lesson.get("activities") or []} - {activity["id"]}
        # Hosts a sentence naming another activity declares are that activity's ("as in b2 (host: {kind: dialogue})"),
        # never this one's; whether they are this activity's too is not read from prose, so they keep ids from failing.
        sentences: list[tuple[str, str]] = []  # (sentence, why it is ambiguous, "" when plain)
        own: list[tuple[str, str | None]] = []
        sibling: list[tuple[str, str | None]] = []
        for sentence in _SENTENCE_BREAK.split(focus):
            named = [ref for ref in _ids(_ACTIVITY_REF, sentence) if ref in others]
            why = [f"names activity {', '.join(named)}"] if named else []
            if _EXCLUDING.search(sentence):
                why.insert(0, "says something is excluded")
            sentences.append((sentence, " and ".join(why)))
            declared = [(match.group(1), match.group(2)) for match in _HOST.finditer(sentence)]
            declared += [("quote", ref) for ref in _quote_host_refs(sentence)]
            hosts = sibling if named else own
            hosts += [host for host in dict.fromkeys(declared) if host not in hosts]
        resolvable = [
            (kind, ref)
            for kind, ref in own
            if (kind == "quote" and ref in self.pack.quotes) or (kind == "video" and ref in self.pack.video_models)
        ]
        quotes = [_STRESS_MARKS.sub("", _nfc(self.pack.quotes[ref])) for kind, ref in resolvable if kind == "quote"]
        modelled = self._modelled([ref for kind, ref in resolvable if kind == "video"])
        host_gaps = []
        if unresolved := [host for host in own if host not in resolvable]:
            host_gaps.append(
                f"host {', '.join(_host_label(host) for host in unresolved)} is not a pack quote or a recording with "
                "models, so what it holds is not decided here (a dialogue is drafted by the writer)"
            )
        if not own:
            host_gaps.append("the activity declares no host outside sentences naming another activity")
        if sibling:
            host_gaps.append(
                f"host {', '.join(_host_label(host) for host in sibling)} is declared in a sentence naming another "
                "activity, so whether it is this activity's host is not read from prose"
            )
        where = ", ".join(_host_label(host) for host in own) or "none"
        if "targets" in activity:
            # Only drafted dialogue content is undecidable for declared targets. Unresolvable,
            # absent or sibling-only hosts cannot shelter a structured declaration.
            host_gaps = ["the dialogue is drafted by the writer"] if any(kind == "dialogue" for kind, _ in own) else []
        return _C26Context(focus, sentences, where, modelled, quotes, host_gaps)

    def _comprehension_target_outcomes(self, context: _C26Context) -> dict[str, tuple[str | None, str]]:
        """W- id -> (its C26 outcome code, None when a host holds the word; its entry in the message) for every W- id
        of the focus.

        The mapping is total over the focus's ids by construction: each id is classified by _comprehension_target,
        which returns an outcome on every path, so no id can end without one."""
        return {item: self._comprehension_target(item, context) for item in _ids(_WORD_ID, context.focus)}

    def _comprehension_target(
        self, item: str, context: _C26Context, *, structured: bool = False
    ) -> tuple[str | None, str]:
        """The C26 outcome of one W- id of a comprehension focus: never absent."""
        if structured:
            why, span = "", "targets declaration"
        else:
            holding = [(sentence, why) for sentence, why in context.sentences if item in _WORD_ID.findall(sentence)]
            plain = [sentence for sentence, why in holding if not why]
            # Sentence splitting never splits an id, so each prose-read id has a holding sentence.
            sentence, why = (plain[0], "") if plain else holding[0] if holding else ("", "is not one sentence")
            span = _span(sentence, item, _WORD_ID)
        record = self.store.records.get(item)
        if record is None:
            return codes.COMPREHENSION_TARGET_UNKNOWN, f"{item} in {span}"
        named = f"{item} {record.lemma!r}"
        if item in context.modelled or any(
            _print_holds(fragment, spelling)
            for quote in context.quotes
            for fragment in re.split(r"\[[^\]]*\]", quote)
            for spelling in (record.lemma, *record.form_texts)
        ):
            return None, named
        if why or context.host_gaps:
            return codes.COMPREHENSION_TARGET_UNVERIFIED, f"{named} in {span}" + (
                f" (the sentence {why})" if why else ""
            )
        if any("[" in text for text in context.quotes):
            return codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED, named
        return codes.COMPREHENSION_TARGET_NOT_IN_HOST, named

    # -- C27 ------------------------------------------------------------------

    def check_letter_recordings(self) -> None:
        introduced = [
            (lesson, step, letter)
            for lesson in self.plan["lessons"]
            for step in lesson["steps"]
            for letter in (step.get("introduces") or {}).get("letters") or []
        ]
        if not introduced or self.letter_state_or_skip("C27", True) is None:
            return
        for lesson, step, letter in introduced:
            videos = self._lesson_videos(lesson)
            modelled = {
                item.casefold()
                for video in videos
                if video in self.pack.video_models
                for item in self.pack.video_models[video].letters
            }
            if letter.casefold() in modelled:
                continue
            without = [video for video in videos if video not in self.pack.video_models]
            cited = ", ".join(videos) or "none"
            if without:
                cited += f"; {', '.join(without)} declare{'s' if len(without) == 1 else ''} no models"
            if any(
                _TEACHER_MODEL.search(sentence) and _names_letter(sentence, letter)
                for sentence in _SENTENCE_BREAK.split(step.get("teach") or "")
            ):
                self.note(
                    codes.LETTER_TEACHER_MODELED_ONLY,
                    f"step {step['id']} introduces {letter}, which no recording the lesson cites models ({cited}); "
                    "the teach text records the teacher modelling it, so the plan review confirms no recording is "
                    "available (#9487 C27)",
                    lesson["n"],
                    step["id"],
                )
                continue
            self.fail(
                codes.LETTER_WITHOUT_RECORDING,
                f"step {step['id']} introduces {letter}, but no recording the lesson cites declares it in "
                f"models.letters ({cited}); bind a recording that models it, or record the teacher's model of "
                f"{letter} in the step (#9487 C27)",
                lesson["n"],
                step["id"],
            )

    # -- C28 ------------------------------------------------------------------

    def check_teach_words_in_inventory(self) -> None:
        for index, lesson in enumerate(self.plan["lessons"]):
            named = [(step, _ids(_WORD_ID, step.get("teach") or "")) for step in lesson["steps"]]
            if not any(items for _step, items in named):
                continue
            allowed = self.allowed_ids(index, "C28")
            if allowed is None:
                return
            for step, items in named:
                outside = [item for item in items if item not in allowed]
                if outside:
                    self.fail(
                        codes.TEACH_WORD_NOT_IN_INVENTORY,
                        f"step {step['id']} teach text names {', '.join(self._shown_records(set(outside)) or outside)}, "
                        "outside the lesson's inventory and the planned prior learner state, so the writer's word "
                        "packet lacks the record; add it to the lesson's inventory (#9487 C28)",
                        lesson["n"],
                        step["id"],
                    )

    # -- C29 (#9582) ---------------------------------------------------------

    def check_a1_reference(self) -> None:
        """Check only newly introduced core/incidental records, with typed exceptions."""
        if self.level != "a1" or self.plan.get("level") != "a1":
            return
        mode = config.A1_REFERENCE_ENFORCEMENT
        if mode not in {"advisory", "failure"}:
            self.fail(codes.A1_REFERENCE_INVALID, "C29: invalid A1_REFERENCE_ENFORCEMENT", None)
            return
        try:
            members, alternatives = a1_reference.reference_spellings(a1_reference.INVENTORY_PATH)
            closed_class = a1_reference.closed_class_a1(a1_reference.CLOSED_CLASS_PATH)
            for path in (a1_reference.INVENTORY_PATH, a1_reference.CLOSED_CLASS_PATH, Path(config.__file__)):
                self.report.inputs[str(path.relative_to(Path(__file__).resolve().parents[3]))] = (
                    hashlib.sha256(path.read_bytes()).hexdigest()
                )
        except (OSError, ValueError, yaml.YAMLError) as error:
            self.fail(codes.A1_REFERENCE_INVALID, f"C29: cannot read reference inventory: {error}", None)
            return
        emit = self.note if mode == "advisory" else self.fail
        for lesson in self.plan["lessons"]:
            vocabulary = lesson["inventory"]["vocabulary"]
            for item in vocabulary["core"] + vocabulary["incidental"]:
                record = self.store.records.get(item["evidence"])
                if record is None:
                    continue  # the existing unknown-word gate owns this failure
                if record.form_tags and all("prop" in tags.split(":") for tags in record.form_tags):
                    continue  # same nonempty, all-forms proper-name flag as pack-verify
                lemma = a1_reference.normalize(record.lemma)
                exception = item.get("a1_reference_exception")
                if lemma in members and exception is None:
                    continue
                step_id = next(
                    (s["id"] for s in lesson["steps"] if record.id in (s.get("introduces") or {}).get("vocabulary", [])), None
                )
                if lemma not in members and exception is None and a1_reference.eligible_closed_class(
                    record.lemma, record.form_tags, closed_class,
                ):
                    self.note(codes.A1_REFERENCE_CLOSED_CLASS_A1,
                              f"C29: {record.id} {record.lemma}: closed_class_a1 source attestation", lesson["n"], step_id)
                    continue
                reason = "absent from the A1 reference inventory"
                if exception is not None:
                    kind = exception["class"]
                    if kind == "phonetics_term":
                        if lemma in config.A1_REFERENCE_PHONETICS_TERMS:
                            continue
                        reason = "phonetics_term is valid only for the closed phonetics allowlist"
                    elif kind == "letter_example_no_a1_word":
                        step_id = exception["step"]
                        letter = a1_reference.normalize(exception["letter"])
                        step = next((s for s in lesson["steps"] if s["id"] == step_id), None)
                        if step is None:
                            reason = f"exception step {step_id} does not exist in this lesson"
                        elif letter not in {a1_reference.normalize(v) for v in (step.get("introduces") or {}).get("letters", [])}:
                            reason = f"exception step {step_id} does not introduce letter {letter}"
                        elif letter not in lemma:
                            reason = f"lemma does not contain exception letter {letter}"
                        elif self.taught_before is None:
                            reason = "exception cannot be verified: taught-letter state is unavailable"
                        else:
                            taught = self._taught_at_steps(lesson)[step_id]
                            available = sorted(w for w in alternatives if letter in w and self._readable(w, taught))
                            if not available:
                                continue
                            reason = f"decodable inventory alternatives for {letter}: {', '.join(available)}"
                    else:
                        reason = "unknown reference exception class"
                emit(
                    codes.A1_REFERENCE_WORD_MISSING if exception is None else codes.A1_REFERENCE_EXCEPTION_INVALID,
                    f"C29: {record.id} {record.lemma}: {reason} (#9582; enforcement={mode})",
                    lesson["n"], step_id,
                )


def _focuses(lesson: dict) -> list[str]:
    return [activity["focus"] for activity in lesson.get("activities") or []]


def _singular(word: str) -> str:
    word = word.casefold()
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def _syllable_swaps(focus: str) -> list[tuple[str, str, str]]:
    """(row as shown, the row with another syllable of the activity in a blanked slot, key) for a pick-syllables focus.

    A row is a source segmentation the focus prints (``ма-ма``, ``По-лі-на``) or a blanked row whose key the focus
    states (``ма- __ -на has key ли``). The slots are the blanked one, else the positions the focus names (first,
    initial, second, middle, final, last), else every slot. The other syllables are every segment and every
    one-vowel token the focus prints: the options a writer draws from the activity."""
    rows: list[tuple[list[str], int | None]] = []  # (syllables, the blanked slot or None)
    for match in _SEGMENTED.finditer(focus):
        parts = [part.strip() for part in match.group(0).split("-")]
        blanks = [index for index, part in enumerate(parts) if _BLANK.fullmatch(part)]
        if not blanks:
            rows.append((parts, None))
            continue
        key = _BLANK_KEY.match(focus, match.end())
        if key is not None and len(blanks) == 1:
            rows.append(([key.group(1) if index == blanks[0] else part for index, part in enumerate(parts)], blanks[0]))
    if not rows:
        return []
    pool = {part.casefold() for parts, _blank in rows for part in parts}
    pool |= {
        token.casefold()
        for token in _ROW_TOKEN.findall(_SEGMENTED.sub(" ", focus))
        if "-" not in token and len(token) >= 2 and _vowel_count(token) == 1
    }
    named = {index for pattern, index in _SLOT_WORDS if pattern.search(focus)}
    swaps = []
    for parts, blank in rows:
        word = "".join(parts).casefold()
        if blank is not None:
            slots = {blank}
        elif named:
            last, middle = len(parts) - 1, len(parts) // 2
            slots = {last if index == -1 else middle if index == "middle" else index for index in named}
            slots = {slot for slot in slots if 0 <= slot < len(parts)}
        else:
            slots = set(range(len(parts)))
        for slot in sorted(slots):
            for other in sorted(pool - {parts[slot].casefold()}):
                made = "".join(other if index == slot else part.casefold() for index, part in enumerate(parts))
                if made != word:
                    shown = "-".join(other if index == slot else part for index, part in enumerate(parts))
                    swaps.append((shown, made, word))
    return swaps


_QUOTE_CODES = {
    quote_bytes.PRIVATE_USE: codes.QUOTE_HOST_PRIVATE_USE,
    quote_bytes.TRANSCRIPTION_SYMBOL: codes.QUOTE_HOST_TRANSCRIPTION_SYMBOL,
    quote_bytes.WATERMARK: codes.QUOTE_HOST_WATERMARK,
}


def check_review_gates(
    report: Report,
    plan: dict,
    *,
    level: str,
    store: WordStore,
    pack: Pack,
    arc: list[ArcPosition] | None,
    level_plans: LevelPlans,
    words_path: Path,
    strict: bool = False,
    vesum_declared_unavailable: bool = False,
) -> None:
    """Run gates C1–C29 on a plan that already passed the schema, with its pack and word store loaded."""
    gates = ReviewGates(
        report,
        plan,
        level,
        store,
        arc,
        level_plans,
        words_path,
        pack=pack,
        strict=strict,
        vesum_declared_unavailable=vesum_declared_unavailable,
    )
    gates.check_named_before_introduction()
    gates.check_duplicate_focus()
    gates.check_listening_single_key()
    gates.check_incidental_decodable()
    gates.check_heard_words()
    gates.check_earlier_core_recycled()
    gates.check_recap_story()
    gates.check_recap_order()
    gates.check_focus_evidence()
    gates.check_step_words_decodable()
    gates.check_odd_one_out_rows()
    gates.check_quote_host_bytes()
    gates.check_computed_key()
    gates.check_duplicate_videos()
    gates.check_adjacent_display()
    gates.check_incidental_used()
    gates.check_video_descriptions()
    gates.check_choice_options_taught()
    gates.check_sentence_decodability()
    gates.check_word_model_segments()
    gates.check_modeled_print_decodable()
    gates.check_choice_key_sets()
    gates.check_construction_distractors()
    gates.check_recycled_categories()
    gates.check_practice_steps_have_content()
    gates.check_comprehension_targets_in_host()
    gates.check_letter_recordings()
    gates.check_teach_words_in_inventory()
    gates.check_a1_reference()
