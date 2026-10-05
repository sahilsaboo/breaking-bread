# Breaking Bread

AI-powered cooking companion (web app) for college students early in off-campus apartment life who are new to cooking. A user pastes a TikTok or reel link and gets a meal they can shop for, afford, and cook.

Full context: `docs/product-brief.md`. Build spec (pipeline, cost rules, schema, guidance rules): `docs/technical-spec.md`. Decisions and open questions: `docs/decisions.md`.

## Sprint MVP (three weeks): one end-to-end flow
Pasted TikTok/reel link -> ingredients extracted -> ZIP code -> user checks off ingredients they own -> grocery list with prices, trip cost and per-meal cost -> per-serving macros -> step-by-step beginner cooking guidance. Delivered as a web app. TikTok must work for the demo; Instagram Reels is best effort.

Success = this flow works reliably end to end. Prioritize work that completes the flow over polishing any one step.

## Scope rules
- Stretch goal only: nearby stores where the user can buy ingredients. Don't start it until the core flow works.
- Out of scope: built-in recipe library, fridge/pantry "what can I make" workflow, recommendations based on goals/likes/dislikes, weekly spend tracking, direct ordering or checkout, native mobile app.
- If a request drifts into an out-of-scope item, say so before doing the work.

## Product principles
- Differentiator is integrated budgeting plus beginner guidance. Macros are supporting value.
- When design choices conflict, favor cost clarity and simplicity.
- All user-facing copy and guidance must be beginner-friendly: plain words, no assumed kitchen knowledge, short steps.
- Cost is always an estimate. Each item's price is tagged `store price` or `estimate`, and totals are always shown as approximate (e.g. "~$8.40"), never as exact.

## Open decisions: do not assume answers
These are unresolved (see `docs/decisions.md`). Propose options with tradeoffs and ask before committing:
- Grocery price data source (demo is in Boston/Cambridge, where Kroger has no stores). Research and verify Boston-area coverage before proposing a source.
- Transcription model size that fits in 512 MB (`docs/decisions.md` #13)
- TikTok and Instagram terms of service for content download
When a decision is made, record it in `docs/decisions.md`.

## Tech stack
- Frontend: Next.js (TypeScript) in `frontend/`. UI only: link input, results view (grocery list, cost, macros), step-by-step cooking view.
- Backend: Python FastAPI in `backend/`. Owns the whole pipeline: link -> content extraction -> Claude API structuring -> price and macro lookup -> response.
- Extraction: `yt-dlp` metadata/caption first, then `ffmpeg` audio + `faster-whisper` transcription, then sampled frames to Claude vision; stop early once the recipe is complete.
- LLM: Claude API. Ask for JSON and validate it against Pydantic models. One shared schema (see `docs/technical-spec.md`) covers ingredients, grocery list, cost, macros, and steps.
- Macros: USDA FoodData Central, behind a `get_macros` adapter.
- Prices: behind a `get_price` adapter, stubbed until the source is decided. Don't hardcode a vendor.
- Cache: SQLite for extraction results (by canonical URL) and USDA `fdcId` mappings, best-effort because the free host wipes its disk. Demo reels are committed as JSON fixtures loaded at startup. No auth, accounts, or stored user data; flag it before adding any.
- Required fallback: when link extraction fails, show a clear error and let the user paste caption or ingredient text.
- Hosting: frontend on Vercel; backend on Render's free tier via `render.yaml` (512 MB RAM, sleeps after 15 min idle, disk wiped on restart). Not Vercel Services: backend functions don't share memory or allow long-running extraction. Keep backend memory use under 512 MB.
- Routing: every backend route lives under `/api`. The browser only calls `/api/*` on the frontend's own domain, and `frontend/next.config.ts` forwards it to `BACKEND_URL` (default http://localhost:8000).

## Conventions
- Frontend talks to the backend over HTTP/JSON only. No business logic in the frontend.
- Secrets (API keys) live in `.env` files and are never committed.
- Keep the backend pipeline as separate, testable steps (extract, structure, price, macros, guidance) so each can be swapped or debugged alone.

## Commands
- Backend setup (Python 3.12): `cd backend && python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"`
- Backend dev server: `cd backend && .venv/bin/uvicorn app.main:app --reload` (http://localhost:8000, docs at /api/docs)
- Backend tests: `cd backend && .venv/bin/pytest`
- Windows: the venv lives at `.venv\Scripts\` instead of `.venv/bin/` (see README "On Windows"). Always pass `encoding="utf-8"` when reading or writing text files; Windows defaults to cp1252.
- Frontend: `cd frontend && npm install && npm run dev` (http://localhost:3000)
- Frontend checks: `cd frontend && npm run lint && npx tsc --noEmit`
- After changing `backend/app/models.py` or routes: `cd backend && .venv/bin/python scripts/export_openapi.py`, then `cd frontend && npm run gen:api`. Commit both `backend/openapi.json` and `frontend/src/lib/api-types.ts`.

## Current state (walking skeleton)
- Every pipeline stage is a stub backed by `backend/app/fixtures/sample_recipe.json`. Stub code is marked `STUB:`.
- Extraction progress is simulated (one stage every `STUB_STAGE_SECONDS`). A link containing `stub-fail` fails on purpose, to exercise the error and paste-text fallback.
- Jobs and recipes live in memory and disappear on restart, until the SQLite cache lands.
- Cost math in `backend/app/costs.py` is real and tested. Prices themselves are stub estimates.
- Keep the repo outside iCloud-synced folders such as `~/Documents`: syncing `.venv` and `node_modules` makes imports and tests hang.

## Team
Sarah Fattah, Sahil Saboo, Brendan Shemer (AI Builder Space Proseminar).
