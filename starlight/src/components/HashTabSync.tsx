import { useEffect } from 'react';

interface HashTabSyncProps {}

type StarlightTabsElement = HTMLElement & {
  switchTab?: (newTab: HTMLAnchorElement, index: number, shouldSync?: boolean) => void;
};

export default function HashTabSync(_props: HashTabSyncProps) {
  useEffect(() => {
    let cancelled = false;
    const timers: number[] = [];

    const syncHashTab = () => {
      let id: string;
      try {
        id = decodeURIComponent(window.location.hash.slice(1));
      } catch {
        id = window.location.hash.slice(1);
      }
      if (!id) return;

      const target = document.getElementById(id);
      if (!target) return;

      const panel = target.closest('[role="tabpanel"]');
      if (panel instanceof HTMLElement && panel.hidden) {
        const tabs = panel.closest('starlight-tabs') as StarlightTabsElement | null;
        if (!tabs) return;

        const panels = Array.from(tabs.querySelectorAll(':scope > [role="tabpanel"]'));
        const index = panels.indexOf(panel);
        if (index < 0) return;

        const tab = tabs.querySelectorAll('[role="tab"]')[index];
        if (!(tab instanceof HTMLAnchorElement)) return;

        if (typeof tabs.switchTab === 'function') {
          tabs.switchTab(tab, index, false);
        } else {
          tab.click();
        }
      }

      const scrollTarget =
        target.nextElementSibling instanceof HTMLElement ? target.nextElementSibling : target;
      const scrollToTarget = () => {
        scrollTarget.scrollIntoView({ block: 'start' });
        const y = scrollTarget.getBoundingClientRect().top + window.scrollY - 16;
        const top = Math.max(0, y);
        window.scrollTo({ top, behavior: 'auto' });
        document.documentElement.scrollTop = top;
        document.body.scrollTop = top;
      };
      requestAnimationFrame(() => requestAnimationFrame(scrollToTarget));
      window.setTimeout(scrollToTarget, 100);
    };

    const runSync = () => {
      if (cancelled) return;
      syncHashTab();
    };

    window.addEventListener('hashchange', syncHashTab);
    if (window.customElements?.whenDefined) {
      window.customElements.whenDefined('starlight-tabs').then(runSync);
    }
    [0, 100, 300, 800, 2000, 3500].forEach((delay) => {
      timers.push(window.setTimeout(runSync, delay));
    });

    return () => {
      cancelled = true;
      window.removeEventListener('hashchange', syncHashTab);
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, []);

  return null;
}
