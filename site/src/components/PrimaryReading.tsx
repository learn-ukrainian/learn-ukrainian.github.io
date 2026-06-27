import React from 'react';
import ReadingText from './ReadingText';

interface PrimaryReadingProps {
  children?: React.ReactNode;
  href?: string;
  mode?: 'verse' | 'prose';
  text?: string;
}

export default function PrimaryReading({ children, href, mode = 'verse', text }: PrimaryReadingProps) {
  return (
    <div className="primary-reading-box">
      <div className="primary-reading-header">
        <span aria-hidden="true">&#x1F4DC; </span>
        Читаємо першоджерело / Read the text
      </div>
      <div className="primary-reading-content">
        {text ? <ReadingText mode={mode} text={text} /> : children}
      </div>
      {href && (
        <div className="primary-reading-footer">
          <a href={href}>📖 Читати повний текст →</a>
        </div>
      )}
    </div>
  );
}
