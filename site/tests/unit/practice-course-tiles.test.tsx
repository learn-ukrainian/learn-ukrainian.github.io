import { describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CoursesTrack, {
  COURSE_SUBTITLE_KEYS,
  CULTURE_DECK_META,
} from '@site/src/components/practice/CoursesTrack';
import { ZNO_PRACTICE_DECK_META } from '@site/src/components/ZnoPractice';
import { CHROME_STRINGS } from '@site/src/lib/i18n/chrome';

const EXPECTED_EN_SUBTITLES: Record<string, string> = {
  'zno-stress': 'Word Stress Exam Prep',
  'zno-paronym': 'Paronyms & Confusable Words',
  'zno-lexical-norm': 'Lexical Norms & Calques',
  'zno-morphological-norm': 'Morphological Norms & Forms',
  'zno-syntactic-norm': 'Syntactic Norms & Agreement',
  'zno-orthography': 'Spelling & Orthography Rules',
  'zno-morphology': 'Parts of Speech & Inflection',
  'zno-syntax': 'Sentence Structure & Punctuation',
  'zno-phonetics': 'Phonetics & Sound Changes',
  'culture-error-correction': 'Error Correction',
};

describe('Practice Hub Course & Exam Tiles (#8381)', () => {
  describe('Denominator: Exactly 10 course tiles', () => {
    test('covers 9 ZNO decks plus 1 Culture of Speech deck', () => {
      expect(ZNO_PRACTICE_DECK_META).toHaveLength(9);
      expect(Object.keys(COURSE_SUBTITLE_KEYS)).toHaveLength(10);
      expect(Object.keys(EXPECTED_EN_SUBTITLES)).toHaveLength(10);
    });
  });

  describe('AC-01: Explanatory English subtitles on EN locale', () => {
    test('renders English subtitles for all 10 course tiles when chromeLocale is en', () => {
      render(
        <CoursesTrack
          chromeLocale="en"
          onSelectZnoDeck={vi.fn()}
          onSelectCulturePractice={vi.fn()}
        />,
      );

      // Verify all 9 ZNO deck subtitles
      for (const znoDeck of ZNO_PRACTICE_DECK_META) {
        const subtitleEl = screen.getByTestId(`practice-course-subtitle-${znoDeck.deckId}`);
        expect(subtitleEl).toBeInTheDocument();
        expect(subtitleEl).toHaveTextContent(EXPECTED_EN_SUBTITLES[znoDeck.deckId]);
      }

      // Verify Culture of Speech subtitle
      const cultureSubtitleEl = screen.getByTestId(
        'practice-course-subtitle-culture-error-correction',
      );
      expect(cultureSubtitleEl).toBeInTheDocument();
      expect(cultureSubtitleEl).toHaveTextContent(EXPECTED_EN_SUBTITLES['culture-error-correction']);

      // Exactly 10 subtitles rendered in total
      const allSubtitles = document.querySelectorAll('.k3-mode-subtitle');
      expect(allSubtitles).toHaveLength(10);
    });

    test('bilingual display: Ukrainian title with English subtitle under it on EN locale', () => {
      render(
        <CoursesTrack
          chromeLocale="en"
          onSelectZnoDeck={vi.fn()}
          onSelectCulturePractice={vi.fn()}
        />,
      );

      // Stress card: "Наголос" with "Word Stress Exam Prep"
      const stressCard = screen.getByTestId('practice-zno-card-zno-stress');
      expect(stressCard).toHaveTextContent('Наголос');
      expect(stressCard).toHaveTextContent('Word Stress Exam Prep');

      // Lexical norm card: "Лексична норма" with "Lexical Norms & Calques"
      const lexicalCard = screen.getByTestId('practice-zno-card-zno-lexical-norm');
      expect(lexicalCard).toHaveTextContent('Лексична норма');
      expect(lexicalCard).toHaveTextContent('Lexical Norms & Calques');

      // Culture of speech card: "Культура мовлення" with "Error Correction"
      const cultureCard = screen.getByTestId('practice-card-culture');
      expect(cultureCard).toHaveTextContent('Культура мовлення');
      expect(cultureCard).toHaveTextContent('Error Correction');
    });
  });

  describe('AC-02: Difficulty badges displayed on all 10 tiles', () => {
    test('displays "B2–C1 / Exam prep" difficulty badge on all 10 tiles on English UI', () => {
      render(
        <CoursesTrack
          chromeLocale="en"
          onSelectZnoDeck={vi.fn()}
          onSelectCulturePractice={vi.fn()}
        />,
      );

      // All 9 ZNO decks have the difficulty badge
      for (const znoDeck of ZNO_PRACTICE_DECK_META) {
        const badgeEl = screen.getByTestId(`practice-course-difficulty-${znoDeck.deckId}`);
        expect(badgeEl).toBeInTheDocument();
        expect(badgeEl).toHaveTextContent('B2–C1 / Exam prep');
      }

      // Culture of speech has the difficulty badge
      const cultureBadge = screen.getByTestId(
        'practice-course-difficulty-culture-error-correction',
      );
      expect(cultureBadge).toBeInTheDocument();
      expect(cultureBadge).toHaveTextContent('B2–C1 / Exam prep');

      // All 10 difficulty badges present in DOM
      const allDifficultyBadges = screen.getAllByText('B2–C1 / Exam prep');
      expect(allDifficultyBadges).toHaveLength(10);
    });
  });

  describe('AC-03 & Stop Policy: Pure Ukrainian on UK locale without English leakage', () => {
    test('does NOT render English subtitles when chromeLocale is uk', () => {
      render(
        <CoursesTrack
          chromeLocale="uk"
          onSelectZnoDeck={vi.fn()}
          onSelectCulturePractice={vi.fn()}
        />,
      );

      // Zero subtitle elements in DOM
      const allSubtitles = document.querySelectorAll('.k3-mode-subtitle');
      expect(allSubtitles).toHaveLength(0);

      for (const znoDeck of ZNO_PRACTICE_DECK_META) {
        expect(
          screen.queryByTestId(`practice-course-subtitle-${znoDeck.deckId}`),
        ).not.toBeInTheDocument();
      }
      expect(
        screen.queryByTestId('practice-course-subtitle-culture-error-correction'),
      ).not.toBeInTheDocument();
    });

    test('renders Ukrainian difficulty badges and authentic terminology on UK locale', () => {
      render(
        <CoursesTrack
          chromeLocale="uk"
          onSelectZnoDeck={vi.fn()}
          onSelectCulturePractice={vi.fn()}
        />,
      );

      // 9 ZNO decks show Ukrainian exam prep badge
      for (const znoDeck of ZNO_PRACTICE_DECK_META) {
        const badgeEl = screen.getByTestId(`practice-course-difficulty-${znoDeck.deckId}`);
        expect(badgeEl).toHaveTextContent('B2–C1 / Підготовка до ЗНО');
      }

      // Culture deck shows Ukrainian speech culture badge
      const cultureBadge = screen.getByTestId(
        'practice-course-difficulty-culture-error-correction',
      );
      expect(cultureBadge).toHaveTextContent('B2–C1 / Культура мовлення');

      // Steps are in Ukrainian
      const znoCards = screen.getAllByTestId(/^practice-zno-card-/);
      expect(znoCards).toHaveLength(9);
      for (const card of znoCards) {
        expect(card).toHaveTextContent('ЗНО / НМТ');
        expect(card).not.toHaveTextContent('ZNO / NMT');
        expect(card).not.toHaveTextContent('Exam prep');
      }

      const cultureCard = screen.getByTestId('practice-card-culture');
      expect(cultureCard).toHaveTextContent(CULTURE_DECK_META.step); // 'Збагачення'
      expect(cultureCard).not.toHaveTextContent(CULTURE_DECK_META.stepEn); // 'Enrichment'
    });
  });

  describe('Interactivity and callbacks', () => {
    test('clicking ZNO deck triggers onSelectZnoDeck callback with correct deckId', async () => {
      const user = userEvent.setup();
      const onSelectZno = vi.fn();
      render(
        <CoursesTrack
          chromeLocale="en"
          onSelectZnoDeck={onSelectZno}
          onSelectCulturePractice={vi.fn()}
        />,
      );

      const stressCard = screen.getByTestId('practice-zno-card-zno-stress');
      await user.click(stressCard);
      expect(onSelectZno).toHaveBeenCalledWith('zno-stress');
    });

    test('clicking Culture deck triggers onSelectCulturePractice callback', async () => {
      const user = userEvent.setup();
      const onSelectCulture = vi.fn();
      render(
        <CoursesTrack
          chromeLocale="en"
          onSelectZnoDeck={vi.fn()}
          onSelectCulturePractice={onSelectCulture}
        />,
      );

      const cultureCard = screen.getByTestId('practice-card-culture');
      await user.click(cultureCard);
      expect(onSelectCulture).toHaveBeenCalledTimes(1);
    });
  });
});
