import React from 'react';

/**
 * Parse simple markdown (bold **text**) and return React elements
 */
export function parseMarkdown(text: string): React.ReactNode {
    if (!text) return text;

    // Split by **text** pattern
    const parts = text.split(/(\*\*[^*]+\*\*)/g);

    return parts.map((part, index) => {
        // Check if this part is bold (**text**)
        if (part.startsWith('**') && part.endsWith('**')) {
            const boldText = part.slice(2, -2);
            return <strong key={index}>{boldText}</strong>;
        }
        return part;
    });
}

/**
 * Strip markdown formatting and return plain text
 */
export function stripMarkdown(text: string): string {
    if (!text) return text;
    return text.replace(/\*\*([^*]+)\*\*/g, '$1');
}
