import React from 'react';

interface SourceBoxProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText false
   */
  title: string;
  /**
   * @schemaDescription Quoted source excerpt preserved in its source language.
   * @ukrainianText maybe
   */
  quote: string;
  /**
   * @schemaDescription Citation metadata preserved verbatim.
   * @ukrainianText false
   */
  citation: string;
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
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
