// @vitest-environment happy-dom

import { describe, expect, test } from 'vitest';
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import DialectComparison from '../../src/components/DialectComparison';
import TranslationCritique from '../../src/components/TranslationCritique';
import Observe, { ObserveActivity } from '../../src/components/Observe';

describe('Activity Components DOM Sanitization & XSS Defense', () => {
  describe('DialectComparison', () => {
    test('renders plain text and escapes malicious markup instead of creating HTML sinks', () => {
      const maliciousPayload = '<img src=x onerror=alert(1)><script>alert("pwned")</script>';
      const { container } = render(
        <DialectComparison
          title="Dialect XSS Test"
          textA={`Safe text A with ${maliciousPayload}`}
          textB={`Safe text B with ${maliciousPayload}`}
          features={[
            {
              featureName: 'XSS feature',
              valueA: 'Safe text A',
              valueB: 'Safe text B',
              explanation: 'Explaining safe behavior',
            },
          ]}
        />
      );

      // Verify no raw script or img tags were injected into the DOM
      expect(container.querySelectorAll('script').length).toBe(0);
      expect(container.querySelectorAll('img').length).toBe(0);

      // Verify text is present as safe escaped text content
      expect(container.textContent).toContain('<script>alert("pwned")</script>');
      expect(container.textContent).toContain('<img src=x onerror=alert(1)>');
    });

    test('highlights matching terms with React <mark> nodes without dangerouslySetInnerHTML', () => {
      const { container, getByText } = render(
        <DialectComparison
          title="Dialect Highlight Test"
          textA="Ходити до лісу щодня"
          textB="Ходити у ліс щодня"
          features={[
            {
              featureName: 'Прийменник',
              valueA: 'до лісу',
              valueB: 'у ліс',
              explanation: 'Відмінність у керуванні',
            },
          ]}
        />
      );

      // Click "Show Differences" button
      const showButton = getByText('Показати відмінності');
      fireEvent.click(showButton);

      const marks = container.querySelectorAll('mark');
      expect(marks.length).toBe(2);
      expect(marks[0].textContent).toBe('до лісу');
      expect(marks[1].textContent).toBe('у ліс');
    });
  });

  describe('TranslationCritique', () => {
    test('renders original and translations safely with malicious inputs', () => {
      const maliciousPayload = '<svg onload=alert("svg-xss")>';
      const { container } = render(
        <TranslationCritique
          title="Translation XSS Test"
          original={`Руська Правда: ${maliciousPayload} аще мужь убьеть мужа`}
          translations={[
            {
              translator: 'Hostile Translator',
              text: `Переклад: ${maliciousPayload} якщо чоловік вб'є чоловіка`,
              accuracyScore: 8,
              notes: 'Safe notes',
            },
          ]}
          focusPoints={['убьеть']}
        />
      );

      expect(container.querySelectorAll('svg').length).toBe(0);
      expect(container.textContent).toContain('<svg onload=alert("svg-xss")>');

      // Highlighted focus points
      const marks = container.querySelectorAll('mark');
      expect(marks.length).toBeGreaterThan(0);
      expect(marks[0].textContent).toBe('убьеть');
    });
  });

  describe('Observe', () => {
    test('renders observe examples without HTML sinks and parses markdown safely', () => {
      const examples = [
        '<img src=x onerror=alert("obs-xss")>',
        'Це **виділений шаблон** у мовленні',
      ];

      const { container } = render(
        <ObserveActivity
          examples={examples}
          prompt="Що ви помітили?"
        />
      );

      expect(container.querySelectorAll('img').length).toBe(0);
      expect(container.textContent).toContain('<img src=x onerror=alert("obs-xss")>');

      // Strong tag parsed safely from markdown
      const strongTags = container.querySelectorAll('strong');
      expect(strongTags.length).toBe(1);
      expect(strongTags[0].textContent).toBe('виділений шаблон');
    });
  });
});
