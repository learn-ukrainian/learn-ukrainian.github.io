import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import SettingsDrawer from '@site/src/components/practice/SettingsDrawer';
import { LexiconCustomDeckManager } from '@site/src/components/LexiconCustomDeckManager';
import PracticeDailyDeck from '@site/src/components/PracticeDailyDeck';
import type { DailyPracticeDeckItem, PracticeLexeme } from '@site/src/lib/lexicon/srs';

function makeLexeme(
  lemmaId: string,
  lemma: string,
  gloss: string,
  cefr: 'A1' | 'A2' | 'B1' = 'A1'
): PracticeLexeme {
  return {
    lemmaId,
    lemma,
    lemmaPlain: lemma,
    gloss,
    ipa: null,
    paradigm: {
      cases: {
        nominative: { singular: lemma },
      },
    },
    cefr,
    pos: 'noun',
    heritage: 'native',
    severity: 'standard',
  };
}

describe('Practice mobile touch targets & desktop non-goal (#8383)', () => {
  it('verifies SettingsDrawer close button retains compact desktop dimensions without forced inline 44px', () => {
    render(
      <SettingsDrawer
        isOpen={true}
        onClose={() => {}}
        learnerLevel="A1"
        selectedDeckFilter="all"
        onRequestDeckSwitch={() => {}}
        onOpenCustomDeckManager={() => {}}
        isDriveConfigured={true}
        onGoogleDriveSync={() => {}}
        isDriveSyncing={false}
        driveSyncMsg={null}
        customSets={[]}
        chromeLocale="uk"
      />
    );

    const closeBtn = screen.getByTestId('settings-drawer-close');
    expect(closeBtn).toBeDefined();
    // Non-goal: Desktop button sizing must NOT be altered by unconditional inline minimums
    expect(closeBtn.style.minWidth).toBe('');
    expect(closeBtn.style.minHeight).toBe('');
    expect(closeBtn.style.fontSize).toBe('1.2rem');
    expect(closeBtn.style.padding).toBe('0.2rem 0.6rem');
  });

  it('verifies LexiconCustomDeckManager close button retains compact desktop dimensions without forced inline 44px', () => {
    render(
      <LexiconCustomDeckManager
        chromeLocale="uk"
        activeDeckFilter="all"
        onSelectDeckFilter={() => {}}
        onClose={() => {}}
      />
    );

    const closeBtn = screen.getByTestId('custom-deck-studio-close');
    expect(closeBtn).toBeDefined();
    // Non-goal: Desktop button sizing must NOT be altered by unconditional inline minimums
    expect(closeBtn.style.minWidth).toBe('');
    expect(closeBtn.style.minHeight).toBe('');
    expect(closeBtn.style.background).toBe('transparent');
  });

  it('verifies PracticeDailyDeck preview atlas link retains standard text styling without forced inline min-height', () => {
    const item = makeLexeme('knyha', 'книга', 'book', 'A1');
    const deckItem: DailyPracticeDeckItem = {
      lemmaId: item.lemmaId,
      lemma: item.lemma,
      gloss: item.gloss,
      cefr: item.cefr,
      pos: item.pos,
      hasAtlasEntry: true,
      origin: 'new',
    };
    render(
      <PracticeDailyDeck
        snapshot={{
          version: 2,
          date: '2026-09-22',
          level: 'A1',
          deckVersion: '1.0',
          createdAt: Date.now(),
          items: [deckItem],
        }}
        rows={{
          pendingDue: [],
          pendingNew: [{ item: deckItem, state: 'new', lastSeenAt: null }],
          done: [],
        }}
        lexemes={new Map([['knyha', item]])}
        atlasLemmaHref={(id) => `/atlas/${id}/`}
        chromeLocale="uk"
        learnerLevel="A1"
        onReRoll={() => {}}
      />
    );

    const atlasLink = screen.getByTestId('practice-preview-atlas-link');
    expect(atlasLink).toBeDefined();
    // Non-goal: Desktop link sizing must NOT be altered by unconditional inline minimums
    expect(atlasLink.style.minHeight).toBe('');
  });

  it('verifies practice.astro encapsulates mobile 44px touch targets inside @media (max-width: 760px)', () => {
    const astroPath = resolve(__dirname, '../../src/pages/practice.astro');
    const astroSource = readFileSync(astroPath, 'utf8');

    // Extract all mobile media query blocks
    const mobileMediaBlocks = [...astroSource.matchAll(/@media\s*\(max-width:\s*760px\)\s*\{([\s\S]*?)\n  \}/g)]
      .map((m) => m[1])
      .join('\n');
    expect(mobileMediaBlocks.length).toBeGreaterThan(0);
    const mobileCss = mobileMediaBlocks;

    // Mobile touch targets (44px min-width/min-height) must be inside mobile media query
    expect(mobileCss).toMatch(/:global\(\.k3-settings-btn\)\s*\{[^}]*min-height:\s*44px;/);
    expect(mobileCss).toMatch(/:global\(\.k3-settings-btn\)\s*\{[^}]*min-width:\s*44px;/);
    expect(mobileCss).toMatch(/:global\(\[data-testid="settings-drawer-close"\]\)/);
    expect(mobileCss).toMatch(/:global\(\[data-testid="custom-deck-studio-close"\]\)/);
    expect(mobileCss).toMatch(/:global\(\.daily-deck-atlas-link\)\s*\{[^}]*min-height:\s*44px;/);
    expect(mobileCss).toMatch(/:global\(\.stage-back\)\s*\{[^}]*min-width:\s*44px;/);
    expect(mobileCss).toMatch(/\.lexicon-practice-back\s*\{[^}]*min-width:\s*44px;/);
    expect(mobileCss).toMatch(/:global\(\.k3-levels button\)\s*\{[^}]*min-width:\s*44px;/);
    expect(mobileCss).toMatch(/:global\(\[data-testid="practice-clear-focus"\]\)/);

    // Desktop rules outside media queries must NOT define min-width: 44px on stage-back, lexicon-practice-back, or k3-levels button
    const desktopSource = astroSource.replace(/@media[^{]+\{([\s\S]+?\n  \})/g, '');
    const desktopStageBack = desktopSource.match(/:global\(\.stage-back\)\s*\{([^}]*)\}/);
    expect(desktopStageBack).not.toBeNull();
    expect(desktopStageBack![1]).not.toContain('min-width: 44px');

    const desktopPracticeBack = desktopSource.match(/\.lexicon-practice-back\s*\{([^}]*)\}/);
    expect(desktopPracticeBack).not.toBeNull();
    expect(desktopPracticeBack![1]).not.toContain('min-width: 44px');
  });

  it('verifies LexiconPractice.tsx clear focus and settings buttons do not have unconditional inline 44px', () => {
    const practicePath = resolve(__dirname, '../../src/components/LexiconPractice.tsx');
    const practiceSource = readFileSync(practicePath, 'utf8');

    // practice-clear-focus button has data-testid and relies on responsive CSS (no inline minHeight/minWidth)
    const clearFocusBlock = practiceSource.match(/data-testid="practice-clear-focus"[\s\S]*?style=\{\{([\s\S]*?)\}\}/);
    expect(clearFocusBlock).not.toBeNull();
    expect(clearFocusBlock![1]).not.toContain('minHeight');
    expect(clearFocusBlock![1]).not.toContain('minWidth');

    // practice-settings-toggle button relies on responsive CSS (no inline minHeight/minWidth)
    const settingsToggleBlock = practiceSource.match(/data-testid="practice-settings-toggle"[\s\S]*?style=\{\{([\s\S]*?)\}\}/);
    expect(settingsToggleBlock).not.toBeNull();
    expect(settingsToggleBlock![1]).not.toContain('minHeight');
    expect(settingsToggleBlock![1]).not.toContain('minWidth');
  });
});
