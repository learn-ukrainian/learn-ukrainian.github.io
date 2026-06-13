import { waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { installHashTabSync } from '@site/src/components/HashTabSync';

const originalScrollIntoView = Element.prototype.scrollIntoView;

describe('HashTabSync', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    Element.prototype.scrollIntoView = originalScrollIntoView;
    delete window.__learnUkrainianHashTabSyncInstalled;
    document.body.innerHTML = '';
    window.history.pushState(null, '', '/');
  });

  it('scrolls to hash targets that are already in the selected tab', async () => {
    window.history.pushState(null, '', '/a1/who-am-i/#fix-common-l2-traps');
    document.body.innerHTML = `
      <starlight-tabs>
        <a role="tab" aria-selected="true">Activities</a>
        <div role="tabpanel">
          <span id="fix-common-l2-traps"></span>
          <h3>Choose the Ukrainian sentence</h3>
        </div>
      </starlight-tabs>
    `;
    class FakeTabs extends HTMLElement {}
    vi.spyOn(window.customElements, 'whenDefined').mockResolvedValue(
      FakeTabs,
    );
    vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
      callback(0);
      return 0;
    });
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;

    installHashTabSync();
    window.dispatchEvent(new Event('hashchange'));

    await waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
  });
});
