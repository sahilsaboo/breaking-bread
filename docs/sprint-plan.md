# Sprint Plan

Proposed build plan for the three-week sprint. Scope and requirements live in `docs/technical-spec.md`; decisions live in `docs/decisions.md`. Items marked **Open** below still need team sign-off.

## Approach: walking skeleton first

Get a stubbed version of the whole flow working end to end in week 1, then replace each stub with the real stage. The app should run end to end from about day 3, and each track can then deepen its stage without blocking the others.

## Architecture

**Contract first.** On day 1, write the Pydantic models from the schema in `technical-spec.md`. Generate the frontend's TypeScript types from FastAPI's OpenAPI output so the two sides share one source of truth.

**API shape (Open: polling vs. streaming).** Extraction takes 30–90 seconds, so it runs as a background job:

| Endpoint | Purpose |
|---|---|
| `POST /recipes` (link or pasted text) | Starts extraction and returns a `job_id` |
| `GET /jobs/{id}` | Returns the current stage, and the recipe when it's ready. The frontend polls every 1–2 seconds |
| `POST /recipes/{id}/plan` (ZIP code, owned ingredients) | Returns the grocery list, costs, macros, and steps |

Polling is proposed because it is simpler to build and deploy than server-sent events or websockets.

**Backend steps.** `extract → structure → plan` (price matching, cost math, macros, guidance). Each step is its own module, and each external service sits behind its own adapter.

**Layout (Open: confirm).** `frontend/` and `backend/` side by side in this repo, as `CLAUDE.md` assumes.

## Tracks

Owners are **Open**.

| Track | Owner | Owns |
|---|---|---|
| **A. Extraction** | TBD | Caption, audio, and frame stages; paste-text fallback; Claude structuring; SQLite cache |
| **B. Pricing, macros, and math** | TBD | Unit conversion and cost/macro math (with tests); USDA adapter; ingredient-to-product matching; pricing source research |
| **C. Frontend and guidance** | TBD | All five screens, progress display, timers, and term definitions; the guidance-generation prompt; deployment |

## Timeline

### Week 1: skeleton running, early answers to risky questions
- [ ] Set up the repo, Pydantic models, a stubbed API, and generated TypeScript types
- [ ] All five screens built against a sample result
- [ ] Caption extraction (`yt-dlp` metadata) and the paste-text fallback working for real
- [ ] Unit conversion and cost math, with tests
- [ ] USDA FoodData Central adapter
- [ ] **Spike: pricing source** for Boston coverage, ending in a decision for `decisions.md` #1
- [ ] **Spike: backend host.** Deploy `yt-dlp`, `ffmpeg`, and `faster-whisper` and confirm they fit its memory and time limits (#8)
- [ ] **Spike: TikTok access from a cloud server.** Check whether `yt-dlp` is blocked from datacenter IPs
- [ ] Terms-of-service review for TikTok and Instagram (#11)

### Week 2: make each stage real
- [ ] Audio stage (`ffmpeg` + `faster-whisper`) and frame stage (Claude vision)
- [ ] Merge step, with `source` and `confidence` on every ingredient
- [ ] Pricing adapter (the chosen source, or a labeled estimate table) and product matching with package sizes
- [ ] Macro math, with tests
- [ ] Guidance generation meeting all four beginner rules; timers and term definitions in the UI
- [ ] SQLite cache, error states, and full integration

### Week 3: get ready for the demo
- [ ] Choose the demo reels, including one whose caption has no ingredients
- [ ] Run each demo reel through the full pipeline several times and commit the results as fixtures
- [ ] Bug fixes, beginner-friendly copy pass, and final deployment
- [ ] Two full demo rehearsals
- [ ] Stretch goal (map of nearby stores), only if everything above is done

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| TikTok blocks `yt-dlp` from cloud servers | Live extraction fails even though it works locally | Committed demo fixtures, paste-text fallback, and running the demo backend locally if needed |
| `faster-whisper` on a small host | Out of memory or slow transcription | Start with the `base` or `small` model; measure during the week 1 host spike |
| No pricing source with Boston coverage | No real store prices | Clearly labeled estimated prices, so the flow never stalls |
