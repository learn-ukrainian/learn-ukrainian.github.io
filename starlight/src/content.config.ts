import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export const collections = {
	docs: defineCollection({
		loader: glob({ pattern: '{a1,a2,folk}/**/*.{md,mdx}', base: './src/content/docs' }),
		schema: z.object({
			title: z.string(),
			description: z.string().optional(),
			template: z.string().optional(),
			sidebar: z.object({
				order: z.number().optional(),
				label: z.string().optional(),
			}).optional(),
			prev: z.union([z.string(), z.boolean()]).optional(),
			next: z.union([z.string(), z.boolean()]).optional(),
			draft: z.boolean().optional(),
			pipeline: z.string().optional(),
			build_status: z.string().optional(),
		}).passthrough(),
	}),
};
