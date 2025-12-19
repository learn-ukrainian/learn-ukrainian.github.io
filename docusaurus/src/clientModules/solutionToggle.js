/**
 * Solution block toggle functionality
 * Makes [!solution] admonitions collapsible with click-to-reveal
 */

if (typeof window !== 'undefined') {
  // Run on initial load and route changes
  const initSolutionToggles = () => {
    const solutionBlocks = document.querySelectorAll('.admonition-solution');

    solutionBlocks.forEach((block) => {
      // Skip if already initialized
      if (block.dataset.initialized) return;
      block.dataset.initialized = 'true';

      const heading = block.querySelector('.admonition-heading');
      if (!heading) return;

      heading.addEventListener('click', () => {
        block.classList.toggle('expanded');
      });
    });
  };

  // Initial load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSolutionToggles);
  } else {
    initSolutionToggles();
  }

  // Re-run on route changes (SPA navigation)
  const observer = new MutationObserver(() => {
    initSolutionToggles();
  });

  // Observe the main content area for changes
  const startObserving = () => {
    const main = document.querySelector('main') || document.body;
    observer.observe(main, { childList: true, subtree: true });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startObserving);
  } else {
    startObserving();
  }
}

export default {};
