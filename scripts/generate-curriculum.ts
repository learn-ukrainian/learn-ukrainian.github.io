// scripts/generate-curriculum.ts
import { mkdir, writeFile } from 'fs/promises';
import { join } from 'path';

// ============================================================================ 
// Vibe v0.1.0 - Clean Type Definitions (from Claude's Schema)
// ============================================================================ 

export type UILanguage = 'en' | 'uk' | 'es' | 'be';
export type TeachingLanguage = 'en' | 'uk' | 'es' | 'be' | 'ru' | 'pl' | 'de' | 'fr' | 'it';
export type CEFRLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';
export type SubjectType =
  | 'language'
  | 'literature'
  | 'history'
  | 'math'
  | 'physics'
  | 'chemistry'
  | 'biology'
  | 'art';

export type ActivityType =
  | 'anagram'
  | 'unjumble'
  | 'quiz'
  | 'match-up'
  | 'flash-cards'
  | 'gap-fill'
  | 'group-sort'
  | 'random-wheel'
  | 'true-false';

export type ActivityVisibility = 'unlisted' | 'private' | 'public';

export type MethodologyKey = 'ppp' | 'ttt' | 'gppc' | 'tbl' | 'custom';
export type LessonVisibility = 'unreleased' | 'private' | 'public';

// Activity Content Interfaces
export interface QuizExercise {
  type: 'quiz';
  questions: Array<{ 
    question: string;
    options: string[];
    correctIndex: number;
    explanation?: string;
  }>;
  shuffleQuestions: boolean;
  shuffleOptions: boolean;
  showCorrectAnswers: boolean;
  instructions?: string;
}

export interface TrueFalseExercise {
  type: 'true-false';
  questions: Array<{ 
    statement: string;
    correctAnswer: boolean;
    explanation?: string;
  }>;
  shuffleQuestions: boolean;
  showFeedback: boolean;
  instructions?: string;
}

export interface GapFillExercise {
  type: 'gap-fill';
  text: string;
  gaps: Array<{ 
    index: number;
    options: string[];
    correctIndex: number;
  }>;
  instructions?: string;
}

export interface MatchUpExercise {
  type: 'match-up';
  pairs: Array<{ left: string; right: string }>;
  instructions?: string;
  shuffleRight: boolean;
}

export interface FlashCardsExercise {
  type: 'flash-cards';
  cards: Array<{ front: string; back: string }>;
  instructions?: string;
  shuffleCards: boolean;
}

export interface GroupSortExercise {
  type: 'group-sort';
  groups: Array<{ name: string; items: string[] }>;
  instructions?: string;
  shuffleItems: boolean;
}

export interface UnjumbleExercise {
  type: 'unjumble';
  sentences: string[];
  instructions?: string;
  allowSkip: boolean;
}

export interface AnagramExercise {
  type: 'anagram';
  words: string[];
  instructions?: string;
  showHints: boolean;
  allowSkip: boolean;
}

export type ActivityContent =
  | QuizExercise
  | TrueFalseExercise
  | GapFillExercise
  | MatchUpExercise
  | FlashCardsExercise
  | GroupSortExercise
  | UnjumbleExercise
  | AnagramExercise;

export interface VibeActivity {
  id: string;
  type: ActivityType;
  subject: SubjectType;
  title: string;
  description: string;
  owner: string;
  visibility: ActivityVisibility;
  language: TeachingLanguage;
  difficultyLevel: CEFRLevel;
  tags: string[];
  createdAt: string;
  modifiedAt: string;
  content: ActivityContent;
}

export interface VibeLesson {
  id: string;
  title: string;
  description: string;
  subject: SubjectType;
  methodology: MethodologyKey;
  owner: string;
  visibility: LessonVisibility;
  targetLevel: CEFRLevel;
  objectives: string[];
  materials: string[];
  totalDuration: number;
  language: TeachingLanguage;
  tags: string[];
  version: number;
  createdAt: string;
  modifiedAt: string;
  phases: Array<{ 
    id: string;
    name: string;
    duration: number;
    items: Array<{ type: 'activity'; activityId: string } | { type: 'canvas'; canvasData: string; teacherNotes?: string }>;
  }>;
}

// ============================================================================ 
// Generator Logic
// ============================================================================ 

const OUTPUT_DIR = 'output/vibe-content';
const OWNER_ID = 'curricula-opus'; // Consistent owner for all generated content

// Helper to ensure directory exists
async function ensureDir(path: string) {
  console.log(`Attempting to create directory: ${path}`);
  try {
    await mkdir(path, { recursive: true });
    console.log(`Directory created/verified: ${path}`);
  } catch (e) {
    console.error(`Error creating directory ${path}:`, e);
  }
}

