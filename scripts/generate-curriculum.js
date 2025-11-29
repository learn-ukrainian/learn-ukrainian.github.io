"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
// scripts/generate-curriculum.ts
var promises_1 = require("fs/promises");
var path_1 = require("path");
// ============================================================================ 
// Generator Logic
// ============================================================================ 
var OUTPUT_DIR = 'output/vibe-content';
var OWNER_ID = 'curricula-opus'; // Consistent owner for all generated content
// Helper to ensure directory exists
function ensureDir(path) {
    return __awaiter(this, void 0, void 0, function () {
        var e_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    console.log("Attempting to create directory: ".concat(path));
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, (0, promises_1.mkdir)(path, { recursive: true })];
                case 2:
                    _a.sent();
                    console.log("Directory created/verified: ".concat(path));
                    return [3 /*break*/, 4];
                case 3:
                    e_1 = _a.sent();
                    console.error("Error creating directory ".concat(path, ":"), e_1);
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    });
}
// Module 01: The Cyrillic Code
function generateModule01() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '01';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-").concat('match-up', "-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-").concat('quiz', "-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-").concat('group-sort', "-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    // Write files
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 01 Vibe JSONs at ".concat(modulePath));
                    return [2 /*return*/];
            }
        });
    });
}
// Module 02: The Ghost Verb
function generateModule02() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '02';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-unjumble-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-true-false-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    // Write files
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 02 Vibe JSONs at ".concat(modulePath));
                    return [2 /*return*/];
            }
        });
    });
}
// Module 03: The Architecture of Nouns (Declensions)
function generateModule03() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '03';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-true-false-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    // Write files
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 03 Vibe JSONs at ".concat(modulePath));
                    return [2 /*return*/];
            }
        });
    });
}
// Module 04: The Polite Stranger
function generateModule04() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '04';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-quiz-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    // Write files
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 04 Vibe JSONs at ".concat(modulePath));
                    return [2 /*return*/];
            }
        });
    });
}
// Module 05: Common Objects
function generateModule05() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '05';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-flash-cards-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-quiz-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 05 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 06: Numbers & Money
function generateModule06() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '06';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-quiz-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 06 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 07: The GPS (Locative Case)
function generateModule07() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '07';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 4:
                    _a.sent();
                    console.log("Generated Module 07 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 08: The City (Vocab)
function generateModule08() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '08';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-flash-cards-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-quiz-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 4:
                    _a.sent();
                    console.log("Generated Module 08 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 09: Accusative Case
function generateModule09() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '09';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 4:
                    _a.sent();
                    console.log("Generated Module 09 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 10: Food (Vocab)
function generateModule10() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '10';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-flash-cards-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 4:
                    _a.sent();
                    console.log("Generated Module 10 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 11: The Lord of Absence (Genitive)
function generateModule11() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '11';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 11 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 12: Family (Relationships)
function generateModule12() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '12';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-quiz-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 12 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 13: Past Tense
function generateModule13() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '13';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-group-sort-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-unjumble-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 13 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 14: The Calendar (Time)
function generateModule14() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '14';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 4:
                    _a.sent();
                    console.log("Generated Module 14 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 15: The Planner (Future Tense)
function generateModule15() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '15';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-unjumble-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-true-false-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 15 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 16: Daily Routine
function generateModule16() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '16';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-flash-cards-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-unjumble-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 16 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 17: Colors & Clothing
function generateModule17() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '17';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-flash-cards-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 17 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 18: Weather
function generateModule18() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '18';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-flash-cards-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-unjumble-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 18 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 19: Modal Verbs
function generateModule19() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '19';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-match-up-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-unjumble-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-quiz-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 19 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Module 20: A1 Capstone Review
function generateModule20() {
    return __awaiter(this, void 0, void 0, function () {
        var lang, level, moduleNum, subject, now, modulePath, act1Id, act1, act2Id, act2, act3Id, act3, lessonId, lesson;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    lang = 'uk';
                    level = 'A1';
                    moduleNum = '20';
                    subject = 'language';
                    now = new Date().toISOString();
                    modulePath = (0, path_1.join)(OUTPUT_DIR, "l2-".concat(lang, "-en"), "module_".concat(moduleNum));
                    return [4 /*yield*/, ensureDir(modulePath)];
                case 1:
                    _a.sent();
                    act1Id = "act-".concat(lang, "-unjumble-").concat(level, "-").concat(moduleNum, "-01");
                    act1 = {
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
                    act2Id = "act-".concat(lang, "-gap-fill-").concat(level, "-").concat(moduleNum, "-02");
                    act2 = {
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
                    act3Id = "act-".concat(lang, "-true-false-").concat(level, "-").concat(moduleNum, "-03");
                    act3 = {
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
                    lessonId = "".concat(lang, "-").concat(subject, "-").concat(level, "-").concat(moduleNum);
                    lesson = {
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
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_01_".concat(act1.type, ".json")), JSON.stringify(act1, null, 2))];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_02_".concat(act2.type, ".json")), JSON.stringify(act2, null, 2))];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "activity_03_".concat(act3.type, ".json")), JSON.stringify(act3, null, 2))];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, (0, promises_1.writeFile)((0, path_1.join)(modulePath, "lesson_".concat(lesson.subject, ".json")), JSON.stringify(lesson, null, 2))];
                case 5:
                    _a.sent();
                    console.log("Generated Module 20 Vibe JSONs");
                    return [2 /*return*/];
            }
        });
    });
}
// Run
function main() {
    return __awaiter(this, void 0, void 0, function () {
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    console.log("Starting Vibe JSON generation script...");
                    return [4 /*yield*/, generateModule01()];
                case 1:
                    _a.sent();
                    return [4 /*yield*/, generateModule02()];
                case 2:
                    _a.sent();
                    return [4 /*yield*/, generateModule03()];
                case 3:
                    _a.sent();
                    return [4 /*yield*/, generateModule04()];
                case 4:
                    _a.sent();
                    return [4 /*yield*/, generateModule05()];
                case 5:
                    _a.sent();
                    return [4 /*yield*/, generateModule06()];
                case 6:
                    _a.sent();
                    return [4 /*yield*/, generateModule07()];
                case 7:
                    _a.sent();
                    return [4 /*yield*/, generateModule08()];
                case 8:
                    _a.sent();
                    return [4 /*yield*/, generateModule09()];
                case 9:
                    _a.sent();
                    return [4 /*yield*/, generateModule10()];
                case 10:
                    _a.sent();
                    return [4 /*yield*/, generateModule11()];
                case 11:
                    _a.sent();
                    return [4 /*yield*/, generateModule12()];
                case 12:
                    _a.sent();
                    return [4 /*yield*/, generateModule13()];
                case 13:
                    _a.sent();
                    return [4 /*yield*/, generateModule14()];
                case 14:
                    _a.sent();
                    return [4 /*yield*/, generateModule15()];
                case 15:
                    _a.sent();
                    return [4 /*yield*/, generateModule16()];
                case 16:
                    _a.sent();
                    return [4 /*yield*/, generateModule17()];
                case 17:
                    _a.sent();
                    return [4 /*yield*/, generateModule18()];
                case 18:
                    _a.sent();
                    return [4 /*yield*/, generateModule19()];
                case 19:
                    _a.sent();
                    return [4 /*yield*/, generateModule20()];
                case 20:
                    _a.sent();
                    return [2 /*return*/];
            }
        });
    });
}
main().catch(console.error);
