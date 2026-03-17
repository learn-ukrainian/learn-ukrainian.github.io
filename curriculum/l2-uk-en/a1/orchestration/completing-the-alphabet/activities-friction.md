**Phase**: Phase 3: Activities + Vocabulary
**Step**: watch-and-repeat generation
**Friction Type**: PLAN_GAP
**Raw Error**: Plan specifies 10 watch-and-repeat items covering Ь, Ц, Ч, Щ, ДЖ, ДЗ but only 6 video URLs are available in pronunciation_videos.letters (Ь, Ц, Ч, Щ, Ф, Ґ). No dedicated videos for digraphs ДЖ and ДЗ.
**Self-Correction**: Generated 6 items using available videos. Added anagram activity to compensate for lower watch-and-repeat count and reach 8 total activities.
**Proposed Tooling Fix**: Pipeline preflight should validate that activity_hints item counts for watch-and-repeat do not exceed available video URLs in pronunciation_videos.