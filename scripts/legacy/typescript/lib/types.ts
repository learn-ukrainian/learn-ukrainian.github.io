/**
 * Type definitions for curricula-opus generator
 */

// =============================================================================
// Activity Types
// =============================================================================

export type ActivityType =
  | 'quiz'
  | 'match-up'
  | 'group-sort'
  | 'fill-blank'
  | 'true-false'
  | 'translate'
  | 'unjumble'
  | 'anagram'
  | 'gap-fill'
  | 'select'
  | 'error-correction'
  | 'fill-in'
  | 'cloze'
  | 'dialogue-reorder'
  | 'mark-the-words';

// =============================================================================
// Frontmatter
// =============================================================================

export interface Frontmatter {
  module: number;
  title: string;
  subtitle?: string;
  titleUk?: string;
  level: 'A1' | 'A2' | 'A2+' | 'B1' | 'B1+' | 'B2' | 'B2+' | 'C1';
  phase: string;
  duration: number;
  transliteration: 'full' | 'partial' | 'first-occurrence' | 'none';
  tags: string[];
  objectives: string[];
  objectivesUk?: string[];
  grammar?: string[];
  pedagogy: 'PPP' | 'TTT' | 'Narrative' | 'CLIL';
}

// =============================================================================
// Module Structure
// =============================================================================

export interface ParsedModule {
  frontmatter: Frontmatter;
  sections: Section[];
  activities: Activity[];
  vocabulary: VocabWord[];
  reviewVocabulary: VocabWord[];
  rawMarkdown: string;
}

export interface Section {
  id: string;
  type: 'intro' | 'content' | 'practice' | 'summary' | 'vocabulary' | 'activities' | 'diagnostic' | 'analysis' | 'consolidation' | 'application';
  title: string;
  titleUk?: string;
  content: string;
}

// =============================================================================
// Vocabulary
// =============================================================================

export interface VocabWord {
  id: string;
  uk: string;
  translit?: string;
  ipa?: string;
  en: string;
  pos: string;
  gender?: 'f' | 'm' | 'n';
  note?: string;
  audio?: string;
  image?: string;
  isNew?: boolean;        // true if first appears in this module
  firstModule?: number;   // module where word was first introduced
}

export interface VocabularySection {
  moduleId: string;
  level: string;
  phase: string;
  wordCount: number;
  newWordCount: number;
  reviewWordCount: number;
  transliterationMode: string;
  words: VocabWord[];
  reviewWords?: VocabWord[];
  letterGroups?: LetterGroup[];
}

export interface LetterGroup {
  name: string;
  letters: string[];
}

// =============================================================================
// Activities - Base
// =============================================================================

export type ExerciseStage = 'recognition' | 'discrimination' | 'controlled-production' | 'free-production';

export interface Activity<T extends ActivityContent = ActivityContent> {
  id: string;
  type: ActivityType;
  title: string;
  titleUk?: string;
  description: string;
  instructions: string;
  instructionsUk?: string;
  content: T;
  tags?: string[];
  stage?: ExerciseStage;  // Pedagogical stage (recognition → production)
}

export interface ActivityContent {
  type: ActivityType;
}

// =============================================================================
// Activity Content Types
// =============================================================================

// Quiz
export interface QuizContent extends ActivityContent {
  type: 'quiz';
  questions: QuizQuestion[];
  shuffleQuestions: boolean;
  shuffleOptions: boolean;
  showCorrectAnswers: boolean;
}

export interface QuizQuestion {
  question: string;
  questionUk?: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  explanationUk?: string;
  imageUrl?: string;
}

// Match-up
export interface MatchUpContent extends ActivityContent {
  type: 'match-up';
  pairs: MatchPair[];
  shuffleRight: boolean;
  shuffleBoth?: boolean;
}

export interface MatchPair {
  left: string;
  right: string;
  leftImageUrl?: string;
  rightImageUrl?: string;
  leftAudio?: string;
  rightAudio?: string;
}

// Group Sort
export interface GroupSortContent extends ActivityContent {
  type: 'group-sort';
  groups: SortGroup[];
  shuffleItems: boolean;
}

export interface SortGroup {
  id: string;
  name: string;
  nameUk?: string;
  items: (string | SortItem)[];
}

export interface SortItem {
  text: string;
  imageUrl?: string;
}

