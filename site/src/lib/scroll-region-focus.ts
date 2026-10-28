/**
 * Lesson tables scroll sideways on narrow screens (`.lu-content table`). A
 * scrolling region has to be reachable from the keyboard (WCAG 2.1.1, axe
 * `scrollable-region-focusable`), but a table that fits needs no extra Tab stop.
 * So a table is focusable only while it actually overflows.
 */
export function syncScrollableFocus(element: HTMLElement): void {
  if (element.scrollWidth > element.clientWidth) {
    element.tabIndex = 0;
  } else {
    element.removeAttribute('tabindex');
  }
}

export function keepScrollableTablesFocusable(root: ParentNode = document): void {
  const observer = new ResizeObserver((entries) => {
    for (const entry of entries) syncScrollableFocus(entry.target as HTMLElement);
  });
  for (const table of root.querySelectorAll<HTMLElement>('.lu-content table')) {
    observer.observe(table);
  }
}
