import React from 'react';

export interface HashTabSyncProps {
  nonce?: string;
}

type StarlightTabsElement = HTMLElement & {
  switchTab?: (tab: Element, index: number, animate?: boolean) => void;
};

declare global {
  interface Window {
    __learnUkrainianHashTabSyncInstalled?: boolean;
  }
}

export function installHashTabSync() {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  let originalHtmlOverflowAnchor: string | undefined;
  let originalBodyOverflowAnchor: string | undefined;
  let restoreOverflowAnchorTimer: number | undefined;

  function currentHashId(): string {
    try {
      return decodeURIComponent(window.location.hash.slice(1));
    } catch {
      return window.location.hash.slice(1);
    }
  }

  const requestedHashId = currentHashId();

  function isInternalTabHash(id: string): boolean {
    return /^tab-panel-\\d+$/.test(id);
  }

  function targetHashId(): string {
    const id = currentHashId();
    if (isInternalTabHash(id) && requestedHashId && !isInternalTabHash(requestedHashId)) {
      return requestedHashId;
    }
    return id;
  }

  function restoreRequestedHash(id: string): void {
    if (!id || currentHashId() === id || !window.history || !window.history.replaceState) return;
    window.history.replaceState(null, '', '#' + encodeURIComponent(id));
  }

  function selectPanelForTarget(target: HTMLElement) {
    const panel = target.closest('[role="tabpanel"]');
    if (!panel || !('hidden' in panel) || !panel.hidden) return;

    const tabs = panel.closest('starlight-tabs') as StarlightTabsElement | null;
    if (!tabs) return;

    const panels = Array.from(tabs.querySelectorAll(':scope > [role="tabpanel"]'));
    const index = panels.indexOf(panel);
    if (index < 0) return;

    const tab = tabs.querySelectorAll('[role="tab"]')[index];
    if (!tab || tab.tagName !== 'A') return;

    if (typeof tabs.switchTab === 'function') {
      tabs.switchTab(tab, index, false);
    } else {
      (tab as HTMLAnchorElement).click();
    }
  }

  function holdScrollAnchor() {
    if (originalHtmlOverflowAnchor === undefined) {
      originalHtmlOverflowAnchor = document.documentElement.style.overflowAnchor;
      originalBodyOverflowAnchor = document.body.style.overflowAnchor;
    }
    document.documentElement.style.overflowAnchor = 'none';
    document.body.style.overflowAnchor = 'none';
    window.clearTimeout(restoreOverflowAnchorTimer);
    restoreOverflowAnchorTimer = window.setTimeout(() => {
      document.documentElement.style.overflowAnchor = originalHtmlOverflowAnchor || '';
      document.body.style.overflowAnchor = originalBodyOverflowAnchor || '';
      originalHtmlOverflowAnchor = undefined;
      originalBodyOverflowAnchor = undefined;
    }, 1800);
  }

  function scrollHashTarget(id: string) {
    const target = document.getElementById(id);
    if (!target) return;

    const scrollTarget = target.closest('.sl-heading-wrapper') || target;
    holdScrollAnchor();

    scrollTarget.scrollIntoView({ block: 'start' });
    const top = Math.max(0, scrollTarget.getBoundingClientRect().top + window.pageYOffset - 16);
    window.scrollTo(0, top);
    if (document.scrollingElement) {
      document.scrollingElement.scrollTop = top;
      if (typeof document.scrollingElement.scrollTo === 'function') {
        document.scrollingElement.scrollTo(0, top);
      }
    }
    document.documentElement.scrollTop = top;
    document.body.scrollTop = top;
  }

  function syncHashTab() {
    const id = targetHashId();
    if (!id) return;

    const target = document.getElementById(id);
    if (!target) return;

    restoreRequestedHash(id);
    selectPanelForTarget(target);
    requestAnimationFrame(() => requestAnimationFrame(() => scrollHashTarget(id)));
    [50, 150, 300, 800, 1600, 3000, 5000, 8000, 12000].forEach((delay) => {
      window.setTimeout(() => scrollHashTarget(id), delay);
    });
  }

  if (window.__learnUkrainianHashTabSyncInstalled) return;
  window.__learnUkrainianHashTabSyncInstalled = true;
  window.addEventListener('hashchange', syncHashTab);
  if (window.customElements && window.customElements.whenDefined) {
    window.customElements.whenDefined('starlight-tabs').then(syncHashTab);
  }
  [0, 100, 300, 800, 2000, 3500].forEach((delay) => {
    window.setTimeout(syncHashTab, delay);
  });
}

const hashTabSyncScript = `(${installHashTabSync.toString()})();`;

export default function HashTabSync({ nonce }: HashTabSyncProps) {
  return <script nonce={nonce} dangerouslySetInnerHTML={{ __html: hashTabSyncScript }} />;
}
