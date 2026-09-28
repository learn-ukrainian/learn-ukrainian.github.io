import React, { useEffect, useRef, useState, useMemo } from 'react';
import styles from './Activities.module.css';
import ActivityHelp from './ActivityHelp';
import {
  chromeFacingBilingual,
  useActivityIsUkrainian,
  useChromeLocale,
} from '../lib/i18n/useChromeLocale';
import { shuffle } from './utils';
import { optionIndicesWithoutSpottedError } from '../../../packages/activity-kit/src/components/utils';

export interface ErrorCorrectionItemProps {
  /**
   * @schemaDescription Sentence shown to the learner.
   * @ukrainianText true
   */
  sentence: string;
  /**
   * @schemaDescription Error Word value consumed by this component.
   * @ukrainianText true
   */
  errorWord: string | null;  // null = no error
  /**
   * @schemaDescription Correct Form value consumed by this component.
   * @ukrainianText true
   */
  correctForm: string;
  /**
   * @schemaDescription Answer options shown to the learner.
   * @ukrainianText true
   */
  options: string[];
  /**
   * @schemaDescription Feedback explanation shown after the learner answers.
   * @ukrainianText true
   */
  explanation: string;
  /**
   * Per-option feedback aligned by index to `options` (before the spotted
   * error is filtered out and the rest are shuffled). Absent on every
   * existing module, which keeps the single `explanation`.
   * @schemaDescription Feedback for each fix option, aligned by original index.
   * @ukrainianText true
   */
  optionWhy?: string[];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  /**
   * `type` makes step 2 a typed answer (checked against `acceptedAnswers`) instead
   * of option chips — for decks whose only options are the error and its
   * correction, where the one remaining chip would give the answer away.
   */
  fixMode?: 'choose' | 'type';
  /**
   * Corrections a typed answer may match (default: `correctForm`).
   * @schemaDescription Accepted typed corrections for this item.
   * @ukrainianText true
   */
  acceptedAnswers?: string[];
  /** Called once after a complete answer; false includes reveal-only completion. */
  onComplete?: (correct: boolean) => void;
  /** Lets a host lock this item after it has recorded the result. */
  disabled?: boolean;
}

type Step = 'identify' | 'fix' | 'complete';

/**
 * Letters + digits + combining stress (U+0301) + Ukrainian apostrophes stay
 * one token. A hyphen flanked by word characters (се-ло) stays inside that
 * token too, so hyphenated words are one clickable unit; a standalone hyphen
 * used as a dash (surrounded by spaces or punctuation) still tokenizes alone.
 */
const WORD_CHAR = `\\p{L}\\p{N}\\p{M}'’ʼʹ`;
const SENTENCE_TOKENS = new RegExp(
  `[${WORD_CHAR}]+(?:-[${WORD_CHAR}]+)*|[^\\s${WORD_CHAR}]+|\\s+`,
  'gu',
);

export function tokenizeErrorSentence(sentence: string): string[] {
  return sentence.match(SENTENCE_TOKENS) || [];
}

