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
| 8 | Hosting for frontend and backend | Decided (pending spike) | Frontend on Vercel. Backend on Render's free tier (`render.yaml`, Virginia). Vercel Services rejected: functions don't share memory or allow long runtimes. Frontend forwards `/api/*` to the backend via `BACKEND_URL` | Free for a low-traffic class demo. Paid always-on options compared: Fly.io ~$13.55/mo, Railway ~$22/mo, Render 1c-2g ~$25/mo (unconfirmed). Free tier limits: 512 MB RAM, sleeps after 15 min idle (~1 min to wake), disk wiped on restart | Team | 2026-10-05 |
| 9 | Caching / storage | Decided (amended) | SQLite cache is best-effort: on Render free the disk is wiped on every restart, redeploy, or spin-down. Demo reels are committed as JSON fixtures loaded at startup, so the demo doesn't depend on the cache. No accounts or user data | Free hosting has no persistent disk; fixtures already cover demo reliability | Team | 2026-10-05 |
| 10 | Core flow steps | Decided | Add ZIP code step and pantry checkoff step; results show trip cost and per-meal cost side by side | Checkoff catches extraction errors and makes trip cost meaningful; ZIP enables local pricing | Team | 2026-10-05 |
| 11 | Platform terms of service review (TikTok, Instagram) | Open | | Required before relying on content download | Team | |
| 12 | API shape for long-running extraction | Decided | Background job + polling: `POST /recipes` returns a job, `GET /jobs/{id}` reports the stage, `POST /recipes/{id}/plan` builds results | Simpler to build and host than server-sent events or websockets; extraction takes 30–90s | Team | 2026-10-05 |
| 13 | Transcription model size on the free tier | Open | | `faster-whisper` small used 1,477 MB (int8, CPU) in its README benchmark, too much for 512 MB. Spike: measure `tiny` and `base` on Render free. If neither fits, drop the audio stage for the MVP (caption + on-screen text + paste fallback) | Team | |

## Notes on open items

- **1 Prices:** Kroger's Developer API (Locations by ZIP, per-store Products prices) was proposed but cannot cover a Boston demo. Candidate sources must be verified for Boston-area coverage and access terms before being listed here. If no source has coverage, fall back to clearly labeled estimates.
- **4-5 Extraction:** Some reels do not list ingredients in captions or descriptions, and platform access may be restricted. Terms of service review is tracked as #11.
- **8 Hosting:** If the free tier proves too small or too slow, the cheapest always-on fallback found is Fly.io shared-cpu-1x 2 GB (~$13.39/mo, must set `auto_stop_machines = "off"`). Running the demo backend on a laptop is the free fallback that keeps full memory.
- Candidate options for each item should be researched and verified before they are written here. Do not record an option as fact without a source.