// Module 01: The Cyrillic Code
async function generateModule01() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1'; // Changed to uppercase 'A1'
  const moduleNum = '01';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Activity 1: False Friends Matching
  const act1Id = `act-${lang}-${'match-up'}-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'False Friends: The Trap Letters',
    description: 'Match the deceptive Cyrillic letters to their true sounds.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level, // Uses uppercase 'A1'
    tags: ['phonetics', 'alphabet'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Р', right: 'R (Sound)' },
        { left: 'Н', right: 'N (Sound)' },
        { left: 'С', right: 'S (Sound)' },
        { left: 'Х', right: 'Kh (Sound)' },
        { left: 'В', right: 'V (Sound)' },
        { left: 'У', right: 'U (Sound)' }
      ],
      instructions: 'These letters look like English but sound completely different! Match them correctly.',
      shuffleRight: true
    }
  };

  // Activity 2: Reading "International" Words (Quiz - refactored from Unjumble)
  const act2Id = `act-${lang}-${'quiz'}-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'quiz',
    subject: subject,
    title: 'Decipher the International Words',
    description: 'Identify these international words written in Cyrillic.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level, // Uses uppercase 'A1'
    tags: ['vocabulary', 'cognates'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'quiz',
      questions: [
        {
          question: 'What does "ТАКСІ" mean?',
          options: ['Taxi', 'Task', 'Text', 'Talk'],
          correctIndex: 0,
          explanation: 'ТАКСІ (Taksi) is the Ukrainian word for "Taxi".'
        },
        {
          question: 'What does "РЕСТОРАН" mean?',
          options: ['Restaurant', 'Resort', 'Restroom', 'Review'],
          correctIndex: 0,
          explanation: 'РЕСТОРАН (Restoran) is the Ukrainian word for "Restaurant".'
        },
        {
          question: 'What does "БАНК" mean?',
          options: ['Bank', 'Book', 'Big', 'Back'],
          correctIndex: 0,
          explanation: 'БАНК (Bank) is the Ukrainian word for "Bank".'
        },
        {
          question: 'What does "МЕТРО" mean?',
          options: ['Metro', 'Meter', 'Meet', 'Month'],
          correctIndex: 0,
          explanation: 'МЕТРО (Metro) is the Ukrainian word for "Metro" or "Subway".'
        },
        {
          question: 'What does "ПІЦА" mean?',
          options: ['Pizza', 'Peace', 'Pick', 'Price'],
          correctIndex: 0,
          explanation: 'ПІЦА (Pitsa) is the Ukrainian word for "Pizza".'
        }
      ],
      shuffleQuestions: false,
      shuffleOptions: true,
      showCorrectAnswers: true,
      instructions: 'Choose the correct English meaning for each Cyrillic word.'
    }
  };

  // Activity 3: Sorting Real vs Fake (Group-sort)
  const act3Id = `act-${lang}-${'group-sort'}-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'group-sort',
    subject: subject,
    title: 'True Friends vs Aliens',
    description: 'Sort letters into those that look English and those that are uniquely Slavic.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level, // Uses uppercase 'A1'
    tags: ['alphabet', 'sorting'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Looks Familiar (True/False Friends)', items: ['А', 'К', 'М', 'Т', 'Р', 'Н', 'С', 'В'] },
        { name: 'Alien (New Shapes)', items: ['Ж', 'Ш', 'Ю', 'Я', 'Є', 'Ї', 'Г', 'Л'] }
      ],
      instructions: 'Drag the letters: Does it look like a Latin letter, or is it a new shape?',
      shuffleItems: true
    }
  };

  // The Lesson
  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Cyrillic Code',
    description: 'Unlock the alphabet by focusing on "False Friends" and cognates.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level, // Uses uppercase 'A1'
    objectives: ['Identify "False Friend" letters', 'Read international words', 'Distinguish unique Slavic letters'],
    materials: ['Cyrillic Cheat Sheet'],
    totalDuration: 45,
    language: lang,
    tags: ['alphabet', 'basics'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      {
        id: 'phase-1-presentation',
        name: 'Presentation',
        duration: 15,
        items: [
          { type: 'canvas', canvasData: '{"type":"excalidraw","elements":[]}', teacherNotes: 'Show the "False Friends" chart.' }, // Placeholder for actual Excalidraw JSON
          { type: 'activity', activityId: act1.id }
        ]
      },
      {
        id: 'phase-2-practice',
        name: 'Practice',
        duration: 20,
        items: [
          { type: 'activity', activityId: act3.id },
          { type: 'activity', activityId: act2.id }
        ]
      },
      {
        id: 'phase-3-production',
        name: 'Production',
        duration: 10,
        items: [
          { type: 'canvas', canvasData: '{}', teacherNotes: 'Show street signs and ask students to read them out loud.' } // Placeholder for actual Excalidraw JSON
        ]
      }
    ]
  };

  // Write files
  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));

  console.log(`Generated Module 01 Vibe JSONs at ${modulePath}`);
}

// Module 02: The Ghost Verb
async function generateModule02() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '02';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Activity 1: Pronoun Match
  const act1Id = `act-${lang}-match-up-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'Pronoun Match: I, You, He, She',
    description: 'Match English pronouns to their Ukrainian equivalents.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'pronouns'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Я', right: 'I' },
        { left: 'Ти', right: 'You (Informal)' },
        { left: 'Він', right: 'He' },
        { left: 'Вона', right: 'She' },
        { left: 'Ми', right: 'We' },
        { left: 'Ви', right: 'You (Formal/Plural)' }
      ],
      instructions: 'Match the Ukrainian pronouns to English.',
      shuffleRight: true
    }
  };

  // Activity 2: Sentence Builder (Unjumble)
  // Note: Vibe unjumble expects sentences where words are scrambled.
  const act2Id = `act-${lang}-unjumble-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'unjumble',
    subject: subject,
    title: 'Build the Sentence (Ghost Verb)',
    description: 'Arrange the words to form correct sentences without "to be".',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'syntax'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'unjumble',
      sentences: [
        'Я не студент.', // Scrambled: студент не Я
        'Це смачна піца.', // Scrambled: піца смачна Це
        'Він там?', // Scrambled: там Він?
        'Ми не вдома.' // Scrambled: вдома не Ми
      ],
      instructions: 'Put the words in the correct order. Remember: no "is/am/are"!',
      allowSkip: false
    }
  };

  // Activity 3: True or False (Grammar Check)
  const act3Id = `act-${lang}-true-false-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'true-false',
    subject: subject,
    title: 'Grammar Check: Is it Natural?',
    description: 'Decide if the sentence sounds natural in Ukrainian.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'style'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'true-false',
      questions: [
        {
          statement: 'Я є студент.',
          correctAnswer: false,
          explanation: 'Natural Ukrainian omits "є" (is/am). Say "Я студент".'
        },
        {
          statement: 'Я студент.',
          correctAnswer: true,
          explanation: 'Correct! The verb "to be" is a ghost.'
        },
        {
          statement: 'Це не піца.',
          correctAnswer: true,
          explanation: 'Correct order: This (Це) not (не) pizza.'
        }
      ],
      shuffleQuestions: true,
      showFeedback: true,
      instructions: 'True or False: Is this sentence natural?'
    }
  };

  // The Lesson
  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Ghost Verb',
    description: 'Learn to make sentences without "am/is/are".',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Use subject pronouns', 'Form sentences with zero copula', 'Ask simple questions'],
    materials: ['Pronoun Chart'],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'basics'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      {
        id: 'phase-1-presentation',
        name: 'Presentation',
        duration: 10,
        items: [
          { type: 'canvas', canvasData: '{}', teacherNotes: 'Explain the "Ghost Verb" concept.' },
          { type: 'activity', activityId: act1.id }
        ]
      },
      {
        id: 'phase-2-practice',
        name: 'Practice',
        duration: 15,
        items: [
          { type: 'activity', activityId: act3.id }
        ]
      },
      {
        id: 'phase-3-production',
        name: 'Production',
        duration: 20,
        items: [
          { type: 'activity', activityId: act2.id }
        ]
      }
    ]
  };

  // Write files
  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));

  console.log(`Generated Module 02 Vibe JSONs at ${modulePath}`);
}

