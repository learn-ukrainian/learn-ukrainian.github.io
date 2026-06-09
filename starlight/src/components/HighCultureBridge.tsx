import React from 'react';
import { parseMarkdown } from './utils';

interface HighCultureBridgeProps {
  /**
   * @schemaDescription Title shown in the bridge header.
   * @ukrainianText true
   */
  title?: string;
  /**
   * @schemaDescription Ordered folk-to-high-culture nodes shown in the bridge flow.
   * @ukrainianText true
   */
  nodes: string[];
  /**
   * @schemaDescription Explanatory note below the bridge flow.
   * @ukrainianText true
   */
  note?: string;
}

export default function HighCultureBridge({
  title = 'Місток до високої культури',
  nodes,
  note
}: HighCultureBridgeProps) {
  return (
    <div className="bridge-box">
      <div className="bridge-head">
        <span aria-hidden="true">&#x1F3BC;</span>
        <span>{title}</span>
      </div>
      <div className="bridge-flow">
        {nodes.map((node, index) => (
          <React.Fragment key={`${node}-${index}`}>
            <span className="bridge-node">{node}</span>
            {index < nodes.length - 1 && <span className="bridge-arrow" aria-hidden="true">&#x2192;</span>}
          </React.Fragment>
        ))}
      </div>
      {note && <div className="bridge-note">{parseMarkdown(note)}</div>}
    </div>
  );
}
