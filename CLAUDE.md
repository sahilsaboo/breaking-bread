# Breaking Bread

AI-powered cooking companion (web app) for college students early in off-campus apartment life who are new to cooking. A user pastes a TikTok or reel link and gets a meal they can shop for, afford, and cook.

Full context: `docs/product-brief.md`. Decisions and open questions: `docs/decisions.md`.

## Sprint MVP (three weeks): one end-to-end flow
Pasted TikTok/reel link -> ingredients identified -> grocery list -> estimated meal cost -> per-meal macros -> step-by-step beginner cooking guidance. Delivered as a web app.

Success = this flow works reliably end to end. Prioritize work that completes the flow over polishing any one step.

## Scope rules
- Stretch goal only: nearby stores where the user can buy ingredients. Don't start it until the core flow works.
- Out of scope: built-in recipe library, fridge/pantry "what can I make" workflow, recommendations based on goals/likes/dislikes, weekly spend tracking, direct ordering or checkout, native mobile app.
- If a request drifts into an out-of-scope item, say so before doing the work.

## Product principles
- Differentiator is integrated budgeting plus beginner guidance. Macros are supporting value.
- When design choices conflict, favor cost clarity and simplicity.
- All user-facing copy and guidance must be beginner-friendly: plain words, no assumed kitchen knowledge, short steps.
- Cost is always an estimate. Show it as approximate and never present it as exact.

## Open decisions: do not assume answers
These are unresolved (see `docs/decisions.md`). Propose options with tradeoffs and ask before committing:
- Grocery price data source, and how accurate cost estimates can be
- Macronutrient data source
- Reliability of ingredient extraction from links (captions may lack ingredients; platform access and terms of service may restrict it)
- Hosting for frontend and backend
When a decision is made, record it in `docs/decisions.md`.

## Tech stack
- Frontend: Next.js (TypeScript) in `frontend/`. UI only: link input, results view (grocery list, cost, macros), step-by-step cooking view.
- Backend: Python FastAPI in `backend/`. Owns the whole pipeline: link -> content extraction -> Claude API structuring -> price and macro lookup -> response.
- LLM: Claude API. Ask for JSON and validate it against Pydantic models. One shared schema covers ingredients, grocery list, cost, macros, and steps.
- Price and macro data: behind adapter interfaces (e.g. `get_price(item)`, `get_macros(item)`), stubbed until sources are decided. Don't hardcode a vendor.
- No database or auth this sprint. The flow is stateless. Flag it before adding either.
- Required fallback: the user can paste caption or ingredient text when link extraction fails.

## Conventions
- Frontend talks to the backend over HTTP/JSON only. No business logic in the frontend.
- Secrets (API keys) live in `.env` files and are never committed.
- Keep the backend pipeline as separate, testable steps (extract, structure, price, macros, guidance) so each can be swapped or debugged alone.

## Commands
TODO: confirm after scaffolding. Expected defaults:
- Frontend: `cd frontend && npm run dev`
- Backend: `cd backend && uvicorn app.main:app --reload`

## Team
Sarah Fattah, Sahil Saboo, Brendan Shemer (AI Builder Space Proseminar).