// Module 03: The Architecture of Nouns (Declensions)
async function generateModule03() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '03';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Activity 1: Sort the Family (Group Sort)
  const act1Id = `act-${lang}-group-sort-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'group-sort',
    subject: subject,
    title: 'Sort the Families',
    description: 'Sort words into their Declension Families.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'declension', 'gender'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Family 1 (-a/-я)', items: ['Мама', 'Кава', 'Тато (M)', 'Микола (M)'] },
        { name: 'Family 2 (Cons/-o/-e)', items: ['Парк', 'Дім', 'Вікно', 'Місто', 'Батько'] },
        { name: 'Family 3 (Soft Fem)', items: ['Ніч', 'Радість', 'Сіль'] }
      ],
      instructions: 'Drag the words to their grammatical family.',
      shuffleItems: true
    }
  };

  // Activity 2: Agreement Match (Match-up)
  const act2Id = `act-${lang}-match-up-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'match-up',
    subject: subject,
    title: 'Adjective Agreement',
    description: 'Match the noun to the correctly gendered adjective.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'agreement'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Кава (Fem)', right: 'Смачн-а' },
        { left: 'Чай (Masc)', right: 'Смачн-ий' },
        { left: 'Вікно (Neut)', right: 'Велик-е' },
        { left: 'Тато (Masc!)', right: 'Добр-ий' }
      ],
      instructions: 'Match the Noun to the correct Adjective ending.',
      shuffleRight: true
    }
  };

  // Activity 3: Gender Logic (True/False)
  const act3Id = `act-${lang}-true-false-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'true-false',
    subject: subject,
    title: 'Gender Logic Check',
    description: 'Test your understanding of Gender vs Declension.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'gender'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'true-false',
      questions: [
        {
          statement: 'Тато (Dad) is Feminine because it ends in -o.',
          correctAnswer: false,
          explanation: 'False! Тато is Masculine (biological gender), but it declines like Family 1.'
        },
        {
          statement: 'Ніч (Night) is Feminine.',
          correctAnswer: true,
          explanation: 'Correct! It belongs to Family 3 (Soft Feminine).'
        },
        {
          statement: 'Моє ім\'я (My Name) is Neuter.',
          correctAnswer: true,
          explanation: 'Correct! Ім\'я is Neuter (Family 4).'
        }
      ],
      shuffleQuestions: true,
      showFeedback: true,
      instructions: 'True or False?'
    }
  };

  // The Lesson
  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Architecture of Nouns',
    description: 'Master Gender and Declension Groups.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Identify Declension Families', 'Determine Gender of Nouns', 'Match Adjectives to Nouns'],
    materials: ['Gender Matrix'],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'nouns'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      {
        id: 'phase-1-presentation',
        name: 'Presentation',
        duration: 15,
        items: [
          { type: 'canvas', canvasData: '{}', teacherNotes: 'Draw the 4 Family Houses.' },
          { type: 'activity', activityId: act1.id }
        ]
      },
      {
        id: 'phase-2-practice',
        name: 'Practice',
        duration: 15,
        items: [
          { type: 'activity', activityId: act3.id }
        ]
      },
      {
        id: 'phase-3-production',
        name: 'Production',
        duration: 15,
        items: [
          { type: 'activity', activityId: act2.id }
        ]
      }
    ]
  };

  // Write files
  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));

  console.log(`Generated Module 03 Vibe JSONs at ${modulePath}`);
}

// Module 04: The Polite Stranger
async function generateModule04() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '04';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Activity 1: Social Sorter (Group Sort)
  const act1Id = `act-${lang}-group-sort-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'group-sort',
    subject: subject,
    title: 'The Social Sorter',
    description: 'Decide which greeting to use based on social distance.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['pragmatics', 'greetings'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Say "ПРИВІТ" (Ty Zone)', items: ['Best Friend', 'Your Cat', 'Child', 'Mom', 'God'] },
        { name: 'Say "ДОБРИЙ ДЕНЬ" (Vy Zone)', items: ['Boss', 'Policeman', 'Stranger', 'Grandmother (Formal)', 'Cashier'] }
      ],
      instructions: 'Sort the people: Who gets a "Hi" and who gets a "Good Day"?',
      shuffleItems: true
    }
  };

  // Activity 2: Dialogue Match (Match-up)
  const act2Id = `act-${lang}-match-up-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'match-up',
    subject: subject,
    title: 'Dialogue Flow',
    description: 'Match the statement to the correct response.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['conversation', 'phrases'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Дякую (Thank you)', right: 'Будь ласка (You\'re welcome)' },
        { left: 'Привіт (Hi)', right: 'Привіт (Hi)' },
        { left: 'До побачення (Goodbye)', right: 'До побачення (Goodbye)' },
        { left: 'Вибачте (Sorry)', right: 'Нічого страшного (No problem)' }
      ],
      instructions: 'Complete the mini-dialogues.',
      shuffleRight: true
    }
  };

  // Activity 3: Scenario Logic (Quiz)
  const act3Id = `act-${lang}-quiz-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'quiz',
    subject: subject,
    title: 'Politeness Scenarios',
    description: 'Choose the best phrase for the situation.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['pragmatics', 'culture'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'quiz',
      questions: [
        {
          question: 'You step on a stranger\'s foot in the Metro. You say:',
          options: ['Вибачте!', 'Привіт!', 'Будь ласка!', 'Дякую!'],
          correctIndex: 0,
          explanation: 'Вибачте (Vybachte) is the formal/plural apology.'
        },
        {
          question: 'You order a coffee. You say:',
          options: ['Каву, будь ласка.', 'Каву, дякую.', 'Каву, вибачте.', 'Каву, привіт.'],
          correctIndex: 0,
          explanation: 'Always use "Будь ласка" (Please) when ordering.'
        },
        {
          question: 'You meet your friend Sasha. You ask:',
          options: ['Як справи?', 'Добрий день!', 'До побачення?', 'Вибачте?'],
          correctIndex: 0,
          explanation: '"Як справи?" (How are things?) is for friends.'
        }
      ],
      shuffleQuestions: true,
      shuffleOptions: true,
      showCorrectAnswers: true,
      instructions: 'What is the polite thing to say?'
    }
  };

  // The Lesson
  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Polite Stranger',
    description: 'Master greetings and the Ty/Vy social rules.',
    subject: subject,
    methodology: 'tbl',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Distinguish Ty vs Vy situations', 'Greet people formally and informally', 'Say Thank you and Sorry'],
    materials: ['Politeness Spectrum Chart'],
    totalDuration: 45,
    language: lang,
    tags: ['culture', 'basics'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      {
        id: 'phase-1-lead-in',
        name: 'Lead-in',
        duration: 10,
        items: [
          { type: 'canvas', canvasData: '{}', teacherNotes: 'Show scenario: A boss and a friend.' },
          { type: 'activity', activityId: act1.id }
        ]
      },
      {
        id: 'phase-2-task',
        name: 'Task',
        duration: 20,
        items: [
          { type: 'activity', activityId: act3.id }
        ]
      },
      {
        id: 'phase-3-consolidation',
        name: 'Consolidation',
        duration: 15,
        items: [
          { type: 'activity', activityId: act2.id }
        ]
      }
    ]
  };

  // Write files
  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));

  console.log(`Generated Module 04 Vibe JSONs at ${modulePath}`);
}

