import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export const collections = {
	docs: defineCollection({
		loader: glob({
			pattern: [
				'{a1,a2,folk}/**/*.{md,mdx}',
				'{b1,b2}/**/*.{md,mdx}',
				'{bio,c1,c2,hist,istorio,lit,lit-drama,lit-essay,lit-fantastika,lit-hist-fic,lit-humor,lit-war,lit-youth,oes,ruth}/index.{md,mdx}',
			],
			base: './src/content/docs',
		}),
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
	// Хрестоматія — a global, cross-track library of full primary-source texts
	// (думи, колядки, Шевченко, chronicles, …). NOT per-track: any lesson in any
	// seminar references a reading the way lessons reference Word Atlas words.
	// Lives OUTSIDE docs/ so the MDX↔source parity gate (which scans docs/) skips it.
	readings: defineCollection({
		loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/readings' }),
		schema: z.object({
			title: z.string(),
			title_en: z.string().optional(),
			author: z.string().optional(),
			collector: z.string().optional(),
			year: z.string().optional(),
			period: z.string().optional(),
			genre: z.string(),
			tracks: z.array(z.string()).default([]),
			taught_in: z.array(z.string()).default([]),
			excerpt: z.string(),
			source: z.string(),
			source_url: z.string().url().optional(),
			public_domain: z.literal(true).optional(),
			published: z.boolean().default(true),
			canonical: z.boolean().default(true),
			order: z.number().optional(),
		}).passthrough().superRefine((reading, ctx) => {
			if (reading.published !== false && reading.public_domain !== true) {
				ctx.addIssue({
					code: z.ZodIssueCode.custom,
					path: ['public_domain'],
					message: 'Published readings require public_domain: true.',
				});
			}
		}),
	}),
};
