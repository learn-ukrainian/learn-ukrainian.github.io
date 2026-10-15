import '@testing-library/jest-dom/vitest';
import { StrictMode, useState } from 'react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import SettingsDrawer from '@site/src/components/practice/SettingsDrawer';

function DrawerControls() {
  const [isOpen, setIsOpen] = useState(false);
  const [isSuspended, setIsSuspended] = useState(false);
  return (
    <>
      <button onClick={() => setIsOpen(true)}>Open settings</button>
      <button onClick={() => setIsSuspended((value) => !value)}>Toggle suspension</button>
      <SettingsDrawer
        isOpen={isOpen}
        isSuspended={isSuspended}
        onClose={() => setIsOpen(false)}
        chromeLocale="en"
        isDriveConfigured={false}
        isDriveSyncing={false}
        driveSyncMsg={null}
        onGoogleDriveSync={() => undefined}
        selectedDeckFilter="all"
        learnerLevel="A1"
        customSets={[]}
        onRequestDeckSwitch={() => undefined}
        onOpenCustomDeckManager={() => undefined}
      />
    </>
  );
}

beforeEach(() => {
  vi.useFakeTimers();
  // happy-dom has no layout; provide geometry to exercise the drawer's trap.
  const rect = new DOMRect(0, 0, 100, 20);
  vi.spyOn(HTMLElement.prototype, 'getClientRects').mockReturnValue(
    Object.assign([rect], { item: (index: number) => index === 0 ? rect : null }),
  );
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('SettingsDrawer focus lifecycle', () => {
  test('focuses on open before accepting keyboard input and restores the opener', () => {
    render(<StrictMode><DrawerControls /></StrictMode>);
    const opener = screen.getByRole('button', { name: 'Open settings' });

    opener.focus();
    fireEvent.click(opener);
    expect(screen.getByTestId('settings-drawer-close')).toHaveFocus();
    fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Escape' });
    expect(opener).toHaveFocus();
    expect(screen.getByTestId('practice-settings-drawer')).toHaveAttribute('inert');

    fireEvent.click(opener);
    expect(screen.getByTestId('settings-drawer-close')).toHaveFocus();
  });

  test('never steals focus back after the learner collapses details and tabs', () => {
    render(<DrawerControls />);
    fireEvent.click(screen.getByRole('button', { name: 'Open settings' }));
    const close = screen.getByTestId('settings-drawer-close');
    const details = screen.getByTestId('practice-secondary-tools');
    const summary = screen.getByText('Sync & decks').closest('summary');
    expect(summary).not.toBeNull();
    if (!summary) throw new Error('drawer summary is missing');

    fireEvent.click(summary);
    expect(details).not.toHaveAttribute('open');
    summary.focus();
    fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Tab' });
    expect(close).toHaveFocus();
    fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Tab', shiftKey: true });
    expect(summary).toHaveFocus();

    act(() => { vi.advanceTimersByTime(50); });
    expect(summary).toHaveFocus();
  });

  test.each([true, false])('traps both tab boundaries with details open=%s', (expanded) => {
    render(<DrawerControls />);
    fireEvent.click(screen.getByRole('button', { name: 'Open settings' }));
    const close = screen.getByTestId('settings-drawer-close');
    const details = screen.getByTestId('practice-secondary-tools');
    const summary = screen.getByText('Sync & decks').closest('summary');
    if (!summary) throw new Error('drawer summary is missing');
    if (!expanded) fireEvent.click(summary);
    expect(details.hasAttribute('open')).toBe(expanded);
    const last = expanded ? screen.getByTestId('practice-deck-teacher-table') : summary;

    close.focus();
    expect(fireEvent.keyDown(close, { key: 'Tab', shiftKey: true })).toBe(false);
    expect(last).toHaveFocus();
    expect(fireEvent.keyDown(last, { key: 'Tab' })).toBe(false);
    expect(close).toHaveFocus();
  });

  test('cancels pending initial focus when suspended and preserves modal handoff focus', () => {
    render(<DrawerControls />);
    const opener = screen.getByRole('button', { name: 'Open settings' });
    opener.focus();
    fireEvent.click(opener);
    const suspension = screen.getByRole('button', { name: 'Toggle suspension' });
    suspension.focus();
    fireEvent.click(suspension);
    const drawer = screen.getByTestId('practice-settings-drawer');
    expect(drawer).toHaveAttribute('inert');

    act(() => { vi.advanceTimersByTime(50); });
    expect(suspension).toHaveFocus();
    fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Escape' });
    expect(drawer).toHaveClass('open');

    suspension.focus();
    fireEvent.click(suspension);
    expect(drawer).not.toHaveAttribute('inert');
    expect(suspension).toHaveFocus();
    fireEvent.keyDown(document.activeElement ?? document.body, { key: 'Escape' });
    expect(opener).toHaveFocus();
  });
});