// Module 05: Common Objects
async function generateModule05() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '05';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Flashcards (Core Vocab)
  const act1Id = `act-${lang}-flash-cards-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'flash-cards',
    subject: subject,
    title: 'Core Objects',
    description: 'Memorize everyday objects.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'objects'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'flash-cards',
      cards: [
        { front: 'Стіл', back: 'Table' },
        { front: 'Книга', back: 'Book' },
        { front: 'Телефон', back: 'Phone' },
        { front: 'Вікно', back: 'Window' },
        { front: 'Кава', back: 'Coffee' },
        { front: 'Вода', back: 'Water' },
        { front: 'Двері', back: 'Door' },
        { front: 'Ручка', back: 'Pen' }
      ],
      instructions: 'Review the words. Try to guess the gender!',
      shuffleCards: true
    }
  };

  // Act 2: Gender Sort
  const act2Id = `act-${lang}-group-sort-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'group-sort',
    subject: subject,
    title: 'Gender Sort: Objects',
    description: 'Sort objects by their grammatical gender.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'gender'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Masculine (Він)', items: ['Стіл', 'Телефон', 'Ключ', 'Чай', 'Сир'] },
        { name: 'Feminine (Вона)', items: ['Кава', 'Вода', 'Книга', 'Ручка', 'Лампа'] },
        { name: 'Neuter (Воно)', items: ['Вікно', 'Ліжко', 'Яблуко', 'Крісло'] }
      ],
      instructions: 'Sort the objects into their Gender Houses.',
      shuffleItems: true
    }
  };

  // Act 3: Quiz (What is this?)
  const act3Id = `act-${lang}-quiz-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'quiz',
    subject: subject,
    title: 'What is this?',
    description: 'Identify the object.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'objects'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'quiz',
      questions: [
        {
          question: 'What is "Стіл"?',
          options: ['Table', 'Chair', 'Bed', 'Lamp'],
          correctIndex: 0
        },
        {
          question: 'What is "Вікно"?',
          options: ['Window', 'Door', 'Wall', 'Floor'],
          correctIndex: 0
        },
        {
          question: 'What is "Книга"?',
          options: ['Book', 'Notebook', 'Pen', 'Pencil'],
          correctIndex: 0
        },
        {
          question: 'What is "Кава"?',
          options: ['Coffee', 'Tea', 'Water', 'Juice'],
          correctIndex: 0
        }
      ],
      shuffleQuestions: true,
      shuffleOptions: true,
      showCorrectAnswers: true,
      instructions: 'Choose the correct translation.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Common Objects',
    description: 'Learn 20 essential household items.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Name common objects', 'Identify object gender'],
    materials: ['Flashcards'],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'objects'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 05 Vibe JSONs`);
}

// Module 06: Numbers & Money
async function generateModule06() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '06';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Match Up (Numbers)
  const act1Id = `act-${lang}-match-up-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'Number Match',
    description: 'Match digits to Ukrainian words.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'numbers'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: '1', right: 'Один' },
        { left: '2', right: 'Два' },
        { left: '5', right: 'П\'ять' },
        { left: '10', right: 'Десять' },
        { left: '20', right: 'Двадцять' },
        { left: '100', right: 'Сто' }
      ],
      instructions: 'Match the digit to the word.',
      shuffleRight: true
    }
  };

  // Act 2: Quiz (Prices)
  const act2Id = `act-${lang}-quiz-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'quiz',
    subject: subject,
    title: 'How Much?',
    description: 'Identify the correct price.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'numbers', 'money'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'quiz',
      questions: [
        {
          question: 'Price: 25 UAH',
          options: ['Двадцять п\'ять', 'Двадцять', 'П\'ятнадцять', 'Сто'],
          correctIndex: 0
        },
        {
          question: 'Price: 100 UAH',
          options: ['Сто', 'Десять', 'Нуль', 'Один'],
          correctIndex: 0
        },
        {
          question: 'Price: 40 UAH',
          options: ['Сорок', 'Чотири', 'Чотирнадцять', 'Сімдесят'],
          correctIndex: 0
        }
      ],
      shuffleQuestions: true,
      shuffleOptions: true,
      showCorrectAnswers: true,
      instructions: 'Choose the correct number for the price.'
    }
  };

  // Act 3: Gap Fill (Counting)
  const act3Id = `act-${lang}-gap-fill-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'gap-fill',
    subject: subject,
    title: 'Counting Objects',
    description: 'Use the correct form for 1 (One).',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'numbers'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: 'У мене [одна] книга. Тут [один] стіл. Там [одне] вікно.',
      gaps: [
        { index: 0, options: ['одна', 'один', 'одне'], correctIndex: 0 },
        { index: 1, options: ['один', 'одна', 'одне'], correctIndex: 0 },
        { index: 2, options: ['одне', 'один', 'одна'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct form of "One".'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Numbers & Money',
    description: 'Count to 100 and understand prices.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Count to 100', 'Ask "How much?"', 'Understand prices'],
    materials: ['Price List'],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'numbers'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act3.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act2.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 06 Vibe JSONs`);
}