// Fill-Blank (single blanks per item)
export interface FillBlankContent extends ActivityContent {
  type: 'fill-blank';
  items: FillBlankItem[];
}

export interface FillBlankItem {
  prompt: string;
  hints?: string[];
  answer: string;
  alternatives?: string[];
  options?: string[];  // Multiple choice options (includes answer + distractors)
  explanation?: string;
}

// True-False
export interface TrueFalseContent extends ActivityContent {
  type: 'true-false';
  statements: TrueFalseStatement[];
}

export interface TrueFalseStatement {
  statement: string;
  statementUk?: string;
  isTrue: boolean;
  explanation: string;
  explanationUk?: string;
}

// Translate
export interface TranslateContent extends ActivityContent {
  type: 'translate';
  items: TranslateItem[];
  direction: 'to-uk' | 'to-en';
}

export interface TranslateItem {
  source: string;
  answer: string;
  alternatives?: string[];
  explanation?: string;
}

// Anagram (reorder letters to form a word)
export interface AnagramContent extends ActivityContent {
  type: 'anagram';
  items: AnagramItem[];
}

export interface AnagramItem {
  letters: string[];      // scrambled letters: ['а', 'м', 'м', 'а']
  answer: string;         // correct word: 'мама'
  translation?: string;   // English: 'mom'
  hint?: string;          // optional hint
}

// Gap-Fill (text passage with multiple blanks)
export interface GapFillContent extends ActivityContent {
  type: 'gap-fill';
  text: string;
  blanks: GapFillBlank[];
  answers: string[];
}

export interface GapFillBlank {
  index: number;
  hint?: string;
}

// Error-Correction (identify and fix errors)
export interface ErrorCorrectionContent extends ActivityContent {
  type: 'error-correction';
  items: ErrorCorrectionItem[];
}

export interface ErrorCorrectionItem {
  sentence: string;
  errorWord: string | null;  // null = no error
  correctForm: string;
  options: string[];
  explanation: string;
}

// =============================================================================
// Parser Context
// =============================================================================

export interface ParseContext {
  level: string;
  moduleNum: number;
  imageMap: Map<string, string>;
  languagePair: string;
  activityCounters: Map<string, number>;
}

// =============================================================================
// Render Context
// =============================================================================

export interface RenderContext {
  moduleNum: number;
  level: string;
  languagePair: string;
  prevModule?: { num: number; title: string };
  nextModule?: { num: number; title: string };
}

// =============================================================================
// JSON Output (Vibe format)
// =============================================================================

export interface VibeModule {
  $schema: string;
  lesson: VibeLesson;
  activities: VibeActivity[];
  vocabulary: VocabularySection;
}

export type ModuleType =
  | 'grammar'
  | 'vocabulary'
  | 'checkpoint'
  | 'history'
  | 'biography'
  | 'idioms'
  | 'skills'
  | 'literature'
  | 'culture'
  | 'functional';

export interface VibeLesson {
  id: string;
  moduleId: string;
  languagePair: string;
  subject: string;
  owner: string;
  visibility: string;
  language: string;
  targetLevel: string;
  phase: string;
  moduleNumber: number;
  moduleType: ModuleType;
  pedagogy?: string;
  immersionLevel: number;
  title: string;
  titleUk?: string;
  subtitle?: string;
  description: string;
  descriptionUk?: string;
  objectives: string[];
  objectivesUk?: string[];
  grammarFocus: string[];
  tags: string[];
  totalDuration: number;
  transliterationMode: string;
  sections: VibeSection[];
  rawMarkdown: string;
  createdAt: string;
  modifiedAt: string;
  version: number;
}

export interface VibeSection {
  id: string;
  name: string;
  nameEn?: string;
  type: string;
  content: string;
}

export interface VibePhase {
  id: string;
  name: string;
  duration: number;
  items: VibePhaseItem[];
}

export interface VibePhaseItem {
  type: 'canvas' | 'activity';
  canvasData?: string;
  teacherNotes?: string;
  activityId?: string;
}

export interface VibeActivity {
  id: string;
  type: ActivityType;
  title: string;
  titleUk?: string;
  description: string;
  content: ActivityContent;
  subject: string;
  owner: string;
  visibility: string;
  language: string;
  difficultyLevel: string;
  duration: number;
  tags: string[];
  createdAt: string;
  modifiedAt: string;
}
