export interface RichnessGuidelines {
    wordCount: number;
    activityCount: number;
    itemsPerActivity: number;
}

export const RICHNESS_GUIDELINES: Record<string, RichnessGuidelines> = {
    A1: { wordCount: 750, activityCount: 8, itemsPerActivity: 12 },
    A2: { wordCount: 1000, activityCount: 10, itemsPerActivity: 12 },
    B1: { wordCount: 1250, activityCount: 12, itemsPerActivity: 14 },
    B2: { wordCount: 1500, activityCount: 14, itemsPerActivity: 16 },
    C1: { wordCount: 1750, activityCount: 16, itemsPerActivity: 18 },
    C2: { wordCount: 2000, activityCount: 16, itemsPerActivity: 18 },
};

/**
 *
 */
export function getGuidelinesForLevel(level: string): RichnessGuidelines {
    const upperLevel = level.toUpperCase();
    // Default to A1 if not found or if checking 'A1' explicitly
    return RICHNESS_GUIDELINES[upperLevel] || RICHNESS_GUIDELINES['A1'];
}

/**
 *
 */
export function detectLevelFromPath(filePath: string): string {
    const match = filePath.match(/\/(a1|a2|b1|b2|c1|c2)\//i);
    return match ? match[1].toUpperCase() : 'A1';
}