// Module 07: The GPS (Locative Case)
async function generateModule07() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '07';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Preposition Sorter
  const act1Id = `act-${lang}-group-sort-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'group-sort',
    subject: subject,
    title: 'In vs On (Locative)',
    description: 'Sort places by preposition.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'locative'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'В / У (In)', items: ['Київ', 'Офіс', 'Парк', 'Таксі', 'Кімната'] },
        { name: 'НА (On/At)', items: ['Робота', 'Концерт', 'Стіл', 'Вулиця', 'Пошта'] }
      ],
      instructions: 'Where are you? In or On?',
      shuffleItems: true
    }
  };

  // Act 2: Locative Endings (Gap Fill)
  const act2Id = `act-${lang}-gap-fill-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'gap-fill',
    subject: subject,
    title: 'Locative Endings',
    description: 'Choose the correct ending.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'locative'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. Я в [офісі]. 2. Він у [парку]. 3. Ми на [роботі].',
      gaps: [
        { index: 0, options: ['офісі', 'офіс', 'офіса'], correctIndex: 0 },
        { index: 1, options: ['парку', 'парк', 'паркі'], correctIndex: 0 },
        { index: 2, options: ['роботі', 'робота', 'роботу'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct Locative form.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The GPS (Locative Case)',
    description: 'Say where things are.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Use Locative case', 'Distinguish In vs On'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'locative'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Practice', duration: 20, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Production', duration: 20, items: [{ type: 'activity', activityId: act2.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 07 Vibe JSONs`);
}

// Module 08: The City (Vocab)
async function generateModule08() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '08';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Flashcards
  const act1Id = `act-${lang}-flash-cards-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'flash-cards',
    subject: subject,
    title: 'City Places',
    description: 'Learn places in the city.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'city'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'flash-cards',
      cards: [
        { front: 'Банк', back: 'Bank' },
        { front: 'Аптека', back: 'Pharmacy' },
        { front: 'Магазин', back: 'Shop' },
        { front: 'Музей', back: 'Museum' },
        { front: 'Метро', back: 'Metro' },
        { front: 'Вокзал', back: 'Station' }
      ],
      instructions: 'Review the places.',
      shuffleCards: true
    }
  };

  // Act 2: Where is it? (Quiz)
  const act2Id = `act-${lang}-quiz-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'quiz',
    subject: subject,
    title: 'Where is it?',
    description: 'Identify the place.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'city'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'quiz',
      questions: [
        { question: 'Where do you buy medicine?', options: ['Аптека', 'Банк', 'Парк', 'Театр'], correctIndex: 0 },
        { question: 'Where do you get money?', options: ['Банк', 'Музей', 'Школа', 'Аптека'], correctIndex: 0 },
        { question: 'Where do you take a train?', options: ['Вокзал', 'Метро', 'Зупинка', 'Аеропорт'], correctIndex: 0 }
      ],
      shuffleQuestions: true,
      shuffleOptions: true,
      showCorrectAnswers: true,
      instructions: 'Choose the correct place.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The City',
    description: 'Learn to name essential city places.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Name city places', 'Ask where something is'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'city'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 20, items: [{ type: 'activity', activityId: act2.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 08 Vibe JSONs`);
}

// Module 09: Accusative Case
async function generateModule09() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '09';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Animate/Inanimate Sort
  const act1Id = `act-${lang}-group-sort-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'group-sort',
    subject: subject,
    title: 'Alive or Not?',
    description: 'Sort for Accusative rule.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'accusative'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Inanimate (No Change)', items: ['Стіл', 'Телефон', 'Автобус', 'Комп\'ютер'] },
        { name: 'Animate (Change to -a)', items: ['Студент', 'Брат', 'Кіт', 'Друг'] }
      ],
      instructions: 'Is it alive? (Animate vs Inanimate)',
      shuffleItems: true
    }
  };

  // Act 2: Gap Fill (I want...)
  const act2Id = `act-${lang}-gap-fill-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'gap-fill',
    subject: subject,
    title: 'I want...',
    description: 'Choose the correct Accusative form.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'accusative'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. Я хочу [піцу]. 2. Я бачу [студента]. 3. Я люблю [каву].',
      gaps: [
        { index: 0, options: ['піцу', 'піца', 'піци'], correctIndex: 0 },
        { index: 1, options: ['студента', 'студент', 'студенту'], correctIndex: 0 },
        { index: 2, options: ['каву', 'кава', 'кави'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct object form.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'I Want Pizza (Accusative)',
    description: 'Express desires and direct objects.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Use Accusative case', 'Distinguish Animate/Inanimate'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'accusative'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Practice', duration: 20, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Production', duration: 20, items: [{ type: 'activity', activityId: act2.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 09 Vibe JSONs`);
}

// Module 10: Food (Vocab)
async function generateModule10() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '10';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Flashcards
  const act1Id = `act-${lang}-flash-cards-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'flash-cards',
    subject: subject,
    title: 'Food Items',
    description: 'Learn food vocabulary.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'food'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'flash-cards',
      cards: [
        { front: 'Кава', back: 'Coffee' },
        { front: 'Чай', back: 'Tea' },
        { front: 'Борщ', back: 'Borshch' },
        { front: 'Піца', back: 'Pizza' },
        { front: 'Салат', back: 'Salad' },
        { front: 'Вода', back: 'Water' }
      ],
      instructions: 'Review the menu items.',
      shuffleCards: true
    }
  };

  // Act 2: Ordering (Gap Fill)
  const act2Id = `act-${lang}-gap-fill-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'gap-fill',
    subject: subject,
    title: 'Order Up!',
    description: 'Order food using Accusative.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'food', 'accusative'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. Мені [каву], будь ласка. 2. Я хочу [борщ]. 3. У вас є [чай]?',
      gaps: [
        { index: 0, options: ['каву', 'кава', 'кави'], correctIndex: 0 },
        { index: 1, options: ['борщ', 'борщу', 'борща'], correctIndex: 0 },
        { index: 2, options: ['чай', 'чаю', 'чаєм'], correctIndex: 0 }
      ],
      instructions: 'Complete the order.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Food & Drink',
    description: 'Order in a restaurant.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Name food items', 'Order food'],
    materials: ['Menu'],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'food'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Production', duration: 20, items: [{ type: 'activity', activityId: act2.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 10 Vibe JSONs`);
}

// Module 11: The Lord of Absence (Genitive)
async function generateModule11() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '11';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: The "No" Transformer (Gap Fill)
  const act1Id = `act-${lang}-gap-fill-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'gap-fill',
    subject: subject,
    title: 'There is no...',
    description: 'Use the Genitive case for absence.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'genitive'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. Тут немає [води]. 2. Немає [часу]. 3. У мене немає [брата].',
      gaps: [
        { index: 0, options: ['води', 'вода', 'воду'], correctIndex: 0 },
        { index: 1, options: ['часу', 'час', 'часа'], correctIndex: 0 },
        { index: 2, options: ['брата', 'брат', 'брату'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct Genitive form.'
    }
  };

  // Act 2: Possession Match
  const act2Id = `act-${lang}-match-up-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'match-up',
    subject: subject,
    title: 'Possession (Of)',
    description: 'Match the English "Of" phrase to Ukrainian Genitive.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'genitive'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Car of Dad', right: 'Машина тата' },
        { left: 'Center of Kyiv', right: 'Центр Києва' },
        { left: 'Cup of Tea', right: 'Чашка чаю' },
        { left: 'Bottle of Water', right: 'Пляшка води' }
      ],
      instructions: 'Match the phrase.',
      shuffleRight: true
    }
  };

  // Act 3: A vs U Sorter (Group Sort)
  const act3Id = `act-${lang}-group-sort-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'group-sort',
    subject: subject,
    title: 'Masculine Genitive: -A vs -U',
    description: 'Sort nouns by their Genitive ending.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'genitive'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Takes -A (People/Objects)', items: ['Брат (Brother)', 'Студент (Student)', 'Стіл (Table)', 'Кіт (Cat)'] },
        { name: 'Takes -U (Abstract/Substance)', items: ['Цукор (Sugar)', 'Чай (Tea)', 'Час (Time)', 'Спорт (Sport)'] }
      ],
      instructions: 'Does it take -A or -U in Genitive?',
      shuffleItems: true
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Lord of Absence (Genitive)',
    description: 'Express absence and possession.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Use "Nemaye" + Genitive', 'Form Genitive Singular nouns'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'genitive'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-2', name: 'Practice', duration: 20, items: [{ type: 'activity', activityId: act3.id }] },
      { id: 'phase-3', name: 'Production', duration: 10, items: [{ type: 'activity', activityId: act1.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 11 Vibe JSONs`);
}

