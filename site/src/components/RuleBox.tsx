import React from 'react';

interface RuleBoxProps {
  /**
   * @schemaDescription Display title shown above the component.
   * @ukrainianText true
   */
  title: string;
  /**
   * @schemaDescription Icon value consumed by this component.
   * @ukrainianText false
   */
  icon?: string;
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
  children: React.ReactNode;
}

/**
 * Grammar rule callout with yellow background and optional icon.
 * Supports table or text content via children.
 *
 * Usage in MDX:
 *   <RuleBox title="Gender by ending" icon="📐">
 *     <table>...</table>
 *   </RuleBox>
 */
export default function RuleBox({ title, icon = '\u{1F4D0}', children }: RuleBoxProps) {
  return (
    <div className="rule-box">
      <div className="rule-box-header">
        <div className="rule-box-icon">{icon}</div>
        {title}
      </div>
      {children}
    </div>
  );
}
