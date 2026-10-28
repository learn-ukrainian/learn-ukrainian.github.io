// @vitest-environment happy-dom

import { afterEach, describe, expect, test, vi } from 'vitest';
import { keepScrollableTablesFocusable, syncScrollableFocus } from '@site/src/lib/scroll-region-focus';

function sized(element: HTMLElement, scrollWidth: number, clientWidth: number): HTMLElement {
  Object.defineProperty(element, 'scrollWidth', { value: scrollWidth, configurable: true });
  Object.defineProperty(element, 'clientWidth', { value: clientWidth, configurable: true });
  return element;
}

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = '';
});

describe('scrollable table focus', () => {
  test('a table that overflows becomes keyboard focusable', () => {
    const table = sized(document.createElement('table'), 640, 320);
    syncScrollableFocus(table);
    expect(table.tabIndex).toBe(0);
  });

  test('a table that fits is not an extra Tab stop, and loses focusability when it stops overflowing', () => {
    const table = sized(document.createElement('table'), 320, 320);
    table.tabIndex = 0;
    syncScrollableFocus(table);
    expect(table).not.toHaveAttribute('tabindex');
  });

  test('only lesson-content tables are observed, and each is synced on resize', () => {
    document.body.innerHTML =
      '<div class="lu-content"><table id="in"></table></div><table id="out"></table>';
    const callbacks: ResizeObserverCallback[] = [];
    const observed: Element[] = [];
    vi.stubGlobal(
      'ResizeObserver',
      class {
        constructor(callback: ResizeObserverCallback) {
          callbacks.push(callback);
        }
        observe(target: Element) {
          observed.push(target);
        }
      },
    );

    keepScrollableTablesFocusable();
    expect(observed.map((el) => el.id)).toEqual(['in']);

    const table = sized(observed[0] as HTMLElement, 900, 300);
    callbacks[0]([{ target: table } as unknown as ResizeObserverEntry], {} as ResizeObserver);
    expect(table.tabIndex).toBe(0);
  });
});
