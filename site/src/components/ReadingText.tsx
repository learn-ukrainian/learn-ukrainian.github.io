import React from 'react';

type ReadingTextMode = 'verse' | 'prose';

interface ReadingTextProps {
  children?: React.ReactNode;
  className?: string;
  mode?: ReadingTextMode;
  text?: string;
}

const textFromChildren = (children: React.ReactNode): string => (
  React.Children.toArray(children)
    .map((child) => (typeof child === 'string' || typeof child === 'number' ? String(child) : ''))
    .join('')
);

const normalizeText = (text: string): string => {
  const lines = text.replace(/\r\n?/g, '\n').split('\n');

  while (lines.length && !lines[0].trim()) lines.shift();
  while (lines.length && !lines[lines.length - 1].trim()) lines.pop();

  return lines.map((line) => line.replace(/[ \t]+$/g, '')).join('\n');
};

export default function ReadingText({ children, className, mode = 'verse', text }: ReadingTextProps) {
  const normalizedText = normalizeText(text ?? textFromChildren(children));
  if (!normalizedText) return null;

  const blocks = normalizedText.split(/\n{2,}/).map((block) => block.trim()).filter(Boolean);
  const classes = ['reading-text', `reading-text--${mode}`, className].filter(Boolean).join(' ');

  return (
    <div className={classes} data-reading-text>
      {blocks.map((block, blockIndex) => {
        if (mode === 'prose') {
          return (
            <p className="reading-text__paragraph" key={blockIndex}>
              {block.replace(/\n+/g, ' ')}
            </p>
          );
        }

        return (
          <p className="reading-text__stanza" key={blockIndex}>
            {block.split('\n').map((line, lineIndex) => (
              <span className="reading-text__line" key={`${blockIndex}-${lineIndex}`}>
                {line}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