// Module 12: Family (Relationships)
async function generateModule12() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '12';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Family Match
  const act1Id = `act-${lang}-match-up-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'Family Members',
    description: 'Match Ukrainian family terms to English.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'family'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Мама', right: 'Mom' },
        { left: 'Тато', right: 'Dad' },
        { left: 'Брат', right: 'Brother' },
        { left: 'Сестра', right: 'Sister' },
        { left: 'Діти', right: 'Children' }
      ],
      instructions: 'Match the Ukrainian word to its English meaning.',
      shuffleRight: true
    }
  };

  // Act 2: Possessive Sorter
  const act2Id = `act-${lang}-group-sort-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'group-sort',
    subject: subject,
    title: 'My / Your',
    description: 'Sort nouns by the correct possessive pronoun.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'possessive'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Мій (My - Masc)', items: ['Брат', 'Тато', 'Телефон', 'Стіл'] },
        { name: 'Моя (My - Fem)', items: ['Мама', 'Сестра', 'Книга', 'Кава'] },
        { name: 'Моє (My - Neut)', items: ['Вікно', 'Фото', 'Ліжко'] }
      ],
      instructions: 'Which "My" belongs to this word?',
      shuffleItems: true
    }
  };

  // Act 3: "I Have" Quiz
  const act3Id = `act-${lang}-quiz-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'quiz',
    subject: subject,
    title: 'I Have...',
    description: 'Choose the correct way to say "I have".',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'possession'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'quiz',
      questions: [
        {
          question: 'How do you say "I have a brother"?',
          options: ['У мене є брат.', 'Я маю брат.', 'Мій брат.'],
          correctIndex: 0
        },
        {
          question: 'How do you say "She has a sister"?',
          options: ['У неї є сестра.', 'Вона має сестра.', 'Її сестра.'],
          correctIndex: 0
        }
      ],
      shuffleQuestions: true,
      shuffleOptions: true,
      showCorrectAnswers: true,
      instructions: 'Choose the correct phrase.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Family',
    description: 'Describe your family using possessives and "U mene ye".',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Name family members', 'Use possessive pronouns', 'Express possession'],
    materials: ['Family Tree'],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'family'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 12 Vibe JSONs`);
}

// Module 13: Past Tense
async function generateModule13() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '13';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Gender Sort
  const act1Id = `act-${lang}-group-sort-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'group-sort',
    subject: subject,
    title: 'Past Tense Gender',
    description: 'Sort verb forms by gender.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'past-tense'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'group-sort',
      groups: [
        { name: 'Він (-В)', items: ['Читав', 'Думав', 'Був', 'Хотів'] },
        { name: 'Вона (-ЛА)', items: ['Читала', 'Думала', 'Була', 'Хотіла'] },
        { name: 'Вони (-ЛИ)', items: ['Читали', 'Думали', 'Були', 'Хотіли'] }
      ],
      instructions: 'Sort the verbs: Who did it?',
      shuffleItems: true
    }
  };

  // Act 2: Sentence Builder (Unjumble)
  const act2Id = `act-${lang}-unjumble-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'unjumble',
    subject: subject,
    title: 'Yesterday\'s Story',
    description: 'Build sentences about the past.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'past-tense'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'unjumble',
      sentences: [
        'Я був вдома вчора.',
        'Вона читала книгу.',
        'Ми не працювали вчора.'
      ],
      instructions: 'Arrange the words to form correct sentences about yesterday.',
      allowSkip: false
    }
  };

  // Act 3: Gap Fill (Past Verbs)
  const act3Id = `act-${lang}-gap-fill-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'gap-fill',
    subject: subject,
    title: 'Complete the Past',
    description: 'Fill in the correct past tense verb form.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'past-tense'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. Марія [читала] книгу. 2. Іван [був] вдома. 3. Вони [працювали] вчора.',
      gaps: [
        { index: 0, options: ['читала', 'читав', 'читали'], correctIndex: 0 },
        { index: 1, options: ['був', 'була', 'було'], correctIndex: 0 },
        { index: 2, options: ['працювали', 'працював', 'працювала'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct past tense form.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Time Traveler (Past Tense)',
    description: 'Talk about the past using gendered verb endings.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Form past tense verbs', 'Match gender to verb ending'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'past-tense'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act3.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act2.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 13 Vibe JSONs`);
}

