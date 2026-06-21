import React from 'react';

interface PrimaryReadingProps {
  children?: React.ReactNode;
  href?: string;
}

export default function PrimaryReading({ children, href }: PrimaryReadingProps) {
  return (
    <div className="primary-reading-box">
      <div className="primary-reading-header">
        <span aria-hidden="true">&#x1F4DC; </span>
        Читаємо першоджерело / Read the text
      </div>
      <div className="primary-reading-content">
        {children}
      </div>
      {href && (
        <div className="primary-reading-footer">
          <a href={href}>📖 Читати повний текст →</a>
        </div>
      )}
    </div>
  );
}
