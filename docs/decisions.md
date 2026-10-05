# Decision Log

Record each decision when it is made: what was decided, why, who decided, and the date. Until a row says "Decided", treat the item as open and propose options rather than assuming.

| # | Question | Status | Decision | Rationale | Owner | Date |
|---|----------|--------|----------|-----------|-------|------|
| 1 | Grocery price data source | Open | | Demo is in Boston/Cambridge; Kroger (original candidate) has no New England stores. Researching sources with verified Boston-area coverage. Stubbed behind `get_price` adapter meanwhile. | Team | |
| 2 | Cost estimate accuracy target and how to show uncertainty to users | Decided | Each item tagged `store price` or `estimate`; trip cost and per-meal cost totals always shown as approximate ("~$") | Prices vary by store and over time; per-item tags show where a number came from, totals stay honest | Team | 2026-10-05 |
| 3 | Macronutrient data source | Decided | USDA FoodData Central (Foundation/SR Legacy; Branded only for named products), fdcId mappings cached | Free, authoritative, generic-ingredient coverage | Team | 2026-10-05 |
| 4 | Ingredient extraction approach from a pasted link | Decided | yt-dlp metadata/caption -> ffmpeg audio + faster-whisper (local) transcription -> sampled frames to Claude vision; stop early when complete. TikTok required for demo, Instagram best effort | Captions often lack ingredients; staged pipeline minimizes cost/time; Instagram often requires login | Team | 2026-10-05 |
| 5 | Fallback when a link has no usable ingredient info or platform access fails | Decided | Clear error plus a paste box for caption/ingredient text, which enters the pipeline at the merge step. Never invent ingredients | Keeps the flow usable when platforms block access | Team | 2026-10-05 |
| 6 | Web app tech stack | Decided | Next.js (TypeScript) frontend + Python FastAPI backend; Claude API for structuring; no auth this sprint (DB amended by #9: SQLite cache only) | Extraction pipeline is the main risk and fits Python tooling; team has Python experience; MVP flow is stateless | | 2026-10-05 |
| 7 | Verify established alternatives (Samsung Food, Paprika, AnyList, Plan to Eat) | Open | | | | |
| 8 | Hosting for frontend and backend | Partly decided | Frontend on Vercel; backend on a long-running host (Render, Railway, or Fly.io; specific host open) | Video download and transcription exceed typical serverless time limits | Team | 2026-10-05 |
| 9 | Caching / storage | Decided | SQLite cache for extraction results (by canonical URL) and fdcId mappings; demo reels committed as JSON fixtures loaded at startup. No accounts or user data | Repeat pastes return instantly; demo must not depend on platform availability or a persistent disk | Team | 2026-10-05 |
| 10 | Core flow steps | Decided | Add ZIP code step and pantry checkoff step; results show trip cost and per-meal cost side by side | Checkoff catches extraction errors and makes trip cost meaningful; ZIP enables local pricing | Team | 2026-10-05 |
| 11 | Platform terms of service review (TikTok, Instagram) | Open | | Required before relying on content download | Team | |
| 12 | API shape for long-running extraction | Decided | Background job + polling: `POST /recipes` returns a job, `GET /jobs/{id}` reports the stage, `POST /recipes/{id}/plan` builds results | Simpler to build and host than server-sent events or websockets; extraction takes 30–90s | Team | 2026-10-05 |

## Notes on open items

- **1 Prices:** Kroger's Developer API (Locations by ZIP, per-store Products prices) was proposed but cannot cover a Boston demo. Candidate sources must be verified for Boston-area coverage and access terms before being listed here. If no source has coverage, fall back to clearly labeled estimates.
- **4-5 Extraction:** Some reels do not list ingredients in captions or descriptions, and platform access may be restricted. Terms of service review is tracked as #11.
- **8 Hosting:** Video download and transcription may exceed serverless time limits, which affects where the backend runs.
- Candidate options for each item should be researched and verified before they are written here. Do not record an option as fact without a source.
