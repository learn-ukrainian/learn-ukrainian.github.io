import React from 'react';

interface SourceBoxProps {
  title: string;
  quote: string;
  citation: string;
  children?: React.ReactNode;
}

/**
 * Primary source callout for seminar tracks.
 * Displays a historical quote with citation and optional analysis.
 *
 * Usage in MDX:
 *   <SourceBox
 *     title="Galician-Volhynian Chronicle"
 *     quote="And Danylo was a great prince..."
 *     citation="Galician-Volhynian Chronicle, entry for 1253"
 *   >
 *     This passage demonstrates the chronicler's perspective on...
 *   </SourceBox>
 */
export default function SourceBox({ title, quote, citation, children }: SourceBoxProps) {
  return (
    <div className="source-box">
      <div className="source-box-header">
        <span aria-hidden="true">&#x1F4DC; </span>
        {title}
      </div>
      <blockquote>{quote}</blockquote>
      <div className="source-cite">&mdash; {citation}</div>
      {children && <div className="source-analysis">{children}</div>}
    </div>
  );
}
