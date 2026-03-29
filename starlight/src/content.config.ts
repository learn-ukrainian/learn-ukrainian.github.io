import { defineCollection, z } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
	docs: defineCollection({
		loader: docsLoader(),
		schema: docsSchema({
			extend: z.object({
				// Build pipeline metadata — used by v6_build.py, safe to ignore in rendering
				pipeline: z.string().optional(),
				build_status: z.string().optional(),
			}),
		}),
	}),
};