export function cleanErrorToken(word: string): string {
  return word
    .replace(/[^\p{L}\p{N}\p{M}'’ʼʹ-]/gu, '')
    .replace(/^-+|-+$/g, '');
}

/**
 * Comparison key for a typed correction: case, apostrophe variants, stress
 * marks, spacing around `, ; :` and final punctuation (including a trailing
 * `, ; :`) do not make an answer wrong.
 */
export function normalizeTypedCorrection(value: string): string {
  return value
    .normalize('NFD')
    .replace(/\u0301/g, '')
    .normalize('NFC')
    .replace(/['ʼʹ`‘]/g, '’')
    .toLocaleLowerCase('uk')
    .replace(/\s*([,;:])\s*/g, '$1 ')
    .replace(/\s+/g, ' ')
    .replace(/[\s.!?…,;:]+$/u, '')
    .trim();
}

export function isAcceptedTypedCorrection(typed: string, acceptedAnswers: readonly string[]): boolean {
  const key = normalizeTypedCorrection(typed);
  return key !== '' && acceptedAnswers.some((answer) => normalizeTypedCorrection(answer) === key);
}

export function ErrorCorrectionItem({
  sentence,
  errorWord,
  correctForm,
  options,
  explanation,
  optionWhy,
  isUkrainian,
  fixMode = 'choose',
  acceptedAnswers,
  onComplete,
  disabled = false,
}: ErrorCorrectionItemProps) {
  const typedFix = fixMode === 'type';
  // Shuffle options on mount, minus the error the learner already spotted.
  // Original (pre-filter, pre-shuffle) indices are kept alongside each entry
  // so per-option feedback (aligned by original index) survives both steps.
  const shuffledOptions = useMemo(() => {
    const survivingIndices = optionIndicesWithoutSpottedError(options, errorWord, correctForm);
    return shuffle(survivingIndices.map((origIndex) => ({ text: options[origIndex], origIndex })));
  }, [options, errorWord, correctForm]);

  const [step, setStep] = useState<Step>('identify');
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [selectedFix, setSelectedFix] = useState<string | null>(null);
  const [wrongAttempts, setWrongAttempts] = useState<string[]>([]);
  const [revealedCorrection, setRevealedCorrection] = useState(false);
  const [typedAnswer, setTypedAnswer] = useState('');
  const [typedCorrect, setTypedCorrect] = useState(false);
  const completionReportedRef = useRef(false);
  const typedInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (typedFix && step === 'fix') typedInputRef.current?.focus();
  }, [typedFix, step]);

  const complete = (correct: boolean) => {
    setStep('complete');
    if (!completionReportedRef.current) {
      completionReportedRef.current = true;
      onComplete?.(correct);
    }
  };

  // Split sentence into words while preserving punctuation and combining stress.
  const words = tokenizeErrorSentence(sentence);

  const handleWordKeyDown = (e: React.KeyboardEvent, word: string) => {
    // Enter and Space activate the span-as-button, matching native
    // <button> keyboard semantics. preventDefault on Space blocks the
    // default scroll behaviour.
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleWordClick(word);
    }
  };

  const handleWordClick = (word: string) => {
    if (disabled || step !== 'identify') return;

    // Clean word for comparison (remove punctuation)
    const cleanWord = cleanErrorToken(word);

    if (errorWord) {
      // For multi-word errors, check if the clicked word is part of the error phrase
      const errorWords = errorWord.split(/\s+/);
      const cleanErrorWords = errorWords.map(w => cleanErrorToken(w).toLowerCase());

      if (cleanErrorWords.includes(cleanWord.toLowerCase())) {
        // Correct word/phrase identified
        setSelectedWord(errorWord); // Store the full error phrase
        setStep('fix');
      } else if (cleanWord.trim()) {
        // Wrong word selected
        setWrongAttempts(prev => [...prev, cleanWord]);
      }
    }
  };

  const handleNoError = () => {
    if (disabled || step !== 'identify') return;

    if (errorWord === null) {
      // Correct - there was no error
      complete(true);
    } else {
      // Wrong - there was an error
      setWrongAttempts(prev => [...prev, '__no_error__']);
    }
  };

  const handleFixSelect = (fix: string) => {
    if (disabled || step !== 'fix') return;

    setRevealedCorrection(false);
    setSelectedFix(fix);
    complete(fix === correctForm);
  };

  const handleTypedSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled || step !== 'fix' || !typedAnswer.trim()) return;

    const correct = isAcceptedTypedCorrection(typedAnswer, acceptedAnswers ?? [correctForm]);
    setRevealedCorrection(false);
    setTypedCorrect(correct);
    setSelectedFix(typedAnswer.trim());
    complete(correct);
  };

  const handleRevealCorrection = () => {
    if (disabled || step !== 'fix' || (!typedFix && shuffledOptions.length > 0)) return;

    setRevealedCorrection(true);
    setSelectedFix(correctForm);
    complete(false);
  };

  const handleReset = () => {
    if (disabled) return;
    setStep('identify');
    setSelectedWord(null);
    setSelectedFix(null);
    setWrongAttempts([]);
    setRevealedCorrection(false);
    setTypedAnswer('');
    setTypedCorrect(false);
    completionReportedRef.current = false;
  };

  const isFixCorrect = typedFix ? typedCorrect : selectedFix === correctForm;
  const isNoErrorCorrect = errorWord === null && step === 'complete';
  const isCorrectionShown = revealedCorrection && step === 'complete';
  const selectedFixOrigIndex = selectedFix !== null
    ? shuffledOptions.find((o) => o.text === selectedFix)?.origIndex
    : undefined;
  const correctFixOrigIndex = options.indexOf(correctForm);
  const chosenFixWhy = selectedFixOrigIndex !== undefined ? optionWhy?.[selectedFixOrigIndex] : undefined;
  const correctFixWhy = correctFixOrigIndex >= 0 ? optionWhy?.[correctFixOrigIndex] : undefined;

  const step1Label = isUkrainian ? 'Крок 1: Знайдіть помилку' : 'Step 1: Find the error';
  const step2Label = typedFix
    ? (isUkrainian ? 'Крок 2: Напишіть правильну форму' : 'Step 2: Type the correct form')
    : (isUkrainian ? 'Крок 2: Оберіть правильну форму' : 'Step 2: Choose the correct form');
  const completeLabel = isUkrainian ? 'Завершено' : 'Complete';
  const noErrorLabel = isUkrainian ? '✓ У цьому реченні немає помилок' : '✓ No error in this sentence';
  const fixPromptLabel = typedFix
    ? (isUkrainian ? 'Напишіть правильну форму замість' : 'Type the correct form for')
    : (isUkrainian ? 'Оберіть правильну форму для' : 'Choose the correct form for');
  const typedInputLabel = isUkrainian ? 'Ваше виправлення' : 'Your correction';
  const checkLabel = isUkrainian ? 'Перевірити' : 'Check';
  const revealCorrectionLabel = isUkrainian ? 'Показати виправлення' : 'Show correction';
  const retryBtnLabel = isUkrainian ? 'Спробувати знову' : 'Try Again';

  return (
    <div className={styles.errorCorrectionItem} data-activity="error-correction-item" data-step={step}>
      {/* Step indicator */}
      <div className={styles.stepIndicator}>
        {step === 'identify' && <span className={styles.stepBadge}>{step1Label}</span>}
        {step === 'fix' && <span className={styles.stepBadge}>{step2Label}</span>}
        {step === 'complete' && <span className={styles.stepBadgeComplete}>{completeLabel}</span>}
      </div>

      {/* Sentence with clickable words */}
      <p className={styles.errorSentence} data-activity="error-correction-sentence">
        {words.map((word, idx) => {
          const cleanWord = cleanErrorToken(word);

          // Check if this word is part of a multi-word error
          const errorWords = errorWord ? errorWord.split(/\s+/).map(w => cleanErrorToken(w).toLowerCase()) : [];
          const isError = errorWords.includes(cleanWord.toLowerCase());
          const isWrongAttempt = wrongAttempts.includes(cleanWord);
          const isSelected = selectedWord && errorWords.includes(cleanWord.toLowerCase()) && step !== 'identify';

          // Non-word tokens (punctuation, spaces)
          if (!cleanWord) {
            return <span key={idx}>{word}</span>;
          }

          // For complete step, strike through the error words and show the correct form after
          // the last one; the learner's own (possibly wrong) attempt stays in the feedback.
          const isLastErrorWord = errorWord && isError && idx === words.findLastIndex(w => {
            const cw = cleanErrorToken(w);
            return errorWords.includes(cw.toLowerCase());
          });

          return (
            <span
              key={idx}
              className={`
                ${styles.clickableWord}
                ${step === 'identify' ? styles.wordHoverable : ''}
                ${isWrongAttempt ? styles.wordWrong : ''}
                ${isSelected ? styles.wordSelected : ''}
                ${step === 'complete' && isError ? styles.wordError : ''}
              `}
              data-activity="error-correction-word"
              data-word={cleanWord}
              data-is-error={isError ? 'true' : 'false'}
              onClick={() => handleWordClick(word)}
              onKeyDown={(e) => handleWordKeyDown(e, word)}
              role="button"
              tabIndex={step === 'identify' ? 0 : -1}
              aria-label={step === 'identify' ? `Click to flag "${cleanWord}" as the error` : undefined}
            >
              {step === 'complete' && isError ? (
                <>
                  <s>{word}</s>
                  {isLastErrorWord ? ` ${correctForm}` : ''}
                </>
              ) : (
                word
              )}
            </span>
          );
        })}
      </p>

      {/* No Error button - only in identify step */}
      {step === 'identify' && (
        <button
          className={`${styles.noErrorButton} ${wrongAttempts.includes('__no_error__') ? styles.noErrorWrong : ''}`}
          data-activity="error-correction-no-error"
          onClick={handleNoError}
          disabled={disabled}
        >
          {noErrorLabel}
        </button>
      )}

      {/* Typed correction - fix step of a typed item */}
      {step === 'fix' && typedFix && (
        <form className={styles.fixOptions} data-activity="error-correction-typed-fix" onSubmit={handleTypedSubmit}>
          <p className={styles.fixPrompt}>{fixPromptLabel} "<strong>{errorWord}</strong>":</p>
          <div className={styles.optionChips}>
            <input
              ref={typedInputRef}
              className={styles.textInput}
              type="text"
              lang="uk"
              autoComplete="off"
              autoCapitalize="off"
              spellCheck={false}
              aria-label={typedInputLabel}
              data-activity="error-correction-typed-input"
              value={typedAnswer}
              onChange={(e) => setTypedAnswer(e.target.value)}
              disabled={disabled}
            />
            <button
              type="submit"
              className={styles.chip}
              data-activity="error-correction-typed-check"
              disabled={disabled || !typedAnswer.trim()}
            >
              {checkLabel}
            </button>
            <button
              type="button"
              className={styles.chip}
              data-activity="error-correction-reveal"
              onClick={handleRevealCorrection}
              disabled={disabled}
            >
              {revealCorrectionLabel}
            </button>
          </div>
        </form>
      )}

      {/* Options - only in fix step */}
      {step === 'fix' && !typedFix && shuffledOptions.length > 0 && (
        <div className={styles.fixOptions} data-activity="error-correction-fix-options">
          <p className={styles.fixPrompt}>{fixPromptLabel} "<strong>{errorWord}</strong>":</p>
          <div className={styles.optionChips}>
            {shuffledOptions.map((option, idx) => (
              <button
                key={idx}
                className={styles.chip}
                data-activity="error-correction-fix-chip"
                onClick={() => handleFixSelect(option.text)}
                disabled={disabled}
              >
                {option.text}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Sentence-level rewrites can intentionally omit multiple-choice chips. */}
      {step === 'fix' && !typedFix && shuffledOptions.length === 0 && (
        <div className={styles.fixOptions} data-activity="error-correction-reveal-panel">
          <p className={styles.fixPrompt}>{fixPromptLabel} "<strong>{errorWord}</strong>":</p>
          <div className={styles.optionChips}>
            <button
              className={styles.chip}
              data-activity="error-correction-reveal"
              onClick={handleRevealCorrection}
              disabled={disabled}
            >
              {revealCorrectionLabel}
            </button>
          </div>
        </div>
      )}

      {/* Result feedback */}
      {step === 'complete' && (
        <>
          <div
            className={`${styles.feedback} ${(isFixCorrect || isNoErrorCorrect || isCorrectionShown) ? styles.feedbackCorrect : styles.feedbackIncorrect}`}
            data-activity="error-correction-feedback"
            data-correct={(isFixCorrect || isNoErrorCorrect || isCorrectionShown) ? 'true' : 'false'}
            {...(optionWhy && !isNoErrorCorrect && !isCorrectionShown
              ? { role: 'status' as const, 'aria-live': 'polite' as const }
              : {})}
          >
            {isNoErrorCorrect ? (
              isUkrainian ? '✓ Правильно! У цьому реченні не було помилок.' : '✓ Correct! There was no error in this sentence.'
            ) : isCorrectionShown ? (
              `✓ ${isUkrainian ? 'Виправлення:' : 'Correction:'} "${errorWord}" → "${correctForm}"`
            ) : isFixCorrect ? (
              `✓ ${isUkrainian ? 'Правильно!' : 'Correct!'} "${errorWord}" → "${correctForm}"`
            ) : (
              <>
                {selectedFix && (
                  <div data-activity="error-correction-learner-answer">
                    {isUkrainian ? 'Ваша відповідь:' : 'Your answer:'} "{selectedFix}"
                  </div>
                )}
                {`${isUkrainian ? '✗ Правильна відповідь:' : '✗ The correct answer is:'} "${errorWord}" → "${correctForm}"`}
              </>
            )}
            {optionWhy && !isNoErrorCorrect && !isCorrectionShown ? (
              <>
                {chosenFixWhy && (
                  <div className={styles.explanation} data-activity="error-correction-option-why">{chosenFixWhy}</div>
                )}
                {!isFixCorrect && correctFixWhy && (
                  <div className={styles.explanation} data-activity="error-correction-correct-why">{correctFixWhy}</div>
                )}
              </>
            ) : (
              explanation && (
                <div className={styles.explanation}>{explanation}</div>
              )
            )}
          </div>
          <div className={styles.buttonRow}>
            <button className={styles.resetButton} onClick={handleReset} disabled={disabled}>
              {retryBtnLabel}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface ErrorCorrectionItemData {
  /**
   * @schemaDescription Sentence shown to the learner.
   * @ukrainianText true
   */
  sentence: string;
  /**
   * @schemaDescription Error Word value consumed by this component.
   * @ukrainianText true
   */
  errorWord: string | null;
  /**
   * @schemaDescription Correct Form value consumed by this component.
   * @ukrainianText true
   */
  correctForm: string;
  /**
   * @schemaDescription Answer options shown to the learner.
   * @ukrainianText true
   */
  options: string[];
  /**
   * @schemaDescription Feedback explanation shown after the learner answers.
   * @ukrainianText true
   */
  explanation: string;
  /**
   * Per-option feedback aligned by index to `options`. Absent on V7 content.
   * @schemaDescription Feedback for each fix option, aligned by original index.
   * @ukrainianText true
   */
  optionWhy?: string[];
}

interface ErrorCorrectionProps {
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items?: ErrorCorrectionItemData[];
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
  children?: React.ReactNode;
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export default function ErrorCorrection({ items, children, instruction, isUkrainian: bakedIsUkrainian }: ErrorCorrectionProps) {
  const isUkrainian = useActivityIsUkrainian(bakedIsUkrainian);
  const locale = useChromeLocale();
  const headerLabel = isUkrainian ? 'Знайдіть і виправте помилку' : 'Find and Fix';
  const shownInstruction = chromeFacingBilingual(instruction, locale);

  return (
    <div className={styles.activityContainer} data-activity="error-correction">
      <div className={styles.activityHeader}>
        <span className={styles.activityIcon}>🔍</span>
        <span>{headerLabel}</span>
        <ActivityHelp activityType="error-correction" isUkrainian={isUkrainian} />
      </div>
      {shownInstruction && (
        <p className={styles.instruction}><strong>{shownInstruction}</strong></p>
      )}
      <div className={styles.activityContent}>
        {items ? items.map((item, index) => (
          <ErrorCorrectionItem
            key={index}
            sentence={item.sentence}
            errorWord={item.errorWord}
            correctForm={item.correctForm}
            options={item.options}
            explanation={item.explanation}
            optionWhy={item.optionWhy}
            isUkrainian={isUkrainian}
          />
        )) : React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<any>, { isUkrainian });
          }
          return child;
        })}
      </div>
    </div>
  );
}