// Module 14: The Calendar (Time)
async function generateModule14() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '14';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Match Up (Days of Week)
  const act1Id = `act-${lang}-match-up-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'Days of the Week',
    description: 'Match Ukrainian days to English.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'time'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Понеділок', right: 'Monday' },
        { left: 'Вівторок', right: 'Tuesday' },
        { left: 'Середа', right: 'Wednesday' },
        { left: 'Четвер', right: 'Thursday' },
        { left: 'П\'ятниця', right: 'Friday' },
        { left: 'Субота', right: 'Saturday' },
        { left: 'Неділя', right: 'Sunday' }
      ],
      instructions: 'Match the Ukrainian day to its English equivalent.',
      shuffleRight: true
    }
  };

  // Act 2: Gap Fill ("On" a Day)
  const act2Id = `act-${lang}-gap-fill-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'gap-fill',
    subject: subject,
    title: 'On Which Day?',
    description: 'Choose the correct Accusative form for "On [Day]".',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'time'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. Я працюю [у понеділок]. 2. Ми відпочиваємо [у суботу]. 3. Ти йдеш в кіно [у неділю].',
      gaps: [
        { index: 0, options: ['у понеділок', 'в понеділок', 'на понеділку'], correctIndex: 0 },
        { index: 1, options: ['у суботу', 'у субота', 'у суботі'], correctIndex: 0 },
        { index: 2, options: ['у неділю', 'у неділя', 'у неділі'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct form of the day.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Calendar',
    description: 'Talk about days of the week and parts of the day.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Name days of week', 'Say "on Monday"', 'Talk about parts of day'],
    materials: ['Calendar'],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'time'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 20, items: [{ type: 'activity', activityId: act2.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 14 Vibe JSONs`);
}

// Module 15: The Planner (Future Tense)
async function generateModule15() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '15';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Budu Match (Pronoun + Helper)
  const act1Id = `act-${lang}-match-up-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'Future Helper Verb',
    description: 'Match pronouns to the correct form of "Бути" (Will be).',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'future-tense'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Я (I)', right: 'Буду' },
        { left: 'Ти (You)', right: 'Будеш' },
        { left: 'Він/Вона (He/She)', right: 'Буде' },
        { left: 'Ми (We)', right: 'Будемо' },
        { left: 'Ви (You pl)', right: 'Будете' },
        { left: 'Вони (They)', right: 'Будуть' }
      ],
      instructions: 'Match the pronoun to the future helper verb.',
      shuffleRight: true
    }
  };

  // Act 2: Future Builder (Unjumble)
  const act2Id = `act-${lang}-unjumble-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'unjumble',
    subject: subject,
    title: 'Future Plans',
    description: 'Build sentences in the future tense.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'syntax'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'unjumble',
      sentences: [
        'Я буду спати завтра.',
        'Ми будемо працювати вдома.',
        'Ти будеш їсти сніданок?'
      ],
      instructions: 'Arrange the words to form future tense sentences.',
      allowSkip: false
    }
  };

  // Act 3: True/False Grammar
  const act3Id = `act-${lang}-true-false-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'true-false',
    subject: subject,
    title: 'Future Tense Rules',
    description: 'Check your understanding of Future Tense rules.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'future-tense'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'true-false',
      questions: [
        {
          statement: 'Я буду читав.',
          correctAnswer: false,
          explanation: 'False! The helper verb "Буду" must be followed by an Infinitive (читати), not a past tense form.'
        },
        {
          statement: 'Він буде працювати завтра.',
          correctAnswer: true,
          explanation: 'Correct! The compound future tense requires "Буде" + Infinitive.'
        }
      ],
      shuffleQuestions: true,
      showFeedback: true,
      instructions: 'True or False: Is the sentence grammatically correct?'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'The Planner (Future Tense)',
    description: 'Make plans using the compound future tense.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Conjugate "Budu"', 'Form compound future sentences'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'future-tense'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 15 Vibe JSONs`);
}

// Module 16: Daily Routine
async function generateModule16() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '16';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Flashcards (Routine Verbs)
  const act1Id = `act-${lang}-flash-cards-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'flash-cards',
    subject: subject,
    title: 'Routine Verbs',
    description: 'Learn verbs for daily activities.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'routine'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'flash-cards',
      cards: [
        { front: 'Прокидатися', back: 'To wake up' },
        { front: 'Вмиватися', back: 'To wash up' },
        { front: 'Снідати', back: 'To have breakfast' },
        { front: 'Працювати', back: 'To work' },
        { front: 'Обідати', back: 'To have lunch' },
        { front: 'Вечеряти', back: 'To have dinner' }
      ],
      instructions: 'Review the verbs.',
      shuffleCards: true
    }
  };

  // Act 2: Reflexive Gap Fill
  const act2Id = `act-${lang}-gap-fill-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'gap-fill',
    subject: subject,
    title: 'Reflexive Verbs',
    description: 'Choose the correct reflexive form.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'reflexive'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. Я [прокидаюся] рано. 2. Ти [вмиваєшся]? 3. Ми [одягаємося].',
      gaps: [
        { index: 0, options: ['прокидаюся', 'прокидаєшся', 'прокидається'], correctIndex: 0 },
        { index: 1, options: ['вмиваєшся', 'вмиваюся', 'вмиваються'], correctIndex: 0 },
        { index: 2, options: ['одягаємося', 'одягаються', 'одягаюся'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct verb form.'
    }
  };

  // Act 3: Routine Builder (Unjumble)
  const act3Id = `act-${lang}-unjumble-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'unjumble',
    subject: subject,
    title: 'My Routine',
    description: 'Describe a typical morning.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'routine'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'unjumble',
      sentences: [
        'Я прокидаюся рано вранці.',
        'Потім я снідаю.',
        'Я працюю вдень.'
      ],
      instructions: 'Arrange the sentences to describe a day.',
      allowSkip: false
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Daily Routine',
    description: 'Describe your typical day using reflexive verbs.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Use routine verbs', 'Conjugate reflexive verbs'],
    materials: ['Clock'],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'routine'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 16 Vibe JSONs`);
}

// Module 17: Colors & Clothing
async function generateModule17() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '17';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Color Match
  const act1Id = `act-${lang}-match-up-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'Colors',
    description: 'Match Ukrainian colors to English.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'colors'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Червоний', right: 'Red' },
        { left: 'Синій', right: 'Blue' },
        { left: 'Зелений', right: 'Green' },
        { left: 'Жовтий', right: 'Yellow' },
        { left: 'Чорний', right: 'Black' },
        { left: 'Білий', right: 'White' }
      ],
      instructions: 'Match the colors.',
      shuffleRight: true
    }
  };

  // Act 2: Clothing Flashcards
  const act2Id = `act-${lang}-flash-cards-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'flash-cards',
    subject: subject,
    title: 'Clothing Items',
    description: 'Learn names of clothes.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'clothing'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'flash-cards',
      cards: [
        { front: 'Сорочка', back: 'Shirt' },
        { front: 'Штани', back: 'Pants' },
        { front: 'Сукня', back: 'Dress' },
        { front: 'Куртка', back: 'Jacket' },
        { front: 'Шапка', back: 'Hat' }
      ],
      instructions: 'Review clothing items.',
      shuffleCards: true
    }
  };

  // Act 3: Adjective Agreement (Gap Fill)
  const act3Id = `act-${lang}-gap-fill-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'gap-fill',
    subject: subject,
    title: 'Colorful Clothes',
    description: 'Choose the correct adjective form.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'adjectives'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. У мене [червона] сорочка. 2. Це [синій] костюм. 3. [Чорні] штани.',
      gaps: [
        { index: 0, options: ['червона', 'червоний', 'червоне'], correctIndex: 0 },
        { index: 1, options: ['синій', 'синя', 'синє'], correctIndex: 0 },
        { index: 2, options: ['чорні', 'чорна', 'чорний'], correctIndex: 0 }
      ],
      instructions: 'Choose the correct color form.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Colors & Clothing',
    description: 'Describe appearance using colors and clothes.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Name colors', 'Name clothes', 'Match adjectives to nouns'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'appearance'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 17 Vibe JSONs`);
}

// Module 18: Weather
async function generateModule18() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '18';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Weather Flashcards
  const act1Id = `act-${lang}-flash-cards-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'flash-cards',
    subject: subject,
    title: 'Weather Vocabulary',
    description: 'Learn weather words.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['vocabulary', 'weather'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'flash-cards',
      cards: [
        { front: 'Сонце', back: 'Sun' },
        { front: 'Дощ', back: 'Rain' },
        { front: 'Сніг', back: 'Snow' },
        { front: 'Тепло', back: 'Warm' },
        { front: 'Холодно', back: 'Cold' }
      ],
      instructions: 'Review weather words.',
      shuffleCards: true
    }
  };

  // Act 2: Impersonal Sentences (Unjumble)
  const act2Id = `act-${lang}-unjumble-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'unjumble',
    subject: subject,
    title: 'Weather Report',
    description: 'Describe the weather.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'syntax'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'unjumble',
      sentences: [
        'Сьогодні дуже тепло.',
        'Завтра буде холодно.',
        'На вулиці йде дощ.'
      ],
      instructions: 'Build weather sentences.',
      allowSkip: false
    }
  };

  // Act 3: Feelings (Gap Fill)
  const act3Id = `act-${lang}-gap-fill-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'gap-fill',
    subject: subject,
    title: 'How do you feel?',
    description: 'Use Dative pronouns for feelings.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'dative'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '1. [Мені] холодно. 2. [Йому] жарко. 3. [Нам] тепло.',
      gaps: [
        { index: 0, options: ['Мені', 'Я', 'Мене'], correctIndex: 0 },
        { index: 1, options: ['Йому', 'Він', 'Його'], correctIndex: 0 },
        { index: 2, options: ['Нам', 'Ми', 'Нас'], correctIndex: 0 }
      ],
      instructions: 'Who is feeling it?'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Weather',
    description: 'Talk about weather and temperature.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Describe weather', 'Express feeling cold/hot'],
    materials: ['Weather Map'],
    totalDuration: 45,
    language: lang,
    tags: ['vocabulary', 'weather'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 18 Vibe JSONs`);
}

// Module 19: Modal Verbs
async function generateModule19() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '19';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Modal Match
  const act1Id = `act-${lang}-match-up-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'match-up',
    subject: subject,
    title: 'Modal Verbs',
    description: 'Match pronouns to modal verbs.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'modals'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'match-up',
      pairs: [
        { left: 'Я (Can)', right: 'Можу' },
        { left: 'Ти (Must)', right: 'Мусиш' },
        { left: 'Він (Wants)', right: 'Хоче' },
        { left: 'Ми (Can)', right: 'Можемо' }
      ],
      instructions: 'Match the pronoun to the verb.',
      shuffleRight: true
    }
  };

  // Act 2: Modal Builder (Unjumble)
  const act2Id = `act-${lang}-unjumble-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'unjumble',
    subject: subject,
    title: 'Modal Sentences',
    description: 'Build sentences with Can, Must, Want.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'syntax'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'unjumble',
      sentences: [
        'Я хочу пити каву.',
        'Ти мусиш працювати.',
        'Ми можемо читати.'
      ],
      instructions: 'Arrange the words.',
      allowSkip: false
    }
  };

  // Act 3: Ability Quiz
  const act3Id = `act-${lang}-quiz-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'quiz',
    subject: subject,
    title: 'Expressing Ability',
    description: 'Choose the correct modal phrase.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['grammar', 'modals'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'quiz',
      questions: [
        {
          question: 'How do you say "I can read"?',
          options: ['Я можу читати.', 'Я хочу читати.', 'Я мушу читати.'],
          correctIndex: 0
        },
        {
          question: 'How do you say "She wants to sleep"?',
          options: ['Вона хоче спати.', 'Вона може спати.', 'Вона мусить спати.'],
          correctIndex: 0
        }
      ],
      shuffleQuestions: true,
      shuffleOptions: true,
      showCorrectAnswers: true,
      instructions: 'Select the correct phrase.'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'Modal Verbs',
    description: 'Express ability, necessity, and desire.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Use Mozhu, Mushu, Khochu', 'Form modal sentences'],
    materials: [],
    totalDuration: 45,
    language: lang,
    tags: ['grammar', 'modals'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Presentation', duration: 15, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 15, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Production', duration: 15, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 19 Vibe JSONs`);
}

// Module 20: A1 Capstone Review
async function generateModule20() {
  const lang = 'uk';
  const level: CEFRLevel = 'A1';
  const moduleNum = '20';
  const subject: SubjectType = 'language';
  const now = new Date().toISOString();

  const modulePath = join(OUTPUT_DIR, `l2-${lang}-en`, `module_${moduleNum}`);
  await ensureDir(modulePath);

  // Act 1: Full Sentence Unjumble (Complex)
  const act1Id = `act-${lang}-unjumble-${level}-${moduleNum}-01`;
  const act1: VibeActivity = {
    id: act1Id,
    type: 'unjumble',
    subject: subject,
    title: 'Complex Sentences',
    description: 'Build sentences using multiple grammar points.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['review', 'syntax'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'unjumble',
      sentences: [
        'Я вчора був у метро і хотів каву.',
        'Завтра ми будемо працювати в офісі.',
        'У мене немає часу на спорт.'
      ],
      instructions: 'Build the sentences.',
      allowSkip: false
    }
  };

  // Act 2: Dialogue Builder (Gap Fill)
  const act2Id = `act-${lang}-gap-fill-${level}-${moduleNum}-02`;
  const act2: VibeActivity = {
    id: act2Id,
    type: 'gap-fill',
    subject: subject,
    title: 'Dialogue Review',
    description: 'Complete the survival dialogue.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['review', 'conversation'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'gap-fill',
      text: '- Добрий [день]. - Привіт. Як [справи]? - [Нормально]. А у тебе? - [Чудово].',
      gaps: [
        { index: 0, options: ['день', 'ранок', 'вечір'], correctIndex: 0 },
        { index: 1, options: ['справи', 'ти', 'воно'], correctIndex: 0 },
        { index: 2, options: ['Нормально', 'Погано', 'Жах'], correctIndex: 0 },
        { index: 3, options: ['Чудово', 'Так собі', 'Не дуже'], correctIndex: 0 }
      ],
      instructions: 'Complete the conversation.'
    }
  };

  // Act 3: Self-Assessment (True/False)
  const act3Id = `act-${lang}-true-false-${level}-${moduleNum}-03`;
  const act3: VibeActivity = {
    id: act3Id,
    type: 'true-false',
    subject: subject,
    title: 'Can-Do Check',
    description: 'Verify your A1 skills.',
    owner: OWNER_ID,
    visibility: 'public',
    language: lang,
    difficultyLevel: level,
    tags: ['review', 'assessment'],
    createdAt: now,
    modifiedAt: now,
    content: {
      type: 'true-false',
      questions: [
        { statement: 'Я можу замовити їжу. (I can order food)', correctAnswer: true, explanation: 'Use "Я хочу..." or "Мені..."' },
        { statement: 'Я можу розказати про родину. (I can describe family)', correctAnswer: true, explanation: 'Use "Це мій тато..."' },
        { statement: 'Я розумію кирилицю. (I understand Cyrillic)', correctAnswer: true, explanation: 'You mastered the alphabet!' }
      ],
      shuffleQuestions: false,
      showFeedback: true,
      instructions: 'Can you do this? (Select True if yes!)'
    }
  };

  const lessonId = `${lang}-${subject}-${level}-${moduleNum}`;
  const lesson: VibeLesson = {
    id: lessonId,
    title: 'A1 Capstone Review',
    description: 'Review all A1 skills.',
    subject: subject,
    methodology: 'ppp',
    owner: OWNER_ID,
    visibility: 'public',
    targetLevel: level,
    objectives: ['Review A1 grammar', 'Practice dialogue', 'Self-assess skills'],
    materials: [],
    totalDuration: 60,
    language: lang,
    tags: ['review', 'capstone'],
    version: 1,
    createdAt: now,
    modifiedAt: now,
    phases: [
      { id: 'phase-1', name: 'Review', duration: 20, items: [{ type: 'activity', activityId: act1.id }] },
      { id: 'phase-2', name: 'Practice', duration: 20, items: [{ type: 'activity', activityId: act2.id }] },
      { id: 'phase-3', name: 'Assessment', duration: 20, items: [{ type: 'activity', activityId: act3.id }] }
    ]
  };

  await writeFile(join(modulePath, `activity_01_${act1.type}.json`), JSON.stringify(act1, null, 2));
  await writeFile(join(modulePath, `activity_02_${act2.type}.json`), JSON.stringify(act2, null, 2));
  await writeFile(join(modulePath, `activity_03_${act3.type}.json`), JSON.stringify(act3, null, 2));
  await writeFile(join(modulePath, `lesson_${lesson.subject}.json`), JSON.stringify(lesson, null, 2));
  console.log(`Generated Module 20 Vibe JSONs`);
}

// Run
async function main() {
  console.log("Starting Vibe JSON generation script...");
  await generateModule01();
  await generateModule02();
  await generateModule03();
  await generateModule04();
  await generateModule05();
  await generateModule06();
  await generateModule07();
  await generateModule08();
  await generateModule09();
  await generateModule10();
  await generateModule11();
  await generateModule12();
  await generateModule13();
  await generateModule14();
  await generateModule15();
  await generateModule16();
  await generateModule17();
  await generateModule18();
  await generateModule19();
  await generateModule20();
}
main().catch(console.error);
